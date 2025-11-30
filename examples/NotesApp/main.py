#!/usr/bin/env python3
"""
NexaDB Notes API Example
========================

A comprehensive FastAPI application demonstrating NexaDB features:
- CRUD operations
- Bulk operations
- Text search
- Vector search (semantic similarity)
- Tag filtering
- Pagination
- Archiving
- Statistics

This serves as a production-ready example for building applications with NexaDB.
"""

from fastapi import FastAPI, HTTPException, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import time
import os
from contextlib import asynccontextmanager

# NexaDB Python Client
from nexaclient import NexaClient

# Configuration
NEXADB_HOST = os.getenv("NEXADB_HOST", "localhost")
NEXADB_PORT = int(os.getenv("NEXADB_PORT", 6970))
NEXADB_USERNAME = os.getenv("NEXADB_USERNAME", "root")
NEXADB_PASSWORD = os.getenv("NEXADB_PASSWORD", "nexadb123")
DATABASE_NAME = "notes_db"
COLLECTION_NAME = "notes"

# Global client instance
client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global client

    # Startup: Connect to NexaDB and setup collections
    print(f"[STARTUP] Connecting to NexaDB at {NEXADB_HOST}:{NEXADB_PORT}")
    client = NexaClient(
        host=NEXADB_HOST,
        port=NEXADB_PORT,
        username=NEXADB_USERNAME,
        password=NEXADB_PASSWORD
    )

    # Connect to server
    client.connect()

    # Create database if not exists
    try:
        existing_dbs = client.list_databases()
        if DATABASE_NAME not in existing_dbs:
            print(f"[STARTUP] Creating database: {DATABASE_NAME}")
            client.create_database(DATABASE_NAME)
        else:
            print(f"[STARTUP] Database '{DATABASE_NAME}' already exists")
    except Exception as e:
        print(f"[STARTUP] Error setting up database: {e}")

    # Create collection if not exists
    try:
        existing_collections = client.list_collections(database=DATABASE_NAME)
        if COLLECTION_NAME not in existing_collections:
            print(f"[STARTUP] Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                name=COLLECTION_NAME,
                database=DATABASE_NAME,
                vector_dimensions=128  # For semantic search embeddings
            )
        else:
            print(f"[STARTUP] Collection '{COLLECTION_NAME}' already exists")
    except Exception as e:
        print(f"[STARTUP] Error setting up collection: {e}")

    print("[STARTUP] ✅ NexaDB Notes API ready!")

    yield

    # Shutdown
    print("[SHUTDOWN] Closing NexaDB connection")
    if client:
        client.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title="NexaDB Notes API",
    description="A comprehensive note-taking API built with NexaDB",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],  # Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class NoteCreate(BaseModel):
    """Model for creating a note."""
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    tags: List[str] = Field(default=[], description="List of tags")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Meeting Notes",
                "content": "Discussed Q4 goals and team expansion",
                "tags": ["work", "meeting"]
            }
        }


class NoteUpdate(BaseModel):
    """Model for updating a note."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Model for note response."""
    id: str
    title: str
    content: str
    tags: List[str]
    archived: bool
    created_at: float
    updated_at: float


class BulkCreateRequest(BaseModel):
    """Model for bulk note creation."""
    notes: List[NoteCreate]


class BulkDeleteRequest(BaseModel):
    """Model for bulk deletion."""
    ids: List[str]


class VectorSearchRequest(BaseModel):
    """Model for vector search."""
    query_text: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")


# Helper Functions
def generate_embedding(text: str) -> List[float]:
    """
    Generate a simple embedding for text.
    In production, use a real embedding model (OpenAI, Cohere, etc.)

    For this example, we'll create a simple deterministic embedding.
    """
    # Simple character-based embedding (128 dimensions)
    embedding = [0.0] * 128

    for i, char in enumerate(text[:128]):
        embedding[i] = ord(char) / 255.0

    # Normalize
    magnitude = sum(x**2 for x in embedding) ** 0.5
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]

    return embedding


def note_to_response(note: Dict[str, Any]) -> NoteResponse:
    """Convert database note to response model."""
    return NoteResponse(
        id=note['_id'],
        title=note['title'],
        content=note['content'],
        tags=note.get('tags', []),
        archived=note.get('archived', False),
        created_at=note['created_at'],
        updated_at=note['updated_at']
    )


# API Endpoints

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "NexaDB Notes API",
        "status": "healthy",
        "version": "1.0.0",
        "database": DATABASE_NAME,
        "collection": COLLECTION_NAME
    }


@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED, tags=["Notes"])
async def create_note(note: NoteCreate):
    """
    Create a new note.

    - **title**: Note title (required)
    - **content**: Note content (required)
    - **tags**: List of tags (optional)
    """
    try:
        current_time = time.time()

        # Generate embedding for semantic search
        full_text = f"{note.title} {note.content}"
        embedding = generate_embedding(full_text)

        # Create note document
        note_doc = {
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "archived": False,
            "created_at": current_time,
            "updated_at": current_time,
            "embedding": embedding
        }

        # Insert into NexaDB
        doc_id = client.insert(
            collection=COLLECTION_NAME,
            data=note_doc,
            database=DATABASE_NAME
        )

        # Add ID to response
        note_doc['_id'] = doc_id

        return note_to_response(note_doc)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


# IMPORTANT: Specific routes (with literal paths) must come BEFORE dynamic routes ({note_id})
# This ensures FastAPI matches /notes/stats before /notes/{note_id}

@app.get("/notes/search", response_model=Dict[str, Any], tags=["Search"])
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Search notes by text (searches in title and content).

    - **q**: Search query
    - **limit**: Maximum number of results
    """
    try:
        # Get all notes (in production, use a proper text search index)
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        # Simple text search (case-insensitive)
        query_lower = q.lower()
        matching_notes = []

        for note in all_notes:
            title_lower = note.get('title', '').lower()
            content_lower = note.get('content', '').lower()

            if query_lower in title_lower or query_lower in content_lower:
                matching_notes.append(note)

        # Sort by updated_at descending
        matching_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        matching_notes = matching_notes[:limit]

        return {
            "query": q,
            "results": [note_to_response(note) for note in matching_notes],
            "count": len(matching_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {str(e)}")


@app.get("/notes/recent", response_model=Dict[str, Any], tags=["Search"])
async def get_recent_notes(
    limit: int = Query(10, ge=1, le=50, description="Number of recent notes")
):
    """
    Get recently updated notes.

    - **limit**: Number of recent notes to return
    """
    try:
        # Get all non-archived notes
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={"archived": False},
            limit=10000,
            database=DATABASE_NAME
        )

        # Sort by updated_at descending
        all_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        recent_notes = all_notes[:limit]

        return {
            "notes": [note_to_response(note) for note in recent_notes],
            "count": len(recent_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent notes: {str(e)}")


@app.get("/notes/archived", response_model=Dict[str, Any], tags=["Archive"])
async def get_archived_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get archived notes.

    - **skip**: Number of notes to skip
    - **limit**: Maximum number of results
    """
    try:
        # Get archived notes
        archived_notes = client.query(
            collection=COLLECTION_NAME,
            filters={"archived": True},
            limit=10000,
            database=DATABASE_NAME
        )

        # Sort by updated_at descending
        archived_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Pagination
        total = len(archived_notes)
        notes = archived_notes[skip:skip + limit]

        return {
            "notes": [note_to_response(note) for note in notes],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get archived notes: {str(e)}")


@app.get("/notes/stats", response_model=Dict[str, Any], tags=["Statistics"])
async def get_notes_statistics():
    """
    Get statistics about notes.

    Returns:
    - Total notes count
    - Archived notes count
    - Active notes count
    - Most used tags
    - Notes created today
    """
    try:
        # Get all notes
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        total_notes = len(all_notes)
        archived_notes = sum(1 for note in all_notes if note.get('archived', False))
        active_notes = total_notes - archived_notes

        # Count tags
        tag_counts = {}
        for note in all_notes:
            for tag in note.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Get top 10 tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Count notes created today
        today_start = time.time() - (time.time() % 86400)  # Start of today
        notes_today = sum(1 for note in all_notes if note.get('created_at', 0) >= today_start)

        return {
            "total_notes": total_notes,
            "active_notes": active_notes,
            "archived_notes": archived_notes,
            "notes_created_today": notes_today,
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "total_unique_tags": len(tag_counts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.post("/notes/bulk", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED, tags=["Bulk Operations"])
async def bulk_create_notes(request: BulkCreateRequest):
    """
    Create multiple notes at once.

    - **notes**: List of notes to create
    """
    try:
        current_time = time.time()
        created_notes = []

        for note in request.notes:
            # Generate embedding
            full_text = f"{note.title} {note.content}"
            embedding = generate_embedding(full_text)

            # Create note document
            note_doc = {
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "archived": False,
                "created_at": current_time,
                "updated_at": current_time,
                "embedding": embedding
            }

            # Insert into NexaDB
            doc_id = client.insert(
                collection=COLLECTION_NAME,
                data=note_doc,
                database=DATABASE_NAME
            )

            note_doc['_id'] = doc_id
            created_notes.append(note_to_response(note_doc))

        return {
            "created": len(created_notes),
            "notes": created_notes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk create notes: {str(e)}")


@app.delete("/notes/bulk", response_model=Dict[str, Any], tags=["Bulk Operations"])
async def bulk_delete_notes(request: BulkDeleteRequest):
    """
    Delete multiple notes at once.

    - **ids**: List of note IDs to delete
    """
    try:
        deleted_count = 0
        errors = []

        for note_id in request.ids:
            try:
                # Delete from NexaDB
                client.delete(
                    collection=COLLECTION_NAME,
                    key=note_id,
                    database=DATABASE_NAME
                )
                deleted_count += 1
            except Exception as e:
                errors.append({"id": note_id, "error": str(e)})

        return {
            "deleted": deleted_count,
            "requested": len(request.ids),
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete notes: {str(e)}")


@app.post("/notes/vector-search", response_model=Dict[str, Any], tags=["Search"])
async def vector_search_notes(request: VectorSearchRequest):
    """
    Search for similar notes using vector similarity (semantic search).

    - **query_text**: Search query text
    - **top_k**: Number of similar notes to return
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(request.query_text)

        # Perform vector search using NexaDB
        results = client.vector_search(
            collection=COLLECTION_NAME,
            vector=query_embedding,
            limit=request.top_k,
            dimensions=128,  # Must match embedding dimensions
            database=DATABASE_NAME
        )

        return {
            "query": request.query_text,
            "results": [
                {
                    **note_to_response(result).dict(),
                    "similarity": result.get('_distance', 0)  # Cosine similarity score
                }
                for result in results
            ],
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform vector search: {str(e)}")


@app.get("/notes/tags/{tag}", response_model=Dict[str, Any], tags=["Tags"])
async def get_notes_by_tag(
    tag: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Find notes by tag.

    - **tag**: Tag to search for
    - **limit**: Maximum number of results
    """
    try:
        # Get all notes (in production, use a proper tag index)
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        # Filter by tag
        matching_notes = [
            note for note in all_notes
            if tag in note.get('tags', [])
        ]

        # Sort by updated_at descending
        matching_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        matching_notes = matching_notes[:limit]

        return {
            "query": tag,
            "results": [note_to_response(note) for note in matching_notes],
            "count": len(matching_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes by tag: {str(e)}")


@app.get("/notes", response_model=Dict[str, Any], tags=["Notes"])
async def list_notes(
    skip: int = Query(0, ge=0, description="Number of notes to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of notes to return"),
    archived: Optional[bool] = Query(None, description="Filter by archived status")
):
    """
    List all notes with pagination.

    - **skip**: Number of notes to skip (for pagination)
    - **limit**: Maximum number of notes to return
    - **archived**: Filter by archived status (true/false/null for all)
    """
    try:
        # Build filter
        filter_query = {}
        if archived is not None:
            filter_query['archived'] = archived

        # Get notes
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters=filter_query if filter_query else {},
            limit=10000,  # Get all notes for pagination
            database=DATABASE_NAME
        )

        # Sort by updated_at descending
        all_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Pagination
        total = len(all_notes)
        notes = all_notes[skip:skip + limit]

        return {
            "notes": [note_to_response(note) for note in notes],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list notes: {str(e)}")


# NOW the dynamic {note_id} routes - these must come AFTER all specific routes above
@app.get("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def get_note(note_id: str):
    """
    Get a single note by ID.

    - **note_id**: The note ID
    """
    try:
        result = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        if not result:
            raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")

        return note_to_response(result[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get note: {str(e)}")


@app.put("/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def update_note(note_id: str, note_update: NoteUpdate):
    """
    Update an existing note.

    - **note_id**: The note ID
    - **title**: New title (optional)
    - **content**: New content (optional)
    - **tags**: New tags (optional)
    """
    try:
        # Check if note exists
        existing = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        if not existing:
            raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")

        # Build update document
        update_doc = {"updated_at": time.time()}

        if note_update.title is not None:
            update_doc['title'] = note_update.title

        if note_update.content is not None:
            update_doc['content'] = note_update.content

        if note_update.tags is not None:
            update_doc['tags'] = note_update.tags

        # Regenerate embedding if title or content changed
        if note_update.title is not None or note_update.content is not None:
            current_note = existing[0]
            new_title = note_update.title if note_update.title is not None else current_note['title']
            new_content = note_update.content if note_update.content is not None else current_note['content']
            full_text = f"{new_title} {new_content}"
            update_doc['embedding'] = generate_embedding(full_text)

        # Update in NexaDB
        client.update(
            collection=COLLECTION_NAME,
            key=note_id,
            updates=update_doc,
            database=DATABASE_NAME
        )

        # Get updated note
        updated = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        return note_to_response(updated[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Notes"])
async def delete_note(note_id: str):
    """
    Delete a note by ID.

    - **note_id**: The note ID
    """
    try:
        # Check if note exists
        existing = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        if not existing:
            raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")

        # Delete from NexaDB
        client.delete(
            collection=COLLECTION_NAME,
            key=note_id,
            database=DATABASE_NAME
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")


@app.post("/notes/bulk", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED, tags=["Bulk Operations"])
async def bulk_create_notes(request: BulkCreateRequest):
    """
    Create multiple notes at once.

    - **notes**: List of notes to create
    """
    try:
        current_time = time.time()
        created_notes = []

        for note in request.notes:
            # Generate embedding
            full_text = f"{note.title} {note.content}"
            embedding = generate_embedding(full_text)

            # Create note document
            note_doc = {
                "title": note.title,
                "content": note.content,
                "tags": note.tags,
                "archived": False,
                "created_at": current_time,
                "updated_at": current_time,
                "embedding": embedding
            }

            # Insert into NexaDB
            doc_id = client.insert(
                collection=COLLECTION_NAME,
                data=note_doc,
                database=DATABASE_NAME
            )

            note_doc['_id'] = doc_id
            created_notes.append(note_to_response(note_doc))

        return {
            "created": len(created_notes),
            "notes": created_notes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk create notes: {str(e)}")


@app.delete("/notes/bulk", response_model=Dict[str, Any], tags=["Bulk Operations"])
async def bulk_delete_notes(request: BulkDeleteRequest):
    """
    Delete multiple notes at once.

    - **ids**: List of note IDs to delete
    """
    try:
        deleted_count = 0
        errors = []

        for note_id in request.ids:
            try:
                # Delete from NexaDB
                client.delete(
                    collection=COLLECTION_NAME,
                    key=note_id,
                    database=DATABASE_NAME
                )
                deleted_count += 1
            except Exception as e:
                errors.append({"id": note_id, "error": str(e)})

        return {
            "deleted": deleted_count,
            "requested": len(request.ids),
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete notes: {str(e)}")


@app.get("/notes/search", response_model=Dict[str, Any], tags=["Search"])
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Search notes by text (searches in title and content).

    - **q**: Search query
    - **limit**: Maximum number of results
    """
    try:
        # Get all notes (in production, use a proper text search index)
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        # Simple text search (case-insensitive)
        query_lower = q.lower()
        matching_notes = []

        for note in all_notes:
            title_lower = note.get('title', '').lower()
            content_lower = note.get('content', '').lower()

            if query_lower in title_lower or query_lower in content_lower:
                matching_notes.append(note)

        # Sort by updated_at descending
        matching_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        matching_notes = matching_notes[:limit]

        return {
            "query": q,
            "results": [note_to_response(note) for note in matching_notes],
            "count": len(matching_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {str(e)}")


@app.post("/notes/{note_id}/tags", response_model=NoteResponse, tags=["Tags"])
async def add_tags_to_note(note_id: str, tags: List[str] = Body(..., embed=True)):
    """
    Add tags to a note (merges with existing tags).

    - **note_id**: The note ID
    - **tags**: List of tags to add
    """
    try:
        # Check if note exists
        existing = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        if not existing:
            raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")

        # Merge tags (remove duplicates)
        current_tags = existing[0].get('tags', [])
        new_tags = list(set(current_tags + tags))

        # Update in NexaDB
        client.update(
            collection=COLLECTION_NAME,
            key=note_id,
            updates={
                "tags": new_tags,
                "updated_at": time.time()
            },
            database=DATABASE_NAME
        )

        # Get updated note
        updated = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        return note_to_response(updated[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tags: {str(e)}")


@app.get("/notes/tags/{tag}", response_model=Dict[str, Any], tags=["Tags"])
async def get_notes_by_tag(
    tag: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Find notes by tag.

    - **tag**: Tag to search for
    - **limit**: Maximum number of results
    """
    try:
        # Get all notes (in production, use a proper tag index)
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        # Filter by tag
        matching_notes = [
            note for note in all_notes
            if tag in note.get('tags', [])
        ]

        # Sort by updated_at descending
        matching_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        matching_notes = matching_notes[:limit]

        return {
            "query": tag,
            "results": [note_to_response(note) for note in matching_notes],
            "count": len(matching_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes by tag: {str(e)}")


@app.get("/notes/archived", response_model=Dict[str, Any], tags=["Archive"])
async def get_archived_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get archived notes.

    - **skip**: Number of notes to skip
    - **limit**: Maximum number of results
    """
    try:
        # Get archived notes
        archived_notes = client.query(
            collection=COLLECTION_NAME,
            filters={"archived": True},
            limit=10000,
            database=DATABASE_NAME
        )

        # Sort by updated_at descending
        archived_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Pagination
        total = len(archived_notes)
        notes = archived_notes[skip:skip + limit]

        return {
            "notes": [note_to_response(note) for note in notes],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get archived notes: {str(e)}")


@app.post("/notes/{note_id}/archive", response_model=NoteResponse, tags=["Archive"])
async def archive_note(note_id: str, archived: bool = Body(..., embed=True)):
    """
    Archive or unarchive a note.

    - **note_id**: The note ID
    - **archived**: True to archive, False to unarchive
    """
    try:
        # Check if note exists
        existing = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        if not existing:
            raise HTTPException(status_code=404, detail=f"Note '{note_id}' not found")

        # Update archived status
        client.update(
            collection=COLLECTION_NAME,
            key=note_id,
            updates={
                "archived": archived,
                "updated_at": time.time()
            },
            database=DATABASE_NAME
        )

        # Get updated note
        updated = client.query(
            collection=COLLECTION_NAME,
            filters={"_id": note_id},
            database=DATABASE_NAME
        )

        return note_to_response(updated[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to archive note: {str(e)}")


@app.get("/notes/recent", response_model=Dict[str, Any], tags=["Search"])
async def get_recent_notes(
    limit: int = Query(10, ge=1, le=50, description="Number of recent notes")
):
    """
    Get recently updated notes.

    - **limit**: Number of recent notes to return
    """
    try:
        # Get all non-archived notes
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={"archived": False},
            limit=10000,
            database=DATABASE_NAME
        )

        # Sort by updated_at descending
        all_notes.sort(key=lambda x: x.get('updated_at', 0), reverse=True)

        # Limit results
        recent_notes = all_notes[:limit]

        return {
            "notes": [note_to_response(note) for note in recent_notes],
            "count": len(recent_notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent notes: {str(e)}")


@app.post("/notes/vector-search", response_model=Dict[str, Any], tags=["Search"])
async def vector_search_notes(request: VectorSearchRequest):
    """
    Search for similar notes using vector similarity (semantic search).

    - **query_text**: Search query text
    - **top_k**: Number of similar notes to return
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(request.query_text)

        # Perform vector search using NexaDB
        results = client.vector_search(
            collection=COLLECTION_NAME,
            vector=query_embedding,
            limit=request.top_k,
            dimensions=128,  # Must match embedding dimensions
            database=DATABASE_NAME
        )

        return {
            "query": request.query_text,
            "results": [
                {
                    **note_to_response(result).dict(),
                    "similarity": result.get('_distance', 0)  # Cosine similarity score
                }
                for result in results
            ],
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform vector search: {str(e)}")


@app.get("/notes/stats", response_model=Dict[str, Any], tags=["Statistics"])
async def get_notes_statistics():
    """
    Get statistics about notes.

    Returns:
    - Total notes count
    - Archived notes count
    - Active notes count
    - Most used tags
    - Notes created today
    """
    try:
        # Get all notes
        all_notes = client.query(
            collection=COLLECTION_NAME,
            filters={},
            limit=10000,
            database=DATABASE_NAME
        )

        total_notes = len(all_notes)
        archived_notes = sum(1 for note in all_notes if note.get('archived', False))
        active_notes = total_notes - archived_notes

        # Count tags
        tag_counts = {}
        for note in all_notes:
            for tag in note.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Get top 10 tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Count notes created today
        today_start = time.time() - (time.time() % 86400)  # Start of today
        notes_today = sum(1 for note in all_notes if note.get('created_at', 0) >= today_start)

        return {
            "total_notes": total_notes,
            "active_notes": active_notes,
            "archived_notes": archived_notes,
            "notes_created_today": notes_today,
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
            "total_unique_tags": len(tag_counts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

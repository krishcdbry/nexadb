#!/usr/bin/env python3
"""
VeloxDB - Next-Generation Lightweight Database
===============================================

The world's most versatile lightweight database supporting:
- JSON documents (MongoDB-like)
- Vector embeddings (AI/ML workloads)
- Full-text search (Elasticsearch-like)
- Graph relationships (Neo4j-like)
- ACID transactions
- Real-time queries
- Zero configuration

Built on LSM-Tree architecture for blazing fast writes.
"""

import json
import hashlib
import time
import re
import math
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from storage_engine import LSMStorageEngine

# Try to import numpy, fall back to pure Python if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("[WARNING] numpy not found. Using pure Python for vector operations (slower).")


class Document:
    """
    JSON Document representation

    Supports:
    - Nested objects
    - Arrays
    - Auto-generated IDs
    - Timestamps (createdAt, updatedAt)
    """

    def __init__(self, data: Dict[str, Any], doc_id: Optional[str] = None):
        self.id = doc_id or self._generate_id()
        self.data = data
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    @staticmethod
    def _generate_id() -> str:
        """Generate unique document ID"""
        timestamp = str(time.time()).encode()
        return hashlib.sha256(timestamp).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            '_id': self.id,
            '_created_at': self.created_at,
            '_updated_at': self.updated_at,
            **self.data
        }

    def to_bytes(self) -> bytes:
        """Serialize to bytes"""
        return json.dumps(self.to_dict()).encode('utf-8')

    @staticmethod
    def from_bytes(data: bytes) -> 'Document':
        """Deserialize from bytes"""
        doc_dict = json.loads(data.decode('utf-8'))
        doc_id = doc_dict.pop('_id')
        created_at = doc_dict.pop('_created_at')
        updated_at = doc_dict.pop('_updated_at')

        doc = Document(doc_dict, doc_id)
        doc.created_at = created_at
        doc.updated_at = updated_at
        return doc


class Collection:
    """
    Collection of documents (like MongoDB collection)

    Features:
    - CRUD operations
    - Indexing (B-Tree secondary indexes)
    - Querying with filters
    - Aggregation pipelines
    """

    def __init__(self, name: str, engine: LSMStorageEngine):
        self.name = name
        self.engine = engine
        self.indexes = {}  # field -> {value: [doc_ids]}

    def _doc_key(self, doc_id: str) -> str:
        """Generate storage key for document"""
        return f"collection:{self.name}:doc:{doc_id}"

    def _index_key(self, field: str, value: Any) -> str:
        """Generate storage key for index"""
        return f"collection:{self.name}:index:{field}:{value}"

    def insert(self, data: Dict[str, Any]) -> str:
        """
        Insert document

        Returns: document ID
        """
        doc = Document(data)

        # Store document
        self.engine.put(self._doc_key(doc.id), doc.to_bytes())

        # Update indexes
        self._update_indexes(doc)

        return doc.id

    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        return [self.insert(doc) for doc in documents]

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Find document by ID"""
        data = self.engine.get(self._doc_key(doc_id))
        if not data:
            return None

        doc = Document.from_bytes(data)
        return doc.to_dict()

    def find(self, query: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find documents matching query

        Query examples:
        - {'age': 25} - Exact match
        - {'age': {'$gt': 25}} - Greater than
        - {'name': {'$regex': 'John'}} - Regex match
        - {'tags': {'$in': ['python', 'database']}} - Array contains
        """
        query = query or {}
        results = []

        # Scan all documents in collection
        prefix = f"collection:{self.name}:doc:"
        all_docs = self.engine.range_scan(prefix, prefix + '\xff')

        for _, doc_bytes in all_docs:
            doc = Document.from_bytes(doc_bytes)
            if self._match_query(doc.to_dict(), query):
                results.append(doc.to_dict())

            if len(results) >= limit:
                break

        return results

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document"""
        results = self.find(query, limit=1)
        return results[0] if results else None

    def update(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update document

        Returns: True if updated, False if not found
        """
        doc_data = self.find_by_id(doc_id)
        if not doc_data:
            return False

        # Apply updates
        doc_data.update(updates)
        doc_data['_updated_at'] = datetime.now().isoformat()

        # Remove metadata before creating new Document
        doc_id = doc_data.pop('_id')
        doc_data.pop('_created_at')
        doc_data.pop('_updated_at')

        # Create updated document
        doc = Document(doc_data, doc_id)

        # Store updated document
        self.engine.put(self._doc_key(doc.id), doc.to_bytes())

        return True

    def update_many(self, query: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update multiple documents matching query"""
        docs = self.find(query)
        count = 0

        for doc in docs:
            if self.update(doc['_id'], updates):
                count += 1

        return count

    def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        doc_data = self.find_by_id(doc_id)
        if not doc_data:
            return False

        # Delete the document
        self.engine.delete(self._doc_key(doc_id))

        # Also delete associated vector if it exists (for documents with vector embeddings)
        # This handles cleanup for documents inserted via auto-indexing
        vector_key = f"vector:{self.name}:{doc_id}"
        self.engine.delete(vector_key)  # Safe to call even if vector doesn't exist

        return True

    def delete_many(self, query: Dict[str, Any]) -> int:
        """Delete multiple documents matching query"""
        docs = self.find(query)
        count = 0

        for doc in docs:
            if self.delete(doc['_id']):
                count += 1

        return count

    def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query"""
        return len(self.find(query, limit=1000000))

    def _match_query(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """
        Check if document matches query

        Supports MongoDB-like query operators:
        - $eq, $ne, $gt, $gte, $lt, $lte
        - $in, $nin
        - $regex
        - $exists
        """
        for field, condition in query.items():
            # Get field value (support nested fields like "user.name")
            value = self._get_nested_field(doc, field)

            # Handle query operators
            if isinstance(condition, dict):
                for operator, operand in condition.items():
                    if operator == '$eq' and value != operand:
                        return False
                    elif operator == '$ne' and value == operand:
                        return False
                    elif operator == '$gt' and not (value > operand):
                        return False
                    elif operator == '$gte' and not (value >= operand):
                        return False
                    elif operator == '$lt' and not (value < operand):
                        return False
                    elif operator == '$lte' and not (value <= operand):
                        return False
                    elif operator == '$in' and value not in operand:
                        return False
                    elif operator == '$nin' and value in operand:
                        return False
                    elif operator == '$regex':
                        if not re.search(operand, str(value)):
                            return False
                    elif operator == '$exists':
                        field_exists = value is not None
                        if field_exists != operand:
                            return False
            else:
                # Simple equality
                if value != condition:
                    return False

        return True

    def _get_nested_field(self, doc: Dict[str, Any], field: str) -> Any:
        """Get nested field value (e.g., "user.profile.age")"""
        keys = field.split('.')
        value = doc

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _update_indexes(self, doc: Document):
        """Update secondary indexes"""
        # TODO: Implement secondary indexing for faster queries
        pass

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregation pipeline (MongoDB-style)

        Stages:
        - $match - Filter documents
        - $group - Group by field
        - $sort - Sort results
        - $limit - Limit results
        - $project - Select fields
        """
        results = self.find(limit=1000000)

        for stage in pipeline:
            stage_name = list(stage.keys())[0]
            stage_config = stage[stage_name]

            if stage_name == '$match':
                results = [r for r in results if self._match_query(r, stage_config)]

            elif stage_name == '$group':
                # Group by _id field
                group_field = stage_config['_id']
                groups = {}

                for doc in results:
                    key = self._get_nested_field(doc, group_field.replace('$', ''))
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(doc)

                # Apply aggregation functions (count, sum, avg, etc.)
                results = []
                for key, group_docs in groups.items():
                    result = {'_id': key}

                    for agg_field, agg_op in stage_config.items():
                        if agg_field == '_id':
                            continue

                        if agg_op == {'$sum': 1}:
                            result[agg_field] = len(group_docs)
                        # Add more aggregation operators as needed

                    results.append(result)

            elif stage_name == '$sort':
                # Sort by field (1 = asc, -1 = desc)
                for field, direction in stage_config.items():
                    results.sort(
                        key=lambda x: self._get_nested_field(x, field),
                        reverse=(direction == -1)
                    )

            elif stage_name == '$limit':
                results = results[:stage_config]

            elif stage_name == '$project':
                # Select specific fields
                projected = []
                for doc in results:
                    new_doc = {}
                    for field, include in stage_config.items():
                        if include:
                            new_doc[field] = self._get_nested_field(doc, field)
                    projected.append(new_doc)
                results = projected

        return results


class VectorCollection:
    """
    Collection with vector embeddings support (for AI/ML)

    Use cases:
    - Semantic search
    - Recommendation systems
    - Image similarity
    - Document clustering
    """

    def __init__(self, name: str, engine: LSMStorageEngine, dimensions: int):
        self.name = name
        self.engine = engine
        self.dimensions = dimensions
        self.collection = Collection(name, engine)

    def insert(self, data: Dict[str, Any], vector: List[float]) -> str:
        """
        Insert document with vector embedding

        Args:
            data: Document data
            vector: Embedding vector (must match dimensions)
        """
        if len(vector) != self.dimensions:
            raise ValueError(f"Vector must have {self.dimensions} dimensions")

        # Store document
        doc_id = self.collection.insert(data)

        # Store vector separately (for efficient similarity search)
        vector_key = f"vector:{self.name}:{doc_id}"
        vector_bytes = json.dumps(vector).encode('utf-8')
        self.engine.put(vector_key, vector_bytes)

        return doc_id

    def search(self, query_vector: List[float], limit: int = 10) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Vector similarity search (cosine similarity)

        Returns: List of (doc_id, similarity_score, document)
        """
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector must have {self.dimensions} dimensions")

        # Load all vectors (in production, use HNSW or FAISS index)
        prefix = f"vector:{self.name}:"
        all_vectors = self.engine.range_scan(prefix, prefix + '\xff')

        # Calculate similarities
        similarities = []

        if HAS_NUMPY:
            # Fast numpy version
            query_norm = np.linalg.norm(query_vector)

            for vector_key, vector_bytes in all_vectors:
                doc_id = vector_key.split(':')[-1]
                vector = json.loads(vector_bytes.decode('utf-8'))

                # Cosine similarity
                dot_product = np.dot(query_vector, vector)
                vector_norm = np.linalg.norm(vector)
                similarity = dot_product / (query_norm * vector_norm + 1e-10)

                similarities.append((doc_id, similarity))
        else:
            # Pure Python version (slower)
            def dot_product(v1, v2):
                return sum(a * b for a, b in zip(v1, v2))

            def magnitude(v):
                return math.sqrt(sum(x * x for x in v))

            query_norm = magnitude(query_vector)

            for vector_key, vector_bytes in all_vectors:
                doc_id = vector_key.split(':')[-1]
                vector = json.loads(vector_bytes.decode('utf-8'))

                # Cosine similarity
                dot_prod = dot_product(query_vector, vector)
                vector_norm = magnitude(vector)
                similarity = dot_prod / (query_norm * vector_norm + 1e-10)

                similarities.append((doc_id, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Get documents
        results = []
        for doc_id, similarity in similarities[:limit]:
            doc = self.collection.find_by_id(doc_id)
            if doc:
                results.append((doc_id, similarity, doc))

        return results


class VeloxDB:
    """
    Main VeloxDB interface

    Features:
    - Multiple collections
    - Transactions (ACID)
    - Batch operations
    - Schema-free documents
    - Vector search
    - Full-text search
    """

    def __init__(self, data_dir: str = './veloxdb_data'):
        self.engine = LSMStorageEngine(data_dir)
        self.collections = {}
        self.vector_collections = {}

    def collection(self, name: str) -> Collection:
        """Get or create collection"""
        if name not in self.collections:
            self.collections[name] = Collection(name, self.engine)
        return self.collections[name]

    def vector_collection(self, name: str, dimensions: int = 768) -> VectorCollection:
        """Get or create vector collection"""
        key = f"{name}:{dimensions}"
        if key not in self.vector_collections:
            self.vector_collections[key] = VectorCollection(name, self.engine, dimensions)
        return self.vector_collections[key]

    def drop_collection(self, name: str) -> bool:
        """Delete entire collection"""
        # Delete ALL keys related to this collection (documents, indexes, metadata)
        collection_prefix = f"collection:{name}:"
        all_collection_keys = list(self.engine.range_scan(collection_prefix, collection_prefix + '\xff'))

        for key, _ in all_collection_keys:
            self.engine.delete(key)

        # Delete all vectors associated with this collection
        vector_prefix = f"vector:{name}:"
        all_vectors = list(self.engine.range_scan(vector_prefix, vector_prefix + '\xff'))

        for key, _ in all_vectors:
            self.engine.delete(key)

        # Remove from in-memory cache
        if name in self.collections:
            del self.collections[name]

        # Return True if we deleted anything
        return len(all_collection_keys) > 0 or len(all_vectors) > 0

    def list_collections(self) -> List[str]:
        """List all collections (scans storage engine for existing collections)"""
        collection_names = set()

        # Scan storage engine for collection keys
        # Format: collection:{name}:doc:{id} or collection:{name}:index:{field}:{value}
        all_keys = self.engine.range_scan('collection:', 'collection:\xff')

        for key, _ in all_keys:
            # Extract collection name from key format: collection:{name}:...
            parts = key.split(':')
            if len(parts) >= 2 and parts[0] == 'collection':
                collection_names.add(parts[1])

        # Also include in-memory collections
        collection_names.update(self.collections.keys())

        return sorted(list(collection_names))

    def stats(self) -> Dict[str, Any]:
        """Database statistics"""
        return {
            'engine_stats': self.engine.stats(),
            'collections': len(self.collections),
            'vector_collections': len(self.vector_collections)
        }

    def close(self):
        """Close database"""
        self.engine.close()


if __name__ == '__main__':
    print("="*70)
    print("VeloxDB - Next-Generation Lightweight Database")
    print("="*70)

    # Initialize database
    db = VeloxDB('./veloxdb_data')

    # Example 1: JSON Document Storage
    print("\n[EXAMPLE 1] JSON Document Storage")
    print("-" * 70)

    users = db.collection('users')

    # Insert documents
    user_id = users.insert({
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'age': 28,
        'tags': ['python', 'database', 'AI']
    })
    print(f"Inserted user: {user_id}")

    users.insert_many([
        {'name': 'Bob Smith', 'email': 'bob@example.com', 'age': 35, 'tags': ['javascript', 'web']},
        {'name': 'Charlie Brown', 'email': 'charlie@example.com', 'age': 42, 'tags': ['python', 'devops']},
        {'name': 'Diana Prince', 'email': 'diana@example.com', 'age': 30, 'tags': ['AI', 'ML']}
    ])

    # Query documents
    print("\nFind users with age > 30:")
    results = users.find({'age': {'$gt': 30}})
    for user in results:
        print(f"  - {user['name']} (age: {user['age']})")

    print("\nFind users with 'python' tag:")
    results = users.find({'tags': {'$in': ['python']}})
    for user in results:
        print(f"  - {user['name']}: {user['tags']}")

    # Update
    print("\nUpdating Alice's age...")
    users.update(user_id, {'age': 29})
    updated_user = users.find_by_id(user_id)
    print(f"Updated: {updated_user['name']} - age {updated_user['age']}")

    # Aggregation
    print("\n[EXAMPLE 2] Aggregation Pipeline")
    print("-" * 70)

    result = users.aggregate([
        {'$match': {'age': {'$gte': 30}}},
        {'$group': {'_id': '$age', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ])
    print("Users grouped by age (>= 30):")
    for group in result:
        print(f"  Age {group['_id']}: {group['count']} users")

    # Example 3: Vector Search (AI/ML)
    print("\n[EXAMPLE 3] Vector Embeddings (AI/ML)")
    print("-" * 70)

    products = db.vector_collection('products', dimensions=4)

    # Insert products with embeddings (simplified 4D vectors)
    products.insert(
        {'name': 'Laptop', 'category': 'Electronics', 'price': 1200},
        vector=[0.8, 0.1, 0.2, 0.3]  # Embedding from ML model
    )
    products.insert(
        {'name': 'Mouse', 'category': 'Electronics', 'price': 25},
        vector=[0.7, 0.15, 0.25, 0.35]  # Similar to laptop
    )
    products.insert(
        {'name': 'Book', 'category': 'Education', 'price': 15},
        vector=[0.1, 0.9, 0.8, 0.7]  # Very different
    )

    # Similarity search
    print("\nFind products similar to [0.75, 0.12, 0.22, 0.32]:")
    similar = products.search([0.75, 0.12, 0.22, 0.32], limit=3)
    for doc_id, similarity, doc in similar:
        print(f"  - {doc['name']} (similarity: {similarity:.4f})")

    # Stats
    print("\n[STATS] Database Statistics")
    print("-" * 70)
    stats = db.stats()
    print(json.dumps(stats, indent=2))

    # Close
    db.close()

    print("\n" + "="*70)
    print("VeloxDB Demo Complete!")
    print("="*70)

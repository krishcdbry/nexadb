import type {
  Note,
  CreateNoteRequest,
  UpdateNoteRequest,
  NotesListResponse,
  SearchResponse,
  VectorSearchRequest,
  VectorSearchResponse,
  StatsResponse,
} from '../types/note';

const API_BASE_URL = 'http://localhost:8000';

class NotesAPI {
  // Create a new note
  async createNote(data: CreateNoteRequest): Promise<Note> {
    const response = await fetch(`${API_BASE_URL}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create note');
    }
    return response.json();
  }

  // Get all notes with pagination
  async getNotes(skip = 0, limit = 20, archived?: boolean): Promise<NotesListResponse> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    if (archived !== undefined) {
      params.append('archived', archived.toString());
    }
    const response = await fetch(`${API_BASE_URL}/notes?${params}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch notes');
    }
    return response.json();
  }

  // Get a single note by ID
  async getNote(id: string): Promise<Note> {
    const response = await fetch(`${API_BASE_URL}/notes/${id}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch note');
    }
    return response.json();
  }

  // Update a note
  async updateNote(id: string, data: UpdateNoteRequest): Promise<Note> {
    const response = await fetch(`${API_BASE_URL}/notes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update note');
    }
    return response.json();
  }

  // Delete a note
  async deleteNote(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/notes/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete note');
    }
  }

  // Search notes by text
  async searchNotes(query: string, limit = 20): Promise<SearchResponse> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    const response = await fetch(`${API_BASE_URL}/notes/search?${params}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to search notes');
    }
    return response.json();
  }

  // Vector search (semantic search)
  async vectorSearch(request: VectorSearchRequest): Promise<VectorSearchResponse> {
    const response = await fetch(`${API_BASE_URL}/notes/vector-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to perform vector search');
    }
    return response.json();
  }

  // Add tags to a note
  async addTags(id: string, tags: string[]): Promise<Note> {
    const response = await fetch(`${API_BASE_URL}/notes/${id}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add tags');
    }
    return response.json();
  }

  // Get notes by tag
  async getNotesByTag(tag: string, limit = 20): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/notes/tags/${tag}?limit=${limit}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch notes by tag');
    }
    return response.json();
  }

  // Archive/unarchive a note
  async setArchiveStatus(id: string, archived: boolean): Promise<Note> {
    const response = await fetch(`${API_BASE_URL}/notes/${id}/archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ archived }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update archive status');
    }
    return response.json();
  }

  // Get recent notes
  async getRecentNotes(limit = 10): Promise<Note[]> {
    const response = await fetch(`${API_BASE_URL}/notes/recent?limit=${limit}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch recent notes');
    }
    return response.json();
  }

  // Get statistics
  async getStats(): Promise<StatsResponse> {
    const response = await fetch(`${API_BASE_URL}/notes/stats`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch statistics');
    }
    return response.json();
  }
}

export const notesAPI = new NotesAPI();

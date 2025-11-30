export interface Note {
  id: string;
  title: string;
  content: string;
  tags: string[];
  archived: boolean;
  created_at: number;
  updated_at: number;
}

export interface CreateNoteRequest {
  title: string;
  content: string;
  tags?: string[];
}

export interface UpdateNoteRequest {
  title?: string;
  content?: string;
  tags?: string[];
}

export interface NotesListResponse {
  notes: Note[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface SearchResponse {
  query: string;
  results: Note[];
  count: number;
}

export interface VectorSearchRequest {
  query_text: string;
  top_k?: number;
}

export interface VectorSearchResponse {
  query: string;
  results: Array<Note & { similarity: number }>;
  count: number;
}

export interface StatsResponse {
  total_notes: number;
  active_notes: number;
  archived_notes: number;
  notes_created_today: number;
  top_tags: Array<{ tag: string; count: number }>;
  total_unique_tags: number;
}

import { useState, useEffect, useRef } from 'react';
import { notesAPI } from './api/notes';
import type { Note, StatsResponse } from './types/note';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  DocumentTextIcon,
  ArchiveBoxIcon,
  TagIcon,
  PencilSquareIcon,
  TrashIcon,
  XMarkIcon,
  CheckIcon,
  ArrowPathIcon,
  BookmarkIcon,
  CommandLineIcon,
  BoltIcon,
} from '@heroicons/react/24/outline';
import {
  DocumentTextIcon as DocumentTextIconSolid,
  ArchiveBoxIcon as ArchiveBoxIconSolid,
} from '@heroicons/react/24/solid';

function App() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // View states
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [currentView, setCurrentView] = useState<'all' | 'archived'>('all');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Edit mode
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editTags, setEditTags] = useState('');

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'text' | 'semantic'>('text');
  const [isSearching, setIsSearching] = useState(false);

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-dismiss notifications
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
      // Cmd/Ctrl + N for new note
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        handleCreateNote();
      }
      // Escape to clear search
      if (e.key === 'Escape' && isSearching) {
        clearFilters();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearching]);

  // Auto-search with debounce
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim()) {
      searchTimeoutRef.current = setTimeout(() => {
        handleSearch();
      }, 500); // 500ms debounce
    } else if (isSearching) {
      clearFilters();
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, searchMode]);

  // Load notes and stats on mount
  useEffect(() => {
    loadNotes();
    loadStats();
  }, []);

  const loadNotes = async (archived = false) => {
    try {
      setLoading(true);
      setError(null);
      const response = await notesAPI.getNotes(0, 100, archived);
      setNotes(response.notes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await notesAPI.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleCreateNote = async () => {
    try {
      setLoading(true);
      setError(null);
      const newNote = await notesAPI.createNote({
        title: 'Untitled Note',
        content: 'Start writing...',
        tags: [],
      });
      await loadNotes(currentView === 'archived');
      await loadStats();
      setSelectedNote(newNote);
      setIsEditing(true);
      setEditTitle(newNote.title);
      setEditContent(newNote.content);
      setEditTags('');
      setSuccess('Note created successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create note');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNote = async () => {
    if (!selectedNote) return;

    try {
      setLoading(true);
      setError(null);
      const updatedNote = await notesAPI.updateNote(selectedNote.id, {
        title: editTitle,
        content: editContent,
        tags: editTags.split(',').map(t => t.trim()).filter(Boolean),
      });
      setSelectedNote(updatedNote);
      setIsEditing(false);
      await loadNotes(currentView === 'archived');
      await loadStats();
      setSuccess('Note saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNote = async (id: string) => {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
      setLoading(true);
      setError(null);
      await notesAPI.deleteNote(id);
      setSelectedNote(null);
      await loadNotes(currentView === 'archived');
      await loadStats();
      setSuccess('Note deleted successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete note');
    } finally {
      setLoading(false);
    }
  };

  const handleArchiveNote = async (note: Note) => {
    try {
      setLoading(true);
      setError(null);
      const updatedNote = await notesAPI.setArchiveStatus(note.id, !note.archived);
      setSelectedNote(updatedNote);
      await loadNotes(currentView === 'archived');
      await loadStats();
      setSuccess(updatedNote.archived ? 'Note archived!' : 'Note restored!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive note');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setIsSearching(false);
      loadNotes(currentView === 'archived');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setIsSearching(true);

      if (searchMode === 'text') {
        const response = await notesAPI.searchNotes(searchQuery, 100);
        setNotes(response.results);
      } else {
        const response = await notesAPI.vectorSearch({
          query_text: searchQuery,
          top_k: 20,
        });
        setNotes(response.results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTagFilter = async (tag: string) => {
    try {
      setLoading(true);
      setError(null);
      setSelectedTag(tag);
      const response = await notesAPI.getNotesByTag(tag, 100);
      setNotes(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to filter by tag');
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedTag(null);
    setIsSearching(false);
    loadNotes(currentView === 'archived');
  };

  const handleViewChange = (view: 'all' | 'archived') => {
    setCurrentView(view);
    setSelectedTag(null);
    setIsSearching(false);
    setSearchQuery('');
    loadNotes(view === 'archived');
    setSelectedNote(null);
  };

  const handleNoteSelect = (note: Note) => {
    setSelectedNote(note);
    setIsEditing(false);
    setEditTitle(note.title);
    setEditContent(note.content);
    setEditTags(note.tags.join(', '));
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-screen flex bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 overflow-hidden">
      {/* Left Sidebar - Navigation */}
      <div className="w-64 bg-white/80 backdrop-blur-xl border-r border-slate-200 flex flex-col shadow-lg">
        {/* Logo */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3 group cursor-pointer">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow">
              <DocumentTextIconSolid className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 group-hover:text-blue-600 transition-colors">NexaDB</h1>
              <p className="text-xs text-slate-500">Notes</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="p-4 border-b border-slate-200">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer group">
                <div className="text-2xl font-bold text-blue-600 group-hover:scale-110 transition-transform">{stats.total_notes}</div>
                <div className="text-xs text-blue-600/70">Total</div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer group">
                <div className="text-2xl font-bold text-green-600 group-hover:scale-110 transition-transform">{stats.active_notes}</div>
                <div className="text-xs text-green-600/70">Active</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="p-4 space-y-1">
          <button
            onClick={() => handleViewChange('all')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-all transform hover:scale-105 ${
              currentView === 'all'
                ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg shadow-blue-500/30'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <DocumentTextIcon className="w-5 h-5" />
            All Notes
          </button>
          <button
            onClick={() => handleViewChange('archived')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg font-medium transition-all transform hover:scale-105 ${
              currentView === 'archived'
                ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/30'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <ArchiveBoxIcon className="w-5 h-5" />
            Archived
          </button>
        </div>

        {/* Tags */}
        {stats && stats.top_tags.length > 0 && (
          <div className="p-4 flex-1 overflow-y-auto">
            <div className="flex items-center gap-2 mb-3">
              <TagIcon className="w-4 h-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-slate-700">Popular Tags</h3>
            </div>
            <div className="space-y-1">
              {stats.top_tags.slice(0, 10).map(({ tag, count }) => (
                <button
                  key={tag}
                  onClick={() => handleTagFilter(tag)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-all hover:scale-105 ${
                    selectedTag === tag
                      ? 'bg-indigo-100 text-indigo-700 font-medium shadow-md'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <span className="truncate">#{tag}</span>
                  <span className="text-xs text-slate-400 ml-2">{count}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Keyboard Shortcuts Hint */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50">
          <div className="text-xs text-slate-500 space-y-1">
            <div className="flex items-center gap-2">
              <CommandLineIcon className="w-3 h-3" />
              <span><kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-300 text-slate-600">⌘K</kbd> Search</span>
            </div>
            <div className="flex items-center gap-2">
              <BoltIcon className="w-3 h-3" />
              <span><kbd className="px-1.5 py-0.5 bg-white rounded border border-slate-300 text-slate-600">⌘N</kbd> New Note</span>
            </div>
          </div>
        </div>

        {/* Create Button */}
        <div className="p-4 border-t border-slate-200">
          <button
            onClick={handleCreateNote}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-blue-500/30 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            <PlusIcon className="w-5 h-5" />
            New Note
          </button>
        </div>
      </div>

      {/* Middle Column - Notes List */}
      <div className="w-96 bg-white/60 backdrop-blur-sm border-r border-slate-200 flex flex-col shadow-lg">
        {/* Search */}
        <div className="p-4 border-b border-slate-200 space-y-3 bg-white/80 backdrop-blur-xl">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search notes... (⌘K)"
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-sm"
            />
            {searchQuery && (
              <button
                onClick={clearFilters}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSearchMode('text')}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all transform hover:scale-105 ${
                searchMode === 'text'
                  ? 'bg-blue-100 text-blue-700 shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <MagnifyingGlassIcon className="w-4 h-4" />
              Text
            </button>
            <button
              onClick={() => setSearchMode('semantic')}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all transform hover:scale-105 ${
                searchMode === 'semantic'
                  ? 'bg-purple-100 text-purple-700 shadow-md'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <SparklesIcon className="w-4 h-4" />
              AI Search
            </button>
          </div>
          {selectedTag && (
            <div className="flex items-center gap-2 text-sm animate-fadeIn">
              <TagIcon className="w-4 h-4 text-indigo-500" />
              <span className="text-slate-600">Filtered by:</span>
              <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-md font-medium">
                #{selectedTag}
              </span>
            </div>
          )}
        </div>

        {/* Notes List */}
        <div className="flex-1 overflow-y-auto">
          {loading && notes.length === 0 ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse bg-white/70 rounded-xl p-4 space-y-3">
                  <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                  <div className="h-3 bg-slate-200 rounded w-full"></div>
                  <div className="h-3 bg-slate-200 rounded w-5/6"></div>
                </div>
              ))}
            </div>
          ) : notes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 animate-fadeIn">
              <DocumentTextIcon className="w-16 h-16 text-slate-300 mb-4" />
              <p className="text-slate-500 font-medium">No notes found</p>
              <p className="text-slate-400 text-sm mt-1">Create your first note to get started</p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {notes.map((note, index) => (
                <button
                  key={note.id}
                  onClick={() => handleNoteSelect(note)}
                  style={{ animationDelay: `${index * 50}ms` }}
                  className={`w-full text-left p-4 rounded-xl transition-all animate-slideIn hover:scale-[1.02] ${
                    selectedNote?.id === note.id
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 shadow-lg'
                      : 'bg-white/70 hover:bg-white border border-slate-100 hover:shadow-md'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-slate-800 line-clamp-1 flex-1">
                      {note.title}
                    </h3>
                    {note.archived && (
                      <ArchiveBoxIconSolid className="w-4 h-4 text-orange-500 ml-2" />
                    )}
                  </div>
                  <p className="text-sm text-slate-500 line-clamp-2 mb-3">
                    {note.content}
                  </p>
                  {note.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {note.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-md hover:bg-blue-200 transition-colors"
                        >
                          {tag}
                        </span>
                      ))}
                      {note.tags.length > 3 && (
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-md">
                          +{note.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                  <div className="text-xs text-slate-400">
                    {formatDate(note.updated_at)} · {formatTime(note.updated_at)}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Column - Note Editor */}
      <div className="flex-1 flex flex-col bg-white/40 backdrop-blur-sm">
        {selectedNote ? (
          <>
            {/* Note Header */}
            <div className="p-6 border-b border-slate-200 bg-white/80 backdrop-blur-xl shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {isEditing ? (
                    <button
                      onClick={handleSaveNote}
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg font-medium hover:from-green-600 hover:to-emerald-600 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 shadow-lg shadow-green-500/30"
                    >
                      <CheckIcon className="w-4 h-4" />
                      Save
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg font-medium hover:bg-blue-200 transition-all transform hover:scale-105 active:scale-95"
                    >
                      <PencilSquareIcon className="w-4 h-4" />
                      Edit
                    </button>
                  )}
                  <button
                    onClick={() => handleArchiveNote(selectedNote)}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-100 text-orange-700 rounded-lg font-medium hover:bg-orange-200 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50"
                  >
                    <ArchiveBoxIcon className="w-4 h-4" />
                    {selectedNote.archived ? 'Restore' : 'Archive'}
                  </button>
                </div>
                <button
                  onClick={() => handleDeleteNote(selectedNote.id)}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg font-medium hover:bg-red-200 transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50"
                >
                  <TrashIcon className="w-4 h-4" />
                  Delete
                </button>
              </div>

              {isEditing ? (
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full text-3xl font-bold text-slate-800 bg-transparent border-none focus:outline-none focus:ring-0 p-0 placeholder-slate-400"
                  placeholder="Note title..."
                />
              ) : (
                <h2 className="text-3xl font-bold text-slate-800">{selectedNote.title}</h2>
              )}
              <div className="mt-2 text-sm text-slate-500">
                Last edited {formatDate(selectedNote.updated_at)} at {formatTime(selectedNote.updated_at)}
              </div>
            </div>

            {/* Note Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {isEditing ? (
                <div className="space-y-4 animate-fadeIn">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full h-96 text-slate-700 text-lg leading-relaxed bg-white/80 rounded-xl p-4 border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none shadow-sm"
                    placeholder="Start writing..."
                  />
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editTags}
                      onChange={(e) => setEditTags(e.target.value)}
                      className="w-full px-4 py-2 bg-white/80 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                      placeholder="work, personal, important..."
                    />
                  </div>
                </div>
              ) : (
                <div className="prose prose-slate max-w-none animate-fadeIn">
                  <div className="text-slate-700 text-lg leading-relaxed whitespace-pre-wrap">
                    {selectedNote.content}
                  </div>
                  {selectedNote.tags.length > 0 && (
                    <div className="mt-8 pt-6 border-t border-slate-200">
                      <div className="flex items-center gap-2 mb-3">
                        <TagIcon className="w-4 h-4 text-slate-500" />
                        <h4 className="text-sm font-semibold text-slate-700">Tags</h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {selectedNote.tags.map((tag) => (
                          <button
                            key={tag}
                            onClick={() => handleTagFilter(tag)}
                            className="px-3 py-1.5 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-lg hover:from-blue-200 hover:to-indigo-200 transition-all font-medium transform hover:scale-105"
                          >
                            #{tag}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center animate-fadeIn">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-3xl flex items-center justify-center mb-6 shadow-lg">
              <BookmarkIcon className="w-12 h-12 text-blue-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-700 mb-2">No Note Selected</h2>
            <p className="text-slate-500 max-w-md">
              Select a note from the list or create a new one to get started
            </p>
            <button
              onClick={handleCreateNote}
              className="mt-6 flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-white rounded-xl font-medium shadow-lg shadow-blue-500/30 transition-all transform hover:scale-105 active:scale-95"
            >
              <PlusIcon className="w-5 h-5" />
              Create Your First Note
            </button>
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-white/80 backdrop-blur-xl">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <span className="font-medium">Powered by</span>
              <a
                href="https://github.com/krishcdbry/nexadb"
                target="_blank"
                rel="noopener noreferrer"
                className="font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent hover:from-blue-700 hover:to-indigo-700 transition-all"
              >
                NexaDB
              </a>
            </div>
            <div className="flex items-center gap-2">
              <BoltIcon className="w-3 h-3 text-yellow-500" />
              <span>10x Faster than REST</span>
            </div>
          </div>
        </div>
      </div>

      {/* Success Toast */}
      {success && (
        <div className="fixed bottom-6 right-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-4 rounded-xl shadow-2xl max-w-md animate-slideUp">
          <div className="flex items-center gap-3">
            <CheckIcon className="w-6 h-6" />
            <div>
              <div className="font-semibold">Success!</div>
              <div className="text-sm opacity-90">{success}</div>
            </div>
            <button
              onClick={() => setSuccess(null)}
              className="ml-4 hover:bg-green-600 rounded-lg p-1 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-6 right-6 bg-gradient-to-r from-red-500 to-pink-500 text-white px-6 py-4 rounded-xl shadow-2xl max-w-md animate-slideUp">
          <div className="flex items-center gap-3">
            <XMarkIcon className="w-6 h-6" />
            <div>
              <div className="font-semibold">Error</div>
              <div className="text-sm opacity-90">{error}</div>
            </div>
            <button
              onClick={() => setError(null)}
              className="ml-4 hover:bg-red-600 rounded-lg p-1 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

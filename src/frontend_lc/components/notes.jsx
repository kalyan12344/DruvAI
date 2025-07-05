import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Book, Plus, Search, Bold, Italic, Underline, Trash2 } from 'lucide-react';
import '../styles/notes.css';

// Custom hook for debouncing
const useDebounce = (value, delay) => {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);
    return debouncedValue;
};

const Notes = () => {
    // --- State Management ---
    const [notes, setNotes] = useState([]);
    const [selectedNote, setSelectedNote] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [wordCount, setWordCount] = useState(0);

    // Modal States
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [noteToDelete, setNoteToDelete] = useState(null);

    const editorRef = useRef(null);
    const debouncedContent = useDebounce(selectedNote?.content, 1500); // Auto-save after 1.5s

    // --- API Calls & Effects ---

    useEffect(() => {
        fetchNotes();
    }, []);

    useEffect(() => {
        if (debouncedContent !== null && selectedNote?.id && selectedNote.content !== undefined) {
            handleSaveNote();
        }
    }, [debouncedContent]);

    const fetchNotes = async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://127.0.0.1:8000/api/notes/notes');
            setNotes(response.data || []);
        } catch (err) {
            setError("Could not load notes.");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectNote = async (noteId) => {
        if (selectedNote?.id === noteId) return;
        // Instantly update the UI to feel faster
        const noteData = notes.find(n => n.id === noteId);
        setSelectedNote(noteData);

        try {
            const response = await axios.get(`http://127.0.0.1:8000/api/notes/notes/${noteId}`);
            setSelectedNote(response.data);
            if (editorRef.current) {
                editorRef.current.innerHTML = response.data.content;
                updateWordCount(editorRef.current.innerText);
            }
        } catch (err) {
            setError("Could not fetch note details.");
        }
    };

    const handleCreateNote = async () => {
        try {
            const response = await axios.post('http://127.0.0.1:8000/api/notes/notes', {
                title: "New Note",
                content: "",
            });
            const newNote = response.data;
            setNotes([newNote, ...notes]);
            handleSelectNote(newNote.id);
        } catch (err) {
            setError("Failed to create a new note.");
        }
    };

    const handleSaveNote = async () => {
        if (!selectedNote) return;
        setIsSaving(true);
        const snippet = editorRef.current ? editorRef.current.innerText.substring(0, 20) : "";

        try {
            const response = await axios.put(`http://127.0.0.1:8000/api/notes/notes/${selectedNote.id}`, {
                title: selectedNote.title,
                content: selectedNote.content,
                snippet: snippet
            });
            setSelectedNote(prev => ({ ...prev, updated_at: response.data.updated_at }));
            const newNotes = notes.map(n => n.id === response.data.id ? { ...n, title: response.data.title, snippet: snippet, updated_at: response.data.updated_at } : n);
            newNotes.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
            setNotes(newNotes);
        } catch (err) {
            console.error("Failed to save note", err);
        } finally {
            setTimeout(() => setIsSaving(false), 1000);
        }
    };

    const handleDeleteNote = (note) => {
        setNoteToDelete(note);
        setIsDeleteModalOpen(true);
    };

    const confirmDelete = async () => {
        if (!noteToDelete) return;
        try {
            await axios.delete(`http://127.0.0.1:8000/api/notes/notes/${noteToDelete.id}`);
            const newNotes = notes.filter(n => n.id !== noteToDelete.id);
            setNotes(newNotes);
            if (selectedNote?.id === noteToDelete.id) {
                setSelectedNote(null);
            }
        } catch (err) {
            setError("Failed to delete note.");
        } finally {
            setIsDeleteModalOpen(false);
            setNoteToDelete(null);
        }
    };

    const updateWordCount = (text) => {
        if (!text || text.trim() === '') {
            setWordCount(0);
            return;
        }
        const words = text.trim().split(/\s+/).filter(Boolean);
        setWordCount(words.length);
    };

    const handleContentChange = (e) => {
        setSelectedNote(prev => ({ ...prev, content: e.target.innerHTML }));
        updateWordCount(e.target.innerText);
    };

    const handleTitleChange = (e) => {
        setSelectedNote(prev => ({ ...prev, title: e.target.value }));
    };

    const applyFormat = (command, value = null) => {
        document.execCommand(command, false, value);
        editorRef.current.focus();
    };

    const handleStyleChange = (e) => {
        applyFormat('formatBlock', e.target.value);
    };

    const filteredNotes = notes.filter(note =>
        note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (note.snippet && note.snippet.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // --- Render Functions ---

    return (
        <div className="notes-page-container">
            {/* Left Pane: Note List */}
            <div className="notes-list-pane">
                <div className="notes-list-header">
                    <Book size={20} />
                    <h2>Notes</h2>
                </div>
                <div className="search-notes-container">
                    <Search size={16} className="search-icon" />
                    <input type="text" placeholder="Search notes" onChange={(e) => setSearchTerm(e.target.value)} />
                </div>
                <div className="notes-list">
                    {loading && <p>Loading...</p>}
                    {error && <p className="error-text">{error}</p>}
                    <AnimatePresence>
                        {filteredNotes.map(note => (
                            <motion.div
                                key={note.id}
                                className={`note-item ${selectedNote?.id === note.id ? 'active' : ''}`}
                                onClick={() => handleSelectNote(note.id)}
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                layout
                            >

                                <span className="note-item-title">{note.title}</span>

                                <span className="note-item-snippet">{note.snippet || "No additional text"}</span>
                                <button className="delete-note-btn" onClick={(e) => { e.stopPropagation(); handleDeleteNote(note); }}><Trash2 size={14} /></button>


                            </motion.div>

                        ))}

                    </AnimatePresence>
                </div>
                <button className="new-note-btn" onClick={handleCreateNote}>
                    <Plus size={16} /> Note +
                </button>
            </div>

            {/* Right Pane: Note Editor */}
            <div className="note-editor-pane">
                {selectedNote ? (
                    <>
                        <div className="editor-toolbar">
                            <select className="text-style-dropdown" onChange={handleStyleChange}>
                                <option value="p">Normal</option>
                                <option value="h2">Heading 1</option>
                                <option value="h3">Heading 2</option>
                            </select>
                            <div className={`save-status ${isSaving ? 'saving' : ''}`}>
                                {isSaving ? "Saving..." : "Saved"}
                            </div>
                            <div className="format-buttons">
                                <button onClick={() => applyFormat('bold')}><Bold size={16} /></button>
                                <button onClick={() => applyFormat('italic')}><Italic size={16} /></button>
                                <button onClick={() => applyFormat('underline')}><Underline size={16} /></button>
                            </div>
                        </div>
                        <div className="note-editor-wrapper">
                            {/* Title input is now inside the scrollable wrapper */}
                            <input type="text" className="title-input-main" value={selectedNote.title} onChange={handleTitleChange} onBlur={handleSaveNote} />
                            <div ref={editorRef} className="note-editor" contentEditable suppressContentEditableWarning onInput={handleContentChange} />
                        </div>
                        <div className="editor-footer">
                            <span>Last updated: {new Date(selectedNote.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            <span>{wordCount} words</span>
                        </div>
                    </>
                ) : (
                    <div className="editor-placeholder">
                        <p>Select a note or create a new one</p>
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            <AnimatePresence>
                {isDeleteModalOpen && (
                    <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <motion.div className="modal-content" initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -50, opacity: 0 }}>
                            <h3>Delete Note</h3>
                            <p>Are you sure you want to delete "{noteToDelete?.title}"? This action cannot be undone.</p>
                            <div className="modal-actions">
                                <button className="action-pill" onClick={() => setIsDeleteModalOpen(false)}>Cancel</button>
                                <button className="action-pill danger" onClick={confirmDelete}>Delete</button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Notes;

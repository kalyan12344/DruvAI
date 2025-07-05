import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Plus, Trash2 } from 'lucide-react';
import '../styles/remainders.css';

// --- Helper to format dates ---
const formatDateTime = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
};


const Reminders = () => {
    // --- State Management ---
    const [reminders, setReminders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isAdding, setIsAdding] = useState(false);

    // State for the new reminder form
    const [newTitle, setNewTitle] = useState('');
    const [newDate, setNewDate] = useState('');
    const [newTime, setNewTime] = useState('');

    // --- API Calls ---

    useEffect(() => {
        fetchReminders();
    }, []);

    const fetchReminders = async () => {
        setLoading(true);
        try {
            const response = await axios.get('http://127.0.0.1:8000/api/reminders/list');
            // --- FIX: Sort reminders by date upon fetching ---
            const sortedReminders = (response.data || []).sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at));
            setReminders(sortedReminders);
            setError(null);
        } catch (err) {
            console.error("Error fetching reminders:", err);
            setError("Could not load reminders. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleAddReminder = async (e) => {
        e.preventDefault();
        if (!newTitle.trim() || !newDate || !newTime) {
            alert("Please fill out all fields.");
            return;
        }

        // Combine date and time into a single ISO 8601 string
        const remindAtISO = new Date(`${newDate}T${newTime}`).toISOString();

        try {
            const response = await axios.post('http://127.0.0.1:8000/api/reminders/add', {
                title: newTitle,
                remind_at: remindAtISO,
            });
            // Add to list and re-sort to maintain chronological order
            const updatedList = [...reminders, response.data].sort((a, b) => new Date(a.remind_at) - new Date(b.remind_at));
            setReminders(updatedList);
            // Reset form
            setNewTitle('');
            setNewDate('');
            setNewTime('');
            setIsAdding(false);
        } catch (err) {
            console.error("Error adding reminder:", err);
            setError("Failed to add the reminder.");
        }
    };

    const handleDeleteReminder = async (id) => {
        try {
            await axios.delete(`http://127.0.0.1:8000/api/reminders/delete/${id}`);
            setReminders(reminders.filter((r) => r.id !== id));
        } catch (err) {
            console.error("Error deleting reminder:", err);
            setError("Failed to delete the reminder.");
        }
    };


    // --- Render Functions ---

    return (
        <div className="reminders-page">
            <div className="glass-panel reminders-widget">
                <div className="widget-header">
                    <h3 className="widget-title">Reminders</h3>
                    <button className="add-button" onClick={() => setIsAdding(!isAdding)} title="Add new reminder">
                        <Plus size={16} />
                    </button>
                </div>

                <AnimatePresence>
                    {isAdding && (
                        <motion.form className="add-reminder-form" onSubmit={handleAddReminder} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                            <input
                                type="text"
                                className="reminder-input"
                                value={newTitle}
                                onChange={(e) => setNewTitle(e.target.value)}
                                placeholder="What do you need to be reminded of?"
                                autoFocus
                            />
                            <div className="datetime-inputs">
                                <input type="date" value={newDate} onChange={(e) => setNewDate(e.target.value)} className="date-time-input" />
                                <input type="time" value={newTime} onChange={(e) => setNewTime(e.target.value)} className="date-time-input" />
                            </div>
                            <div className="form-actions">
                                <button type="button" className="form-button" onClick={() => setIsAdding(false)}>Cancel</button>
                                <button type="submit" className="form-button primary">Add Reminder</button>
                            </div>
                        </motion.form>
                    )}
                </AnimatePresence>

                <div className="reminders-list">
                    {loading ? (
                        <div className='centered-state'>Loading...</div>
                    ) : error ? (
                        <div className='centered-state error'>{error}</div>
                    ) : reminders.length === 0 ? (
                        <div className='centered-state'>No reminders scheduled.</div>
                    ) : (
                        <AnimatePresence>
                            {reminders.map((reminder) => (
                                <motion.div
                                    key={reminder.id}
                                    className="reminder-item"
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, x: -30, transition: { duration: 0.2 } }}
                                    layout
                                >
                                    <div className="reminder-icon"><Bell size={18} /></div>
                                    <div className="reminder-details">
                                        <span className="reminder-title">{reminder.title}</span>
                                        <span className="reminder-time">{formatDateTime(reminder.remind_at)}</span>
                                    </div>
                                    <button className="delete-reminder-btn" onClick={() => handleDeleteReminder(reminder.id)} title="Delete reminder">
                                        <Trash2 size={16} />
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Reminders;

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckSquare, Plus, X, Search, MoreHorizontal, Check, Calendar, Flag, Trash2 } from 'lucide-react';
import axios from 'axios';
import '../styles/todolist.css';

const TodoListWidget = () => {
    // --- State Management ---
    const [tasks, setTasks] = useState([]);
    const [newTaskText, setNewTaskText] = useState('');
    const [newPriority, setNewPriority] = useState('Medium'); // Default to 'Medium'
    const [newEndDate, setNewEndDate] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [isAdding, setIsAdding] = useState(false);
    const [filter, setFilter] = useState('Active');
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);

    // --- NEW: Loading and Error States ---
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // --- API Integration ---

    // Fetch tasks when the component mounts
    useEffect(() => {
        fetchTasks();
    }, []);

    const fetchTasks = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get('https://druv-backend-338967818277.us-central1.run.app/api/tasks/retrieve');
            setTasks(response.data || []);
        } catch (err) {
            console.error("Error fetching tasks:", err);
            setError("Could not load tasks. Please try again later.");
        } finally {
            setLoading(false);
        }
    };

    // Add a new task
    const handleAddTask = async (e) => {
        e.preventDefault();
        if (newTaskText.trim() === '') return;

        const newTaskPayload = {
            name: newTaskText,
            priority: newPriority,
            due_date: newEndDate || null,
        };

        try {
            const response = await axios.post('https://druv-backend-338967818277.us-central1.run.app/api/tasks/add', newTaskPayload);
            setTasks(prevTasks => [response.data, ...prevTasks]);
            // Reset form
            setNewTaskText('');
            setNewPriority('Medium');
            setNewEndDate('');
            setIsAdding(false);
        } catch (err) {
            console.error("Error adding task:", err);
            setError("Failed to add the new task.");
        }
    };

    // Toggle task completion
    const handleToggleTask = async (task) => {
        const newStatus = task.status === 'Completed' ? 'To Do' : 'Completed';
        try {
            const response = await axios.put(`https://druv-backend-338967818277.us-central1.run.app/api/tasks/update/${task.id}`, {
                status: newStatus
            });
            setTasks(tasks.map(t => (t.id === task.id ? response.data : t)));
        } catch (err) {
            console.error("Error updating task status:", err);
            // Optionally revert the change on error
        }
    };

    // Delete a task
    const handleDeleteTask = async (id) => {
        try {
            await axios.delete(`http://127.0.0.1:8000/api/tasks/delete/${id}`);
            setTasks(tasks.filter((task) => task.id !== id));
        } catch (err) {
            console.error("Error deleting task:", err);
            setError("Failed to delete the task.");
        }
    };


    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [dropdownRef]);


    // Filter and sort tasks
    const processedTasks = useMemo(() => {
        return tasks
            .filter(task => {
                const matchesFilter =
                    (filter === 'Active' && task.status !== 'Completed') ||
                    (filter === 'Done' && task.status === 'Completed') ||
                    filter === 'All';
                const matchesSearch = task.name.toLowerCase().includes(searchTerm.toLowerCase());
                return matchesFilter && matchesSearch;
            })
            .sort((a, b) => {
                if (a.status === 'Completed' && b.status !== 'Completed') return 1;
                if (a.status !== 'Completed' && b.status === 'Completed') return -1;
                const priorityMap = { High: 1, Medium: 2, Low: 3 };
                return (priorityMap[a.priority] || 4) - (priorityMap[b.priority] || 4);
            });
    }, [tasks, searchTerm, filter]);

    // --- Helper & Animation ---
    const itemVariants = { hidden: { opacity: 0, y: -10 }, visible: { opacity: 1, y: 0 }, exit: { opacity: 0, x: -30, transition: { duration: 0.2 } } };
    const formatDate = (dateString) => {
        if (!dateString) return null;
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const priorityMap = {
        High: 1,
        Medium: 2,
        Low: 3,
    };

    // --- Render Functions ---
    return (
        <div className='tasks-page'>
            <div className="glass-panel todo-widget-v2">
                <div className="widget-header-v2">
                    <h3 className="widget-title">To-dos</h3>
                    <div className="search-container">
                        <Search size={18} className="search-icon" />
                        <input type="text" placeholder="Search to-dos" className="search-input" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                    </div>
                </div>

                <div className="widget-toolbar">
                    <motion.button className="add-task-button" onClick={() => setIsAdding(!isAdding)} title="Add new task"><Plus size={14} /></motion.button>
                    <div className="filter-dropdown-container" ref={dropdownRef}>
                        <button className="filter-dropdown" onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
                            <span>{filter}</span>
                            <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 1L5 5L9 1" stroke="#A0B1D4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                        </button>
                        <AnimatePresence>
                            {isDropdownOpen && (
                                <motion.div className="filter-dropdown-menu" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                                    {['All', 'Active', 'Done'].map(option => (
                                        <div key={option} className="dropdown-item" onClick={() => { setFilter(option); setIsDropdownOpen(false); }}>{option}</div>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                    <button className="more-options-button" title="More options"><MoreHorizontal size={14} /></button>
                </div>

                <AnimatePresence>
                    {isAdding && (
                        <motion.form className="add-task-form-v2" onSubmit={handleAddTask} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                            <div className="main-input-wrapper"><input type="text" value={newTaskText} onChange={(e) => setNewTaskText(e.target.value)} placeholder="What needs to be done?" autoFocus /></div>
                            <div className="sub-inputs-wrapper">
                                <div className="date-input-container">
                                    <Calendar size={16} /><input type="date" value={newEndDate} onChange={(e) => setNewEndDate(e.target.value)} className="date-input" />
                                </div>
                                <div className="priority-input-container">
                                    <Flag size={16} />
                                    <select value={newPriority} onChange={(e) => setNewPriority(e.target.value)} className="priority-select">
                                        <option value="Low">Low</option>
                                        <option value="Medium">Medium</option>
                                        <option value="High">High</option>
                                    </select>
                                </div>
                                <button type="submit" className="submit-task-button">Add Task</button>
                            </div>
                        </motion.form>
                    )}
                </AnimatePresence>

                <div className="task-list-v2">
                    <AnimatePresence>
                        {loading ? (
                            <div className='centered-state'>Loading...</div>
                        ) : error ? (
                            <div className='centered-state error'>{error}</div>
                        ) : processedTasks.length === 0 ? (
                            <div className='centered-state'>No {filter.toLowerCase()} tasks found.</div>
                        ) : (
                            processedTasks.map((task) => (
                                <motion.div key={task.id} className="task-item-v2" variants={itemVariants} initial="hidden" animate="visible" exit="exit" layout>
                                    <div className={`round-checkbox ${task.status === 'Completed' ? 'completed' : ''}`} onClick={() => handleToggleTask(task)}>
                                        {task.status === 'Completed' && (<motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}><Check size={14} /></motion.div>)}
                                    </div>
                                    <div className="task-details">
                                        <span className={`task-text-v2 ${task.status === 'Completed' ? 'completed' : ''}`}>{task.name}</span>
                                        {task.due_date && (<div className="task-end-date"><Calendar size={12} /><span>{formatDate(task.due_date)}</span></div>)}
                                    </div>
                                    <div className={`priority-indicator priority-${(task.priority || 'low').toLowerCase()}`} title={`Priority ${task.priority}`}></div>
                                    <button className="delete-task-btn-v2" onClick={() => handleDeleteTask(task.id)} title="Delete task"><Trash2 size={16} /></button>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default TodoListWidget;

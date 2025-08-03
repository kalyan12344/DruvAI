import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Sparkles, Calendar, CheckCircle2, AlertTriangle, ExternalLink, Newspaper, Paperclip, X, FileText } from 'lucide-react';
import '../styles/home.css';
import axios from "axios";
import { auth } from '../../firebase';
import { onAuthStateChanged } from 'firebase/auth';
import AIMessage from './AIMessage';

const api = axios.create({ baseURL: "http://127.0.0.1:8000" });

const suggestionChips = [
    { text: "What's on my calendar today?" },
    { text: "Summarize the latest news on AI." },
];

export const CalendarCard = ({ data }) => {
    const formatTime = (timeString) => {
        if (!timeString) return "All-day";
        if (!timeString.includes('T')) {
            if (/^\d{2}:\d{2}$/.test(timeString)) {
                const [hour, minute] = timeString.split(':');
                const date = new Date();
                date.setHours(parseInt(hour, 10), parseInt(minute, 10));
                return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            }
            return timeString;
        }
        try {
            return new Date(timeString).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
        } catch (e) { return timeString; }
    };

    return (
        <div className="structured-card calendar-card">
            <div className="card-header">
                <Calendar size={16} />
                <h4>{data.message || "Your Schedule"}</h4>
            </div>
            <div className="card-content">
                {data.events?.map((event, index) => (
                    <a href={event.htmlLink} target="_blank" rel="noopener noreferrer" className="event-item" key={index}>
                        <div className="event-details">
                            <div className="event-time-range">
                                <span>{formatTime(event.start_time)}</span> - <span>{formatTime(event.end_time)}</span>
                            </div>
                            <div className="event-summary">{event.summary}</div>
                        </div>
                        <ExternalLink className="event-link-icon" size={16} />
                    </a>
                ))}
            </div>
        </div>
    );
};

export const ConfirmationCard = ({ data }) => {
    const isSuccess = data.status === 'success';
    return (
        <div className={`structured-card confirmation-card ${isSuccess ? 'success' : 'error'}`}>
            <div className="card-header">
                {isSuccess ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <h4>{isSuccess ? 'Success' : 'Notice'}</h4>
            </div>
            <div className="card-content"><p>{data.message}</p></div>
        </div>
    );
};

export const NewsCard = ({ data }) => { /* ... component code ... */ };

const Home = () => {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const [fileToUpload, setFileToUpload] = useState(null);
    const [documentContext, setDocumentContext] = useState(null);
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);
    const [userDocuments, setUserDocuments] = useState([]);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
            setUser(firebaseUser);
            if (firebaseUser) {
                fetchChatHistory(firebaseUser);
            } else {
                setMessages([]);
            }
        });

        const handlePaste = (event) => {
            const items = event.clipboardData.items;
            for (const item of items) {
                if (item.type.indexOf('image') !== -1) {
                    const file = item.getAsFile();
                    setFileToUpload(file);
                    setDocumentContext(null);
                }
            }
        };
        window.addEventListener('paste', handlePaste);
        return () => {
            unsubscribe();
            window.removeEventListener('paste', handlePaste);
        };
    }, []);

    const fetchChatHistory = async (firebaseUser) => {
        try {
            const token = await firebaseUser.getIdToken();
            const response = await api.get("/api/chat/history", { headers: { 'Authorization': `Bearer ${token}` } });
            setMessages(response.data || []);
        } catch (error) { console.error("Failed to fetch chat history:", error); }
    };

    const saveMessageToHistory = async (sender, content) => {
        try {
            const token = await user?.getIdToken();
            if (!token) return;
            await api.post("/api/chat/history", { sender, content }, { headers: { 'Authorization': `Bearer ${token}` } });
        } catch (error) { console.error("Failed to save message:", error); }
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setFileToUpload(file);
            setDocumentContext(null); // Clear document context when a new file is attached
        }
    };

    const handleOpenDocSelector = async () => {
        try {
            const token = await user?.getIdToken();
            const response = await api.get("/api/documents/list", { headers: { 'Authorization': `Bearer ${token}` } });
            setUserDocuments(response.data || []);
            setIsDocModalOpen(true);
        } catch (error) { console.error("Failed to fetch documents:", error); }
    };

    const handleSelectDocument = (doc) => {
        setDocumentContext(doc);
        setFileToUpload(null); // Clear any pending file uploads
        setIsDocModalOpen(false);
    };

    const handleSendMessage = async (content = message) => {
        const trimmedMessage = content.trim();
        if ((!trimmedMessage && !fileToUpload) || isTyping) return;

        const userMessage = { text: trimmedMessage, sender: "user" };
        setMessages(prev => [...prev, userMessage]);
        saveMessageToHistory("user", trimmedMessage);
        setMessage('');
        setIsTyping(true);

        try {
            const token = await user?.getIdToken();
            if (!token) throw new Error("User not authenticated.");
            const headers = { 'Authorization': `Bearer ${token}` };

            if (fileToUpload) {
                const statusMessageId = `status-${Date.now()}`;
                const statusMessage = { id: statusMessageId, content: { output: `📄 Processing '${fileToUpload.name}'...` }, sender: "bot", isStatus: true };
                setMessages(prev => [...prev, statusMessage]);

                const formData = new FormData();
                formData.append('prompt', trimmedMessage);
                formData.append('file', fileToUpload);

                const uploadResponse = await api.post("/agent/ask_with_file", formData, { headers: { ...headers, 'Content-Type': 'multipart/form-data' } });
                const { document_id } = uploadResponse.data;
                const originalQuestion = trimmedMessage || `Summarize this document: ${fileToUpload.name}`;
                setFileToUpload(null);

                const pollStatus = setInterval(async () => {
                    try {
                        const statusResponse = await api.get(`/api/documents/status/${document_id}`, { headers });
                        if (statusResponse.data.status === 'Indexed' || statusResponse.data.status === 'Error') {
                            clearInterval(pollStatus);
                            setMessages(prev => prev.filter(m => m.id !== statusMessageId));

                            const finalPayload = { input: originalQuestion, context: { mode: 'document_qa', document_filename: statusResponse.data.filename } };
                            const finalResponse = await api.post("/agent/ask", finalPayload, { headers });

                            setMessages(prev => [...prev, { content: finalResponse.data, sender: "bot" }]);
                            saveMessageToHistory("bot", finalResponse.data);
                            setIsTyping(false);
                        }
                    } catch (pollError) {
                        clearInterval(pollStatus);
                        setIsTyping(false);
                    }
                }, 4000);

            } else {
                const payload = {
                    input: trimmedMessage,
                    context: { mode: documentContext ? 'document_qa' : 'general', document_filename: documentContext ? documentContext.filename : null }
                };
                const response = await api.post("/agent/ask", payload, { headers });
                setMessages(prev => [...prev, { content: response.data, sender: "bot" }]);
                saveMessageToHistory("bot", response.data);
                setIsTyping(false);
            }
        } catch (error) {
            console.error("API Error:", error);
            const errorContent = { output: { response_type: "confirmation", status: "error", message: "An error occurred." }, intermediate_steps: [] };
            setMessages(prev => [...prev, { content: errorContent, sender: "bot" }]);
            saveMessageToHistory("bot", errorContent);
            setIsTyping(false);
        }
    };

    const handleKeyPress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } };
    useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);
    const hasUserSentMessage = messages.length > 0;

    const renderDocumentModal = () => (
        <AnimatePresence>
            {isDocModalOpen && (
                <motion.div className="modal-overlay" onClick={() => setIsDocModalOpen(false)}>
                    <motion.div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h3>Select a Document for Context</h3>
                        <div className="document-list">
                            {userDocuments.length > 0 ? (
                                userDocuments.map(doc => (
                                    <div key={doc.id} className="document-item" onClick={() => handleSelectDocument(doc)}>
                                        <FileText size={16} />
                                        <span>{doc.filename}</span>
                                    </div>
                                ))
                            ) : (
                                <p>You haven't uploaded any documents yet.</p>
                            )}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    return (
        <div className="home-container">
            {renderDocumentModal()}
            <div className="main-content-area">
                <AnimatePresence>
                    {!hasUserSentMessage && (
                        <motion.div className="welcome-view" key="welcome" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9, position: 'absolute' }} transition={{ duration: 0.4, ease: "easeInOut" }}>
                            <div className="welcome-icon"><Sparkles size={48} /></div>
                            <h2 className="welcome-text">Hi, I’m Druv. How can I help you today?</h2>
                            <div className="suggestion-chips">
                                {suggestionChips.map((chip, i) => (
                                    <motion.button key={i} onClick={() => handleSendMessage(chip.text)} whileHover={{ y: -3 }} whileTap={{ scale: 0.97 }}>
                                        {chip.text}
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                {hasUserSentMessage && (
                    <motion.div className="chat-container" key="chat">
                        {messages.map((msg, index) => (
                            <motion.div key={index} className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}>
                                {msg.sender === 'user' ? <p>{msg.text}</p> : <AIMessage content={msg.content} />}
                            </motion.div>
                        ))}
                        {isTyping && (
                            <motion.div className="message bot-message">
                                <div className="typing-indicator"><div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div></div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </motion.div>
                )}
            </div>
            <div className="input-section">
                <AnimatePresence>
                    {fileToUpload && (
                        <motion.div className="file-preview">
                            <span>Ready to upload: <strong>{fileToUpload.name}</strong></span>
                            <button onClick={() => setFileToUpload(null)}><X size={14} /></button>
                        </motion.div>
                    )}
                    {documentContext && (
                        <motion.div className="file-preview">
                            <span>Asking about: <strong>{documentContext.filename}</strong></span>
                            <button onClick={() => setDocumentContext(null)}><X size={14} /></button>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div className="input-container">
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileChange} />
                    <motion.button className="attach-button" whileTap={{ scale: 0.9 }} onClick={() => fileInputRef.current.click()}>
                        <Paperclip size={22} />
                    </motion.button>
                    <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} onKeyPress={handleKeyPress} placeholder="Ask Druv anything, or paste an image..." className="input-field" disabled={isTyping} />
                    <div className="input-buttons">
                        <motion.button
                            className={`mode-toggle-btn ${documentContext ? 'active' : ''}`}
                            onClick={handleOpenDocSelector}
                            title="Ask about a specific document"
                        >
                            <FileText size={20} />
                        </motion.button>
                        <motion.button className="mic-button" whileTap={{ scale: 0.9 }}><Mic size={22} /></motion.button>
                        <motion.button onClick={() => handleSendMessage()} className="send-button" whileTap={{ scale: 0.9 }}><Send size={20} /></motion.button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
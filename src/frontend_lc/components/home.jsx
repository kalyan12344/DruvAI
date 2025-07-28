// src/components/Home.jsx

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Sparkles, Calendar, CheckCircle2, AlertTriangle, ExternalLink, Newspaper } from 'lucide-react';
import '../styles/home.css'; // This component will now use the new styles
import axios from "axios";
import { auth } from '../../firebase';
import { onAuthStateChanged } from 'firebase/auth';

const api = axios.create({ baseURL: "https://druv-backend-338967818277.us-central1.run.app/agent" });

// Suggestion chips to engage the user
const suggestionChips = [
    { text: "What are my most important tasks for today?" },
    { text: "Find me remote Senior Product Manager roles." },
    { text: "Summarize the latest news on AI hardware." },
];


// --- Component to render a structured calendar view ---
const CalendarCard = ({ data }) => {

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
            return new Date(timeString).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        } catch (e) {
            return timeString;
        }
    };

    return (
        <div className="structured-card calendar-card">
            <div className="card-header">
                <Calendar size={16} />
                <h4>{data.message || "Your Schedule"}</h4>
            </div>
            <div className="card-content">
                {data.events?.map((event, index) => (
                    <a
                        href={event.htmlLink} // Assumes backend provides this link
                        target="_blank"
                        rel="noopener noreferrer"
                        className="event-item"
                        key={index}
                    >
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

// --- Component to render a confirmation message ---
const ConfirmationCard = ({ data }) => {
    const isSuccess = data.status === 'success';
    return (
        <div className={`structured-card confirmation-card ${isSuccess ? 'success' : 'error'}`}>
            <div className="card-header">
                {isSuccess ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                <h4>{isSuccess ? 'Success' : 'Notice'}</h4>
            </div>
            <div className="card-content">
                <p>{data.message}</p>
            </div>
        </div>
    )
}

// --- NEW: Component to render a structured news summary ---
const NewsCard = ({ data }) => {
    return (
        <div className="structured-card news-card">
            <div className="card-header">
                <Newspaper size={16} />
                <h4>{data.message || "Latest News"}</h4>
            </div>
            <div className="card-content">
                {data.articles?.map((article, index) => (
                    <div className="article-item" key={index}>
                        <div className="article-header">
                            <span className="article-source">{article.source}</span>
                            <h5 className="article-headline">{article.headline}</h5>
                        </div>
                        <ul className="summary-points">
                            {article.summary_points?.map((point, i) => (
                                <li key={i}>{point}</li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
};


const Home = () => {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const hasUserSentMessage = messages.some(msg => msg.sender === 'user');

    const [user, setUser] = useState(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
            setUser(firebaseUser);
        });
        return () => unsubscribe();
    }, []);

    // --- This single function now handles all message types ---
    const renderMessageContent = (msg) => {
        if (typeof msg.text === 'object' && msg.text !== null) {
            const data = msg.text;
            switch (data.response_type) {
                case 'calendar_view':
                    return <CalendarCard data={data} />;
                case 'confirmation':
                    return <ConfirmationCard data={data} />;
                case 'news_summary': // ADDED: Case for news
                    return <NewsCard data={data} />;
                case 'no_events':
                    return <p>🎉 {data.message || `You're free on ${data.date_checked}!`}</p>;
                case 'conversational':
                    return <p>{data.message}</p>;
                default:
                    return <pre>{JSON.stringify(data, null, 2)}</pre>;
            }
        }
        return <p>{msg.text}</p>;
    };


    const handleSendMessage = async (content = message) => {
        const trimmedMessage = content.trim();
        if (!trimmedMessage || isTyping) return;

        const userMessage = { text: trimmedMessage, sender: "user" };
        setMessages(prev => [...prev, userMessage]);
        setMessage('');
        setIsTyping(true);

        const payload = { input: trimmedMessage };

        try {
            const response = await api.post("/ask", payload);

            let rawReply = response.data;
            let aiReply;

            if (rawReply && typeof rawReply === 'object' && rawReply.response && typeof rawReply.response === 'string') {
                try {
                    aiReply = JSON.parse(rawReply.response);
                } catch (e) {
                    aiReply = { response_type: "conversational", message: rawReply.response };
                }
            } else if (typeof rawReply === 'string') {
                try {
                    aiReply = JSON.parse(rawReply);
                } catch (e) {
                    aiReply = { response_type: "conversational", message: rawReply };
                }
            } else if (typeof rawReply === 'object' && rawReply !== null) {
                aiReply = rawReply;
            } else {
                aiReply = { response_type: "confirmation", status: "error", message: "Received an unexpected response format." };
            }

            setMessages(prev => [...prev, { text: aiReply, sender: "bot" }]);
        } catch (error) {
            console.error("API Error:", error);
            const errorMessage = {
                response_type: "confirmation",
                status: "error",
                message: "An error occurred while contacting the AI."
            };
            setMessages(prev => [...prev, { text: errorMessage, sender: "bot" }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
    };

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    return (
        <div className="home-container">
            <div className="main-content-area">
                <AnimatePresence>
                    {!hasUserSentMessage && (
                        <motion.div
                            className="welcome-view"
                            key="welcome"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9, position: 'absolute' }}
                            transition={{ duration: 0.4, ease: "easeInOut" }}
                        >
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
                    <motion.div className="chat-container" key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
                        {messages.map((msg, index) => (
                            <motion.div
                                key={index}
                                className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, ease: 'easeOut' }}
                            >
                                {renderMessageContent(msg)}
                            </motion.div>
                        ))}
                        {isTyping && (
                            <motion.div className="message bot-message" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                                <div className="typing-indicator"><div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div></div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </motion.div>
                )}
            </div>

            <div className="input-section">
                <div className="input-container">
                    <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} onKeyPress={handleKeyPress} placeholder="Ask Druv anything..." className="input-field" disabled={isTyping} />
                    <div className="input-buttons">
                        <motion.button className="mic-button" whileTap={{ scale: 0.9 }}><Mic size={22} /></motion.button>
                        <motion.button onClick={() => handleSendMessage()} className="send-button" whileTap={{ scale: 0.9 }}><Send size={20} /></motion.button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;

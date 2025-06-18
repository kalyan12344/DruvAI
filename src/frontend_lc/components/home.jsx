import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Sparkles } from 'lucide-react';
import '../styles/home.css';
import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/agent" });

// Suggestion chips to engage the user
const suggestionChips = [
    { text: "What are my most important tasks for today?" },
    { text: "Find me remote Senior Product Manager roles." },
    { text: "Summarize the latest news on AI hardware." },
];

const Home = () => {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const hasUserSentMessage = messages.some(msg => msg.sender === 'user');

    // This function correctly formats lists and bold text from the AI
    const renderFormattedMessage = (text) => {
        const lines = text?.split('\n').filter(l => l.trim() !== '');
        if (lines.length > 1 && lines.some(line => /^\s*\d+\.\s*|\s*•\s*|\s*-\s*/.test(line))) {
            return (
                <ul className="structured-list">
                    {lines.map((line, idx) => (
                        <li key={idx} dangerouslySetInnerHTML={{
                            __html: line.replace(/^\s*\d+\.\s*|\s*•\s*|\s*-\s*/, '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        }} />
                    ))}
                </ul>
            );
        }
        return <p dangerouslySetInnerHTML={{ __html: text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />;
    };

    // Handles sending a message to the backend
    const handleSendMessage = async (content = message) => {
        const trimmedMessage = content.trim();
        if (!trimmedMessage || isTyping) return;

        setMessages(prev => [...prev, { text: trimmedMessage, sender: "user" }]);
        setMessage('');
        setIsTyping(true);

        const pageContentForAgent = window.currentPageTextForAgent || null;
        const payload = pageContentForAgent
            ? { input: { question: trimmedMessage, page_content: pageContentForAgent } }
            : { input: trimmedMessage };

        try {
            const response = await api.post("/ask", payload);
            const aiReply = response.data.response || "I could not find an answer.";
            setMessages(prev => [...prev, { text: aiReply, sender: "bot" }]);
        } catch (error) {
            console.error("API Error:", error);
            const errorMessage = "An error occurred while contacting the AI.";
            setMessages(prev => [...prev, { text: errorMessage, sender: "bot" }]);
        } finally {
            setIsTyping(false);
        }
    };

    // Allows sending messages with the Enter key
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Auto-scrolls to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    return (
        <div className="home-container">
            {/* The main content area grows to fill the space above the input */}
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
                                    <motion.button
                                        key={i}
                                        onClick={() => handleSendMessage(chip.text)}
                                        whileHover={{ y: -3 }}
                                        whileTap={{ scale: 0.97 }}
                                    >
                                        {chip.text}
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {hasUserSentMessage && (
                    <motion.div
                        className="chat-container"
                        key="chat"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.5 }}
                    >
                        {messages.map((msg, index) => (
                            <motion.div
                                key={index}
                                className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.3, ease: 'easeOut' }}
                            >
                                {renderFormattedMessage(msg.text)}
                            </motion.div>
                        ))}
                        {isTyping && (
                            <motion.div
                                className="message bot-message"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <div className="typing-indicator">
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                    <div className="typing-dot"></div>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </motion.div>
                )}
            </div>

            {/* The input section is now a permanent part of the layout */}
            <div className="input-section">
                <div className="input-container">
                    <input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask Druv anything, or describe a task..."
                        className="input-field"
                        disabled={isTyping}
                    />
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

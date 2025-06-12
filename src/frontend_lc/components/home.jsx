import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic } from 'lucide-react';
import '../styles/home.css';

import axios from "axios";
const api = axios.create({ baseURL: "http://localhost:8000/agent" });


const Home = () => {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([

    ]);
    const messagesEndRef = useRef(null);
    const hasUserSentMessage = messages.some(msg => msg.sender === 'user');
    const renderFormattedMessage = (text) => {
        const isBulletOrNumberedList = /^\d+\.\s|\•\s|-\s/.test(text);

        // Convert to lines
        const lines = text?.split('\n').filter(l => l.trim() !== '');

        // Auto-format if list detected
        if (lines.length > 1 && lines.some(line => /^\d+\.\s|\•\s|-\s/.test(line))) {
            return (
                <ul className="structured-list">
                    {lines.map((line, idx) => (
                        <li key={idx} dangerouslySetInnerHTML={{
                            __html: line
                                .replace(/^\d+\.\s|\•\s|-\s/, '') // Remove list prefix
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // bold
                        }} />
                    ))}
                </ul>
            );
        }

        // Bold only
        if (/\*\*(.*?)\*\*/.test(text)) {
            return <p dangerouslySetInnerHTML={{
                __html: text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            }} />;
        }

        return <p>{text}</p>;
    };


    const handleSendMessage = async () => {
        const trimmedMessage = message.trim();
        if (!trimmedMessage) return;

        // Add user message to UI
        setMessages(prev => [...prev, { text: trimmedMessage, sender: "user" }]);
        setMessage('');

        // Construct payload (same as AIInterface logic)
        const pageContentForAgent = window.currentPageTextForAgent || null;
        const payload = pageContentForAgent && pageContentForAgent.trim() !== ""
            ? { input: { question: trimmedMessage, page_content: pageContentForAgent } }
            : { input: trimmedMessage };

        try {
            const response = await api.post("/ask", payload);
            const aiReply = response.data.response || "⚠️ No answer received from agent.";
            setMessages(prev => [...prev, { text: aiReply, sender: "bot" }]);
        } catch (error) {
            console.error("API Error:", error);
            const errorMessage = "❌ Failed to get a response from the AI.";
            setMessages(prev => [...prev, { text: errorMessage, sender: "bot" }]);
        }
    };


    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    return (
        <div className={`home-container ${hasUserSentMessage ? 'chat-mode' : ''}`}>
            <div className="main-content">
                {/* Robot Avatar - Only visible before first user message */}
                {!hasUserSentMessage && (
                    <div className="robot-section">

                        <div className="robot-glow"></div>
                        <div className="robot-glass">
                            <div className="robot-body">
                                <div className="robot-head">
                                    <div className="robot-eye left"></div>
                                    <div className="robot-eye right"></div>
                                    <div className="robot-eye-glow left"></div>
                                    <div className="robot-eye-glow right"></div>
                                </div>

                            </div>
                        </div>
                    </div>
                )}

                {/* Greeting - Only visible before first user message */}
                {!hasUserSentMessage && (
                    <div className="greeting">
                        <h2>Hi, how can I help today?</h2>
                    </div>
                )}

                {/* Chat Container */}
                <div className="chat-container">
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'}`}
                        >
                            <div className="message-content">
                                {/* {renderFormattedMessage(msg)} */}
                                {msg.text}
                            </div>

                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area - Fixed at bottom in chat mode */}
                <div className="input-section">
                    <div className="input-container">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask Druv anything..."
                            className="input-field"
                        />
                        <div className="input-buttons">
                            <button className="mic-button">
                                <Mic size={24} />
                            </button>
                            <button
                                onClick={handleSendMessage}
                                className="send-button"
                            >
                                <Send size={20} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
import { useState, useEffect } from "react";
import axios from "axios";

// Icon Imports - added FaSearch
import { FaPlus, FaTimes, FaPen, FaPaperPlane, FaArchive, FaSearch } from "react-icons/fa";
import { SiGmail } from "react-icons/si";
import { BsInboxFill, BsQuestionCircleFill } from "react-icons/bs";
import { IoSparkles } from "react-icons/io5";

import { motion, AnimatePresence } from "framer-motion";
import "../styles/gmail.css";
import Contacts from "./contacts";

const Gmail = () => {
    // --- Core State ---
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [connections, setConnections] = useState({ connected: false, user_email: null });
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [selectedMessage, setSelectedMessage] = useState(null);
    const [isDetailLoading, setIsDetailLoading] = useState(false);

    // --- State for AI Actions & Modals ---
    const [isAgentReplying, setIsAgentReplying] = useState(false);
    const [aiDraft, setAiDraft] = useState("");
    const [askAiResponse, setAskAiResponse] = useState("");
    const [isPerspectiveModalOpen, setIsPerspectiveModalOpen] = useState(false);
    const [replyPerspective, setReplyPerspective] = useState("");
    const [isAskAiModalOpen, setIsAskAiModalOpen] = useState(false);
    const [askAiQuery, setAskAiQuery] = useState("");

    // --- NEW: State for Search ---
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearchVisible, setIsSearchVisible] = useState(false);
    const [isSearchActive, setIsSearchActive] = useState(false);


    // --- Data Fetching and Event Handlers ---

    const fetchInitialData = async () => {
        setLoading(true);
        setError(null);
        setIsSearchActive(false); // Reset search state
        setSearchQuery("");
        try {
            const statusResponse = await axios.get("http://127.0.0.1:8000/api/gmail/status");
            const gmailConnection = statusResponse.data?.google_gmail;
            if (gmailConnection && gmailConnection.connected) {
                setConnections(gmailConnection);
                const messagesResponse = await axios.get("http://127.0.0.1:8000/api/gmail/messages");
                setMessages(messagesResponse.data || []);
            } else {
                setConnections({ connected: false, user_email: null });
            }
        } catch (err) {
            console.error("Error fetching initial data:", err);
            setError("Could not load connection status from the server.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInitialData();
    }, []);

    const handleEmailClick = async (messageId) => {
        if (selectedMessage?.id === messageId) return;
        setIsDetailLoading(true);
        setSelectedMessage(null);
        setAiDraft("");
        setAskAiResponse("");
        try {
            const response = await axios.get(`http://127.0.0.1:8000/api/gmail/message/${messageId}`);
            setSelectedMessage(response.data);
        } catch (err) {
            console.error("Failed to fetch email details", err);
        } finally {
            setIsDetailLoading(false);
        }
    };

    const handleConnectGmail = () => {
        const authUrl = `https://druv-backend-338967818277.us-central1.run.app/api/google/auth/login?service=gmail`;
        const popup = window.open(authUrl, `gmail-auth-popup`, 'width=600,height=700');
        setIsMenuOpen(false);
        const checkPopupClosed = setInterval(() => {
            if (!popup || popup.closed) {
                clearInterval(checkPopupClosed);
                window.location.reload();
            }
        }, 1000);
    };

    const handleDraftReply = async (perspective) => {
        if (!selectedMessage) return;
        setIsAgentReplying(true);
        setAiDraft("");
        try {
            const response = await axios.post("http://127.0.0.1:8000/api/gmail/draft-reply", {
                subject: selectedMessage.subject,
                snippet: selectedMessage.snippet,
                perspective: perspective
            });
            setAiDraft(response.data.draft);
        } catch (err) {
            setAiDraft("Sorry, I couldn't generate a draft.");
        } finally {
            setIsAgentReplying(false);
            setReplyPerspective("");
        }
    };

    const handleAskAi = async (query) => {
        if (!selectedMessage || !query.trim()) return;
        setIsAgentReplying(true);
        setAskAiResponse("");
        try {
            const response = await axios.post(`http://127.0.0.1:8000/api/gmail/message/${selectedMessage.id}/agent-query`, { query });
            setAskAiResponse(response.data.response);
        } catch (err) {
            setAskAiResponse("Sorry, I couldn't process your request.");
        } finally {
            setIsAgentReplying(false);
            setAskAiQuery("");
        }
    };

    // --- NEW: Handler for Search ---
    const handleSearch = async (e) => {
        if (e.key === 'Enter' && searchQuery.trim()) {
            setLoading(true);
            setSelectedMessage(null); // Close any open message
            try {
                const response = await axios.get(`http://127.0.0.1:8000/api/gmail/search?q=${searchQuery}`);
                setMessages(response.data || []);
                setIsSearchActive(true);
            } catch (err) {
                console.error("Error searching emails:", err);
                setError("Failed to perform search.");
            } finally {
                setLoading(false);
            }
        }
    };


    // --- Render Functions ---

    const renderHeader = () => (
        <div className="gmail-header">
            <div className="gmail-title"><BsInboxFill /><h2>Inbox</h2></div>
            <div className="gmail-actions">
                {/* --- NEW: Search UI --- */}
                <AnimatePresence>
                    {isSearchVisible && (
                        <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 'auto', opacity: 1 }} exit={{ width: 0, opacity: 0 }}>
                            <input
                                type="text"
                                className="search-input"
                                placeholder="Search mail..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={handleSearch}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
                <button onClick={() => setIsSearchVisible(!isSearchVisible)} className="action-btn !p-2 !rounded-full" title="Search mail">
                    <FaSearch size={12} />
                </button>
                <div className="connected-accounts">
                    {connections.connected && (
                        <SiGmail color="#D93025" size={22} className="icon" title={`Gmail Connected: ${connections.user_email}`} />
                    )}
                    <div className="action-btn-wrapper">
                        <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="action-btn !p-2 !rounded-full" title="Connect account">
                            <FaPlus size={12} />
                        </button>
                        <AnimatePresence>
                            {isMenuOpen && (
                                <motion.div className="connect-menu" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}>
                                    <button onClick={handleConnectGmail} disabled={connections.connected}>
                                        <SiGmail /> Connect Gmail
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderContentList = () => {
        if (loading) { return <div className="centered-state">Loading...</div>; }
        if (error) { return <div className="centered-state error">{error}</div>; }
        if (!connections.connected) { return <div className="centered-state">Please connect your Gmail account.</div>; }

        return (
            <>
                {/* --- NEW: Clear Search button --- */}
                {isSearchActive && (
                    <div className="search-results-header">
                        <span>Showing results for "{searchQuery}"</span>
                        <button onClick={fetchInitialData} className="action-pill">Clear Search</button>
                    </div>
                )}
                {messages.length === 0 ? (
                    <div className="centered-state">{isSearchActive ? "No results found." : "Your inbox is empty."}</div>
                ) : (
                    <div className="email-list-container">
                        {messages.map((msg) => (
                            <motion.div key={msg.id} className={`email-item ${selectedMessage?.id === msg.id ? 'active' : ''}`} onClick={() => handleEmailClick(msg.id)}>
                                <div className="email-sender">{msg.from || 'No Sender'}</div>
                                <div className="email-subject">{msg.subject || 'No Subject'}</div>
                                <div className="email-snippet">{msg.snippet || 'No content'}</div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </>
        );
    };

    const renderDetailView = () => {
        if (isDetailLoading) { return <div className="centered-state">Loading Email...</div>; }
        if (!selectedMessage) { return <div className="centered-state">Select an email to read</div>; }
        return (
            <>
                <div className="detail-header">
                    <div className="detail-header-info">
                        <h3 className="detail-subject">{selectedMessage.subject}</h3>
                        <p className="detail-from">{selectedMessage.from}</p>
                    </div>
                    <button onClick={() => setSelectedMessage(null)} className="close-btn" title="Close"><FaTimes /></button>
                </div>
                <div className="detail-actions">
                    <button className="action-pill" onClick={() => alert('Archived!')}><FaArchive /> Archive</button>
                    <button className="action-pill" onClick={() => setIsAskAiModalOpen(true)} disabled={isAgentReplying}><BsQuestionCircleFill /> Ask AI</button>
                    <button className="action-pill primary" onClick={() => setIsPerspectiveModalOpen(true)} disabled={isAgentReplying}>
                        <IoSparkles /> {isAgentReplying ? 'Thinking...' : 'Draft Reply with AI'}
                    </button>
                </div>
                <div className="detail-body">
                    <div dangerouslySetInnerHTML={{ __html: selectedMessage.body }} />
                </div>
                <AnimatePresence>
                    {askAiResponse && (
                        <motion.div className="ai-response-card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                            <div className="ai-response-header">
                                <span>AI Assistant</span>
                                <button onClick={() => setAskAiResponse("")}><FaTimes /></button>
                            </div>
                            <div className="ai-response-content">{askAiResponse}</div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <AnimatePresence>
                    {aiDraft && (
                        <motion.div className="ai-draft-container" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                            <textarea className="ai-draft-textarea" value={aiDraft} onChange={(e) => setAiDraft(e.target.value)} />
                            <div className="ai-draft-actions">
                                <button className="action-pill" onClick={() => setAiDraft("")}>Discard</button>
                                <button className="action-pill send" onClick={() => alert('Sending!')}><FaPaperPlane /> Send</button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </>
        );
    };

    const renderPerspectiveModal = () => (
        <AnimatePresence>
            {isPerspectiveModalOpen && (
                <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <motion.div className="modal-content" initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -50, opacity: 0 }} onClick={(e) => e.stopPropagation()}>
                        <h3>What's the goal of your reply?</h3>
                        <p>E.g., "Politely decline", "Ask for a 10% discount", "Sound excited"</p>
                        <input type="text" className="modal-input" value={replyPerspective} onChange={(e) => setReplyPerspective(e.target.value)} placeholder="Enter perspective..." autoFocus />
                        <div className="modal-actions">
                            <button className="action-pill" onClick={() => setIsPerspectiveModalOpen(false)}>Cancel</button>
                            <button className="action-pill primary" onClick={() => { setIsPerspectiveModalOpen(false); handleDraftReply(replyPerspective); }}>Generate Draft</button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    const renderAskAiModal = () => (
        <AnimatePresence>
            {isAskAiModalOpen && (
                <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <motion.div className="modal-content" initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -50, opacity: 0 }} onClick={(e) => e.stopPropagation()}>
                        <h3>Ask AI about this email</h3>
                        <p>E.g., "Summarize this", "What is the order number?", "Track this package"</p>
                        <input type="text" className="modal-input" value={askAiQuery} onChange={(e) => setAskAiQuery(e.target.value)} placeholder="Enter your question..." autoFocus />
                        <div className="modal-actions">
                            <button className="action-pill" onClick={() => setIsAskAiModalOpen(false)}>Cancel</button>
                            <button className="action-pill primary" onClick={() => { setIsAskAiModalOpen(false); handleAskAi(askAiQuery); }}>Ask</button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    return (
        <div className="gmail-page">
            <div className="gmail-container">
                {renderHeader()}
                <div className="gmail-split-container">
                    <div className="email-list-pane">{renderContentList()}</div>
                    <div className="email-detail-pane">{renderDetailView()}</div>
                </div>
                {renderPerspectiveModal()}
                {renderAskAiModal()}
            </div>
            <div>
                <Contacts />
            </div>
        </div>
    );
};

export default Gmail;

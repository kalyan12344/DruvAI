import { useState, useEffect } from "react";
import axios from "axios";
// Added new icons for the connection prompt
import { FaSearch, FaUserCircle, FaArrowRight } from "react-icons/fa";
import { SiGoogle } from "react-icons/si";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/contacts.css";

const Contacts = () => {
    // --- State Management ---
    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearchVisible, setIsSearchVisible] = useState(false);
    const [isSearchActive, setIsSearchActive] = useState(false);
    const [isConnected, setIsConnected] = useState(false);

    // --- Data Fetching ---
    useEffect(() => {
        const checkConnectionAndFetch = async () => {
            setLoading(true);
            setError(null);
            try {
                // This endpoint should check db.json for the 'connected_contacts' status
                const statusResponse = await axios.get("http://127.0.0.1:8000/api/contacts/status");
                const contactsConnection = statusResponse.data?.google;

                if (contactsConnection && contactsConnection.connected) {
                    setIsConnected(true);
                    await fetchInitialContacts();
                } else {
                    setIsConnected(false);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error checking connection status:", err);
                setError("Could not verify your connection status.");
                setIsConnected(false);
                setLoading(false);
            }
        };
        checkConnectionAndFetch();
    }, []);

    const fetchInitialContacts = async () => {
        setLoading(true); // Show loading specific to this fetch
        setError(null);
        setIsSearchActive(false);
        setSearchQuery("");
        try {
            // This now fetches ALL contacts from the updated backend endpoint
            const response = await axios.get("http://127.0.0.1:8000/api/contacts/list");
            setContacts(response.data || []);
        } catch (err) {
            console.error("Error fetching initial contacts:", err);
            setError("Could not load contacts. Please ensure permissions are granted.");
            setContacts([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async (e) => {
        if (e.key === 'Enter' && searchQuery.trim()) {
            setLoading(true);
            setError(null);
            try {
                const response = await axios.get(`http://127.0.0.1:8000/api/contacts/search?name=${searchQuery}`);
                setContacts(response.data ? [response.data] : []);
                setIsSearchActive(true);
            } catch (err) {
                setError(`No contact found for "${searchQuery}".`);
                setContacts([]);
            } finally {
                setLoading(false);
            }
        }
    };

    const handleConnectContacts = () => {
        const authUrl = `http://127.0.0.1:8000/api/google/auth/login?service=contacts`;
        const popup = window.open(authUrl, `contacts-auth-popup`, 'width=600,height=700');
        const checkPopupClosed = setInterval(() => {
            if (!popup || popup.closed) {
                clearInterval(checkPopupClosed);
                window.location.reload();
            }
        }, 1000);
    };

    // --- Render Functions ---

    const renderHeader = () => (
        <div className="contacts-header">
            <div className="contacts-title">
                <FaUserCircle />
                <h2>Contacts</h2>
            </div>
            {isConnected && (
                <div className="contacts-actions">
                    <AnimatePresence>
                        {isSearchVisible && (
                            <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 'auto', opacity: 1 }} exit={{ width: 0, opacity: 0 }}>
                                <input type="text" className="search-input" placeholder="Search contacts..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={handleSearch} autoFocus />
                            </motion.div>
                        )}
                    </AnimatePresence>
                    <button onClick={() => setIsSearchVisible(!isSearchVisible)} className="action-btn !p-2 !rounded-full" title="Search contacts">
                        <FaSearch size={12} />
                    </button>
                </div>
            )}
        </div>
    );

    const renderConnectPrompt = () => (
        <div className="connect-prompt-container">
            <h3>Let Druv manage your contacts</h3>
            <p>He can find and organize contact details.</p>
            <button className="connect-button" onClick={handleConnectContacts}>
                <SiGoogle />
                <span>Connect Google Contacts</span>
                <FaArrowRight />
            </button>
        </div>
    );

    const renderContactList = () => {
        // --- UPDATED LOGIC ---
        // This structure ensures the header is always shown when a search is active.
        return (
            <div className="contact-list-container">
                {isSearchActive && (
                    <div className="search-results-header">
                        <span>Showing results for "{searchQuery}"</span>
                        <button onClick={fetchInitialContacts} className="action-pill">Clear Search & View All</button>
                    </div>
                )}
                {loading ? (
                    <div className="centered-state">Loading...</div>
                ) : error ? (
                    <div className="centered-state error">{error}</div>
                ) : contacts.length === 0 ? (
                    <div className="centered-state">{isSearchActive ? `No results found for "${searchQuery}".` : "No contacts found in your Google account."}</div>
                ) : (
                    contacts.map((contact, index) => <ContactCard key={index} contact={contact} index={index} />)
                )}
            </div>
        );
    };

    const ContactCard = ({ contact, index }) => (
        <motion.div className="contact-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.02 }}>
            <div className="contact-avatar"><FaUserCircle /></div>
            <div className="contact-info">
                <span className="contact-name">{contact.name || 'No Name'}</span>
                <span className="contact-email">{contact.email || 'No Email'}</span>
                <span className="contact-phone">{contact.phone || 'No Phone Number'}</span>
            </div>
        </motion.div>
    );

    return (
        <div className="contacts-container">
            {renderHeader()}
            {/* The main render logic is simplified */}
            {!isConnected && !loading ? renderConnectPrompt() : renderContactList()}
        </div>
    );
};

export default Contacts;

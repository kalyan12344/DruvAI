import { useState, useEffect } from "react";
import axios from "axios";
import { FaNewspaper, FaCog, FaSync } from "react-icons/fa";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../context/authcontext";
import "../styles/news.css";

const API_BASE_URL = "https://druv-backend-338967818277.us-central1.run.app";

const News = () => {
    const [briefings, setBriefings] = useState([]);
    const [settings, setSettings] = useState({ topics: [], enabled: true });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isNewsEnabled, setIsNewsEnabled] = useState(true);
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
    const [tempTopics, setTempTopics] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    const { getAuthToken } = useAuth();

    const fetchNewsData = async () => {
        setLoading(true);
        setError(null);
        try {
            const token = await getAuthToken();
            if (!token) throw new Error("User not authenticated.");
            const headers = { 'Authorization': `Bearer ${token}` };

            const settingsResponse = await axios.get(`${API_BASE_URL}/api/news/settings`, { headers });
            const fetchedSettings = settingsResponse.data || { topics: [], enabled: false };
            console.log(fetchedSettings)

            setSettings(fetchedSettings);
            setIsNewsEnabled(fetchedSettings.enabled);
            // This is the corrected line
            setTempTopics((fetchedSettings.topics || []).join("\n"));

            if (fetchedSettings.enabled) {
                const briefingsResponse = await axios.get(`${API_BASE_URL}/api/news/briefings/latest`, { headers });
                console.log("briefing", briefingsResponse)
                setBriefings(briefingsResponse.data || []);
            } else {
                setBriefings([]);
            }

        } catch (err) {
            console.error("Error fetching news data:", err);
            setError("Could not load your news briefing. Please try again later.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNewsData();
    }, [getAuthToken]);

    const handleSaveSettings = async () => {
        setIsSaving(true);
        const topicsArray = tempTopics.split('\n').map(t => t.trim()).filter(t => t);
        const newSettings = { ...settings, topics: topicsArray };

        try {
            const token = await getAuthToken();
            if (!token) throw new Error("User not authenticated.");
            const headers = { 'Authorization': `Bearer ${token}` };

            await axios.post(`${API_BASE_URL}/api/news/settings`, newSettings, { headers });
            setSettings(newSettings);
            setIsSettingsModalOpen(false);
        } catch (err) {
            console.error("Failed to save settings:", err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleRefresh = async () => {
        setIsRefreshing(true);
        setError(null);
        try {
            const token = await getAuthToken();
            if (!token) throw new Error("User not authenticated.");
            const headers = { 'Authorization': `Bearer ${token}` };

            await axios.get(`${API_BASE_URL}/api/news/briefings/generate`, { headers });
            await fetchNewsData();
        } catch (err) {
            console.error("Error refreshing briefings:", err);
            setError("Failed to generate a new briefing.");
        } finally {
            setIsRefreshing(false);
        }
    };

    const handleOpenSettings = () => {
        setTempTopics((settings.topics || []).join("\n"));
        setIsSettingsModalOpen(true);
    };

    const renderHeader = () => (
        <div className="news-header">
            <div className="news-title"><FaNewspaper /><h2>Daily Briefing</h2></div>
            <div className="news-actions">
                <button onClick={handleRefresh} className={`action-btn !p-2 !rounded-full ${isRefreshing ? 'refreshing' : ''}`} title="Refresh Now" disabled={isRefreshing}>
                    <FaSync size={14} />
                </button>
                <button onClick={handleOpenSettings} className="action-btn !p-2 !rounded-full" title="News Settings">
                    <FaCog size={14} />
                </button>
            </div>
        </div>
    );

    const renderBriefingList = () => {
        if (loading) { return <div className="centered-state">Loading your briefing...</div>; }
        if (error) { return <div className="centered-state error">{error}</div>; }

        if (briefings.length === 0) {
            return (
                <div className="centered-state">
                    <span>Your briefing is empty.</span>
                    <button onClick={handleOpenSettings} className="action-pill mt-4">Add Topics</button>
                </div>
            );
        }

        return (
            <div className="briefing-list-container">
                {briefings.map((briefing, index) => (
                    <motion.div
                        key={index}
                        className="briefing-item"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <h3 className="briefing-topic">{briefing.topic}</h3>
                        <p className="briefing-summary">{briefing.summary}</p>
                    </motion.div>
                ))}
            </div>
        );
    };

    const renderSettingsModal = () => (
        <AnimatePresence>
            {isSettingsModalOpen && (
                <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <motion.div className="modal-content" initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -50, opacity: 0 }} onClick={(e) => e.stopPropagation()}>
                        <h3>News Briefing Topics</h3>
                        <p>Enter one topic per line. These will be used to generate your briefing each morning.</p>
                        <textarea
                            className="modal-textarea"
                            value={tempTopics}
                            onChange={(e) => setTempTopics(e.target.value)}
                            placeholder="e.g., latest AI developments&#10;e.g., Formula 1 results"
                            rows={5}
                        />
                        <div className="modal-actions">
                            <button className="action-pill" onClick={() => setIsSettingsModalOpen(false)}>Cancel</button>
                            <button className="action-pill primary" onClick={handleSaveSettings} disabled={isSaving}>
                                {isSaving ? "Saving..." : "Save Topics"}
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    if (!isNewsEnabled) {
        return null;
    }

    return (
        <div className="news-page">
            <div className="news-container">
                {renderHeader()}
                {renderBriefingList()}
            </div>
            {renderSettingsModal()}
        </div>
    );
};

export default News;
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useJobsFeature } from '../context/jobfeaturecontext.jsx';
import ResumeUploadOverlay from './resumeoverlay.jsx';
import '../styles/settings.css';

const SettingsTab = () => {
    // --- State from Jobs Context ---
    const {
        jobsEnabled,
        setJobsEnabled,
        hasUploadedResume,
        isResumeModalOpen,
        setIsResumeModalOpen
    } = useJobsFeature();

    // --- Local State for this Component ---
    const [newsEnabled, setNewsEnabled] = useState(false);
    const [savingJobs, setSavingJobs] = useState(false);
    const [savingNews, setSavingNews] = useState(false);

    // --- Fetch initial state for the news toggle ---
    useEffect(() => {
        const fetchNewsSettings = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/news/settings');
                if (response.data && typeof response.data.enabled !== 'undefined') {
                    setNewsEnabled(response.data.enabled);
                }
            } catch (error) {
                console.error("Failed to fetch news settings:", error);
            }
        };
        fetchNewsSettings();
    }, []);


    // --- Logic for AI Job Assistant Toggle ---
    const saveJobToggleState = async (enabledState) => {
        setSavingJobs(true);
        try {
            await axios.post('http://localhost:8000/api/settings/jobs-toggle', {
                enabled: enabledState
            });
        } catch (error) {
            console.error("Failed to save job setting:", error);
            setJobsEnabled(!enabledState); // Revert on failure
        } finally {
            setSavingJobs(false);
        }
    };

    const handleJobToggleClick = () => {
        const isTurningOn = !jobsEnabled;
        setJobsEnabled(isTurningOn); // Optimistic UI update

        if (isTurningOn) {
            if (!hasUploadedResume) {
                setIsResumeModalOpen(true);
            } else {
                saveJobToggleState(true);
            }
        } else {
            saveJobToggleState(false);
        }
    };

    // --- Logic for AI News Briefing Toggle (Simplified) ---
    const saveNewsToggleState = async (enabledState) => {
        setSavingNews(true);
        try {
            // Directly post the new enabled state to a dedicated endpoint.
            // This no longer needs to fetch other settings first.
            await axios.post('http://localhost:8000/api/news/settings/toggle', {
                enabled: enabledState
            });
        } catch (error) {
            console.error("Failed to save news setting:", error);
            setNewsEnabled(!enabledState); // Revert on failure
        } finally {
            setSavingNews(false);
        }
    };

    const handleNewsToggleClick = () => {
        const isTurningOn = !newsEnabled;
        setNewsEnabled(isTurningOn); // Optimistic UI update
        saveNewsToggleState(isTurningOn);
    };

    return (
        <div className="settings-tab-glass">
            <h2 className="settings-title">🔧 Settings</h2>
            <div style={{ display: "flex", flexWrap: "wrap", flexDirection: "row", gap: "30px" }}>
                {/* --- Job Assistant Card --- */}
                <div className="setting-card">
                    <div className="setting-info">
                        <h3 className="setting-name">Enable AI Job Assistant</h3>
                        <p className="setting-desc">
                            Let Druv automatically match jobs based on your resume and show 20 daily openings tailored to you.
                        </p>
                    </div>
                    <label className="glass-switch">
                        <input
                            type="checkbox"
                            checked={jobsEnabled}
                            onChange={handleJobToggleClick}
                            disabled={savingJobs}
                        />
                        <span className="glass-slider"></span>
                    </label>
                </div>

                {/* --- News Briefing Card --- */}
                <div className="setting-card">
                    <div className="setting-info">
                        <h3 className="setting-name">Enable AI News Briefing Assistant</h3>
                        <p className="setting-desc">
                            Let Druv automatically fetch you news on topics you want every morning.
                        </p>
                    </div>
                    <label className="glass-switch">
                        <input
                            type="checkbox"
                            checked={newsEnabled}
                            onChange={handleNewsToggleClick}
                            disabled={savingNews}
                        />
                        <span className="glass-slider"></span>
                    </label>
                </div>
            </div>

            {/* Conditionally render the overlay for resume upload */}
            {isResumeModalOpen && <ResumeUploadOverlay />}

            {(savingJobs || savingNews) && <div className="save-status">Saving your preference...</div>}
        </div>
    );
};

export default SettingsTab;

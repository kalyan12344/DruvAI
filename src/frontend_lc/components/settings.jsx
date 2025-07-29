import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useJobsFeature } from '../context/jobfeaturecontext.jsx';
import { useAuth } from '../context/authcontext.jsx';
import ResumeUploadOverlay from './resumeoverlay.jsx';
import '../styles/settings.css';

const API_BASE_URL = "https://druv-backend-338967818277.us-central1.run.app";

const SettingsTab = () => {
    const {
        jobsEnabled,
        setJobsEnabled,
        hasUploadedResume,
        isResumeModalOpen,
        setIsResumeModalOpen
    } = useJobsFeature();

    const { getAuthToken } = useAuth();
    const [newsEnabled, setNewsEnabled] = useState(false);
    const [savingJobs, setSavingJobs] = useState(false);
    const [savingNews, setSavingNews] = useState(false);

    useEffect(() => {
        const fetchNewsSettings = async () => {
            try {
                const token = await getAuthToken();
                if (!token) return;

                const response = await axios.get(`${API_BASE_URL}/api/news/settings`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                console.log(response)
                if (response.data && typeof response.data.enabled !== 'undefined') {
                    setNewsEnabled(response.data.enabled);
                }
            } catch (error) {
                console.error("Failed to fetch news settings:", error);
            }
        };
        fetchNewsSettings();
    }, [getAuthToken]);


    const saveJobToggleState = async (enabledState) => {
        setSavingJobs(true);
        try {
            const token = await getAuthToken();
            if (!token) throw new Error("User not authenticated.");

            await axios.post(`${API_BASE_URL}/api/settings/jobs-toggle`, {
                enabled: enabledState
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
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
        setJobsEnabled(isTurningOn);

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

    const saveNewsToggleState = async (enabledState) => {
        setSavingNews(true);
        try {
            const token = await getAuthToken();
            if (!token) throw new Error("User not authenticated.");

            await axios.post(`${API_BASE_URL}/api/news/settings/toggle`, {
                enabled: enabledState
            }, {
                headers: { 'Authorization': `Bearer ${token}` }
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
        setNewsEnabled(isTurningOn);
        saveNewsToggleState(isTurningOn);
    };

    return (
        <div className="settings-tab-glass">
            <h2 className="settings-title">🔧 Settings</h2>
            <div style={{ display: "flex", flexWrap: "wrap", flexDirection: "row", gap: "30px" }}>
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

            {isResumeModalOpen && <ResumeUploadOverlay />}
            {(savingJobs || savingNews) && <div className="save-status">Saving your preference...</div>}
        </div>
    );
};

export default SettingsTab;
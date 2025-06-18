// frontend_lc/components/settings.jsx (Corrected)

import React, { useState } from 'react';
import { useJobsFeature } from '../context/jobfeaturecontext.jsx';
import ResumeUploadOverlay from './resumeoverlay.jsx'; // Import the overlay
import '../styles/settings.css';

const SettingsTab = () => {
    // Get all the necessary state and setters from the context
    const {
        jobsEnabled,
        setJobsEnabled,
        loading,
        hasUploadedResume,
        isResumeModalOpen,
        setIsResumeModalOpen
    } = useJobsFeature();

    const [saving, setSaving] = useState(false);

    // Reusable function to save the toggle state to the backend
    const saveToggleState = async (enabledState) => {
        setSaving(true);
        try {
            // --- THIS IS THE FIX ---
            // Use the full URL to your FastAPI backend
            const response = await fetch('http://localhost:8000/api/settings/jobs-toggle', {
                // --- END OF FIX ---
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: enabledState })
            });
            if (!response.ok) {
                throw new Error('API call failed');
            }
        } catch (error) {
            console.error("Failed to save setting:", error);
            // If API fails, revert the state to what it was before the click
            setJobsEnabled(!enabledState);
        } finally {
            setSaving(false);
        }
    };

    const handleToggleClick = () => {
        const isTurningOn = !jobsEnabled;
        setJobsEnabled(isTurningOn); // Optimistically update the UI

        if (isTurningOn) {
            if (!hasUploadedResume) {
                // If turning on for the first time, open the overlay.
                // The overlay's logic will handle saving the state upon successful upload.
                setIsResumeModalOpen(true);
            } else {
                // If they already have a resume, just save the "enabled" state.
                saveToggleState(true);
            }
        } else {
            // Logic for turning the feature OFF
            saveToggleState(false);
        }

    };



    return (
        <div className="settings-tab-glass">
            <h2 className="settings-title">🔧 Settings</h2>
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
                        onChange={handleToggleClick}
                        disabled={saving}
                    />
                    <span className="glass-slider"></span>
                </label>
            </div>
            {saving && <div className="save-status">Saving your preference...</div>}

            {/* Conditionally render the overlay */}
            {isResumeModalOpen && <ResumeUploadOverlay />}
        </div>
    );
};

export default SettingsTab;
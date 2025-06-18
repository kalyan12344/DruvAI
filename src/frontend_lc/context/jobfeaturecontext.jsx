// frontend_lc/context/jobfeaturecontext.jsx (Corrected)

import React, { createContext, useState, useContext, useEffect } from 'react';

// Create the context
export const JobsFeatureContext = createContext();

// Create the provider component
export const JobsFeatureProvider = ({ children }) => {
    const [jobsEnabled, setJobsEnabled] = useState(false);
    const [loading, setLoading] = useState(true);
    const [hasUploadedResume, setHasUploadedResume] = useState(false);
    const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);

    // This useEffect hook runs once when the component is first mounted.
    useEffect(() => {
        const fetchInitialSettings = async () => {
            setLoading(true);
            try {
                // --- THIS CODE IS NOW ACTIVE ---
                // Fetch the toggle status from the backend
                const settingsResponse = await fetch('http://localhost:8000/api/settings/jobs-toggle-status');
                const settingsData = await settingsResponse.json();
                setJobsEnabled(settingsData.enabled);

                // Fetch the resume status from the backend
                const resumeResponse = await fetch('http://localhost:8000/api/resume/status');
                const resumeData = await resumeResponse.json();
                setHasUploadedResume(resumeData.hasUploadedResume);
                // --- END OF ACTIVE CODE ---

            } catch (error) {
                console.error("Failed to load user settings:", error);
                // In case of error, we'll just stick with the default 'false' states
            } finally {
                setLoading(false);
            }
        };

        fetchInitialSettings();
    }, []); // The empty dependency array [] ensures this runs only once on load

    const value = {
        jobsEnabled,
        setJobsEnabled,
        loading,
        hasUploadedResume,
        setHasUploadedResume,
        isResumeModalOpen,
        setIsResumeModalOpen,
    };

    return (
        <JobsFeatureContext.Provider value={value}>
            {children}
        </JobsFeatureContext.Provider>
    );
};

// Custom hook to use the context
export const useJobsFeature = () => useContext(JobsFeatureContext);
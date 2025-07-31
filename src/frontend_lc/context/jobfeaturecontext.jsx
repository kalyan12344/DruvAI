import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './authcontext'; // Make sure this path is correct

const API_BASE_URL = "https://druv-backend-338967818277.us-central1.run.app"

export const JobsFeatureContext = createContext();

export const JobsFeatureProvider = ({ children }) => {
    const [jobsEnabled, setJobsEnabled] = useState(false);
    const [loading, setLoading] = useState(true);
    const [hasUploadedResume, setHasUploadedResume] = useState(false);
    const [isResumeModalOpen, setIsResumeModalOpen] = useState(false);

    const { getAuthToken } = useAuth();

    useEffect(() => {
        const fetchInitialSettings = async () => {
            const token = await getAuthToken();
            if (!token) {
                setLoading(false);
                return; // Can't fetch without a token
            }
            const headers = { 'Authorization': `Bearer ${token}` };
            setLoading(true);

            try {
                // Fetch both settings in parallel
                const [settingsResponse, resumeResponse] = await Promise.all([
                    axios.get(`${API_BASE_URL}/api/settings/jobs-toggle-status`, { headers }),
                    axios.get(`${API_BASE_URL}/api/resume/status`, { headers })
                ]);

                setJobsEnabled(settingsResponse.data.enabled);
                setHasUploadedResume(resumeResponse.data.hasUploadedResume);

            } catch (error) {
                console.error("Failed to load user settings:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchInitialSettings();
    }, [getAuthToken]); // Re-run if the user logs in/out

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

export const useJobsFeature = () => useContext(JobsFeatureContext);
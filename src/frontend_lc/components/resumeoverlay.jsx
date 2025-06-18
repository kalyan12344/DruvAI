// frontend_lc/components/ResumeUploadOverlay.jsx (Corrected)

import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useJobsFeature } from '../context/jobfeaturecontext.jsx';
import '../styles/overlay.css';

const ResumeUploadOverlay = () => {
    const { setIsResumeModalOpen, setHasUploadedResume, setJobsEnabled } = useJobsFeature();
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState('');

    const { getRootProps, getInputProps } = useDropzone({
        onDrop: acceptedFiles => setSelectedFile(acceptedFiles[0]),
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
        },
        maxFiles: 1
    });

    const handleUpload = async () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append('file', selectedFile);
        setIsUploading(true);
        setError('');

        try {
            // Step 1: Upload the resume file
            const uploadResponse = await fetch('http://localhost:8000/api/resume/upload', {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                // Try to get a detailed error message from the FastAPI backend
                const errorData = await uploadResponse.json().catch(() => ({ detail: 'Upload failed. The server did not provide a reason.' }));
                throw new Error(errorData.detail || 'Upload failed. Please try again.');
            }

            // --- THIS IS THE FIX ---
            // Step 2: After successful upload, save the "jobs enabled" state to the backend
            console.log("Resume uploaded. Now saving the 'enabled: true' setting...");
            const settingsResponse = await fetch('http://localhost:8000/api/settings/jobs-toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: true })
            });

            if (!settingsResponse.ok) {
                // This is an edge case, but good to handle
                throw new Error('Resume uploaded, but failed to save the setting. Please try toggling the switch again.');
            }
            console.log("Setting saved successfully.");
            // --- END OF FIX ---

            // Step 3: Update the global React state and close the overlay
            setHasUploadedResume(true);
            setJobsEnabled(true);
            setIsResumeModalOpen(false); // Close the overlay

        } catch (err) {
            setError(err.message);
        } finally {
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        // If the user closes the modal without uploading, the toggle should revert to OFF
        setJobsEnabled(false);
        setIsResumeModalOpen(false);
    }

    return (
        <div className="resume-overlay">
            <div className="overlay-content-box">
                {/* Updated close button to correctly revert the toggle state */}
                <button className="close-button" onClick={handleClose}>×</button>
                <h2>AI Job Assistant Setup</h2>
                <p>To get started, please upload your résumé. Druv will analyze it to find jobs that match your skills.</p>

                <div {...getRootProps()} className="dropzone">
                    <input {...getInputProps()} />
                    {selectedFile ? <p>✅ {selectedFile.name}</p> : <p>Drag & drop a file here, or click to select</p>}
                </div>

                {error && <p className="error-message">{error}</p>}

                <button onClick={handleUpload} disabled={!selectedFile || isUploading} className="upload-button">
                    {isUploading ? 'Uploading...' : 'Upload and Enable'}
                </button>
            </div>
        </div>
    );
};

export default ResumeUploadOverlay;
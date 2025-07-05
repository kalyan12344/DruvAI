import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../styles/jobs.css'; // Assuming you have this stylesheet

const JobsTab = () => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchJobs = async () => {
            setLoading(true);
            try {
                const response = await axios.get('http://localhost:8000/api/jobs/today');

                let jobData = response.data;

                // --- THIS IS THE FIX ---
                // If the data is a string, try to parse it into an object/array.
                if (typeof jobData === 'string') {
                    try {
                        jobData = JSON.parse(jobData);
                    } catch (e) {
                        console.error("Failed to parse jobs JSON string:", e);
                        setError("Received invalid data format from the server.");
                        setJobs([]);
                        return; // Exit if parsing fails
                    }
                }

                // Now that we're sure jobData is an object/array, check if it's an array.
                if (Array.isArray(jobData)) {
                    setJobs(jobData);
                    setError('');
                } else {
                    console.error("API did not return an array:", jobData);
                    setError("Received unexpected data structure from the server.");
                    setJobs([]);
                }

            } catch (err) {
                console.error("Failed to fetch jobs:", err);
                setError("Could not connect to the jobs API.");
                setJobs([]);
            } finally {
                setLoading(false);
            }
        };

        fetchJobs();
    }, []);

    if (loading) {
        return <div className="jobs-wrapper"><p className="status-message">Loading jobs...</p></div>;
    }

    if (error) {
        return <div className="jobs-wrapper"><p className="status-message error">{error}</p></div>;
    }

    return (
        <div className="jobs-wrapper">
            <h2 className="jobs-header">
                💼 Based on your résumé, here are <span className="accent">{jobs.length}</span> jobs for today
            </h2>

            <div className="jobs-grid">
                {jobs.map(job => (
                    <a
                        key={job.id || job.url} // Use URL as a fallback key
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="job-card"
                    >
                        <div className="job-content">
                            <h3 className="job-title">{job.title}</h3>
                            <p className="job-meta">{job.company} • {job.location}</p>

                            {/* <div className="match-bar">
                                <div
                                    className="match-fill"
                                    style={{ width: `${Math.round(job.match_score * 100)}%` }}
                                />
                                <span className="match-score-text">{Math.round(job.match_score * 100)}% Match</span>
                            </div> */}
                        </div>

                        <span className="apply-btn">Apply →</span>
                    </a>
                ))}
            </div>
        </div>
    );
};

export default JobsTab;

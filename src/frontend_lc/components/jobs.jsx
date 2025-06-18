import React, { useEffect, useState } from 'react';
import axios from 'axios'; // Import axios
import '../styles/jobs.css';

const JobsTab = () => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);

    // In JobsTab.jsx

    useEffect(() => {
        console.log("Fetching jobs from API...");
        axios.get('http://localhost:8000/api/jobs/today')
            .then(response => {
                // Check if the received data is actually an array
                if (Array.isArray(response.data)) {
                    setJobs(response.data);
                } else {
                    // If it's not an array, log an error and set jobs to an empty array
                    console.error("API did not return an array:", response.data);
                    setJobs([]);
                }
            })
            .catch(error => {
                console.error("Failed to fetch jobs:", error);
                setJobs([]); // Also ensure jobs is an array on error
            })
            .finally(() => {
                setLoading(false); // This will run on success or failure
            });
    }, []);

    return (
        <div className="jobs-wrapper">
            <h2 className="jobs-header">
                💼 Based on your résumé, here are <span className="accent">{jobs.length}</span> jobs for today
            </h2>

            <div className="jobs-grid">
                {jobs?.map(job => (
                    <a
                        key={job.id}
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="job-card"
                    >
                        <div className="job-content">
                            <h3 className="job-title">{job.title}</h3>
                            <p className="job-meta">{job.company} • {job.location}</p>

                            <div className="match-bar">
                                <div
                                    className="match-fill"
                                    style={{ width: `${Math.round(job.match_score * 100)}%` }}
                                />
                            </div>
                        </div>

                        <span className="apply-btn">Apply →</span>
                    </a>
                ))}
            </div>
        </div>
    );
};

export default JobsTab;
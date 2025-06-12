import { useState, useEffect } from 'react';
import { FaRobot, FaCalendarAlt, FaMicrophone, FaPaperPlane } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import './dashboard.css';
import Calendar from '../calender/calender';
import WeatherWidget from '../weather/weather';
import AIInterface from '../chatInterface/voice';
import axios from 'axios';

export default function DarkDashboard() {
    const [activeTab, setActiveTab] = useState('calendar');
    const [isListening, setIsListening] = useState(false);
    const [input, setInput] = useState('');
    const [jobSummary, setJobSummary] = useState(null);


    const [jobSummaryLoading, setJobSummaryLoading] = useState(true);
    // Mock data
    const today = new Date().toISOString().split("T")[0]; // "2025-05-16"
    console.log("Today:", today);

    useEffect(() => {
        axios.get('http://localhost:5001/api/jobs/summary')
            .then((response) => {
                setJobSummary(response.data);
                setJobSummaryLoading(false);
            })
            .catch((error) => {
                console.error("Error fetching job summary:", error);
                setJobSummaryLoading(false);
            });
    }, []);

    console.log("Job Summary:", jobSummary?.daily_applications);


    const events = [
        { title: 'Team Meeting', time: '2:00 PM - 3:00 PM' }
    ];

    const news = [
        'U.S. housing starts unexpectedly jump in March',
        'Ecuador\'s president declares state of emergency',
        'Apple to open first retail store in Malaysia'
    ];

    const assignments = [
        { title: 'Essay 3', subject: 'History', date: 'Apr 18' },
        { title: 'Project Proposal', subject: 'Computer Science', date: 'Apr 22' }
    ];



    return (
        <div className="dark-dashboard">
            {/* Header */}
            <motion.header
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="dashboard-header"
            >
                <div className="header-left">
                    <motion.h1
                        whileHover={{ scale: 1.02 }}
                        className="logo"
                    >
                        <FaRobot className="robot-icon" />
                        <span>DRUV</span>
                    </motion.h1>
                    <motion.div
                        className="date-display"
                        whileTap={{ scale: 0.95 }}
                    >

                    </motion.div>
                </div>

                <motion.div
                    className=""
                    whileHover={{}}
                >
                    <div className="weather-info">
                        <WeatherWidget />
                    </div>
                </motion.div>
            </motion.header>

            {/* Main Content */}
            <div className="dashboard-grid">
                {/* Left Column */}
                <motion.div
                    className="dashboard-column"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                >
                    <motion.div
                        className="calendar-card"
                        whileHover={{ y: -5 }}
                    >
                        <h3>Calendar</h3>
                        {/* Calendar component would go here */}
                        <div className="mini-calendar">
                            {/* Mini calendar visualization */}
                            <Calendar />
                        </div>
                    </motion.div>

                    {/* <motion.div
                        className="events-card"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4, duration: 0.5 }}
                    >
                        <h3>Today's Events</h3>
                        <ul>
                            {events.map((event, index) => (
                                <motion.li
                                    key={index}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.3 + index * 0.1 }}
                                >
                                    <strong>{event.title}</strong>
                                    <span>{event.time}</span>
                                </motion.li>
                            ))}
                        </ul>
                    </motion.div> */}
                </motion.div>

                {/* Middle Column */}
                <motion.div
                    className="dashboard-column"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                >
                    <motion.div
                        className="news-card"
                        whileHover={{ y: -5 }}
                    >
                        <h3>Daily News</h3>
                        <ul>
                            {news.map((item, index) => (
                                <motion.li
                                    key={index}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: 0.5 + index * 0.1 }}
                                >
                                    {item}
                                </motion.li>
                            ))}
                        </ul>
                    </motion.div>

                    <motion.div
                        className="mail-card"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.6, duration: 0.5 }}
                    >
                        <h3>Smart Mail</h3>
                        <div className="mail-item">
                            <div>
                                <strong>Meeting Schedule</strong>
                                <span>10:12 AM</span>
                            </div>
                            <small>Sarah Davis</small>
                        </div>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="draft-button"
                        >
                            Draft Reply
                        </motion.button>
                    </motion.div>
                </motion.div>

                {/* Right Column */}
                <motion.div
                    className="dashboard-column"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4, duration: 0.5 }}
                >
                    <motion.div
                        className="notes-card"
                        whileHover={{ y: -5 }}
                    >
                        <h3>Notes & Reminders</h3>
                        <div className="reminder-item">
                            <p>Call the dentist</p>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="add-reminder"
                            >
                                + Set Reminder
                            </motion.button>
                        </div>
                    </motion.div>

                    <motion.div
                        className="jobs-card"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.7, duration: 0.5 }}
                    >
                        <h3>Job Finder</h3>
                        <div className="job-listing">
                            <h4>Software Engineer</h4>
                            <p>Google</p>
                            <small>New York, NY</small>
                        </div>
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className="find-more"
                        >
                            Find More
                        </motion.button>
                    </motion.div>
                </motion.div>
            </div>

            {/* Bottom Section */}
            <motion.div
                className="dashboard-footer"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.5 }}
            >
                <motion.div
                    className="assignments-card"
                    whileHover={{ y: -5 }}
                >
                    <h3>Upcoming Assignments</h3>
                    {assignments.map((assignment, index) => (
                        <motion.div
                            key={index}
                            className="assignment-item"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.9 + index * 0.1 }}
                        >
                            <div>
                                <strong>{assignment.title}</strong>
                                <small>{assignment.subject}</small>
                            </div>
                            <span>{assignment.date}</span>
                        </motion.div>
                    ))}
                </motion.div>

                <motion.div
                    className="quote-card"
                    whileHover={{ y: -5 }}
                >
                    <motion.p
                        animate={{
                            opacity: [0.8, 1, 0.8],
                            transition: { duration: 4, repeat: Infinity }
                        }}
                    >
                        "Nothing will work unless you do."
                    </motion.p>
                    <small>– Maya Angelou</small>
                </motion.div>

                <motion.div
                    className="grades-card"
                    whileHover={{ y: -5 }}
                >
                    <h3>Recent Grade</h3>
                    <div className="grade-item">
                        <p>Math</p>
                        <motion.span
                            animate={{
                                color: ['#a5d6a7', '#4caf50', '#a5d6a7'],
                                transition: { duration: 3, repeat: Infinity }
                            }}
                        >
                            B
                        </motion.span>
                        <small>Date 4</small>
                    </div>
                </motion.div>

                <motion.div
                    className="tracker-card"
                    whileHover={{ y: -5 }}
                >
                    <h3>Job Tracker</h3>
                    <div className="tracker-stats" style={{ display: 'flex', flexDirection: 'column' }}>
                        <div className='tracker-summary' style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', marginBottom: '15px' }}>
                            <motion.div
                                animate={{
                                    scale: [1, 1, 1],
                                    transition: { duration: 2, repeat: Infinity }
                                }}
                            >
                                <span>{jobSummary?.total_applied}</span>
                                <small>Applied</small>
                            </motion.div>
                            <motion.div
                                animate={{
                                    scale: [1, 1, 1],
                                    transition: { delay: 0.5, duration: 2, repeat: Infinity }
                                }}
                            >
                                <span>{jobSummary?.total_interview_scheduled}</span>
                                <small>Interviews</small>
                            </motion.div>
                            <motion.div
                                animate={{
                                    scale: [1, 1, 1],
                                    transition: { delay: 1, duration: 2, repeat: Infinity }
                                }}
                            >
                                <span>{jobSummary?.total_offers}</span>
                                <small>Offer</small>
                            </motion.div>
                            <motion.div
                                animate={{
                                    scale: [1, 1, 1],
                                    transition: { delay: 1, duration: 2, repeat: Infinity }
                                }}
                            >
                                <span>{jobSummary?.total_rejected}</span>
                                <small>Rejected</small>
                            </motion.div>
                        </div>
                        <div className='today-summary'>
                            <motion.div
                                animate={{
                                    scale: [1, 1, 1],
                                    transition: { delay: 1, duration: 2, repeat: Infinity }
                                }}
                            >
                                <span>{jobSummary?.daily_applications[today]}</span>
                                <small>Today's Applications</small>
                            </motion.div></div>
                    </div>
                </motion.div>
            </motion.div>

            {/* AI Assistant */}
            <motion.div
                className="ai-assistant"
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1, duration: 0.5 }}
            >
                <div className="input-container">
                    <AIInterface />

                </div>
            </motion.div>
        </div>
    );
}
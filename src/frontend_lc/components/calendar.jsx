// src/components/Calendar.jsx

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { FaChevronLeft, FaChevronRight, FaSpinner, FaAngleDown } from "react-icons/fa";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/calendar.css"; // Ensure your CSS path is correct

const Calendar = () => {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(null);
    const [events, setEvents] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAllEvents, setShowAllEvents] = useState(false);
    const eventsPanelRef = useRef(null);

    const months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    const daysOfWeek = ["S", "M", "T", "W", "T", "F", "S"];

    // NEW: Get today's date once for efficiency. We'll use this for comparison.
    const today = new Date();

    // ... (fetchEvents and useEffect logic remains the same) ...
    const fetchEvents = async () => {
        try {
            setError(null);
            setLoading(true);
            const response = await axios.get("http://localhost:8000/api/calendar/events");

            const eventsByDate = {};
            response.data.forEach((event) => {
                const eventDate = new Date(event.start.dateTime || event.start.date);
                const dateKey = eventDate.toDateString();
                if (!eventsByDate[dateKey]) {
                    eventsByDate[dateKey] = [];
                }
                eventsByDate[dateKey].push(event);
            });
            setEvents(eventsByDate);

        } catch (err) {
            setError("Failed to load calendar events. Please try again.");
            console.error("Error fetching events:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEvents();
    }, []);


    const handleDateClick = (date) => {
        setSelectedDate(date);
        setShowAllEvents(false);
        setTimeout(() => {
            eventsPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);
    };

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const renderMonth = (monthOffset = 0) => {
        const date = new Date(currentDate);
        date.setMonth(currentDate.getMonth() + monthOffset);

        const year = date.getFullYear();
        const month = date.getMonth();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const firstDayOfMonth = new Date(year, month, 1).getDay();

        const daysArray = [];

        for (let i = 0; i < firstDayOfMonth; i++) {
            daysArray.push(<div key={`empty-${month}-${i}`} className="calendar-day empty"></div>);
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const dayDate = new Date(year, month, day);
            const dateKey = dayDate.toDateString();

            const isSelected = selectedDate && selectedDate.toDateString() === dateKey;

            // NEW: Check if the current day in the loop is today.
            // We compare `toDateString()` to ignore the time part of the date.
            const isToday = today.toDateString() === dateKey;

            const hasEvents = events[dateKey] && events[dateKey].length > 0;

            daysArray.push(
                <div
                    key={`day-${month}-${day}`}
                    // UPDATED: Added the `isToday` condition to the class list.
                    className={`calendar-day 
                        ${isSelected ? "selected" : ""}
                        ${isToday ? "today" : ""}
                        ${hasEvents ? "has-events" : ""}`
                    }
                    onClick={() => handleDateClick(dayDate)}
                >
                    <span>{day}</span>
                    {hasEvents && <div className="event-dot"></div>}
                </div>
            );
        }

        return (
            <div className="month-calendar">
                <h3>{months[month]} {year}</h3>
                <div className="calendar-grid">
                    {daysOfWeek.map(day => (
                        <div key={day} className="calendar-day-header">{day}</div>
                    ))}
                    {daysArray}
                </div>
            </div>
        );
    };

    // ... (rest of the component remains the same) ...
    const selectedDateEvents = selectedDate ? events[selectedDate.toDateString()] || [] : [];
    const hasMultipleEvents = selectedDateEvents.length > 3;
    const displayedEvents = showAllEvents ? selectedDateEvents : selectedDateEvents.slice(0, 3);

    return (
        <div className="calendar-container">
            <div className="calendar-header">
                <h2>Calendar</h2>
                <div className="month-navigation">
                    <motion.button onClick={handlePrevMonth} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                        <FaChevronLeft />
                    </motion.button>
                    <span>{months[currentDate.getMonth()]} {currentDate.getFullYear()}</span>
                    <motion.button onClick={handleNextMonth} whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                        <FaChevronRight />
                    </motion.button>
                </div>
            </div>
            {loading ? (
                <div className="loading-state">
                    <FaSpinner className="spinner" /> Loading events...
                </div>
            ) : error ? (
                <div className="error-state">
                    {error} <button onClick={fetchEvents}>Retry</button>
                </div>
            ) : (
                <div className="dual-month-view">
                    {renderMonth(0)}
                    {renderMonth(1)}
                </div>
            )}
            <div ref={eventsPanelRef}>
                {selectedDate && (
                    <motion.div
                        className="events-panel"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <h3>
                            Events for {selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
                            {today.toDateString() === selectedDate.toDateString() && <span className="today-badge">Today</span>}
                        </h3>

                        <AnimatePresence>
                            {selectedDateEvents.length > 0 ? (
                                <div className="events-list">
                                    {displayedEvents.map((event, index) => (
                                        <motion.div
                                            key={index}
                                            className="event-item"
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: index * 0.1 }}
                                        >
                                            <div className="event-time">
                                                {event.start.dateTime
                                                    ? new Date(event.start.dateTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                                    : "All Day"}
                                            </div>
                                            <div className="event-details">
                                                <div className="event-title">{event.summary}</div>
                                                {event.description && <p className="event-description">{event.description}</p>}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            ) : (
                                <motion.div className="no-events" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                    No events scheduled.
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {hasMultipleEvents && !showAllEvents && (
                            <motion.button
                                className="show-more-btn"
                                onClick={() => setShowAllEvents(true)}
                                whileHover={{ scale: 1.05 }}
                            >
                                <FaAngleDown /> Show all {selectedDateEvents.length} events
                            </motion.button>
                        )}
                    </motion.div>
                )}
            </div>
        </div>
    );
};

export default Calendar;
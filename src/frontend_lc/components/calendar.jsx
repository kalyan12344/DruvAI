import { useState, useEffect } from "react";
import axios from "axios";
import { FaChevronLeft, FaChevronRight, FaPlus, FaBrain } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";
import { SiGooglecalendar } from "react-icons/si"
import googleCalendarIcon from "../assets/Google_Calendar_icon.svg";

// --- FIX: Corrected the icon name from SiMicrosoftoutlook to SiMicrosoftOutlook ---
import { PiMicrosoftOutlookLogoLight } from "react-icons/pi";
import { motion, AnimatePresence } from "framer-motion";
import "../styles/calendar.css";

// --- Helper Functions & Constants ---
const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const today = new Date();

// --- Main Calendar Component ---
const Calendar = () => {
    const [view, setView] = useState('month');
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [events, setEvents] = useState({});
    const [loading, setLoading] = useState(true);

    const [connections, setConnections] = useState({ google: {}, outlook: {}, icloud: {} });
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                setLoading(true);

                const [statusResponse, eventsResponse] = await Promise.all([
                    axios.get("http://127.0.0.1:8000/api/calendars/status"),
                    axios.get("http://127.0.0.1:8000/api/calendar/events"),

                ]);

                const eventsByDate = {};
                eventsResponse.data.forEach((event) => {
                    const eventDate = new Date(event.start.dateTime || `${event.start.date}T00:00:00`);
                    const dateKey = eventDate.toDateString();
                    if (!eventsByDate[dateKey]) {
                        eventsByDate[dateKey] = { allDay: [], timed: [] };
                    }
                    const eventWithSource = { ...event, source: 'google' };
                    if (event.start.dateTime) {
                        eventsByDate[dateKey].timed.push(eventWithSource);
                    } else {
                        eventsByDate[dateKey].allDay.push(eventWithSource);
                    }
                });

                for (const dateKey in eventsByDate) {
                    eventsByDate[dateKey].timed.sort((a, b) => new Date(a.start.dateTime) - new Date(b.start.dateTime));
                }
                setEvents(eventsByDate);
                setConnections(statusResponse.data);

            } catch (err) {
                console.error("Error fetching initial data:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchInitialData();
    }, []);

    const handleConnectCalendar = (provider) => {
        const authUrl = `http://127.0.0.1:8000/api/${provider}/auth/login`;
        const popup = window.open(authUrl, `${provider}-auth-popup`, 'width=600,height=700');
        setIsMenuOpen(false);

        const checkPopupClosed = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkPopupClosed);
                axios.get("http://127.0.0.1:8000/api/calendars/status")
                    .then(res => setConnections(res.data));
            }
        }, 1000);
    };

    const handleDateClick = (date) => {
        setSelectedDate(date);
        setView('day');
    };
    const handlePrevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    const handleNextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    const handleToday = () => {
        setCurrentDate(new Date());
        setView('month');
    };

    const renderHeader = () => (
        <div className="calendar-header">
            <h2>Calendar</h2>
            <div className="calendar-actions">
                <div className="connected-accounts">
                    {connections.google?.connected && (
                        <img src={googleCalendarIcon} alt="Google Calendar" className="icon" title={`Google Calendar Connected: ${connections.google.user_email}`} />
                    )}
                    {connections.outlook?.connected && (
                        // --- FIX: Corrected the component name to SiMicrosoftOutlook ---
                        <PiMicrosoftOutlookLogoLight size={18} className="icon" title={`Outlook Connected: ${connections.outlook.user_email}`} />
                    )}

                    <div className="action-btn-wrapper">
                        <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="action-btn !p-2 !rounded-full" title="Connect another account">
                            <FaPlus size={12} />
                        </button>
                        <AnimatePresence>
                            {isMenuOpen && (
                                <motion.div
                                    className="connect-menu"
                                    initial={{ opacity: 0, y: -10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                >
                                    <button onClick={() => handleConnectCalendar('google')} disabled={connections.google?.connected}>
                                        <SiGooglecalendar /> Connect Google Calendar
                                    </button>
                                    <button onClick={() => alert("Outlook integration coming soon!")} disabled>
                                        {/* --- FIX: Corrected the component name to SiMicrosoftOutlook --- */}
                                        <PiMicrosoftOutlookLogoLight color="#0072C6" /> Connect Outlook Calendar
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
                <button className="action-btn"><FaBrain size={14} /> Find a Time</button>
            </div>
        </div>
    );

    const renderMonthView = () => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const daysArray = Array.from({ length: firstDayOfMonth }, (_, i) => (
            <div key={`empty-${i}`} className="calendar-day not-current-month"></div>
        ));

        for (let day = 1; day <= daysInMonth; day++) {
            const dayDate = new Date(year, month, day);
            const dateKey = dayDate.toDateString();
            const isToday = today.toDateString() === dateKey;
            const dayEventData = events[dateKey];
            const hasEvents = dayEventData && (dayEventData.allDay.length > 0 || dayEventData.timed.length > 0);

            daysArray.push(
                <motion.div key={`day-${day}`} onClick={() => handleDateClick(dayDate)} className={`calendar-day ${isToday ? "today" : ""}`} whileHover={{ scale: 1.05, y: -2 }} transition={{ type: 'spring', stiffness: 300 }}>
                    <span>{day}</span>
                    {hasEvents && (<div className="event-dots"><div className="event-dot dot-google"></div></div>)}
                </motion.div>
            );
        }
        return (
            <motion.div key="month-view" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
                <div className="month-navigation">
                    <button className="nav-btn" onClick={handlePrevMonth}><FaChevronLeft /></button>
                    <span style={{ fontSize: "15px" }}>{months[month]} {year}</span>
                    <button className="nav-btn" onClick={handleNextMonth}><FaChevronRight /></button>
                    <button className="action-btn today-pill" style={{ borderRadius: "20px", height: "25px", fontSize: "14px" }} onClick={handleToday} title="Go to today">Today</button>
                </div>
                <div className="calendar-grid">
                    {daysOfWeek.map((day, index) => <div key={`${day}-${index}`} className="calendar-day-header">{day}</div>)}
                    {daysArray}
                </div>
            </motion.div>
        );
    };

    const renderDayView = () => {
        const dayEventData = events[selectedDate.toDateString()] || { allDay: [], timed: [] };
        const hours = Array.from({ length: 24 }, (_, i) => i);

        return (
            <motion.div key="day-view" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}>
                <div className="month-navigation">
                    <button className="action-btn !px-4" onClick={() => setView('month')}><FaChevronLeft size={12} /> Back to Month</button>
                    <span className="!text-left !min-w-0 flex-grow">{selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
                </div>
                {dayEventData.allDay.length > 0 && (
                    <div className="all-day-events-container">
                        <span className="timeline-time !transform-none">All-day</span>
                        <div className="all-day-events-list">
                            {dayEventData.allDay.map(event => (<div key={event.id} className="event-block all-day">{event.summary}</div>))}
                        </div>
                    </div>
                )}
                <div className="daily-timeline">
                    {hours.map(hour => (
                        <div key={hour} className="timeline-hour">
                            <div className="timeline-time">{hour % 12 === 0 ? 12 : hour % 12} {hour < 12 ? 'AM' : 'PM'}</div>
                            <div className="timeline-slot">
                                {dayEventData.timed.map(event => {
                                    const eventStart = new Date(event.start.dateTime);
                                    if (eventStart.getHours() !== hour) return null;
                                    const eventEnd = new Date(event.end.dateTime);
                                    const durationMinutes = (eventEnd - eventStart) / (1000 * 60);
                                    const topPosition = (eventStart.getMinutes() / 60) * 100;
                                    const height = (durationMinutes / 60) * 100;
                                    return (
                                        <div key={event.id} className="event-block" style={{ top: `${topPosition}%`, height: `max(10%, ${height}%)` }}>
                                            <span className="font-bold">{event.summary}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </motion.div>
        );
    };

    // --- Main Return ---
    return (
        <div className="calendar-container">
            {renderHeader()}
            {loading ? (
                <div className="centered-state">Loading Calendar...</div>
            ) : (
                <AnimatePresence mode="wait">
                    {view === 'month' ? renderMonthView() : renderDayView()}
                </AnimatePresence>
            )}
        </div>
    );
};

export default Calendar;
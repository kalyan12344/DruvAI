import { useState, useEffect, useRef } from "react";
import {
  FaChevronLeft,
  FaChevronRight,
  FaCalendarAlt,
  FaSpinner,
  FaAngleDown,
} from "react-icons/fa";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import "../calender/calender.css";

const Calendar = ({ onDateSelect }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAllEvents, setShowAllEvents] = useState(false);
  const eventsCardRef = useRef(null);

  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

  // Check if a date is today
  const isToday = (date) => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  // Fetch events from backend
  const fetchEvents = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await axios.get(
        "http://localhost:5001/api/calendar/events"
      );
      setEvents(response.data);
    } catch (err) {
      setError("Failed to load calendar events");
      console.error("Error fetching events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  // Group events by date
  const eventsByDate = {};
  events.forEach((event) => {
    const eventDate = new Date(event.start.dateTime || event.start.date);
    const dateKey = eventDate.toDateString();
    if (!eventsByDate[dateKey]) {
      eventsByDate[dateKey] = [];
    }
    eventsByDate[dateKey].push(event);
  });

  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay();
  };

  const handlePrevMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1)
    );
  };

  const handleNextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
    );
  };

  const handleDateClick = (day) => {
    const selected = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth(),
      day
    );
    setSelectedDate(selected);
    setShowAllEvents(false);
    if (onDateSelect) onDateSelect(selected);

    // Scroll to events card
    setTimeout(() => {
      eventsCardRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  const renderCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);

    const daysArray = [];
    let day = 1;

    // Previous month days
    const prevMonthDays = getDaysInMonth(year, month - 1);
    for (let i = 0; i < firstDay; i++) {
      daysArray.push(
        <div key={`prev-${i}`} className="calendar-day other-month">
          {prevMonthDays - firstDay + i + 1}
        </div>
      );
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      const hasEvents = eventsByDate[date.toDateString()];
      const isSelected =
        selectedDate &&
        selectedDate.getDate() === i &&
        selectedDate.getMonth() === month &&
        selectedDate.getFullYear() === year;
      const today = isToday(date);

      daysArray.push(
        <div
          key={`current-${i}`}
          className={`calendar-day 
            ${isSelected ? "selected" : ""} 
            ${hasEvents ? "has-events" : ""}
            ${today ? "today" : ""}`}
          onClick={() => handleDateClick(i)}
        >
          {i}
          {hasEvents && <div className="event-dot"></div>}
        </div>
      );
    }

    // Next month days
    const totalCells = Math.ceil((daysInMonth + firstDay) / 7) * 7;
    for (let i = daysInMonth + firstDay; i < totalCells; i++) {
      daysArray.push(
        <div key={`next-${i}`} className="calendar-day other-month">
          {i - daysInMonth - firstDay + 1}
        </div>
      );
    }

    return daysArray;
  };

  // Get events for selected date
  const selectedDateEvents = selectedDate
    ? eventsByDate[selectedDate.toDateString()] || []
    : [];
  const hasMultipleEvents = selectedDateEvents.length > 3;
  const displayedEvents = showAllEvents
    ? selectedDateEvents
    : selectedDateEvents.slice(0, 3);

  return (
    <motion.div
      className="dashboard-calendar-wrapper"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Calendar Grid */}
      <div className="dashboard-calendar-container">
        <div className="calendar-header">
          <motion.button
            onClick={handlePrevMonth}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <FaChevronLeft />
          </motion.button>
          <h3>
            <FaCalendarAlt /> {months[currentDate.getMonth()]},{" "}
            {currentDate.getFullYear()}
          </h3>
          <motion.button
            onClick={handleNextMonth}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <FaChevronRight />
          </motion.button>
        </div>

        {loading ? (
          <div className="loading">
            <FaSpinner className="spinner" />
            Loading calendar events...
          </div>
        ) : error ? (
          <div className="error">
            {error} <button onClick={fetchEvents}>Retry</button>
          </div>
        ) : (
          <div className="calendar-grid">
            {days.map((day) => (
              <div key={day} className="calendar-day-header">
                {day}
              </div>
            ))}
            {renderCalendar()}
          </div>
        )}
      </div>

      {/* Events Card */}
      <div className="dashboard-events-card" ref={eventsCardRef}>
        {selectedDate && (
          <motion.div
            className="events-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="events-card-header">
              <h3>
                {selectedDate.toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
                {isToday(selectedDate) && <span className="today-badge">Today</span>}
              </h3>
              {selectedDateEvents.length > 0 && (
                <span className="events-count">
                  {selectedDateEvents.length} events
                </span>
              )}
            </div>

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
                          ? new Date(event.start.dateTime).toLocaleTimeString(
                            [],
                            { hour: "2-digit", minute: "2-digit" }
                          )
                          : "All day"}
                      </div>
                      <div className="event-content">
                        <div className="event-summary">{event.summary}</div>
                        {event.description && (
                          <div className="event-description">
                            {event.description}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <motion.div
                  className="no-events"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  No events scheduled
                </motion.div>
              )}
            </AnimatePresence>

            {hasMultipleEvents && !showAllEvents && (
              <motion.button
                className="show-more-btn"
                onClick={() => setShowAllEvents(true)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <FaAngleDown /> Show all {selectedDateEvents.length} events
              </motion.button>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default Calendar;
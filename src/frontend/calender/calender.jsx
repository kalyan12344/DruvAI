import { useState, useEffect, useRef } from "react";
import {
  FaChevronLeft,
  FaChevronRight,
  FaCalendarAlt,
  FaSpinner,
  FaAngleDown,
} from "react-icons/fa";
import axios from "axios";
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

  // Fetch events from backend
  const fetchEvents = async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await axios.get(
        "http://localhost:5000/api/calendar/events"
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

      daysArray.push(
        <div
          key={`current-${i}`}
          className={`calendar-day ${isSelected ? "selected" : ""} ${
            hasEvents ? "has-events" : ""
          }`}
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
    <div className="calendar-wrapper">
      <div className="calendar-container">
        <div className="calendar-header">
          <button
            onClick={handlePrevMonth}
            className=""
            style={
              {
                // borderRadius: "50%",
              }
            }
          >
            <FaChevronLeft />
          </button>
          <h3>
            <FaCalendarAlt /> {months[currentDate.getMonth()]},{" "}
            {currentDate.getFullYear()}
          </h3>
          <button onClick={handleNextMonth} className="">
            <FaChevronRight />
          </button>
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
      <div className="events-card-container" ref={eventsCardRef}>
        {selectedDate && (
          <div className="events-card">
            <div className="events-card-header">
              <h3>
                {" "}
                {selectedDate.toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
              </h3>
              {selectedDateEvents.length > 0 && (
                <span className="events-count">
                  {selectedDateEvents.length} events
                </span>
              )}
            </div>

            {selectedDateEvents.length > 0 ? (
              <div className="events-list">
                {displayedEvents.map((event, index) => (
                  <div key={index} className="event-item">
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
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-events">No events scheduled</div>
            )}

            {hasMultipleEvents && !showAllEvents && (
              <button
                className="show-more-btn"
                onClick={() => setShowAllEvents(true)}
              >
                <FaAngleDown /> Show all {selectedDateEvents.length} events
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Calendar;

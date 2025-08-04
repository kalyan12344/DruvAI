import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import "../styles/eventscard.css"

const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const EventsCard = ({ events, selectedDate }) => {
    const [agendaView, setAgendaView] = useState('day'); // 'day' or 'week'

    const { dayEvents, weekEvents } = useMemo(() => {
        const getEventsForDay = (date) => {
            return events[date.toDateString()] || { allDay: [], timed: [] };
        };

        const dayEventsData = getEventsForDay(selectedDate);
        const allDayEvents = [...dayEventsData.allDay, ...dayEventsData.timed];

        const weekStart = new Date(selectedDate);
        weekStart.setDate(selectedDate.getDate() - selectedDate.getDay());

        const weekEventsList = [];
        for (let i = 0; i < 7; i++) {
            const day = new Date(weekStart);
            day.setDate(weekStart.getDate() + i);
            const dayEventData = getEventsForDay(day);
            const allEventsForDay = [...dayEventData.allDay, ...dayEventData.timed];
            allEventsForDay.forEach(event => weekEventsList.push({ ...event, eventDate: day }));
        }
        weekEventsList.sort((a, b) => new Date(a.start.dateTime || a.start.date) - new Date(b.start.dateTime || b.start.date));

        return {
            dayEvents: allDayEvents,
            weekEvents: weekEventsList
        };
    }, [selectedDate, events]);

    const eventsToShow = agendaView === 'day' ? dayEvents : weekEvents;
    const title = agendaView === 'day'
        ? selectedDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
        : 'This Week';

    return (
        <div className="agenda-card">
            <div className="agenda-header">
                <h3>{title}</h3>
                <div className="view-toggle">
                    <button className={agendaView === 'day' ? 'active' : ''} onClick={() => setAgendaView('day')}>Day</button>
                    <button className={agendaView === 'week' ? 'active' : ''} onClick={() => setAgendaView('week')}>Week</button>
                </div>
            </div>
            <div className="agenda-content">
                {eventsToShow.length > 0 ? (
                    eventsToShow.map(event => (
                        <motion.div
                            key={event.id + (event.eventDate || '')}
                            className="agenda-event-item"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            layout
                        >
                            <div className="event-time">
                                {agendaView === 'week' && <span className="event-day-label">{daysOfWeek[event.eventDate.getDay()]}</span>}
                                {event.start.dateTime ? new Date(event.start.dateTime).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : 'All Day'}
                            </div>
                            <div className="event-details">
                                <span className="event-title">{event.summary}</span>
                            </div>
                        </motion.div>
                    ))
                ) : (
                    <div className="no-events-message">No events scheduled for Today.</div>
                )}
            </div>
        </div>
    );
};

export default EventsCard;
import React from 'react';
import '../styles/dashboard.css';

const Dashboard = () => {
    const tasks = [
        { id: 1, title: 'Review design mockups', due: 'Due Today', completed: false },
        { id: 2, title: 'Update project documentation', due: 'Due Tomorrow', completed: false },
        { id: 3, title: 'Team standup meeting', due: 'Due Wednesday', completed: true },
        { id: 4, title: 'Code review for new features', due: 'Due Thursday', completed: false }
    ];

    const projects = [
        { id: 1, name: 'E-commerce Platform', members: 8, progress: 75 },
        { id: 2, name: 'Mobile App Development', members: 5, progress: 45 },
        { id: 3, name: 'Marketing Website', members: 12, progress: 80 }
    ];

    const reminders = [
        { id: 1, title: 'Team Meeting', time: '10:00 AM' },
        { id: 2, title: 'Client Call', time: '2:30 PM' }
    ];

    const goals = [
        { id: 1, title: 'Complete project milestone', progress: 75 },
        { id: 2, title: 'Learn new technology stack', progress: 20 }
    ];

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <div>
                    <h1>Hello, Courtney</h1>
                    <p>{new Date().toDateString()}</p>
                </div>
                <div className="header-actions">
                    <button className="primary-btn">Ask AI</button>
                    <button className="secondary-btn">Get Tasks Update</button>
                    <button className="secondary-btn">Create Workspace</button>
                    <button className="secondary-btn">Connect Apps</button>
                </div>
            </header>

            <div className="dashboard-content">
                <div className="content-row">
                    <div className="card tasks-card">
                        <h2>My Tasks</h2>
                        <ul className="task-list">
                            {tasks.map(task => (
                                <li key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
                                    <div className="task-info">
                                        {!task.completed ? <span className="task-indicator"></span> : <span className="task-completed">✓</span>}
                                        <span className="task-title">{task.title}</span>
                                    </div>
                                    <span className="task-due">{task.due}</span>
                                </li>
                            ))}
                        </ul>
                        <button className="add-btn">+ Add Task</button>
                    </div>

                    <div className="card calendar-card">
                        <h2>Calendar</h2>
                        <div className="calendar-header">
                            <button className="nav-btn">←</button>
                            <span>{new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</span>
                            <button className="nav-btn">→</button>
                        </div>
                        <div className="calendar-grid">
                            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(day => (
                                <div key={day} className="calendar-day-header">{day}</div>
                            ))}
                            {Array.from({ length: 31 }, (_, i) => (
                                <div
                                    key={i}
                                    className={`calendar-day ${[7, 14, 21, 28].includes(i + 1) ? 'highlight' : ''}`}
                                >
                                    {i + 1}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="content-row">
                    <div className="card goals-card">
                        <h2>My Goals</h2>
                        <ul className="goal-list">
                            {goals.map(goal => (
                                <li key={goal.id} className="goal-item">
                                    <div className="goal-header">
                                        <h3>{goal.title}</h3>
                                        <span>{goal.progress}%</span>
                                    </div>
                                    <div className="progress-bar">
                                        <div className="progress-fill" style={{ width: `${goal.progress}%` }}></div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="content-row">
                    <div className="card projects-card">
                        <h2>Projects</h2>
                        <ul className="project-list">
                            {projects.map(project => (
                                <li key={project.id} className="project-item">
                                    <div className="project-header">
                                        <h3>{project.name}</h3>
                                        <span className="project-members">{project.members} members</span>
                                    </div>
                                    <div className="progress-container">
                                        <div className="progress-bar">
                                            <div className="progress-fill" style={{ width: `${project.progress}%` }}></div>
                                        </div>
                                        <span className="progress-percent">{project.progress}%</span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        <button className="add-btn">+ Add Project</button>
                    </div>

                    <div className="card reminders-card">
                        <h2>Reminders</h2>
                        <ul className="reminder-list">
                            {reminders.map(reminder => (
                                <li key={reminder.id} className="reminder-item">
                                    <h3>{reminder.title}</h3>
                                    <p>{reminder.time}</p>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;

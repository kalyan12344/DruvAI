import React from 'react';
import '../styles/sidebar.css';
import { useState } from 'react';
const Sidebar = ({ activeTab, setActiveTab }) => {
    const [projects] = useState([
        { id: 1, name: 'Design System', members: 8, color: 'purple' },
        { id: 2, name: 'Mobile App', members: 5, color: 'blue' },
        { id: 3, name: 'Website Redesign', members: 12, color: 'green' },
        { id: 4, name: 'Marketing Campaign', members: 6, color: 'orange' }
    ]);

    const navItems = [
        { id: 1, name: 'Home', icon: '🏠' },
        { id: 2, name: 'Druv AI', icon: '🤖' },
        { id: 3, name: 'My Tasks', icon: '📝' },
        { id: 4, name: 'Inbox', icon: '📥' },
        { id: 5, name: 'Calendar', icon: '📅' },
        { id: 6, name: 'Reports & Analytics', icon: '📊' },
        { id: 7, name: 'Settings', icon: '⚙️' }
    ];

    return (
        <div className="sidebar">
            <div className="profile">
                <div className="avatar">CW</div>
                <div className="profile-info">
                    <div className="name">Courtney Wilson</div>
                    <div className="status">● Online</div>
                </div>
            </div>

            <ul className="nav-links">
                {navItems.map(item => (
                    <li
                        key={item.id}
                        className={`nav-item ${activeTab === item.name ? 'active' : ''}`}
                        onClick={() => setActiveTab(item.name)}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span>{item.name}</span>
                    </li>
                ))}
            </ul>

            <div className="projects-section">
                <div className="projects-header">MY PROJECTS +</div>
                <ul className="projects-list">
                    {projects.map(project => (
                        <li key={project.id} className="project-item">
                            <span className={`dot ${project.color}`}></span>
                            <span className="project-name">{project.name}</span>
                            <span className="project-members">{project.members} members</span>
                        </li>
                    ))}
                </ul>
            </div>

            <div className="upgrade-box">
                <p className="prodify">Prodify</p>
                <p>Upgrade to unlock all features</p>
                <button className="upgrade-btn">Invite people</button>
            </div>
        </div>
    );
};

export default Sidebar;
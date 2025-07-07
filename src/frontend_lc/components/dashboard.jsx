import React from 'react';
import '../styles/dashboard.css';
import Calendar from './calendar';
import News from './news';

const Dashboard = () => {


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

                <News />

            </div>
        </div>
    );
};

export default Dashboard;

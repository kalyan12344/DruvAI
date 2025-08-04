import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import the provider
import { JobsFeatureProvider } from './frontend_lc/context/jobfeaturecontext.jsx';

import './App.css';
import Dashboard from './frontend_lc/components/dashboard.jsx';
import Sidebar from './frontend_lc/components/sidebar.jsx';
import Home from './frontend_lc/components/home.jsx';
import LandingPage from './frontend_lc/components/landingpage.jsx';
import Tasks from './frontend_lc/components/tasks.jsx';
import Calendar from './frontend_lc/components/calendar.jsx';
import SettingsTab from './frontend_lc/components/settings.jsx';
import JobsTab from './frontend_lc/components/jobs.jsx';
import TodoListWidget from './frontend_lc/components/todolist.jsx';
import Gmail from './frontend_lc/components/gmail.jsx';
import Auth from './frontend_lc/components/auth.jsx';
import { auth } from './firebase';
import ReportsAnalytics from './frontend_lc/components/ra.jsx';



function App() {
  // Initialize activeTab from localStorage or default to 'Druv AI'
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('activeTab') || 'Druv AI';
  });
  const user = auth.currentUser;

  // Save to localStorage whenever activeTab changes
  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'Home':
        return <Dashboard />;
      case 'Druv AI':
        return < Home />;
      case 'My Tasks':
        return <Tasks />;
      case 'Reports & Analytics':
        return <ReportsAnalytics />
      case 'Inbox':
        return <Gmail />
      case 'Calendar':
        return <Calendar />;
      case 'Settings':
        return <SettingsTab />;
      case 'Jobs':
        return <JobsTab />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<Auth />} />
        <Route
          path="/dashboard"
          element={
            <JobsFeatureProvider>
              <div className="app-container">
                <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} user={user} />
                <div className="content">{renderActiveTab()}</div>
              </div>
            </JobsFeatureProvider>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
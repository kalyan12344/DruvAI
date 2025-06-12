import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import LandingPage from './frontend_lc/components/landingpage';
import Sidebar from './frontend_lc/components/sidebar';
import Dashboard from './frontend_lc/components/dashboard';
import Tasks from './frontend_lc/components/tasks';
// Future imports for other tabs
// import Inbox from './frontend_lc/components/inbox';
// import Calendar from './frontend_lc/components/calendar';
// import Reports from './frontend_lc/components/reports';
// import Settings from './frontend_lc/components/settings';

import './App.css';
import Home from './frontend_lc/components/home';
import Calendar from './frontend_lc/components/calendar';

function App() {
  const [activeTab, setActiveTab] = useState('Prodify AI');

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'Home':
        return <Home />;
      case 'Prodify AI':
        return <Dashboard />;
      case 'My Tasks':
        return <Tasks />;
      // case 'Inbox':
      //   return <Inbox />;
      case 'Calendar':
        return <Calendar />;
      // case 'Reports & Analytics':
      //   return <Reports />;
      // case 'Settings':
      //   return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/dashboard"
          element={
            <div className="app-container">
              <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
              <div className="content">{renderActiveTab()}</div>
            </div>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;

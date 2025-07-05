// src/components/Sidebar.jsx

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useJobsFeature } from '../context/jobfeaturecontext.jsx';
import '../styles/sidebar.css';

// Import sleek icons from lucide-react
import {
    LayoutDashboard, Bot, CheckSquare, Inbox, Calendar, BarChart2, Briefcase, Settings, Sparkles
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
    const { jobsEnabled } = useJobsFeature();

    // Mapping strings to actual icon components
    const iconMap = {
        'Home': LayoutDashboard,
        'Druv AI': Bot,
        'My Tasks': CheckSquare,
        'Inbox': Inbox,
        'Calendar': Calendar,
        'Reports & Analytics': BarChart2,
        'Jobs': Briefcase,
        'Settings': Settings,
    };

    const staticNavItems = [
        { id: 'Home', name: 'Home' },
        { id: 'Druv AI', name: 'Druv AI' },
        { id: 'My Tasks', name: 'My Tasks' },
        { id: 'Inbox', name: 'Inbox' },
        { id: 'Calendar', name: 'Calendar' },
        { id: 'Reports & Analytics', name: 'Reports & Analytics' },
    ];

    const settingsItem = { id: 'Settings', name: 'Settings' };
    const jobsNavItem = { id: 'Jobs', name: 'Jobs' };

    const navItems = [...staticNavItems];
    if (jobsEnabled) {
        navItems.push(jobsNavItem);
    }
    navItems.push(settingsItem);

    // Sidebar container animation
    const sidebarVariants = {
        hidden: { x: '-100%', opacity: 0 },
        visible: {
            x: 0,
            opacity: 1,
            transition: { duration: 0.5, ease: "easeInOut" }
        }
    };

    // Staggered animation for list items
    const listVariants = {
        visible: {
            transition: { staggerChildren: 0.05, delayChildren: 0.2 }
        },
        hidden: {}
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { type: 'spring', stiffness: 100 }
        }
    };

    return (
        <motion.aside
            className="sidebar"
            variants={sidebarVariants}
            initial="hidden"
            animate="visible"
        >
            <div className="profile">
                <div className="avatar">CW</div>
                <div className="profile-info">
                    <div className="profile-name">Courtney Wilson</div>
                    <div className="profile-status"><span className="dot"></span>Online</div>
                </div>
            </div>

            <motion.nav
                className="nav-links"
                variants={listVariants}
                initial="hidden"
                animate="visible"
            >
                {navItems.map(item => {
                    const Icon = iconMap[item.name];
                    return (
                        <motion.div
                            key={item.id}
                            className={`nav-item ${activeTab === item.name ? 'active' : ''}`}
                            onClick={() => setActiveTab(item.name)}
                            variants={itemVariants}
                            whileHover={{ scale: 1.02, color: 'gold' }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <Icon className="nav-icon" size={20} />
                            <span>{item.name}</span>
                        </motion.div>
                    );
                })}
            </motion.nav>

            {/* Redesigned "Upgrade" section - sleek and unobtrusive */}
            <div className="upgrade-section">
                <motion.a
                    href="#"
                    className="upgrade-link"
                    whileHover={{ scale: 1.03 }}
                >
                    <Sparkles className="icon" size={18} />
                    <span>Unlock Pro Features</span>
                </motion.a>
            </div>
        </motion.aside>
    );
};

export default Sidebar;
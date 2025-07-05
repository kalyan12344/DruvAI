import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { FaPlus, FaTrash, FaRegCircle, FaCheckCircle } from 'react-icons/fa';
import '../styles/tasks.css';
import TodoListWidget from './todolist';
import Remainders from './remainders'
import Notes from './notes';

// // --- Helper to format dates ---
// const formatDate = (dateString) => {
//     if (!dateString) return '';
//     const date = new Date(dateString);
//     const today = new Date();
//     const tomorrow = new Date();
//     tomorrow.setDate(today.getDate() + 1);

//     if (date.toDateString() === today.toDateString()) return 'Due Today';
//     if (date.toDateString() === tomorrow.toDateString()) return 'Due Tomorrow';

//     return `Due ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
// };


const Tasks = () => {


    return (
        <>
            <div className="" >
                {/* <TodoListWidget />
                <Remainders /> */}

                <Notes />
            </div>
        </>
    );
};

export default Tasks;

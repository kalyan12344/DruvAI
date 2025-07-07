import React from 'react';
import '../styles/tasks.css'; // Stylesheet import added
import TodoListWidget from './todolist';
import Remainders from './remainders';
import Notes from './notes';

const Tasks = () => {
    return (
        <div className="tasks-page-container">
            <div className="tasks-layout" >
                <div className="task-widget">
                    <Notes />
                </div>
                <div className="task-widget">
                    <TodoListWidget />
                </div>

                <div className="task-widget">
                    <Remainders />
                </div>

            </div>
        </div>
    );
};

export default Tasks;

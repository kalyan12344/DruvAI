import React from 'react';
import '../styles/tasks.css';

const Tasks = () => {
    const tasks = [
        { id: 1, title: 'Review design mockups', due: 'Due Today', priority: 'high' },
        { id: 2, title: 'Update project documentation', due: 'Due Tomorrow', priority: 'medium' },
        { id: 3, title: 'Team standup meeting', due: 'Due Wednesday', priority: 'low', completed: true },
        { id: 4, title: 'Code review for new features', due: 'Due Thursday', priority: 'high' }
    ];

    return (
        <div className="tasks-container">
            <div className="tasks-header">
                <h2>My Tasks</h2>
                <button className="add-task-btn">+ Add Task</button>
            </div>
            <ul className="task-list">
                {tasks.map(task => (
                    <li key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
                        <div className="task-info">
                            {!task.completed && (
                                <span className={`priority-dot ${task.priority}`}></span>
                            )}
                            {task.completed && (
                                <span className="completed-check">✓</span>
                            )}
                            <span className="task-title">{task.title}</span>
                        </div>
                        <span className="task-due">{task.due}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Tasks;
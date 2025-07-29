import React, { useState } from 'react';
import { Reorder } from 'framer-motion'; // Import Reorder
import '../styles/tasks.css';
import TodoListWidget from './todolist';
import Reminders from './remainders';
import Notes from './notes';

// Helper object to map string names to actual components
const componentMap = {
    Notes: <Notes />,
    ToDos: <TodoListWidget />,
    Reminders: <Reminders />,
};

const Tasks = () => {
    // 1. Manage the order of widgets in state
    const [widgets, setWidgets] = useState(['Notes', 'ToDos', 'Reminders']);

    return (
        <div className="tasks-page-container">
            {/* 2. Use Reorder.Group as the draggable container */}
            <Reorder.Group
                axis="y" // Allow dragging both horizontally and vertically
                values={widgets}
                onReorder={setWidgets}
                className="tasks-layout"
            >
                {/* 3. Map over the state array to render each widget */}
                {widgets.map((widgetName) => (
                    // 4. Wrap each widget in a Reorder.Item
                    <Reorder.Item
                        key={widgetName}
                        value={widgetName}
                        className="task-widget"
                    >
                        {componentMap[widgetName]}
                    </Reorder.Item>
                ))}
            </Reorder.Group>
        </div>
    );
};

export default Tasks;
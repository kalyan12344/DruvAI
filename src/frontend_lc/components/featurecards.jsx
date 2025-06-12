import React, { useState, useEffect } from 'react';
import '../styles/featurecards.css';

const features = [
    {
        title: "Effortless Scheduling",
        desc: "Manage appointments and meetings with AI ease.",
        icon: "📅",
    },
    {
        title: "Smart Summarization",
        desc: "Ask Druv to read and simplify any article.",
        icon: "🧠",
    },
    {
        title: "Voice Control",
        desc: "Control Druv hands-free with natural voice commands.",
        icon: "🎙️",
    },
    {
        title: "Task Automation",
        desc: "Druv takes care of repetitive online tasks for you.",
        icon: "⚙️",
    },
];

const CardStack = () => {
    const [activeIndex, setActiveIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setActiveIndex((prev) => (prev + 1) % features.length);
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="backgrnd">
            <div className="card-stack-container">
                {features.map((feature, index) => {
                    const position = (index - activeIndex + features.length) % features.length;
                    return (
                        <div
                            key={`${feature.title}-${index}`}
                            className="feature-card"
                            style={{
                                zIndex: features.length - position,
                                transform: `translateX(${position * 30}px) scale(${1 - position * 0.05})`,
                                opacity: 1 - position * 0.2,
                                transition: 'all 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
                            }}
                        >
                            <div className="card-icon">{feature.icon}</div>
                            <div className="card-title">{feature.title}</div>
                            <div className="card-desc">{feature.desc}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default CardStack;

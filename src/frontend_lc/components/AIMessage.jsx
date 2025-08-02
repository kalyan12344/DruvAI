import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Import all your card components
import { CalendarCard, ConfirmationCard, NewsCard } from './Home'; // Assuming they are exported from Home.jsx

const AIMessage = ({ content }) => {
    const [isReasoningVisible, setIsReasoningVisible] = useState(false);

    const { final_answer, reasoning_trace } = content;

    // This is the renderer from your Home.jsx, now inside this component
    const renderFinalAnswer = (answer) => {
        if (typeof answer === 'object' && answer !== null) {
            switch (answer.response_type) {
                case 'calendar_view':
                    return <CalendarCard data={answer} />;
                case 'confirmation':
                    return <ConfirmationCard data={answer} />;
                case 'news_summary':
                    return <NewsCard data={answer} />;
                // Add other cases as needed
                default:
                    // Fallback for any other structured JSON
                    return <pre>{JSON.stringify(answer, null, 2)}</pre>;
            }
        }
        // Fallback for a simple string answer
        return <p>{answer}</p>;
    };

    return (
        <div className="ai-message-wrapper">
            {renderFinalAnswer(final_answer)}

            {reasoning_trace && reasoning_trace.length > 0 && (
                <div className="reasoning-toggle">
                    <button onClick={() => setIsReasoningVisible(!isReasoningVisible)}>
                        {isReasoningVisible ? <FaChevronUp size={12} /> : <FaChevronDown size={12} />}
                        <span>{isReasoningVisible ? 'Hide Reasoning' : 'Show Reasoning'}</span>
                    </button>
                </div>
            )}

            <AnimatePresence>
                {isReasoningVisible && (
                    <motion.div
                        className="reasoning-trace"
                        initial={{ height: 0, opacity: 0, marginTop: 0 }}
                        animate={{ height: 'auto', opacity: 1, marginTop: '16px' }}
                        exit={{ height: 0, opacity: 0, marginTop: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        {reasoning_trace.map((step, index) => (
                            <div key={index} className="reasoning-step">
                                <div className="step-header">
                                    <span className="step-number">{index + 1}</span>
                                    <span className="step-tool-name">Tool: <strong>{step.tool}</strong></span>
                                </div>
                                <SyntaxHighlighter language="json" style={vscDarkPlus} PreTag="div">
                                    {JSON.stringify(step.tool_input, null, 2)}
                                </SyntaxHighlighter>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default AIMessage;
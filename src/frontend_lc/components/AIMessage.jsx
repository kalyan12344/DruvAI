import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Import the card components you want to use
import { CalendarCard, ConfirmationCard, NewsCard } from './Home';

const AIMessage = ({ content }) => {
    console.log(content, "content from aimessage")
    if (!content || !content.output) {
        return (
            <div className="ai-message-wrapper">
                <ConfirmationCard data={{ status: 'error', message: 'Received an empty or invalid response.' }} />
            </div>
        );
    }

    const [isReasoningVisible, setIsReasoningVisible] = useState(false);

    const { output, intermediate_steps } = content;

    const renderFinalAnswer = (answer) => {
        let data = answer; // Start with the original answer

        // This is the new block that fixes the issue.
        // It checks if the answer is a string that looks like JSON.
        if (typeof data === 'string' && data.trim().startsWith('{') && data.trim().endsWith('}')) {
            try {
                // If it is, we parse it into a real object.
                data = JSON.parse(data);
            } catch (e) {
                console.error("Failed to parse stringified JSON in AIMessage:", e);
                // If parsing fails, we'll just fall through and render it as a string.
            }
        }

        // Now, your original check will work correctly with the parsed 'data' object.
        if (typeof data === 'object' && data !== null && data.response_type) {
            switch (data.response_type) {
                case 'calendar_view':
                    return <CalendarCard data={data} />;
                case 'no_events':
                    return (
                        <div className="structured-card no-events-card">
                            <div className="card-header">
                                <h4>Schedule Check</h4>
                            </div>
                            <div className="card-content">
                                <p>🎉 {data.message}</p>
                            </div>
                        </div>
                    );
                case 'confirmation':
                    return <ConfirmationCard data={data} />;
                case 'news_summary':
                    return <NewsCard data={data} />;
                default:
                    return <ReactMarkdown>{`\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``}</ReactMarkdown>;
            }
        }

        // This is the fallback for "normal strings" or unhandled data.
        return <ReactMarkdown>{String(answer)}</ReactMarkdown>;
    };

    return (
        <div className="ai-message-wrapper">
            {renderFinalAnswer(output)}

            {intermediate_steps && intermediate_steps.length > 0 && (
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
                        {intermediate_steps.map((step, index) => {
                            const [action] = step;
                            return (
                                <div key={index} className="reasoning-step">
                                    <p className="thought-text">{action.log.split("Action:")[0].replace("Thought:", "").trim()}</p>
                                    <div className="step-header">
                                        <span className="step-tool-name">Tool Used: <strong>{action.tool}</strong></span>
                                    </div>
                                    <SyntaxHighlighter language="json" style={vscDarkPlus} PreTag="div">
                                        {JSON.stringify(action.tool_input, null, 2)}
                                    </SyntaxHighlighter>
                                </div>
                            );
                        })}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default AIMessage;
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CalendarCard, ConfirmationCard, NewsCard } from './Home';

const AIMessage = ({ content }) => {
    console.log(content, "from aimessage")

    if (!content) {
        return (
            <div className="ai-message-wrapper">
                <ConfirmationCard data={{ status: 'error', message: 'Received an empty or invalid response.' }} />
            </div>
        );
    }

    const [isReasoningVisible, setIsReasoningVisible] = useState(false);

    const { output, intermediate_steps } = content;

    const renderFinalAnswer = (answer) => {
        if (typeof answer === 'object' && answer !== null) {
            switch (answer.response_type) {
                case 'calendar_view': return <CalendarCard data={answer} />;
                case 'confirmation': return <ConfirmationCard data={answer} />;
                case 'news_summary': return <NewsCard data={answer} />;
                default: return <ReactMarkdown>{`\`\`\`json\n${JSON.stringify(answer, null, 2)}\n\`\`\``}</ReactMarkdown>;
            }
        }
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
                            const [action, observation] = step;
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
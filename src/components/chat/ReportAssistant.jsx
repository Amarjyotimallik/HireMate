import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, Brain, User, Loader2, ChevronDown, BarChart3 } from 'lucide-react';
import { apiPost } from '../../api/client';
import { useTheme } from '../../context/ThemeContext';

const LIGHT_COLORS = {
    accent: '#3B82F6',
    accentLight: '#EFF6FF',
    accentDark: '#1E40AF',
    cardBg: '#FFFFFF',
    pageBg: '#F7F9FF',
    textPrimary: '#0F172A',
    textSecondary: '#475569',
    textMuted: '#94A3B8',
    border: '#E2E8F0',
    purple: '#7C3AED',
    purpleLight: '#EDE9FE',
    success: '#059669',
    successLight: '#ECFDF5',
};

const DARK_COLORS = {
    accent: '#60A5FA',
    accentLight: '#0c1929',
    accentDark: '#93C5FD',
    cardBg: '#0a0a0a',
    pageBg: '#000000',
    textPrimary: '#FAFAFA',
    textSecondary: '#D4D4D4',
    textMuted: '#A3A3A3',
    border: '#262626',
    purple: '#A78BFA',
    purpleLight: '#1e1033',
    success: '#34D399',
    successLight: '#052e16',
};

// Page-specific welcome messages
const WELCOME_MESSAGES = {
    dashboard: "Hi! I'm Kiwi 🥝 — ask me about your dashboard stats, candidates, or how any metric works.",
    all_candidates: "Hi! I'm Kiwi 🥝 — ask me about any candidate, compare profiles, or spot red flags.",
    skill_reports: "Hi! I'm Kiwi 🥝 — ask me about skill distributions, radar charts, or what any metric means.",
    compare: "Hi! I'm Kiwi 🥝 — ask me to compare candidates or explain differences in their profiles.",
    live_assessment: "Hi! I'm Kiwi 🥝 — ask me how any metric is calculated.",
    settings: "Hi! I'm Kiwi 🥝 — ask me anything about how HireMate works.",
    general: "Hi! I'm Kiwi 🥝 — your HireMate assistant. Ask me anything!",
};

// Page-specific quick questions
const QUICK_QUESTIONS = {
    dashboard: [
        "How many assessments today?",
        "What's my completion rate?",
        "Recent activity summary",
    ],
    all_candidates: [
        "Who scored highest?",
        "Compare top candidates",
        "Any red flags?",
    ],
    skill_reports: [
        "Which skills are most common?",
        "Explain the radar chart",
        "What does firmness mean?",
    ],
    compare: [
        "How do these candidates differ?",
        "Who's the better fit?",
        "Compare their decision styles",
    ],
    live_assessment: [
        "Why this authenticity score?",
        "Explain decision firmness",
        "What anomalies were found?",
    ],
    settings: [
        "How does HireMate work?",
        "Explain the grading system",
        "What is the fit score formula?",
    ],
    general: [
        "How does HireMate work?",
        "What are the 8 layers?",
        "How is fit score calculated?",
    ],
};

/**
 * Lightweight markdown renderer for Kiwi responses.
 * Converts **bold**, headings, numbered lists, bullet lists,
 * and paragraphs into structured JSX with proper spacing.
 */
const renderMarkdown = (text, colors) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let i = 0;

    while (i < lines.length) {
        const line = lines[i];
        const trimmed = line.trim();

        // Skip empty lines (they create paragraph breaks)
        if (!trimmed) {
            i++;
            continue;
        }

        // Headings: **Text:** at the start of a line (bold heading pattern)
        if (/^\*\*[^*]+\*\*:?\s*$/.test(trimmed)) {
            const headingText = trimmed.replace(/\*\*/g, '').replace(/:$/, '');
            elements.push(
                <h4 key={i} style={{
                    color: colors.textPrimary,
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    marginTop: elements.length > 0 ? '14px' : '0',
                    marginBottom: '6px',
                    letterSpacing: '-0.01em'
                }}>
                    {headingText}
                </h4>
            );
            i++;
            continue;
        }

        // Numbered list items: 1. Text or 1) Text
        if (/^\d+[.)\s]/.test(trimmed)) {
            const listItems = [];
            while (i < lines.length && /^\d+[.)\s]/.test(lines[i].trim())) {
                const itemText = lines[i].trim().replace(/^\d+[.)\s]+/, '');
                listItems.push(itemText);
                i++;
            }
            elements.push(
                <ol key={`ol-${i}`} style={{
                    margin: '8px 0',
                    paddingLeft: '20px',
                    listStyleType: 'decimal',
                }}>
                    {listItems.map((item, j) => (
                        <li key={j} style={{
                            color: colors.textSecondary,
                            fontSize: '0.875rem',
                            lineHeight: '1.65',
                            marginBottom: '4px',
                            paddingLeft: '4px'
                        }}>
                            {renderInlineMarkdown(item, colors)}
                        </li>
                    ))}
                </ol>
            );
            continue;
        }

        // Bullet list items: - Text or * Text or • Text
        if (/^[-*•]\s/.test(trimmed)) {
            const listItems = [];
            while (i < lines.length && /^[-*•]\s/.test(lines[i].trim())) {
                const itemText = lines[i].trim().replace(/^[-*•]\s+/, '');
                listItems.push(itemText);
                i++;
            }
            elements.push(
                <ul key={`ul-${i}`} style={{
                    margin: '8px 0',
                    paddingLeft: '20px',
                    listStyleType: 'disc',
                }}>
                    {listItems.map((item, j) => (
                        <li key={j} style={{
                            color: colors.textSecondary,
                            fontSize: '0.875rem',
                            lineHeight: '1.65',
                            marginBottom: '4px',
                            paddingLeft: '4px'
                        }}>
                            {renderInlineMarkdown(item, colors)}
                        </li>
                    ))}
                </ul>
            );
            continue;
        }

        // Regular paragraph
        elements.push(
            <p key={i} style={{
                color: colors.textSecondary,
                fontSize: '0.875rem',
                lineHeight: '1.7',
                marginBottom: '10px'
            }}>
                {renderInlineMarkdown(trimmed, colors)}
            </p>
        );
        i++;
    }

    return <div style={{ display: 'flex', flexDirection: 'column' }}>{elements}</div>;
};

/** Render inline markdown: **bold** and *italic* */
const renderInlineMarkdown = (text, colors) => {
    // Split on **bold** patterns
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return (
                <strong key={i} style={{ color: colors.textPrimary, fontWeight: 600 }}>
                    {part.slice(2, -2)}
                </strong>
            );
        }
        return <span key={i}>{part}</span>;
    });
};

const ReportAssistant = ({ attemptId, pageContext = 'general', inline = false }) => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;
    const [isOpen, setIsOpen] = useState(inline ? true : false);
    const [isMinimized, setIsMinimized] = useState(false);

    const welcomeMessage = WELCOME_MESSAGES[pageContext] || WELCOME_MESSAGES.general;
    const quickQuestions = QUICK_QUESTIONS[pageContext] || QUICK_QUESTIONS.general;

    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: welcomeMessage,
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (isOpen && !isMinimized && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen, isMinimized]);

    // Reset messages when attemptId or pageContext changes
    useEffect(() => {
        const msg = WELCOME_MESSAGES[pageContext] || WELCOME_MESSAGES.general;
        setMessages([
            {
                role: 'assistant',
                content: msg,
            },
        ]);
    }, [attemptId, pageContext]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input.trim() };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const history = messages.slice(1).map((m) => ({
                role: m.role,
                content: m.content,
            }));

            // Use the new global Kiwi endpoint
            const response = await apiPost('/api/v1/kiwi/chat', {
                query: userMessage.content,
                page_context: pageContext,
                attempt_id: attemptId || null,
                history: history,
            });

            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: response.response },
            ]);
        } catch (error) {
            console.error('Chat error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: "Unable to analyze at the moment. Please ensure the backend is running.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Inline mode: render directly in-page, always open
    if (inline) {
        return (
            <div
                className="rounded-2xl flex flex-col overflow-hidden h-full"
                style={{
                    backgroundColor: COLORS.cardBg,
                    border: `1px solid ${COLORS.border}`,
                    minHeight: '400px',
                }}
            >
                {/* Inline Header */}
                <div
                    className="flex items-center justify-between px-5 py-4"
                    style={{
                        background: `linear-gradient(135deg, ${COLORS.purpleLight} 0%, ${COLORS.accentLight} 100%)`,
                        borderBottom: `1px solid ${COLORS.border}`,
                    }}
                >
                    <div className="flex items-center gap-3">
                        <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm"
                            style={{ background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.accent} 100%)` }}
                        >
                            <BarChart3 className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <span className="font-bold text-base block" style={{ color: COLORS.textPrimary }}>Kiwi</span>
                            <div className="flex items-center gap-1.5">
                                <Sparkles className="w-3.5 h-3.5" style={{ color: COLORS.purple }} />
                                <span className="text-sm font-medium" style={{ color: COLORS.textMuted }}>AI Analysis Assistant</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Messages Area */}
                <div
                    className="flex-1 overflow-y-auto p-5 space-y-4"
                    style={{ backgroundColor: COLORS.pageBg }}
                >
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div
                                className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm"
                                style={{ backgroundColor: msg.role === 'user' ? COLORS.accent : COLORS.purpleLight }}
                            >
                                {msg.role === 'user' ? (
                                    <User className="w-5 h-5 text-white" />
                                ) : (
                                    <Brain className="w-5 h-5" style={{ color: COLORS.purple }} />
                                )}
                            </div>
                            <div
                                className="max-w-[88%] px-4 py-3 rounded-2xl text-base leading-relaxed shadow-sm"
                                style={{
                                    backgroundColor: msg.role === 'user' ? COLORS.accent : COLORS.cardBg,
                                    color: msg.role === 'user' ? '#FFFFFF' : COLORS.textPrimary,
                                    border: msg.role === 'assistant' ? `1px solid ${COLORS.border}` : 'none',
                                }}
                            >
                                {msg.role === 'assistant' ? renderMarkdown(msg.content, COLORS) : msg.content}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-start gap-3">
                            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: COLORS.purpleLight }}>
                                <Brain className="w-5 h-5" style={{ color: COLORS.purple }} />
                            </div>
                            <div className="px-4 py-3 rounded-2xl text-base flex items-center gap-3 shadow-sm" style={{ backgroundColor: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}>
                                <Loader2 className="w-4 h-4 animate-spin" style={{ color: COLORS.purple }} />
                                <span style={{ color: COLORS.textMuted }}>Analyzing...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Quick Questions */}
                {messages.length <= 2 && (
                    <div className="px-5 pb-3 flex gap-2 flex-wrap" style={{ backgroundColor: COLORS.pageBg }}>
                        {quickQuestions.map((q, i) => (
                            <button
                                key={i}
                                onClick={() => { setInput(q); inputRef.current?.focus(); }}
                                className="text-sm px-3 py-2 rounded-xl transition-all shadow-sm hover:shadow hover:scale-[1.02]"
                                style={{ backgroundColor: COLORS.cardBg, color: COLORS.textSecondary, border: `1px solid ${COLORS.border}` }}
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                )}

                {/* Input Area */}
                <div className="p-4 border-t" style={{ borderColor: COLORS.border, backgroundColor: COLORS.cardBg }}>
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl shadow-inner" style={{ backgroundColor: COLORS.pageBg, border: `1px solid ${COLORS.border}` }}>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about metrics, scores..."
                            className="flex-1 bg-transparent outline-none text-base"
                            style={{ color: COLORS.textPrimary }}
                            disabled={isLoading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="p-2 rounded-lg transition-all disabled:opacity-40 hover:scale-105"
                            style={{ background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.accent} 100%)` }}
                        >
                            <Send className="w-5 h-5 text-white" />
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* Floating Button - Analytical Style */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-6 right-6 px-4 py-3 rounded-xl shadow-lg flex items-center gap-2 transition-all hover:scale-105 z-50"
                    style={{
                        background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.accent} 100%)`,
                        boxShadow: '0 8px 32px rgba(124, 58, 237, 0.3)',
                    }}
                    title="Ask AI about this analysis"
                >
                    <Brain className="w-5 h-5 text-white" />
                    <span className="text-white font-medium text-sm">Ask Kiwi</span>
                </button>
            )}

            {/* Analysis Panel */}
            {isOpen && (
                <div
                    className="fixed bottom-6 right-6 rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50 transition-all"
                    style={{
                        backgroundColor: COLORS.cardBg,
                        border: `1px solid ${COLORS.border}`,
                        width: isMinimized ? '320px' : '560px',
                        height: isMinimized ? 'auto' : '720px',
                        maxHeight: '85vh',
                    }}
                >
                    {/* Header - Gradient with Analysis Theme */}
                    <div
                        className="flex items-center justify-between px-5 py-4 cursor-pointer"
                        style={{
                            background: `linear-gradient(135deg, ${COLORS.purpleLight} 0%, ${COLORS.accentLight} 100%)`,
                            borderBottom: `1px solid ${COLORS.border}`,
                        }}
                        onClick={() => isMinimized && setIsMinimized(false)}
                    >
                        <div className="flex items-center gap-3">
                            <div
                                className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm"
                                style={{ background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.accent} 100%)` }}
                            >
                                <BarChart3 className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <span className="font-bold text-base block" style={{ color: COLORS.textPrimary }}>
                                    Kiwi
                                </span>
                                <div className="flex items-center gap-1.5">
                                    <Sparkles className="w-3.5 h-3.5" style={{ color: COLORS.purple }} />
                                    <span className="text-sm font-medium" style={{ color: COLORS.textMuted }}>Analysis Helper</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
                                className="p-2 rounded-lg transition-colors"
                                style={{ ':hover': { backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.5)' } }}
                            >
                                <ChevronDown
                                    className="w-5 h-5 transition-transform"
                                    style={{
                                        color: COLORS.textSecondary,
                                        transform: isMinimized ? 'rotate(180deg)' : 'rotate(0deg)',
                                    }}
                                />
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 rounded-lg transition-colors hover:opacity-75"
                            >
                                <X className="w-5 h-5" style={{ color: COLORS.textSecondary }} />
                            </button>
                        </div>
                    </div>

                    {!isMinimized && (
                        <>
                            {/* Messages Area */}
                            <div
                                className="flex-1 overflow-y-auto p-5 space-y-4"
                                style={{ backgroundColor: COLORS.pageBg }}
                            >
                                {messages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                                    >
                                        <div
                                            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm"
                                            style={{
                                                backgroundColor: msg.role === 'user' ? COLORS.accent : COLORS.purpleLight,
                                            }}
                                        >
                                            {msg.role === 'user' ? (
                                                <User className="w-5 h-5 text-white" />
                                            ) : (
                                                <Brain className="w-5 h-5" style={{ color: COLORS.purple }} />
                                            )}
                                        </div>
                                        <div
                                            className="max-w-[88%] px-4 py-3 rounded-2xl text-base leading-relaxed shadow-sm"
                                            style={{
                                                backgroundColor: msg.role === 'user' ? COLORS.accent : COLORS.cardBg,
                                                color: msg.role === 'user' ? '#FFFFFF' : COLORS.textPrimary,
                                                border: msg.role === 'assistant' ? `1px solid ${COLORS.border}` : 'none',
                                            }}
                                        >
                                            {msg.role === 'assistant'
                                                ? renderMarkdown(msg.content, COLORS)
                                                : msg.content
                                            }
                                        </div>
                                    </div>
                                ))}

                                {isLoading && (
                                    <div className="flex items-start gap-3">
                                        <div
                                            className="w-9 h-9 rounded-xl flex items-center justify-center"
                                            style={{ backgroundColor: COLORS.purpleLight }}
                                        >
                                            <Brain className="w-5 h-5" style={{ color: COLORS.purple }} />
                                        </div>
                                        <div
                                            className="px-4 py-3 rounded-2xl text-base flex items-center gap-3 shadow-sm"
                                            style={{ backgroundColor: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}
                                        >
                                            <Loader2 className="w-4 h-4 animate-spin" style={{ color: COLORS.purple }} />
                                            <span style={{ color: COLORS.textMuted }}>Analyzing...</span>
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </div>

                            {/* Quick Questions */}
                            {messages.length <= 2 && (
                                <div className="px-5 pb-3 flex gap-2 flex-wrap" style={{ backgroundColor: COLORS.pageBg }}>
                                    {quickQuestions.map((q, i) => (
                                        <button
                                            key={i}
                                            onClick={() => { setInput(q); inputRef.current?.focus(); }}
                                            className="text-sm px-3 py-2 rounded-xl transition-all shadow-sm hover:shadow hover:scale-[1.02]"
                                            style={{
                                                backgroundColor: COLORS.cardBg,
                                                color: COLORS.textSecondary,
                                                border: `1px solid ${COLORS.border}`,
                                            }}
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* Input Area */}
                            <div
                                className="p-4 border-t"
                                style={{ borderColor: COLORS.border, backgroundColor: COLORS.cardBg }}
                            >
                                <div
                                    className="flex items-center gap-3 px-4 py-3 rounded-xl shadow-inner"
                                    style={{
                                        backgroundColor: COLORS.pageBg,
                                        border: `1px solid ${COLORS.border}`,
                                    }}
                                >
                                    <input
                                        ref={inputRef}
                                        type="text"
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Ask about metrics, scores..."
                                        className="flex-1 bg-transparent outline-none text-base"
                                        style={{ color: COLORS.textPrimary }}
                                        disabled={isLoading}
                                    />
                                    <button
                                        onClick={handleSend}
                                        disabled={!input.trim() || isLoading}
                                        className="p-2 rounded-lg transition-all disabled:opacity-40 hover:scale-105"
                                        style={{
                                            background: `linear-gradient(135deg, ${COLORS.purple} 0%, ${COLORS.accent} 100%)`,
                                        }}
                                    >
                                        <Send className="w-5 h-5 text-white" />
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </>
    );
};

export default ReportAssistant;

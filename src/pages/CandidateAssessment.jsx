import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Clock,
    CheckCircle,
    AlertCircle,
    Loader,
    ArrowRight,
    Brain,
    Target,
    MessageSquare,
    Wifi,
    WifiOff,
    SkipForward
} from 'lucide-react';

const API_URL_VAR = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = API_URL_VAR.trim().replace(/\/$/, '');

const CandidateAssessment = () => {
    const { token } = useParams();
    const navigate = useNavigate();

    // State
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [assessmentInfo, setAssessmentInfo] = useState(null);
    const [currentTaskIndex, setCurrentTaskIndex] = useState(0);
    const [currentTask, setCurrentTask] = useState(null);
    const [selectedOption, setSelectedOption] = useState(null);
    const [reasoning, setReasoning] = useState('');
    const [isCompleted, setIsCompleted] = useState(false);
    const [showInstructions, setShowInstructions] = useState(true);
    const [wsStatus, setWsStatus] = useState('disconnected'); // 'connecting', 'connected', 'disconnected'
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Behavioral tracking
    const [questionStartTime, setQuestionStartTime] = useState(Date.now());
    const [firstInteractionTime, setFirstInteractionTime] = useState(null);
    const [optionSelectionHistory, setOptionSelectionHistory] = useState([]);
    const [idleTimer, setIdleTimer] = useState(0);
    const [totalAnswered, setTotalAnswered] = useState(0);
    const [totalTimeSpent, setTotalTimeSpent] = useState(0);
    const [totalSkipped, setTotalSkipped] = useState(0);

    // WebSocket refs
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const MAX_RECONNECT_ATTEMPTS = 5;

    const totalTasks = assessmentInfo?.total_tasks || 0;
    const progress = totalTasks > 0 ? ((currentTaskIndex + 1) / totalTasks) * 100 : 0;

    // API helpers with better error handling
    const apiFetch = async (path, options = {}) => {
        try {
            const url = `${API_BASE}/api/v1${path}`;
            const res = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!res.ok) {
                const error = await res.json().catch(() => ({ detail: 'Request failed' }));
                // Provide user-friendly error messages
                let errorMessage = error.detail || 'Request failed';
                if (res.status === 404) {
                    errorMessage = 'Assessment not found. Please check your link.';
                } else if (res.status === 403) {
                    errorMessage = error.detail || 'Access denied. This assessment may have expired or been completed.';
                } else if (res.status >= 500) {
                    errorMessage = 'Server error. Please try again in a moment.';
                } else if (res.status === 0 || !navigator.onLine) {
                    errorMessage = 'No internet connection. Please check your network.';
                }
                throw new Error(errorMessage);
            }
            return res.json();
        } catch (err) {
            // Handle network errors
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                throw new Error('Network error. Please check your internet connection.');
            }
            throw err;
        }
    };

    // Validate token and get assessment info (does NOT start the timer)
    const validateToken = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            // Validate token first (just check if valid, don't start yet)
            const info = await apiFetch(`/assessment/${token}`);
            setAssessmentInfo(info);

            // Check if already completed
            if (info.status === 'completed' || info.status === 'locked') {
                setIsCompleted(true);
                setLoading(false);
                return;
            }

            // If already in progress (resumed), skip instructions and continue
            if (info.status === 'in_progress') {
                setCurrentTaskIndex(info.current_task_index || 0);
                setShowInstructions(false);
                await fetchTask(info.current_task_index || 0);
                connectWebSocket();
            }
            // Otherwise, show instructions and wait for user to click Start

        } catch (err) {
            console.error('Error validating assessment:', err);
            // If the error is about assessment already completed, show completion screen instead of error
            if (err.message && err.message.includes('already been completed')) {
                setIsCompleted(true);
                setLoading(false);
                return;
            }
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [token]);

    // Actually start the assessment (called when user clicks Start button)
    const startAssessmentNow = async () => {
        try {
            setLoading(true);

            // Start the assessment - this sets started_at in backend
            const startResult = await apiFetch(`/assessment/${token}/start`, { method: 'POST' });

            // Update assessment info with start result
            setAssessmentInfo(prev => ({
                ...prev,
                ...startResult,
                status: 'in_progress',
            }));

            // Set current task index from start result
            const resumeIndex = startResult.current_task_index || 0;
            setCurrentTaskIndex(resumeIndex);

            // Fetch the first task
            await fetchTask(resumeIndex);

            // Connect WebSocket
            connectWebSocket();

            // Hide instructions
            setShowInstructions(false);

        } catch (err) {
            console.error('Error starting assessment:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Fetch a specific task
    const fetchTask = async (taskIndex) => {
        try {
            const task = await apiFetch(`/assessment/${token}/task/${taskIndex}`);
            setCurrentTask(task);
            setQuestionStartTime(Date.now());
            setFirstInteractionTime(null);
            setSelectedOption(null);
            setReasoning('');
            setOptionSelectionHistory([]);
            setIdleTimer(0);

            // Send task_started event
            sendEvent('task_started', task.id, {});
        } catch (err) {
            console.error('Error fetching task:', err);
            setError(err.message);
        }
    };

    // Connect WebSocket with reconnection logic
    const connectWebSocket = useCallback(() => {
        // Prevent multiple simultaneous connection attempts
        if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
            console.log('WS: Already connected or connecting...');
            return;
        }

        setWsStatus('connecting');

        // Clean up API_BASE and build wsUrl robustly
        const wsProtocol = API_BASE.startsWith('https') ? 'wss' : 'ws';
        const wsBase = API_BASE.replace(/^https?/, wsProtocol);
        const wsUrl = `${wsBase}/ws/assessment/${encodeURIComponent(token)}`;

        console.log(`WS: Connecting to ${wsUrl} (Attempt ${reconnectAttemptsRef.current + 1})`);

        try {
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WS: Connected successfully');
                setWsStatus('connected');
                reconnectAttemptsRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    // console.log('WS: Message received:', data.type);
                } catch (e) {
                    console.warn('WS: Failed to parse message:', event.data);
                }
            };

            ws.onerror = (err) => {
                console.error('WS: Connection error:', err);
                // Status will be updated via onclose
            };

            ws.onclose = (event) => {
                console.log(`WS: Connection closed (Code: ${event.code}, Reason: ${event.reason || 'No reason'})`);
                setWsStatus('disconnected');
                wsRef.current = null;

                // Auto-reconnect if not at max attempts and assessment not completed
                if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS && !isCompleted) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
                    reconnectAttemptsRef.current++;
                    console.log(`WS: Reconnecting in ${delay}ms...`);

                    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
                    reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
                } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
                    console.warn('WS: Max reconnection attempts reached.');
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error('WS: Failed to create WebSocket instance:', err);
            setWsStatus('disconnected');

            // Try to reconnect even if constructor failed
            if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS && !isCompleted) {
                const delay = 2000;
                reconnectAttemptsRef.current++;
                reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
            }
        }
    }, [token, isCompleted]);

    // Send event via WebSocket with HTTP fallback for critical events
    const sendEvent = async (eventType, taskId, payload = {}) => {
        const event = {
            type: 'event',
            event_type: eventType,
            task_id: taskId,
            payload,
            client_timestamp: new Date().toISOString(),
        };

        // Try WebSocket first
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(event));
            return;
        }

        // HTTP fallback for critical events (task_completed, task_started)
        const criticalEvents = ['task_completed', 'task_started'];
        if (criticalEvents.includes(eventType)) {
            console.warn(`WebSocket not connected, using HTTP fallback for ${eventType}`);
            try {
                await apiFetch(`/assessment/${token}/event`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(event),
                });
                console.log(`[HTTP Fallback] ${eventType} event sent successfully`);
            } catch (err) {
                console.error(`[HTTP Fallback] Failed to send ${eventType}:`, err);
            }
        } else {
            console.warn('WebSocket not connected, non-critical event dropped:', eventType);
        }
    };

    // Initialize assessment (validate only, don't start timer yet)
    useEffect(() => {
        validateToken();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [validateToken]);

    // Track idle time
    useEffect(() => {
        if (isCompleted || loading) return;

        const interval = setInterval(() => {
            setIdleTimer(prev => prev + 1);
        }, 1000);

        return () => clearInterval(interval);
    }, [isCompleted, loading]);

    // Anti-Cheat: Emit IDLE_DETECTED event at 30s threshold
    useEffect(() => {
        if (idleTimer === 30 && currentTask) {
            sendEvent('idle_detected', currentTask.id, {
                idle_duration_ms: 30000,
                last_activity_type: 'interaction_timeout'
            });
        }
    }, [idleTimer, currentTask]);

    // Anti-Cheat: Focus/Blur detection (tab switching)
    useEffect(() => {
        if (isCompleted || loading || !currentTask) return;

        const handleBlur = () => {
            sendEvent('focus_lost', currentTask.id, {
                trigger: 'tab_switch'
            });
        };

        const handleFocus = () => {
            sendEvent('focus_gained', currentTask.id, {
                trigger: 'tab_switch'
            });
        };

        window.addEventListener('blur', handleBlur);
        window.addEventListener('focus', handleFocus);

        return () => {
            window.removeEventListener('blur', handleBlur);
            window.removeEventListener('focus', handleFocus);
        };
    }, [isCompleted, loading, currentTask]);

    // Reset idle timer on any interaction
    const handleInteraction = () => {
        setIdleTimer(0);
    };

    const handleOptionSelect = (optionIndex) => {
        if (!currentTask) return;

        if (!firstInteractionTime) {
            setFirstInteractionTime(Date.now());
        }

        const isChange = selectedOption !== null && selectedOption !== optionIndex;
        const selectedOptionId = currentTask.options[optionIndex].id;

        // Record selection history
        setOptionSelectionHistory(prev => [...prev, {
            option: optionIndex,
            option_id: selectedOptionId,
            timestamp: Date.now()
        }]);

        // Send event
        if (isChange) {
            sendEvent('option_changed', currentTask.id, {
                previous_option_index: selectedOption,
                new_option_index: optionIndex,
                option_id: selectedOptionId, // Send ID for backend robust matching
            });
        } else {
            sendEvent('option_selected', currentTask.id, {
                option_index: optionIndex,
                option_id: selectedOptionId, // Send ID for backend robust matching
            });
        }

        setSelectedOption(optionIndex);
        handleInteraction();
    };

    const handleNext = async () => {
        // Prevent double submission
        if (selectedOption === null || reasoning.trim().length < 20 || !currentTask || isSubmitting) return;

        setIsSubmitting(true);
        try {
            const timeSpent = (Date.now() - questionStartTime) / 1000;
            const hesitation = firstInteractionTime
                ? (firstInteractionTime - questionStartTime) / 1000
                : timeSpent;

            const selectedOptionId = currentTask.options[selectedOption].id;

            // Send task_completed event
            sendEvent('task_completed', currentTask.id, {
                selected_option_index: selectedOption,
                selected_option_id: selectedOptionId, // Send ID is critical for randomization
                reasoning: reasoning.trim(),
                time_spent_seconds: timeSpent,
                hesitation_seconds: hesitation,
                option_changes: optionSelectionHistory.length - 1,
            });

            setTotalAnswered(prev => prev + 1);
            setTotalTimeSpent(prev => prev + timeSpent);

            if (currentTaskIndex < totalTasks - 1) {
                // Move to next task
                const nextIndex = currentTaskIndex + 1;
                setCurrentTaskIndex(nextIndex);
                await fetchTask(nextIndex);
                setIsSubmitting(false); // Re-enable for next question
            } else {
                // Complete assessment - add small delay to ensure last task_completed event is processed
                await new Promise(resolve => setTimeout(resolve, 500));
                await completeAssessment();
            }
        } catch (error) {
            console.error('Error in handleNext:', error);
            setError(error.message || 'Failed to submit answer. Please try again.');
            setIsSubmitting(false);
        }
    };

    const handleSkip = async () => {
        if (!currentTask || isSubmitting) return;

        setIsSubmitting(true);
        try {
            const timeSpent = (Date.now() - questionStartTime) / 1000;

            // Send task_skipped event
            sendEvent('task_skipped', currentTask.id, {
                time_spent_seconds: timeSpent,
                had_selection: selectedOption !== null,
                had_reasoning: reasoning.trim().length > 0,
            });

            setTotalAnswered(prev => prev + 1);
            setTotalSkipped(prev => prev + 1);
            setTotalTimeSpent(prev => prev + timeSpent);

            if (currentTaskIndex < totalTasks - 1) {
                const nextIndex = currentTaskIndex + 1;
                setCurrentTaskIndex(nextIndex);
                await fetchTask(nextIndex);
                setIsSubmitting(false);
            } else {
                await new Promise(resolve => setTimeout(resolve, 500));
                await completeAssessment();
            }
        } catch (error) {
            console.error('Error in handleSkip:', error);
            setError(error.message || 'Failed to skip question.');
            setIsSubmitting(false);
        }
    };

    const completeAssessment = async () => {
        try {
            await apiFetch(`/assessment/${token}/complete`, { method: 'POST' });
            setIsCompleted(true);

            // Close WebSocket
            if (wsRef.current) {
                wsRef.current.close();
            }
        } catch (err) {
            console.error('Error completing assessment:', err);
            setError(err.message);
            setIsSubmitting(false); // Re-enable if error occurs
        }
    };

    // Loading state with better UX
    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-black flex items-center justify-center p-6">
                <div className="glass-card p-12 text-center animate-fade-in">
                    <Loader className="w-16 h-16 text-primary-500 animate-spin mx-auto mb-4" />
                    <h1 className="text-2xl font-bold text-white mb-2">Loading Assessment...</h1>
                    <p className="text-gray-400 mb-4">Please wait while we prepare your assessment.</p>
                    {wsStatus === 'connecting' && (
                        <p className="text-sm text-gray-500">Connecting to server...</p>
                    )}
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-black flex items-center justify-center p-6">
                <div className="glass-card p-12 text-center max-w-md">
                    <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h1 className="text-2xl font-bold text-white mb-2">Assessment Error</h1>
                    <p className="text-gray-400 mb-6">{error}</p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <button
                            onClick={() => window.location.reload()}
                            className="btn-gradient"
                        >
                            Try Again
                        </button>
                        <button
                            onClick={() => navigate('/')}
                            className="px-6 py-3 rounded-lg border-2 border-gray-600 text-white hover:border-gray-500 hover:bg-white/5 transition-all"
                        >
                            Go Back
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Completed state
    if (isCompleted) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-black flex items-center justify-center p-4 sm:p-6">
                <div className="max-w-2xl w-full glass-card p-8 sm:p-12 text-center animate-fade-in">
                    <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 rounded-full bg-green-500/20 flex items-center justify-center">
                        <CheckCircle className="w-10 h-10 sm:w-12 sm:h-12 text-green-400" />
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">Assessment Completed!</h1>
                    <p className="text-lg sm:text-xl text-gray-300 mb-8">
                        {totalAnswered > 0
                            ? "Thank you for completing the assessment. Your responses have been recorded."
                            : "This assessment has already been completed. Your responses have been recorded."}
                    </p>
                    {totalAnswered > 0 && (
                        <div className="grid grid-cols-3 gap-4 sm:gap-6 mb-8">
                            <div className="glass-card p-4 sm:p-6">
                                <p className="text-gray-400 text-sm mb-2">Questions Answered</p>
                                <p className="text-2xl sm:text-3xl font-bold text-gradient">{totalAnswered - totalSkipped}</p>
                            </div>
                            <div className="glass-card p-4 sm:p-6">
                                <p className="text-gray-400 text-sm mb-2">Skipped</p>
                                <p className={`text-2xl sm:text-3xl font-bold ${totalSkipped > 0 ? 'text-yellow-400' : 'text-gradient'}`}>{totalSkipped}</p>
                            </div>
                            <div className="glass-card p-4 sm:p-6">
                                <p className="text-gray-400 text-sm mb-2">Total Time</p>
                                <p className="text-2xl sm:text-3xl font-bold text-gradient">
                                    {Math.floor(totalTimeSpent / 60)}m
                                </p>
                            </div>
                        </div>
                    )}
                    <p className="text-gray-400 mb-6">
                        Your recruiter will review your results and contact you soon.
                    </p>
                    <button
                        onClick={() => navigate('/')}
                        className="btn-gradient"
                    >
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    // Instruction screen
    if (showInstructions) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-black flex items-center justify-center p-4 sm:p-6">
                <div className="max-w-2xl w-full animate-fade-in">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-primary-500/20 to-secondary-500/20 flex items-center justify-center">
                            <Brain className="w-10 h-10 text-primary-400" />
                        </div>
                        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">Welcome to Your Assessment</h1>
                        <p className="text-lg text-gray-300">
                            {assessmentInfo?.candidate_name && `Hello ${assessmentInfo.candidate_name.split(' ')[0]}! `}
                            Let's understand how you think and make decisions.
                        </p>
                    </div>

                    {/* Instructions Card */}
                    <div className="glass-card p-6 sm:p-8 mb-6">
                        <h2 className="text-xl font-semibold text-white mb-6">How It Works</h2>

                        <div className="space-y-4">
                            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5">
                                <div className="w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center flex-shrink-0">
                                    <Target className="w-5 h-5 text-primary-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-medium mb-1">No Wrong Answers</h3>
                                    <p className="text-gray-400 text-sm">
                                        This isn't a test of knowledge. We want to understand your thinking style and decision-making approach.
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5">
                                <div className="w-10 h-10 rounded-full bg-secondary-500/20 flex items-center justify-center flex-shrink-0">
                                    <MessageSquare className="w-5 h-5 text-secondary-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-medium mb-1">Share Your Reasoning</h3>
                                    <p className="text-gray-400 text-sm">
                                        After selecting an option, explain why you chose it. Your reasoning matters as much as your choice.
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5">
                                <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                                    <Clock className="w-5 h-5 text-green-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-medium mb-1">Take Your Time</h3>
                                    <p className="text-gray-400 text-sm">
                                        There's no time pressure. Answer thoughtfully and at your own pace.
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4 p-4 rounded-lg bg-white/5">
                                <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                                    <SkipForward className="w-5 h-5 text-yellow-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-medium mb-1">Skip Option Available</h3>
                                    <p className="text-gray-400 text-sm">
                                        You can skip questions, but skipping applies a penalty to your score. Use it wisely.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Assessment Info */}
                    <div className="glass-card p-4 sm:p-6 mb-6">
                        <div className="grid grid-cols-2 gap-4 text-center">
                            <div>
                                <p className="text-gray-400 text-sm mb-1">Total Questions</p>
                                <p className="text-2xl font-bold text-white">{totalTasks}</p>
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm mb-1">Estimated Time</p>
                                <p className="text-2xl font-bold text-white">{Math.ceil(totalTasks * 1.5)}m</p>
                            </div>
                        </div>
                    </div>

                    {/* Start Button - Actually starts the assessment timer */}
                    <button
                        onClick={startAssessmentNow}
                        disabled={loading}
                        className={`w-full btn-gradient py-4 text-lg font-semibold flex items-center justify-center gap-2 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {loading ? (
                            <>
                                <Loader className="w-5 h-5 animate-spin" />
                                <span>Starting...</span>
                            </>
                        ) : (
                            <>
                                <span>Start Assessment</span>
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>

                    <p className="text-center text-gray-500 text-sm mt-4">
                        By starting, you agree that your responses will be shared with the hiring team.
                    </p>
                </div>
            </div>
        );
    }

    // Assessment in progress
    return (
        <div className="min-h-screen bg-gradient-to-br from-black via-neutral-950 to-black flex flex-col">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/80 backdrop-blur-md sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
                    <div className="flex items-center justify-between mb-3">
                        <div>
                            <div className="flex items-center gap-2">
                                <img
                                    src="/hiremate-logo.svg"
                                    alt="HireMate Logo"
                                    className="w-8 h-8"
                                />
                                <h1 className="text-lg sm:text-xl font-bold text-gradient">HireMate Assessment</h1>
                            </div>
                            <p className="text-xs sm:text-sm text-gray-400">Question {currentTaskIndex + 1} of {totalTasks}</p>
                        </div>
                        <div className="flex items-center gap-3 sm:gap-4">
                            {/* Connection Status */}
                            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs ${wsStatus === 'connected'
                                ? 'bg-green-500/20 text-green-400'
                                : wsStatus === 'connecting'
                                    ? 'bg-yellow-500/20 text-yellow-400'
                                    : 'bg-red-500/20 text-red-400'
                                }`}>
                                {wsStatus === 'connected' ? (
                                    <Wifi className="w-3 h-3" />
                                ) : (
                                    <WifiOff className="w-3 h-3" />
                                )}
                                <span className="hidden sm:inline">
                                    {wsStatus === 'connected' ? 'Connected' : wsStatus === 'connecting' ? 'Connecting...' : 'Offline'}
                                </span>
                            </div>
                            {/* Timer */}
                            <div className="flex items-center gap-1.5 sm:gap-2 text-gray-300">
                                <Clock className="w-4 h-4" />
                                <span className="text-xs sm:text-sm">
                                    {Math.floor((Date.now() - questionStartTime) / 1000)}s
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-700 rounded-full h-1.5 sm:h-2">
                        <div
                            className="bg-gradient-to-r from-primary-500 to-secondary-500 h-1.5 sm:h-2 rounded-full transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex items-center justify-center p-4 sm:p-6">
                {
                    currentTask ? (
                        <div className="max-w-4xl w-full animate-fade-in">
                            {/* Question */}
                            <div className="glass-card p-5 sm:p-8 mb-4 sm:mb-6">
                                <div className="flex items-start gap-3 sm:gap-4 mb-4 sm:mb-6">
                                    <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-lg sm:text-xl flex-shrink-0">
                                        {currentTaskIndex + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                                            <span className="px-2 sm:px-3 py-1 rounded-full bg-primary-500/20 text-primary-400 text-xs font-semibold">
                                                {currentTask.category || 'General'}
                                            </span>
                                            <span className="px-2 sm:px-3 py-1 rounded-full bg-secondary-500/20 text-secondary-400 text-xs font-semibold">
                                                {currentTask.difficulty || 'Medium'}
                                            </span>
                                        </div>
                                        <h2
                                            className="text-lg sm:text-2xl font-semibold text-white leading-relaxed cursor-text selection:bg-red-500/30"
                                            onCopy={(e) => {
                                                // Anti-Cheat: Detect copying question text
                                                const copiedText = document.getSelection().toString();
                                                if (copiedText.length > 10 && currentTask) {
                                                    sendEvent('copy_detected', currentTask.id, {
                                                        text_preview: copiedText.substring(0, 50),
                                                        char_count: copiedText.length,
                                                        source: 'question_text'
                                                    });
                                                }
                                            }}
                                        >
                                            {currentTask.scenario}
                                        </h2>
                                    </div>
                                </div>

                                {/* Options */}
                                <div className="space-y-2 sm:space-y-3" >
                                    {
                                        currentTask.options?.map((option, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleOptionSelect(index)}
                                                className={`w-full text-left p-3 sm:p-4 rounded-lg border-2 transition-all duration-200 active:scale-[0.98] ${selectedOption === index
                                                    ? 'border-primary-500 bg-primary-500/10 shadow-lg shadow-primary-500/20'
                                                    : 'border-gray-600 hover:border-gray-500 hover:bg-white/5 hover:shadow-md'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-3 sm:gap-4">
                                                    <div className={`w-5 h-5 sm:w-6 sm:h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${selectedOption === index
                                                        ? 'border-primary-500 bg-primary-500'
                                                        : 'border-gray-500'
                                                        }`}>
                                                        {selectedOption === index && (
                                                            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 bg-white rounded-full" />
                                                        )}
                                                    </div>
                                                    <span className="text-sm sm:text-base text-white font-medium">{option.text || option}</span>
                                                </div>
                                            </button>
                                        ))
                                    }
                                </div>
                            </div >

                            {/* Reasoning */}
                            < div className="glass-card p-6 mb-6" >
                                <label className="block text-white font-semibold mb-1">
                                    Explain your reasoning <span className="text-red-400">*</span>
                                </label>
                                <p className="text-sm text-gray-400 mb-3">
                                    Minimum 20 characters required
                                </p>
                                <textarea
                                    value={reasoning}
                                    onChange={(e) => {
                                        setReasoning(e.target.value);
                                        handleInteraction();
                                    }}
                                    onPaste={(e) => {
                                        // Anti-Cheat: Detect paste events
                                        const pastedText = e.clipboardData?.getData('text') || '';
                                        if (pastedText.length > 50 && currentTask) {
                                            sendEvent('paste_detected', currentTask.id, {
                                                char_count: pastedText.length,
                                                source: 'reasoning'
                                            });
                                        }
                                        handleInteraction();
                                    }}
                                    placeholder="Share your thought process... (minimum 20 characters)"
                                    className={`input-field w-full min-h-[100px] resize-none transition-all duration-200 ${reasoning.length > 0 && reasoning.length < 20 ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20' : 'focus:border-primary-500 focus:ring-primary-500/20'}`}
                                    required
                                />
                                <div className="flex items-center justify-between mt-2">
                                    <span className={`text-xs ${reasoning.length < 20 ? 'text-red-400' : 'text-green-400'}`}>
                                        {reasoning.length < 20 ? `${20 - reasoning.length} characters remaining` : '✓ Requirement met'}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {reasoning.length} / 500 characters
                                    </span>
                                </div>
                            </div >

                            {/* Navigation */}
                            < div className="flex items-center justify-between" >
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={handleSkip}
                                        disabled={isSubmitting}
                                        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-all text-sm ${isSubmitting ? 'opacity-50 cursor-not-allowed' : 'active:scale-95'}`}
                                    >
                                        <SkipForward className="w-4 h-4" />
                                        Skip
                                    </button>
                                    <span className="text-xs text-yellow-500/70 hidden sm:inline">⚠ Penalty applies</span>
                                </div>

                                <div className="flex items-center gap-3">
                                    <div className="text-sm text-gray-400 hidden sm:block">
                                        {selectedOption !== null && reasoning.trim().length >= 20 ? (
                                            <span className="text-green-400">✓ Ready</span>
                                        ) : selectedOption === null ? (
                                            <span className="text-yellow-400">⚠ Select an answer</span>
                                        ) : (
                                            <span className="text-yellow-400">⚠ Add reasoning</span>
                                        )}
                                    </div>

                                    <button
                                        onClick={handleNext}
                                        disabled={selectedOption === null || reasoning.trim().length < 20 || isSubmitting}
                                        className={`btn-gradient flex items-center gap-2 transition-all ${(selectedOption === null || reasoning.trim().length < 20 || isSubmitting) ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 active:scale-95'}`}
                                    >
                                        {isSubmitting && <Loader className="w-4 h-4 animate-spin" />}
                                        {isSubmitting
                                            ? (currentTaskIndex < totalTasks - 1 ? 'Submitting...' : 'Completing...')
                                            : (currentTaskIndex < totalTasks - 1 ? 'Next Question' : 'Complete Assessment')
                                        }
                                    </button>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="glass-card p-12 text-center">
                            <Loader className="w-12 h-12 text-primary-500 animate-spin mx-auto mb-4" />
                            <p className="text-gray-400">Loading task...</p>
                        </div>
                    )}
            </main>
        </div>
    );
};

export default CandidateAssessment;

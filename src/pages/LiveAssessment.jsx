import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Clock,
    Users,
    Activity,
    CheckCircle2,
    AlertCircle,
    RefreshCcw,
    FileText,
    ThumbsUp,
    ThumbsDown,
    Pause,
    Eye,
    MessageSquare,
    TrendingUp,
    TrendingDown,
    Minus,
    Zap,
    Brain,
    Target,
    Timer,
    Shield,
    ChevronLeft,
    ChevronRight,
    Sun,
    Moon,
    Trophy,
    Crown,
    Medal,
    EyeOff,
    Clipboard,
    Copy,
    ChevronDown,
    ChevronUp,
    Trash2,
    AlignLeft,
    ShieldAlert,
} from 'lucide-react';
import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
} from 'recharts';
import { getAuthToken, apiDelete, apiGet, apiPost } from '../api/client';
import TermTooltip from '../components/ui/TermTooltip';
import TrustDisclaimer from '../components/ui/TrustDisclaimer';
import PopulationIntelligence from '../components/charts/PopulationIntelligence';
import ReportAssistant from '../components/chat/ReportAssistant';
import { useTheme } from '../context/ThemeContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Theme-aware color palettes
const LIGHT_COLORS = {
    // Backgrounds
    pageBg: '#F7F9FF',
    cardBg: '#FFFFFF',
    cardBgAlt: '#F1F5F9',
    // Borders & Lines
    border: '#E2E8F0',
    borderLight: '#F1F5F9',

    // Text
    textPrimary: '#0F172A',
    textSecondary: '#475569',
    textMuted: '#94A3B8',

    // Accent colors (subtle, professional)
    accent: '#3B82F6',       // Blue - primary accent
    accentLight: '#EFF6FF',
    accentDark: '#1E40AF',

    // Status colors (muted but visible)
    success: '#059669',
    successLight: '#ECFDF5',
    successBg: '#D1FAE5',

    warning: '#D97706',
    warningLight: '#FFFBEB',
    warningBg: '#FEF3C7',

    danger: '#DC2626',
    dangerLight: '#FEF2F2',
    dangerBg: '#FEE2E2',

    // Special
    purple: '#7C3AED',
    purpleLight: '#EDE9FE',

    teal: '#0D9488',
    tealLight: '#CCFBF1',
};

const DARK_COLORS = {
    // Backgrounds - Pure Black
    pageBg: '#000000',
    cardBg: '#0a0a0a',
    cardBgAlt: '#171717',
    // Borders & Lines
    border: '#262626',
    borderLight: '#171717',

    // Text
    textPrimary: '#FAFAFA',
    textSecondary: '#D4D4D4',
    textMuted: '#A3A3A3',

    // Accent colors (vibrant for dark mode)
    accent: '#60A5FA',       // Lighter blue for dark mode
    accentLight: '#0c1929',
    accentDark: '#93C5FD',

    // Status colors (adjusted for dark mode)
    success: '#34D399',
    successLight: '#052e16',
    successBg: '#065F46',

    warning: '#FBBF24',
    warningLight: '#451a03',
    warningBg: '#92400E',

    danger: '#F87171',
    dangerLight: '#450a0a',
    dangerBg: '#991B1B',

    // Special
    purple: '#A78BFA',
    purpleLight: '#1e1033',

    teal: '#2DD4BF',
    tealLight: '#0d2927',
};

const LiveAssessment = () => {
    const navigate = useNavigate();
    const { isDark, toggleTheme } = useTheme();

    // Dynamic colors based on theme
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;
    const [activeAssessments, setActiveAssessments] = useState([]);
    const [completedAssessments, setCompletedAssessments] = useState([]);
    const [selectedAttemptId, setSelectedAttemptId] = useState(null);
    const [liveData, setLiveData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [metricsLoading, setMetricsLoading] = useState(false);

    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [viewingQuestionIndex, setViewingQuestionIndex] = useState(null); // null = live view, number = viewing specific question
    const [showAntiCheat, setShowAntiCheat] = useState(false); // Collapsible anti-cheat flags
    const [showDetailedBehavior, setShowDetailedBehavior] = useState(true); // Toggle for behavioral cards
    const [showCandidateDropdown, setShowCandidateDropdown] = useState(false); // Active candidate switcher
    const [isViewingCompleted, setIsViewingCompleted] = useState(false); // Track if viewing a completed assessment
    const [sidebarTab, setSidebarTab] = useState('all'); // 'all' or 'leaderboard'
    const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'profile' | 'livefeed' | 'ai'
    const [showDetailedMetrics, setShowDetailedMetrics] = useState(false); // Expand full metrics in Profile tab
    const [confirmDeleteId, setConfirmDeleteId] = useState(null); // ID pending delete confirmation
    const [deletingId, setDeletingId] = useState(null); // ID currently being deleted
    const [candidateDecisions, setCandidateDecisions] = useState({}); // Store recruiter decisions {attemptId: 'shortlist'|'hold'|'reject'}
    const [predictionsLoading, setPredictionsLoading] = useState(false);
    const [interviewSuccess, setInterviewSuccess] = useState(null);
    const [behavioralTraits, setBehavioralTraits] = useState(null);
    const [atsScore, setAtsScore] = useState(null);
    const [recentEvents, setRecentEvents] = useState([]); // Real-time behavioral log
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const selectedAttemptIdRef = useRef(null); // Ref to avoid stale closure in WebSocket

    // Load candidate decisions from localStorage on mount
    useEffect(() => {
        const savedDecisions = localStorage.getItem('candidateDecisions');
        if (savedDecisions) {
            setCandidateDecisions(JSON.parse(savedDecisions));
        }
    }, []);

    // Handler for recruiter decision buttons
    const handleRecruiterDecision = (decision) => {
        if (!selectedAttemptId) return;

        const updatedDecisions = {
            ...candidateDecisions,
            [selectedAttemptId]: {
                decision,
                candidateName: displayData.candidate.name,
                candidateEmail: displayData.candidate.email,
                candidatePosition: displayData.candidate.position,
                timestamp: new Date().toISOString(),
                score: displayData.overall_fit.score
            }
        };

        setCandidateDecisions(updatedDecisions);
        localStorage.setItem('candidateDecisions', JSON.stringify(updatedDecisions));
    };

    // Get decision info for a candidate
    const getDecisionInfo = (attemptId) => {
        return candidateDecisions[attemptId];
    };

    // --- Delete assessment ---
    const deleteAssessment = async (attemptId) => {
        setDeletingId(attemptId);
        try {
            await apiDelete(`/live-assessment/${attemptId}`);
            // Clear selection if deleted candidate was the selected one
            if (selectedAttemptId === attemptId) {
                setSelectedAttemptId(null);
                setLiveData(null);
            }
            // Refresh lists
            await fetchActiveAssessments();
            await fetchCompletedAssessments();
        } catch (err) {
            console.error('Failed to delete assessment:', err);
            alert(`Failed to delete: ${err.message}`);
        } finally {
            setDeletingId(null);
            setConfirmDeleteId(null);
        }
    };

    useEffect(() => {
        // Load BOTH lists before clearing loading state
        // This prevents the "Upload Resume" empty state from flashing
        const initialLoad = async () => {
            try {
                await Promise.all([
                    fetchActiveAssessments(true),
                    fetchCompletedAssessments()
                ]);
            } finally {
                setLoading(false);
            }
        };
        initialLoad();

        // Poll for assessments list every 10 seconds
        const assessmentInterval = setInterval(() => {
            fetchActiveAssessments(false); // Polling update - no auto-select
            fetchCompletedAssessments();
        }, 10000);

        // Poll for live metrics every 5 seconds as fallback for WebSocket
        // Use silent fetch (no loading state) to avoid UI flickering
        const metricsInterval = setInterval(async () => {
            const attemptId = selectedAttemptIdRef.current;
            if (attemptId) {
                try {
                    const data = await apiGet(`/api/v1/live-assessment/${attemptId}/stats`);
                    setLiveData(data);
                    if (data.current_question) setCurrentQuestion(data.current_question);
                } catch (err) {
                    // Silent fail for polling
                }
            }
        }, 5000);

        return () => {
            clearInterval(assessmentInterval);
            clearInterval(metricsInterval);
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        };
    }, []);

    // Effect 1: Handle Profile Switching (Blocking fetch)
    useEffect(() => {
        if (selectedAttemptId) {
            selectedAttemptIdRef.current = selectedAttemptId;
            // CRITICAL: Clear old data immediately to prevent flickering
            setLiveData(null);
            setCurrentQuestion(null);
            setViewingQuestionIndex(null);
            setRecentEvents([]); // Clear activity feed when switching candidates
            fetchLiveMetrics(selectedAttemptId);
        }
    }, [selectedAttemptId]);

    // Effect 2: Handle Connection & Status (Silent update)
    useEffect(() => {
        if (selectedAttemptId) {
            // Check if this is a completed assessment (from leaderboard)
            const isCompleted = completedAssessments.some(a => a.id === selectedAttemptId);
            setIsViewingCompleted(isCompleted);

            // Only connect WebSocket for active assessments, not completed ones
            if (!isCompleted) {
                // connectWebSocket handles its own internal "already connected" logic or we can just let it re-connect if needed
                connectWebSocket(selectedAttemptId);
            } else if (wsRef.current) {
                wsRef.current.close();
            }
        }
        return () => { if (wsRef.current) wsRef.current.close(); };
    }, [selectedAttemptId, completedAssessments]);

    // Fetch ML predictions + ATS score when viewing a candidate with data
    useEffect(() => {
        if (!selectedAttemptId || selectedAttemptId === 'demo-1') {
            setInterviewSuccess(null);
            setBehavioralTraits(null);
            setAtsScore(null);
            return;
        }
        let cancelled = false;
        setPredictionsLoading(true);
        setInterviewSuccess(null);
        setBehavioralTraits(null);
        setAtsScore(null);
        (async () => {
            try {
                const [successRes, behavioralRes, atsRes] = await Promise.allSettled([
                    apiPost('predictions/interview-success', { attempt_id: selectedAttemptId, include_resume: true }),
                    apiGet(`predictions/behavioral/${selectedAttemptId}`),
                    apiGet(`/api/v1/attempts/${selectedAttemptId}/ats-score`),
                ]);
                if (cancelled) return;
                if (successRes.status === 'fulfilled') setInterviewSuccess(successRes.value);
                if (behavioralRes.status === 'fulfilled') setBehavioralTraits(behavioralRes.value);
                if (atsRes.status === 'fulfilled') setAtsScore(atsRes.value);
            } catch (_) {
                if (!cancelled) setInterviewSuccess(null);
            } finally {
                if (!cancelled) setPredictionsLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [selectedAttemptId]);

    // Use a ref to track if we've done the initial auto-select
    const hasInitialSelectedRef = useRef(false);

    const fetchActiveAssessments = async (isInitial = false) => {
        try {
            const data = await apiGet('/api/v1/live-assessment/active');
            setActiveAssessments(data.assessments || []);

            // Only auto-select on the very first successful load
            if (isInitial && data.assessments?.length > 0 && !hasInitialSelectedRef.current) {
                setSelectedAttemptId(data.assessments[0].id);
                hasInitialSelectedRef.current = true;
            }
            return data.assessments || [];
        } catch (err) {
            console.error('LiveAssessment: active fetch failed', err);
            setActiveAssessments([]);
            return [];
        }
    };

    const fetchCompletedAssessments = async () => {
        try {
            const data = await apiGet('/api/v1/live-assessment/completed');
            setCompletedAssessments(data.assessments || []);

            // Auto-select first completed assessment if no active assessments and no selection yet
            if (data.assessments?.length > 0 && !hasInitialSelectedRef.current && activeAssessments.length === 0) {
                setSelectedAttemptId(data.assessments[0].id);
                setIsViewingCompleted(true);
                hasInitialSelectedRef.current = true;
            }
        } catch (err) {
            console.error('Failed to fetch completed assessments:', err);
        }
    };

    const fetchLiveMetrics = async (attemptId) => {
        setMetricsLoading(true);
        try {
            const data = await apiGet(`/api/v1/live-assessment/${attemptId}/stats`);
            setLiveData(data);
            if (data.current_question) setCurrentQuestion(data.current_question);
        } catch (err) {
            console.error('Failed to fetch live metrics:', err);
        } finally {
            setMetricsLoading(false);
        }
    };

    const connectWebSocket = (attemptId) => {
        if (attemptId === 'demo-1') return;
        // Don't connect WebSocket for completed assessments
        const isCompleted = completedAssessments.some(a => a.id === attemptId);
        if (isCompleted) return;

        const token = getAuthToken();
        if (!token) return;

        // CRITICAL: Close existing connection first to prevent resource leaks
        if (wsRef.current) {
            wsRef.current.onclose = null; // Prevent reconnect loop
            wsRef.current.close();
            wsRef.current = null;
        }

        const wsUrl = `${API_URL.replace('http', 'ws')}/ws/live/${attemptId}?token=${token}`;

        // Throttle: only allow one fetch per 3 seconds for WebSocket updates
        let lastFetchTime = 0;
        const THROTTLE_MS = 3000;

        try {
            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onmessage = async (event) => {
                const msg = JSON.parse(event.data);
                const currentAttemptId = selectedAttemptIdRef.current;

                // Handle real-time event logging for the feed
                if (msg.type === 'event_logged') {
                    const behavioralEvents = ['paste_detected', 'copy_detected', 'focus_lost', 'focus_gained', 'idle_detected'];
                    if (behavioralEvents.includes(msg.event_type)) {
                        setRecentEvents(prev => [{
                            id: msg.event_id,
                            type: msg.event_type,
                            timestamp: msg.timestamp,
                            payload: msg.payload || {}
                        }, ...prev].slice(0, 30));
                    }
                }

                // Throttle metrics fetches to prevent flooding
                const now = Date.now();
                if (['event_logged', 'metrics_update'].includes(msg.type)) {
                    if (now - lastFetchTime > THROTTLE_MS) {
                        lastFetchTime = now;
                        try {
                            const data = await apiGet(`/api/v1/live-assessment/${currentAttemptId}/stats`);
                            setLiveData(data);
                        } catch (err) {
                            // Silently fail - polling will handle it
                        }
                    }
                }
                if (['status_update', 'assessment_completed'].includes(msg.type)) {
                    fetchActiveAssessments(false);
                    fetchCompletedAssessments();
                }
            };

            wsRef.current.onerror = () => {
                // Silently handle errors - polling is the fallback
            };

            wsRef.current.onclose = () => {
                // DON'T auto-reconnect - polling handles all updates now
                // WebSocket is just a nice-to-have for real-time feel
            };
        } catch (err) {
            console.warn('WebSocket connection failed, using polling fallback');
        }
    };

    const formatTime = (s) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
    const summarizeExplanation = (text) => {
        if (!text) return '';
        const firstSentence = text.split('. ')[0];
        return firstSentence.endsWith('.') ? firstSentence : `${firstSentence}.`;
    };

    // Helper: check if a candidate is selected and has data loaded
    const hasSelectedCandidate = selectedAttemptId && liveData;

    // Default values used when liveData is loading or null
    const emptyDefaults = {
        candidate: { name: 'Candidate', email: '...', position: '...', avatar: 'C' },
        progress: { current: 0, total: 3, status: 'pending' },
        time_elapsed_seconds: 0,
        metrics: {
            avg_response_time: 0,
            decision_speed: 'N/A',
            session_continuity: 0,
            decision_firmness: 0,
            idle_time: 0,
            reasoning_depth: 0,
            cheating_resilience: 100,
            focus_loss_count: 0,
            paste_count: 0,
            copy_count: 0,
            paste_detected: false,
            copy_detected: false,
        },
        skill_profile: {
            problem_solving: 0,
            analytical_thinking: 0,
            decision_speed: 0,
            creativity: 0,
            risk_assessment: 0,
        },
        behavioral_summary: {
            approach_pattern: 'Analyzing...',
            approach: 'Calculating...',
            under_pressure: 'Observing...',
            correctness_rate: 0,
            verdict: null,
        },
        resume_comparison: {
            observed_skills: [],
            overall_score: 0,
        },
        overall_fit: {
            score: 0,
            grade: '—',
            grade_label: 'Not Started',
            grade_color: 'gray',
            breakdown: {},
        },
    };

    // Display data: merge liveData with defaults
    const displayData = liveData ? {
        ...emptyDefaults,
        ...liveData,
        candidate: { ...emptyDefaults.candidate, ...liveData.candidate },
        progress: { ...emptyDefaults.progress, ...(liveData.progress || {}) },
        metrics: { ...emptyDefaults.metrics, ...(liveData.metrics || {}) },
        skill_profile: { ...emptyDefaults.skill_profile, ...(liveData.skill_profile || {}) },
        behavioral_summary: { ...emptyDefaults.behavioral_summary, ...(liveData.behavioral_summary || {}) },
        resume_comparison: { ...emptyDefaults.resume_comparison, ...(liveData.resume_comparison || {}) },
        overall_fit: { ...emptyDefaults.overall_fit, ...(liveData.overall_fit || {}) },
    } : emptyDefaults;

    const getRadarData = () => {
        const sp = displayData.skill_profile;
        return [
            { skill: 'Task Completion', termKey: 'taskCompletion', value: sp.problem_solving || 0 },
            { skill: 'Selection Speed', termKey: 'selectionSpeed', value: sp.decision_speed || 0 },
            { skill: 'Deliberation', termKey: 'deliberation', value: sp.analytical_thinking || 0 },
            { skill: 'Exploration', termKey: 'optionExploration', value: sp.creativity || 0 },
            { skill: 'Risk Distribution', termKey: 'riskDistribution', value: sp.risk_assessment || 0 },
        ];
    };

    const radarExplanationKey = {
        taskCompletion: 'task_completion',
        selectionSpeed: 'selection_speed_score',
        deliberation: 'deliberation_pattern',
        optionExploration: 'option_exploration',
        riskDistribution: 'risk_preference',
    };

    const getDecisionFirmnessLevel = () => {
        const score = displayData.metrics.decision_firmness || 0;
        if (score >= 75) return { label: 'High', color: COLORS.success, bg: COLORS.successLight };
        if (score >= 50) return { label: 'Medium', color: COLORS.warning, bg: COLORS.warningLight };
        return { label: 'Low', color: COLORS.danger, bg: COLORS.dangerLight };
    };

    const firmness = getDecisionFirmnessLevel();

    // Check if candidate has COMPLETED at least one question (not just started)
    // per_task_metrics contains is_completed flag for each task
    const completedTasks = (liveData?.per_task_metrics || []).filter(t => t.is_completed);
    const hasCompletedAnyTask = completedTasks.length > 0;

    // hasStarted should be true ONLY when at least one question is fully answered
    // progress.current = 1 means ON question 1, not that question 1 is DONE
    const hasStarted = liveData && hasCompletedAnyTask;


    return (
        <div
            className="h-screen overflow-hidden"
            style={{
                backgroundColor: COLORS.pageBg,
                backgroundImage: isDark
                    ? `radial-gradient(1200px 700px at 15% -10%, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0) 60%),
                       radial-gradient(900px 520px at 85% -5%, rgba(124, 58, 237, 0.1) 0%, rgba(124, 58, 237, 0) 60%),
                       radial-gradient(700px 520px at 70% 85%, rgba(13, 148, 136, 0.1) 0%, rgba(13, 148, 136, 0) 55%),
                       linear-gradient(180deg, #000000 0%, #0a0a0a 45%, #000000 100%)`
                    : `radial-gradient(1200px 700px at 15% -10%, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0) 60%),
                       radial-gradient(900px 520px at 85% -5%, rgba(124, 58, 237, 0.12) 0%, rgba(124, 58, 237, 0) 60%),
                       radial-gradient(700px 520px at 70% 85%, rgba(13, 148, 136, 0.12) 0%, rgba(13, 148, 136, 0) 55%),
                       linear-gradient(180deg, #F7F9FF 0%, #F4F7FF 45%, #F8FAFC 100%)`,
                fontFamily: 'Inter, system-ui, sans-serif'
            }}
        >
            {/* Header with subtle accent */}
            <header
                className="px-6 py-3 border-b shadow-sm"
                style={{
                    background: isDark
                        ? `linear-gradient(90deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`
                        : `linear-gradient(90deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`,
                    borderColor: COLORS.border,
                    backdropFilter: 'saturate(160%) blur(6px)'
                }}
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <img
                            src="/hiremate-logo.svg"
                            alt="HireMate Logo"
                            className="w-10 h-10"
                            style={{ filter: isDark ? 'brightness(1.2)' : 'none' }}
                        />
                        <div>
                            <span className="font-bold text-lg" style={{ color: COLORS.accent }}>HireMate</span>
                            <span className="font-semibold ml-2" style={{ color: COLORS.textPrimary }}>Live Assessment</span>
                            <span className="ml-2 text-xs" style={{ color: COLORS.textMuted }}>Real-time Monitoring</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Dark/Light Mode Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg transition-all duration-300 hover:scale-105"
                            style={{
                                backgroundColor: COLORS.cardBgAlt,
                                border: `1px solid ${COLORS.border}`,
                                color: COLORS.textSecondary
                            }}
                            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                        >
                            {isDark ? (
                                <Sun className="w-4 h-4" style={{ color: '#FBBF24' }} />
                            ) : (
                                <Moon className="w-4 h-4" style={{ color: '#6366F1' }} />
                            )}
                        </button>
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="text-sm px-3 py-1.5 rounded-lg transition-colors"
                            style={{
                                color: COLORS.textSecondary,
                                backgroundColor: isDark ? COLORS.cardBgAlt : 'transparent'
                            }}
                        >
                            ← Dashboard
                        </button>
                    </div>
                </div>
            </header>

            {loading ? (
                <div className="p-6 h-full w-full animate-pulse" style={{ backgroundColor: COLORS.pageBg }}>
                    <div className="flex gap-4 h-full">
                        {/* Skeleton Sidebar (20%) */}
                        <div style={{ width: '20%' }} className="space-y-4">
                            <div className="h-40 rounded-2xl bg-gray-200 dark:bg-gray-800"></div>
                            <div className="h-24 rounded-xl bg-gray-200 dark:bg-gray-800"></div>
                            <div className="space-y-2 pt-4">
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="h-16 rounded-lg bg-gray-200 dark:bg-gray-800"></div>
                                ))}
                            </div>
                        </div>

                        {/* Skeleton Main Panel (80%) */}
                        <div style={{ width: '80%' }} className="space-y-4">
                            <div className="h-32 rounded-2xl bg-gray-200 dark:bg-gray-800"></div>
                            <div className="h-10 rounded-xl bg-gray-200 dark:bg-gray-800" style={{ width: '60%' }}></div>
                            <div className="h-64 rounded-xl bg-gray-200 dark:bg-gray-800"></div>
                        </div>
                    </div>
                </div>
            ) : activeAssessments.length === 0 && completedAssessments.length === 0 && !selectedAttemptId ? (
                <div className="flex flex-col items-center justify-center h-full">
                    <div className="p-8 rounded-2xl text-center" style={{ backgroundColor: COLORS.cardBg, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
                        <div className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-5" style={{ backgroundColor: COLORS.accentLight }}>
                            <Users className="w-10 h-10" style={{ color: COLORS.accent }} />
                        </div>
                        <h2 className="text-2xl font-bold mb-2" style={{ color: COLORS.textPrimary }}>No Active Assessments</h2>
                        <p className="text-sm mb-6" style={{ color: COLORS.textSecondary, maxWidth: '300px' }}>
                            No candidates are currently taking an assessment. Upload a resume to invite a new candidate.
                        </p>
                        <button
                            onClick={() => navigate('/upload-resume')}
                            className="px-6 py-3 text-sm font-medium rounded-xl text-white transition-all hover:opacity-90 flex items-center gap-2 mx-auto"
                            style={{ backgroundColor: COLORS.accent }}
                        >
                            <FileText className="w-4 h-4" /> Upload Resume
                        </button>
                    </div>
                </div>
            ) : (
                <div style={{ display: 'flex', gap: '16px', padding: '16px', height: 'calc(100vh - 56px)', overflow: 'hidden' }}>

                    {/* SIDEBAR — Candidate List + Recruiter Decision (20%) */}
                    <div className="minimal-scrollbar" style={{ width: '20%', minWidth: '240px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '4px' }}>
                        {/* Combined Candidate Card + Recruiter Decision */}
                        <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 45%, ${COLORS.purpleLight} 100%)`, borderColor: COLORS.accent, boxShadow: '0 12px 26px rgba(59, 130, 246, 0.12)' }}>
                            {/* Candidate Info - Clickable for Switching if multiple active */}
                            <div className="flex items-center gap-3 mb-4 relative">
                                <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-lg font-bold shrink-0" style={{ background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`, color: 'white', boxShadow: '0 8px 18px rgba(124, 58, 237, 0.25)' }}>
                                    {displayData.candidate.avatar}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-semibold text-lg truncate" style={{ color: COLORS.textPrimary }}>
                                            {displayData.candidate.name}
                                        </h3>
                                        {metricsLoading && (
                                            <RefreshCcw className="w-4 h-4 animate-spin ml-1" style={{ color: COLORS.accent }} />
                                        )}
                                        {activeAssessments.length > 1 && (
                                            <button
                                                onClick={() => setShowCandidateDropdown(!showCandidateDropdown)}
                                                className="p-1 rounded-full hover:bg-black/5 transition-colors"
                                                title="Switch Candidate"
                                            >
                                                {showCandidateDropdown ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                            </button>
                                        )}
                                    </div>
                                    <p className="text-sm truncate" style={{ color: COLORS.textSecondary }}>
                                        {displayData.candidate.position}
                                    </p>
                                </div>

                                {/* Active Candidates Dropdown */}
                                {showCandidateDropdown && activeAssessments.length > 0 && (
                                    <div className="absolute top-16 left-0 w-full z-50 rounded-xl border shadow-xl animate-in fade-in slide-in-from-top-2" style={{
                                        backgroundColor: COLORS.cardBg,
                                        borderColor: COLORS.border,
                                        maxHeight: '300px',
                                        overflowY: 'auto'
                                    }}>
                                        <div className="p-2 space-y-1">
                                            <div className="text-[10px] font-bold uppercase tracking-wider px-2 py-1" style={{ color: COLORS.textMuted }}>
                                                Active Candidates ({activeAssessments.length})
                                            </div>
                                            {activeAssessments.map(candidate => (
                                                <button
                                                    key={candidate.id}
                                                    onClick={() => {
                                                        setSelectedAttemptId(candidate.id);
                                                        setShowCandidateDropdown(false);
                                                    }}
                                                    className="w-full text-left p-2 rounded-lg flex items-center gap-3 hover:bg-black/5 transition-colors"
                                                    style={{
                                                        background: selectedAttemptId === candidate.id ? COLORS.accentLight : 'transparent',
                                                        border: selectedAttemptId === candidate.id ? `1px solid ${COLORS.accent}` : '1px solid transparent'
                                                    }}
                                                >
                                                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0" style={{
                                                        background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.teal})`,
                                                        color: 'white',
                                                    }}>
                                                        {(candidate.candidate?.name || 'C').charAt(0).toUpperCase()}
                                                    </div>
                                                    <div className="min-w-0 flex-1">
                                                        <div className="text-sm font-medium truncate" style={{ color: COLORS.textPrimary }}>
                                                            {candidate.candidate?.name || 'Candidate'}
                                                        </div>
                                                        <div className="text-[10px]" style={{ color: COLORS.textSecondary }}>
                                                            Q{candidate.progress?.current || 1}/{candidate.progress?.total || 3} • {candidate.time_elapsed || '0m'}
                                                        </div>
                                                    </div>
                                                    {selectedAttemptId === candidate.id && (
                                                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                                    )}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Overall Fit Score Badge */}
                            {hasStarted && (
                                <div className="mb-4 p-3 rounded-xl border" style={{
                                    background: displayData.overall_fit.grade_color === 'gold' ? `linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)` :
                                        displayData.overall_fit.grade_color === 'green' ? `linear-gradient(135deg, ${COLORS.successLight} 0%, ${COLORS.cardBg} 100%)` :
                                            displayData.overall_fit.grade_color === 'blue' ? `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)` :
                                                displayData.overall_fit.grade_color === 'yellow' ? `linear-gradient(135deg, ${COLORS.warningLight} 0%, ${COLORS.cardBg} 100%)` :
                                                    displayData.overall_fit.grade_color === 'red' ? `linear-gradient(135deg, ${COLORS.dangerLight} 0%, ${COLORS.cardBg} 100%)` :
                                                        `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`,
                                    borderColor: displayData.overall_fit.grade_color === 'gold' ? '#F59E0B' :
                                        displayData.overall_fit.grade_color === 'green' ? COLORS.success :
                                            displayData.overall_fit.grade_color === 'blue' ? COLORS.accent :
                                                displayData.overall_fit.grade_color === 'yellow' ? COLORS.warning :
                                                    displayData.overall_fit.grade_color === 'red' ? COLORS.danger :
                                                        COLORS.border
                                }}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            {/* Grade Badge */}
                                            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-black" style={{
                                                background: displayData.overall_fit.grade_color === 'gold' ? 'linear-gradient(135deg, #F59E0B, #D97706)' :
                                                    displayData.overall_fit.grade_color === 'green' ? `linear-gradient(135deg, ${COLORS.success}, #047857)` :
                                                        displayData.overall_fit.grade_color === 'blue' ? `linear-gradient(135deg, ${COLORS.accent}, #1D4ED8)` :
                                                            displayData.overall_fit.grade_color === 'yellow' ? `linear-gradient(135deg, ${COLORS.warning}, #B45309)` :
                                                                displayData.overall_fit.grade_color === 'red' ? `linear-gradient(135deg, ${COLORS.danger}, #991B1B)` :
                                                                    `linear-gradient(135deg, ${COLORS.textMuted}, ${COLORS.textSecondary})`,
                                                color: 'white',
                                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                            }}>
                                                {displayData.overall_fit.grade}
                                            </div>
                                            <div>
                                                <div className="text-xs uppercase font-semibold tracking-wider" style={{ color: COLORS.textMuted }}>
                                                    Fit Score
                                                </div>
                                                <div className="text-2xl font-bold" style={{
                                                    color: displayData.overall_fit.grade_color === 'gold' ? '#B45309' :
                                                        displayData.overall_fit.grade_color === 'green' ? COLORS.success :
                                                            displayData.overall_fit.grade_color === 'blue' ? COLORS.accent :
                                                                displayData.overall_fit.grade_color === 'yellow' ? COLORS.warning :
                                                                    displayData.overall_fit.grade_color === 'red' ? COLORS.danger :
                                                                        COLORS.textSecondary
                                                }}>
                                                    {displayData.overall_fit.score}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm font-semibold" style={{
                                                color: displayData.overall_fit.grade_color === 'gold' ? '#B45309' :
                                                    displayData.overall_fit.grade_color === 'green' ? COLORS.success :
                                                        displayData.overall_fit.grade_color === 'blue' ? COLORS.accent :
                                                            displayData.overall_fit.grade_color === 'yellow' ? COLORS.warning :
                                                                displayData.overall_fit.grade_color === 'red' ? COLORS.danger :
                                                                    COLORS.textSecondary
                                            }}>
                                                {displayData.overall_fit.grade_label}
                                            </div>
                                            <div className="text-[10px]" style={{ color: COLORS.textMuted }}>
                                                {displayData.overall_fit.breakdown?.task_score?.details?.correct_answers || 0}/
                                                {displayData.overall_fit.breakdown?.task_score?.details?.total_tasks || 0} correct
                                            </div>
                                            {displayData.metrics.cheating_resilience != null && (
                                                <div className="text-[10px] mt-0.5" style={{ color: COLORS.textMuted }}>
                                                    🛡 {displayData.metrics.cheating_resilience}% behavioral alignment
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Progress with visual indicator */}
                            <div className="mb-4 p-3 rounded-xl border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.border }}>
                                <div className="flex justify-between text-sm mb-2">
                                    <span style={{ color: COLORS.textSecondary }}>Assessment Progress</span>
                                    <span className="font-semibold" style={{ color: COLORS.accent }}>{displayData.progress.current} of {displayData.progress.total}</span>
                                </div>
                                <div className="w-full h-2.5 rounded-full" style={{ backgroundColor: COLORS.cardBg }}>
                                    <div className="h-2.5 rounded-full transition-all duration-700" style={{ background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.teal})`, width: `${(displayData.progress.current / displayData.progress.total) * 100}%` }} />
                                </div>
                            </div>

                            {/* Divider */}
                            <div className="border-t my-4" style={{ borderColor: COLORS.border }}></div>

                            {/* Anti-Cheat Flags (Phase 10) - Collapsible */}
                            {(displayData.metrics.focus_loss_count > 0 || displayData.metrics.paste_detected || displayData.metrics.copy_detected || displayData.metrics.long_idle_count > 0) && (
                                <div className="mb-4 rounded-xl border overflow-hidden transition-all duration-300" style={{
                                    background: `linear-gradient(135deg, ${COLORS.dangerLight} 0%, ${COLORS.cardBg} 100%)`,
                                    borderColor: COLORS.danger
                                }}>
                                    <button
                                        onClick={() => setShowAntiCheat(!showAntiCheat)}
                                        className="w-full flex items-center justify-between p-3 hover:bg-black/5 transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <AlertCircle className="w-4 h-4" style={{ color: COLORS.danger }} />
                                            <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.danger }}>
                                                Behavioral Anomalies
                                            </h4>
                                            {/* Summary Badge when collapsed */}
                                            {!showAntiCheat && (
                                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-600 border border-red-200">
                                                    {(displayData.metrics.focus_loss_count > 0 ? 1 : 0) +
                                                        (displayData.metrics.paste_detected ? 1 : 0) +
                                                        (displayData.metrics.copy_detected ? 1 : 0) +
                                                        (displayData.metrics.long_idle_count > 0 ? 1 : 0)} Detected
                                                </span>
                                            )}
                                        </div>
                                        {showAntiCheat ? <ChevronUp className="w-4 h-4 text-red-400" /> : <ChevronDown className="w-4 h-4 text-red-400" />}
                                    </button>

                                    {showAntiCheat && (
                                        <div className="px-3 pb-3 space-y-1.5 animate-fade-in">
                                            {displayData.metrics.focus_loss_count > 0 && (
                                                <div className="flex items-center justify-between text-xs p-2 rounded-lg" style={{ backgroundColor: COLORS.cardBg }}>
                                                    <span style={{ color: COLORS.textSecondary }}>Tab Switches</span>
                                                    <span className="font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.dangerLight, color: COLORS.danger }}>
                                                        {displayData.metrics.focus_loss_count}x
                                                    </span>
                                                </div>
                                            )}
                                            {displayData.metrics.paste_detected && (
                                                <div className="flex items-center justify-between text-xs p-2 rounded-lg" style={{ backgroundColor: COLORS.cardBg }}>
                                                    <span style={{ color: COLORS.textSecondary }}>Paste Detected</span>
                                                    <span className="font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.dangerLight, color: COLORS.danger }}>
                                                        {displayData.metrics.paste_count || 1}x
                                                    </span>
                                                </div>
                                            )}
                                            {displayData.metrics.copy_detected && (
                                                <div className="flex items-center justify-between text-xs p-2 rounded-lg" style={{ backgroundColor: COLORS.cardBg }}>
                                                    <span style={{ color: COLORS.textSecondary }}>Question Copied</span>
                                                    <span className="font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.dangerLight, color: COLORS.danger }}>
                                                        {displayData.metrics.copy_count || 1}x
                                                    </span>
                                                </div>
                                            )}
                                            {displayData.metrics.long_idle_count > 0 && (
                                                <div className="flex items-center justify-between text-xs p-2 rounded-lg" style={{ backgroundColor: COLORS.cardBg }}>
                                                    <span style={{ color: COLORS.textSecondary }}>Long Pauses (30s+)</span>
                                                    <span className="font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.warningLight, color: COLORS.warning }}>
                                                        {displayData.metrics.long_idle_count}x
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                        </div>

                        {/* All / Leaderboard Toggle Section */}
                        <div className="p-4 rounded-2xl border flex-1 overflow-hidden flex flex-col" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${sidebarTab === 'leaderboard' ? COLORS.warningLight : COLORS.accentLight} 100%)`, borderColor: sidebarTab === 'leaderboard' ? COLORS.warning : COLORS.accent, boxShadow: sidebarTab === 'leaderboard' ? '0 10px 24px rgba(251, 191, 36, 0.1)' : '0 10px 24px rgba(59, 130, 246, 0.1)' }}>
                            {/* Segmented Toggle */}
                            <div className="flex items-center gap-1 p-1 rounded-xl mb-3" style={{ backgroundColor: COLORS.cardBgAlt, border: `1px solid ${COLORS.border}` }}>
                                <button
                                    onClick={() => setSidebarTab('all')}
                                    className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200"
                                    style={{
                                        backgroundColor: sidebarTab === 'all' ? COLORS.cardBg : 'transparent',
                                        color: sidebarTab === 'all' ? COLORS.accent : COLORS.textMuted,
                                        boxShadow: sidebarTab === 'all' ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
                                        border: sidebarTab === 'all' ? `1px solid ${COLORS.accent}` : '1px solid transparent'
                                    }}
                                >
                                    <Users className="w-3.5 h-3.5" />
                                    All ({activeAssessments.length + completedAssessments.length})
                                </button>
                                <button
                                    onClick={() => setSidebarTab('leaderboard')}
                                    className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all duration-200"
                                    style={{
                                        backgroundColor: sidebarTab === 'leaderboard' ? COLORS.cardBg : 'transparent',
                                        color: sidebarTab === 'leaderboard' ? COLORS.warning : COLORS.textMuted,
                                        boxShadow: sidebarTab === 'leaderboard' ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
                                        border: sidebarTab === 'leaderboard' ? `1px solid ${COLORS.warning}` : '1px solid transparent'
                                    }}
                                >
                                    <Trophy className="w-3.5 h-3.5" />
                                    Leaderboard ({completedAssessments.length})
                                </button>
                            </div>

                            {/* Candidate List */}
                            <div className="space-y-1.5 overflow-y-auto flex-1 pr-1">
                                {sidebarTab === 'all' ? (
                                    /* === ALL TAB: Active + Completed candidates === */
                                    (activeAssessments.length + completedAssessments.length) > 0 ? (
                                        <>
                                            {/* Active candidates first */}
                                            {activeAssessments.map(candidate => (
                                                <div
                                                    key={candidate.id}
                                                    onClick={() => setSelectedAttemptId(candidate.id)}
                                                    onKeyDown={(e) => e.key === 'Enter' && setSelectedAttemptId(candidate.id)}
                                                    role="button"
                                                    tabIndex={0}
                                                    className={`w-full text-left p-2.5 rounded-lg text-sm transition-all flex items-center gap-3 cursor-pointer ${selectedAttemptId === candidate.id ? 'shadow-md ring-2 ring-blue-200' : 'hover:scale-[1.02]'}`}
                                                    style={{
                                                        background: selectedAttemptId === candidate.id ? `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)` : COLORS.cardBg,
                                                        border: `1.5px solid ${selectedAttemptId === candidate.id ? COLORS.accent : COLORS.border}`,
                                                    }}
                                                >
                                                    {/* Avatar with live pulse */}
                                                    <div className="relative">
                                                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0" style={{
                                                            background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.teal})`,
                                                            color: 'white',
                                                        }}>
                                                            {(candidate.candidate?.name || 'C').charAt(0).toUpperCase()}
                                                        </div>
                                                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 flex items-center justify-center" style={{ borderColor: COLORS.cardBg, backgroundColor: COLORS.success }}>
                                                            <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
                                                        </div>
                                                    </div>

                                                    {/* Candidate Info */}
                                                    <div className="min-w-0 flex-1">
                                                        <div className="font-medium truncate" style={{ color: COLORS.textPrimary }}>
                                                            {candidate.candidate?.name || 'Candidate'}
                                                        </div>
                                                        <div className="text-[10px]" style={{ color: COLORS.textSecondary }}>
                                                            Q{candidate.progress?.current || 1}/{candidate.progress?.total || 3} • {candidate.time_elapsed || '0m'}
                                                        </div>
                                                    </div>


                                                    {/* Active Badge + Decision Status + Delete */}
                                                    <div className="flex flex-col items-end gap-1 shrink-0">
                                                        <div className="flex items-center gap-1">
                                                            <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.successLight, color: COLORS.success, border: `1px solid ${COLORS.success}` }}>
                                                                LIVE
                                                            </span>
                                                            {confirmDeleteId === candidate.id ? (
                                                                <div className="flex items-center gap-1">
                                                                    <button onClick={(e) => { e.stopPropagation(); deleteAssessment(candidate.id); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.dangerBg, color: COLORS.danger }} disabled={deletingId === candidate.id}>
                                                                        {deletingId === candidate.id ? '...' : 'Yes'}
                                                                    </button>
                                                                    <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.textMuted }}>
                                                                        No
                                                                    </button>
                                                                </div>
                                                            ) : (
                                                                <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(candidate.id); }} className="p-1 rounded-md transition-colors hover:bg-red-50" title="Delete assessment">
                                                                    <Trash2 className="w-3.5 h-3.5" style={{ color: COLORS.textMuted }} />
                                                                </button>
                                                            )}
                                                        </div>
                                                        {/* Decision Status Tag */}
                                                        {getDecisionInfo(candidate.id) && (
                                                            <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full uppercase" style={{
                                                                backgroundColor: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.successBg :
                                                                    getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.dangerBg :
                                                                        COLORS.warningBg,
                                                                color: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                    getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                        COLORS.warning,
                                                                border: `1px solid ${getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                    getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                        COLORS.warning}`
                                                            }}>
                                                                {getDecisionInfo(candidate.id).decision}
                                                            </span>
                                                        )}
                                                    </div>

                                                </div>
                                            ))}

                                            {/* Divider between active and completed */}
                                            {activeAssessments.length > 0 && completedAssessments.length > 0 && (
                                                <div className="flex items-center gap-2 py-1">
                                                    <div className="flex-1 h-px" style={{ backgroundColor: COLORS.border }}></div>
                                                    <span className="text-[9px] font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Completed</span>
                                                    <div className="flex-1 h-px" style={{ backgroundColor: COLORS.border }}></div>
                                                </div>
                                            )}

                                            {/* Completed candidates */}
                                            {completedAssessments.map(candidate => {
                                                const score = candidate.overall_fit?.score ?? (candidate.overall_score || 0);
                                                return (
                                                    <div
                                                        key={candidate.id}
                                                        onClick={() => setSelectedAttemptId(candidate.id)}
                                                        onKeyDown={(e) => e.key === 'Enter' && setSelectedAttemptId(candidate.id)}
                                                        role="button"
                                                        tabIndex={0}
                                                        className={`w-full text-left p-2.5 rounded-lg text-sm transition-all flex items-center gap-3 cursor-pointer ${selectedAttemptId === candidate.id ? 'shadow-md ring-2 ring-blue-200' : 'hover:scale-[1.02]'}`}
                                                        style={{
                                                            background: selectedAttemptId === candidate.id ? `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)` : COLORS.cardBg,
                                                            border: `1.5px solid ${selectedAttemptId === candidate.id ? COLORS.accent : COLORS.border}`,
                                                        }}
                                                    >
                                                        {/* Avatar */}
                                                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0" style={{
                                                            background: `linear-gradient(135deg, ${COLORS.cardBgAlt} 0%, ${COLORS.cardBg} 100%)`,
                                                            color: COLORS.textSecondary,
                                                            border: `2px solid ${COLORS.border}`,
                                                        }}>
                                                            {(candidate.candidate?.name || 'C').charAt(0).toUpperCase()}
                                                        </div>

                                                        {/* Candidate Info */}
                                                        <div className="min-w-0 flex-1">
                                                            <div className="font-medium truncate" style={{ color: COLORS.textPrimary }}>
                                                                {candidate.candidate?.name || 'Candidate'}
                                                            </div>
                                                            <div className="text-[10px] truncate" style={{ color: COLORS.textMuted }}>
                                                                {candidate.candidate?.position || 'Position'}
                                                            </div>
                                                        </div>


                                                        {/* Score + Decision Status + Delete */}
                                                        <div className="flex flex-col items-end gap-1 shrink-0">
                                                            <div className="flex items-center gap-1">
                                                                <span className="text-sm font-bold" style={{
                                                                    color: score >= 85 ? COLORS.success : score >= 70 ? COLORS.warning : COLORS.danger
                                                                }}>
                                                                    {score}
                                                                </span>
                                                                {confirmDeleteId === candidate.id ? (
                                                                    <div className="flex items-center gap-1">
                                                                        <button onClick={(e) => { e.stopPropagation(); deleteAssessment(candidate.id); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.dangerBg, color: COLORS.danger }} disabled={deletingId === candidate.id}>
                                                                            {deletingId === candidate.id ? '...' : 'Yes'}
                                                                        </button>
                                                                        <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.textMuted }}>
                                                                            No
                                                                        </button>
                                                                    </div>
                                                                ) : (
                                                                    <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(candidate.id); }} className="p-1 rounded-md transition-colors hover:bg-red-50" title="Delete assessment">
                                                                        <Trash2 className="w-3.5 h-3.5" style={{ color: COLORS.textMuted }} />
                                                                    </button>
                                                                )}
                                                            </div>
                                                            {/* Decision Status Tag */}
                                                            {getDecisionInfo(candidate.id) && (
                                                                <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full uppercase" style={{
                                                                    backgroundColor: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.successBg :
                                                                        getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.dangerBg :
                                                                            COLORS.warningBg,
                                                                    color: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                        getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                            COLORS.warning,
                                                                    border: `1px solid ${getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                        getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                            COLORS.warning}`
                                                                }}>
                                                                    {getDecisionInfo(candidate.id).decision}
                                                                </span>
                                                            )}
                                                        </div>

                                                    </div>
                                                );
                                            })}
                                        </>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-8 gap-3">
                                            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: COLORS.cardBgAlt }}>
                                                <Users className="w-6 h-6" style={{ color: COLORS.textMuted }} />
                                            </div>
                                            <p className="text-sm" style={{ color: COLORS.textMuted }}>No candidates yet</p>
                                        </div>
                                    )
                                ) : (
                                    /* === LEADERBOARD TAB: Completed sorted by score === */
                                    completedAssessments.length > 0 ? (
                                        [...completedAssessments]
                                            .sort((a, b) => (b.overall_fit?.score || b.overall_score || 0) - (a.overall_fit?.score || a.overall_score || 0))
                                            .map((candidate, index) => {
                                                const rank = index + 1;
                                                const score = candidate.overall_fit?.score ?? (candidate.overall_score || 0);
                                                const isTop3 = rank <= 3;
                                                const rankColors = {
                                                    1: { bg: 'linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)', border: '#F59E0B', text: '#B45309', icon: Crown },
                                                    2: { bg: 'linear-gradient(135deg, #E5E7EB 0%, #D1D5DB 100%)', border: '#9CA3AF', text: '#4B5563', icon: Medal },
                                                    3: { bg: 'linear-gradient(135deg, #FED7AA 0%, #FDBA74 100%)', border: '#F97316', text: '#C2410C', icon: Medal },
                                                };
                                                const rankStyle = rankColors[rank] || { bg: COLORS.cardBg, border: COLORS.border, text: COLORS.textSecondary };
                                                const RankIcon = rankStyle.icon || null;

                                                return (
                                                    <div
                                                        key={candidate.id}
                                                        onClick={() => setSelectedAttemptId(candidate.id)}
                                                        onKeyDown={(e) => e.key === 'Enter' && setSelectedAttemptId(candidate.id)}
                                                        role="button"
                                                        tabIndex={0}
                                                        className={`w-full text-left p-2.5 rounded-lg text-sm transition-all flex items-center gap-3 cursor-pointer ${selectedAttemptId === candidate.id ? 'shadow-md ring-2 ring-amber-200' : 'hover:scale-[1.02]'}`}
                                                        style={{
                                                            background: isTop3 ? rankStyle.bg : (selectedAttemptId === candidate.id ? `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)` : COLORS.cardBg),
                                                            border: `1.5px solid ${isTop3 ? rankStyle.border : COLORS.border}`,
                                                        }}
                                                    >
                                                        {/* Rank Badge */}
                                                        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0" style={{
                                                            background: isTop3 ? rankStyle.bg : `linear-gradient(135deg, ${COLORS.cardBgAlt} 0%, ${COLORS.cardBg} 100%)`,
                                                            color: isTop3 ? rankStyle.text : COLORS.textSecondary,
                                                            border: `2px solid ${isTop3 ? rankStyle.border : COLORS.border}`,
                                                        }}>
                                                            {isTop3 && RankIcon ? <RankIcon className="w-4 h-4" /> : `#${rank}`}
                                                        </div>

                                                        {/* Candidate Info */}
                                                        <div className="min-w-0 flex-1">
                                                            <div className="font-medium truncate" style={{ color: isTop3 ? rankStyle.text : COLORS.textPrimary }}>
                                                                {candidate.candidate?.name || 'Candidate'}
                                                            </div>
                                                            <div className="text-xs truncate" style={{ color: COLORS.textMuted }}>
                                                                {candidate.candidate?.position || 'Position'}
                                                            </div>
                                                        </div>


                                                        {/* Score Badge + Decision Status + Delete */}
                                                        <div className="shrink-0 flex items-center gap-1">
                                                            <div className="flex flex-col items-end gap-1">
                                                                <div className="flex flex-col items-end">
                                                                    <span className="text-lg font-bold" style={{
                                                                        color: score >= 85 ? COLORS.success : score >= 70 ? COLORS.warning : COLORS.danger
                                                                    }}>
                                                                        {score}
                                                                    </span>
                                                                    <span className="text-[10px]" style={{ color: COLORS.textMuted }}>points</span>
                                                                </div>
                                                                {/* Decision Status Tag */}
                                                                {getDecisionInfo(candidate.id) && (
                                                                    <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full uppercase" style={{
                                                                        backgroundColor: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.successBg :
                                                                            getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.dangerBg :
                                                                                COLORS.warningBg,
                                                                        color: getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                            getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                                COLORS.warning,
                                                                        border: `1px solid ${getDecisionInfo(candidate.id).decision === 'shortlist' ? COLORS.success :
                                                                            getDecisionInfo(candidate.id).decision === 'reject' ? COLORS.danger :
                                                                                COLORS.warning}`
                                                                    }}>
                                                                        {getDecisionInfo(candidate.id).decision}
                                                                    </span>
                                                                )}
                                                            </div>
                                                            {confirmDeleteId === candidate.id ? (
                                                                <div className="flex flex-col gap-0.5">
                                                                    <button onClick={(e) => { e.stopPropagation(); deleteAssessment(candidate.id); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.dangerBg, color: COLORS.danger }} disabled={deletingId === candidate.id}>
                                                                        {deletingId === candidate.id ? '...' : 'Yes'}
                                                                    </button>
                                                                    <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null); }} className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.textMuted }}>
                                                                        No
                                                                    </button>
                                                                </div>
                                                            ) : (
                                                                <button onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(candidate.id); }} className="p-1 rounded-md transition-colors hover:bg-red-50" title="Delete assessment">
                                                                    <Trash2 className="w-3.5 h-3.5" style={{ color: COLORS.textMuted }} />
                                                                </button>
                                                            )}
                                                        </div>

                                                    </div>
                                                );
                                            })
                                    ) : activeAssessments.length > 0 ? (
                                        <div className="flex flex-col items-center justify-center py-8 gap-3">
                                            <div className="w-12 h-12 rounded-full border-2 border-dashed flex items-center justify-center" style={{ borderColor: COLORS.warning }}>
                                                <Trophy className="w-6 h-6" style={{ color: COLORS.warning, opacity: 0.6 }} />
                                            </div>
                                            <div className="text-center">
                                                <p className="text-sm font-medium" style={{ color: COLORS.textSecondary }}>Leaderboard building...</p>
                                                <p className="text-xs mt-1" style={{ color: COLORS.textMuted }}>Rankings appear after assessments complete</p>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-8 gap-3">
                                            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: COLORS.cardBgAlt }}>
                                                <Trophy className="w-6 h-6" style={{ color: COLORS.textMuted }} />
                                            </div>
                                            <p className="text-sm" style={{ color: COLORS.textMuted }}>No candidates ranked yet</p>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>
                    </div>

                    {/* MAIN CONTENT PANEL (80%) - Horizontal 3-column: Sidebar | Tabs | Kiwi */}
                    <div style={{
                        width: '80%',
                        display: 'flex',
                        flexDirection: 'row',
                        gap: '16px',
                        overflow: 'hidden',
                        opacity: metricsLoading ? 0.6 : 1,
                        transition: 'opacity 0.2s ease-in-out',
                        pointerEvents: metricsLoading ? 'none' : 'auto'
                    }}>

                        {!hasSelectedCandidate ? (
                            /* Empty state when no candidate is selected */
                            <div className="flex-1 flex items-center justify-center" style={{ width: '100%' }}>
                                <div className="p-10 rounded-2xl text-center border" style={{ backgroundColor: COLORS.cardBg, borderColor: COLORS.border, boxShadow: '0 4px 24px rgba(0,0,0,0.06)', maxWidth: '400px' }}>
                                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5" style={{ background: `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.purpleLight} 100%)`, border: `2px dashed ${COLORS.accent}` }}>
                                        <Activity className="w-8 h-8" style={{ color: COLORS.accent }} />
                                    </div>
                                    <h3 className="text-lg font-bold mb-2" style={{ color: COLORS.textPrimary }}>No Active Session</h3>
                                    <p className="text-sm mb-5" style={{ color: COLORS.textSecondary, lineHeight: '1.6' }}>
                                        Select a candidate from the left panel to view their assessment data, or wait for a new session to begin.
                                    </p>
                                    <div className="flex items-center justify-center gap-3">
                                        <button
                                            onClick={() => navigate('/upload-resume')}
                                            className="px-4 py-2 text-sm font-medium rounded-xl text-white transition-all hover:opacity-90 flex items-center gap-2"
                                            style={{ backgroundColor: COLORS.accent }}
                                        >
                                            <FileText className="w-4 h-4" /> Upload Resume
                                        </button>
                                        <button
                                            onClick={() => { fetchActiveAssessments(false); fetchCompletedAssessments(); }}
                                            className="px-4 py-2 text-sm font-medium rounded-xl transition-all hover:opacity-90 flex items-center gap-2"
                                            style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.textSecondary, border: `1px solid ${COLORS.border}` }}
                                        >
                                            <RefreshCcw className="w-4 h-4" /> Refresh
                                        </button>
                                    </div>
                                    {(activeAssessments.length > 0 || completedAssessments.length > 0) && (
                                        <p className="text-xs mt-4" style={{ color: COLORS.textMuted }}>
                                            {activeAssessments.length > 0 ? `${activeAssessments.length} active` : ''}
                                            {activeAssessments.length > 0 && completedAssessments.length > 0 ? ' · ' : ''}
                                            {completedAssessments.length > 0 ? `${completedAssessments.length} completed` : ''}
                                            {' — click a candidate to view details'}
                                        </p>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <>
                                {/* ═══ MIDDLE COLUMN: Tabs (Overview, Live Feed, Full Profile) + content ═══ */}
                                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>

                                    {/* HERO SECTION: Identity + Quick Actions + ML Score */}
                                    <div className="mb-4 p-4 rounded-2xl border shadow-sm flex flex-wrap items-center justify-between gap-4" style={{ backgroundColor: COLORS.cardBg, borderColor: COLORS.border }}>
                                        <div className="flex items-center gap-4">
                                            {/* Avatar */}
                                            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-xl font-bold transition-transform hover:scale-105" style={{
                                                background: `linear-gradient(135deg, ${COLORS.accent}, ${COLORS.purple})`,
                                                color: 'white',
                                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                            }}>
                                                {displayData.candidate.avatar}
                                            </div>
                                            <div>
                                                <h2 className="text-xl font-bold leading-tight" style={{ color: COLORS.textPrimary }}>
                                                    {displayData.candidate.name}
                                                </h2>
                                                <div className="flex items-center gap-2 text-sm mt-1" style={{ color: COLORS.textSecondary }}>
                                                    <FileText className="w-3.5 h-3.5" />
                                                    {displayData.candidate.position}
                                                </div>
                                            </div>

                                            {/* Score Badge */}
                                            {hasStarted && (
                                                <div className="ml-2 pl-4 border-l flex flex-col items-start" style={{ borderColor: COLORS.border }}>
                                                    <div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Current Fit</div>
                                                    <div className="flex items-baseline gap-1">
                                                        <span className="text-2xl font-black" style={{
                                                            color: displayData.overall_fit.grade_color === 'gold' ? '#B45309' :
                                                                displayData.overall_fit.grade_color === 'green' ? COLORS.success :
                                                                    displayData.overall_fit.grade_color === 'blue' ? COLORS.accent :
                                                                        displayData.overall_fit.grade_color === 'red' ? COLORS.danger : COLORS.textPrimary
                                                        }}>{displayData.overall_fit.grade}</span>
                                                        <span className="text-sm font-semibold" style={{ color: COLORS.textSecondary }}>{displayData.overall_fit.score}%</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Right Side: Decisions & ML */}
                                        <div className="flex items-center gap-4">
                                            {/* ML Prediction Mini-Display */}
                                            {interviewSuccess && (
                                                <div className="hidden xl:flex flex-col items-end mr-2 text-right">
                                                    <div className="text-[10px] font-bold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>AI Prediction</div>
                                                    <div className="flex items-center gap-1.5">
                                                        <div className={`w-2 h-2 rounded-full ${interviewSuccess.probability > 70 ? 'animate-pulse' : ''}`}
                                                            style={{ backgroundColor: interviewSuccess.probability > 70 ? COLORS.success : interviewSuccess.probability > 50 ? COLORS.warning : COLORS.danger }}></div>
                                                        <span className="text-lg font-bold" style={{ color: COLORS.textPrimary }}>
                                                            {interviewSuccess.probability}%
                                                        </span>
                                                        <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>Success</span>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Action Buttons */}
                                            <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-xl border" style={{ backgroundColor: COLORS.cardBgAlt, borderColor: COLORS.border }}>
                                                <button
                                                    onClick={() => handleRecruiterDecision('shortlist')}
                                                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${getDecisionInfo(selectedAttemptId)?.decision === 'shortlist' ? 'shadow-md scale-105' : 'hover:bg-white hover:shadow-sm'}`}
                                                    style={{
                                                        backgroundColor: getDecisionInfo(selectedAttemptId)?.decision === 'shortlist' ? COLORS.success : 'transparent',
                                                        color: getDecisionInfo(selectedAttemptId)?.decision === 'shortlist' ? 'white' : COLORS.success,
                                                    }}
                                                    title="Shortlist Candidate"
                                                >
                                                    <ThumbsUp className="w-4 h-4" />
                                                    <span className="hidden sm:inline">Shortlist</span>
                                                </button>
                                                <button
                                                    onClick={() => handleRecruiterDecision('reject')}
                                                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${getDecisionInfo(selectedAttemptId)?.decision === 'reject' ? 'shadow-md scale-105' : 'hover:bg-white hover:shadow-sm'}`}
                                                    style={{
                                                        backgroundColor: getDecisionInfo(selectedAttemptId)?.decision === 'reject' ? COLORS.danger : 'transparent',
                                                        color: getDecisionInfo(selectedAttemptId)?.decision === 'reject' ? 'white' : COLORS.danger,
                                                    }}
                                                    title="Reject Candidate"
                                                >
                                                    <ThumbsDown className="w-4 h-4" />
                                                    <span className="hidden sm:inline">Reject</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-1 mb-2 p-1 rounded-xl shrink-0" style={{ backgroundColor: COLORS.cardBgAlt, border: `1px solid ${COLORS.border}` }}>
                                        {[
                                            { id: 'overview', label: 'Overview', icon: Target },
                                            { id: 'livefeed', label: 'Live Feed', icon: Activity },
                                            { id: 'profile', label: 'Full Profile', icon: Brain },
                                        ].map(tab => (
                                            <button
                                                key={tab.id}
                                                onClick={() => setActiveTab(tab.id)}
                                                className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-semibold transition-all duration-200"
                                                style={{
                                                    backgroundColor: activeTab === tab.id ? COLORS.cardBg : 'transparent',
                                                    color: activeTab === tab.id ? COLORS.accent : COLORS.textMuted,
                                                    boxShadow: activeTab === tab.id ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
                                                    border: activeTab === tab.id ? `1px solid ${COLORS.accent}` : '1px solid transparent'
                                                }}
                                            >
                                                <tab.icon className="w-3.5 h-3.5" />
                                                {tab.label}
                                            </button>
                                        ))}
                                    </div>

                                    {/* ═══ TAB CONTENT (scrollable) ═══ */}
                                    <div className="minimal-scrollbar" style={{ flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: '4px' }}>

                                        {/* === OVERVIEW TAB === */}
                                        {activeTab === 'overview' && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                                {/* ─── Resume ATS (always first: from resume only, not behavior) ─── */}
                                                <div
                                                    className="p-5 rounded-2xl border"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${COLORS.tealLight || COLORS.cardBgAlt} 0%, ${COLORS.cardBg} 50%, ${COLORS.cardBgAlt} 100%)`,
                                                        borderColor: (COLORS.teal || COLORS.accent) + '40',
                                                        borderLeftWidth: '4px',
                                                        borderLeftColor: COLORS.teal || COLORS.accent,
                                                    }}
                                                >
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <FileText className="w-4 h-4 shrink-0" style={{ color: COLORS.teal || COLORS.accent }} />
                                                        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Resume ATS</span>
                                                        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: (COLORS.teal || COLORS.accent) + '20', color: COLORS.teal || COLORS.accent }}>From resume only</span>
                                                    </div>
                                                    <div className="flex flex-wrap items-center gap-6">
                                                        <div className="flex items-center gap-4">
                                                            <div style={{ position: 'relative', width: '56px', height: '56px' }}>
                                                                <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                                                                    <circle cx="50" cy="50" r="42" fill="none" stroke={COLORS.border} strokeWidth="8" opacity="0.3" />
                                                                    <circle cx="50" cy="50" r="42" fill="none" stroke={COLORS.teal || COLORS.accent} strokeWidth="8" strokeLinecap="round"
                                                                        strokeDasharray={atsScore != null ? `${(Math.min(100, atsScore.ats_score || 0) / 100) * 264} 264` : '0 264'}
                                                                    />
                                                                </svg>
                                                                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                                                    <span className="text-lg font-black" style={{ color: COLORS.teal || COLORS.accent }}>
                                                                        {predictionsLoading ? '…' : atsScore != null ? Math.round(atsScore.ats_score || 0) : '—'}
                                                                    </span>
                                                                    <span className="text-[9px] font-medium" style={{ color: COLORS.textMuted }}>%</span>
                                                                </div>
                                                            </div>
                                                            <div>
                                                                <div className="text-sm font-bold" style={{ color: COLORS.textPrimary }}>
                                                                    {predictionsLoading ? 'Calculating...' : atsScore != null ? 'Resume score' : 'No resume'}
                                                                </div>
                                                                <div className="text-[11px] mt-0.5" style={{ color: COLORS.textMuted }}>
                                                                    Formatting, sections, contact · Does not depend on questions
                                                                </div>
                                                                {atsScore?.breakdown && (atsScore.breakdown.formatting != null || atsScore.breakdown.sections != null) && (
                                                                    <div className="flex flex-wrap gap-2 mt-2 text-[10px]" style={{ color: COLORS.textMuted }}>
                                                                        {atsScore.breakdown.formatting != null && <span>Format {atsScore.breakdown.formatting}%</span>}
                                                                        {atsScore.breakdown.sections != null && <span>· Sections {atsScore.breakdown.sections}%</span>}
                                                                        {atsScore.breakdown.contact != null && <span>· Contact {atsScore.breakdown.contact}%</span>}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Behavioral Anomalies Alert Box - High Visibility */}
                                                {hasStarted && (displayData.metrics.paste_detected || displayData.metrics.copy_detected || displayData.metrics.focus_loss_count > 0) && (
                                                    <div className="px-5 py-4 rounded-2xl border flex items-start gap-4 transition-all animate-in fade-in slide-in-from-left-4" style={{ backgroundColor: COLORS.dangerBg, borderColor: COLORS.danger }}>
                                                        <div className="p-3 rounded-xl" style={{ backgroundColor: COLORS.cardBg, boxShadow: '0 4px 12px rgba(239, 68, 68, 0.1)' }}>
                                                            <ShieldAlert className="w-6 h-6" style={{ color: COLORS.danger }} />
                                                        </div>
                                                        <div className="flex-1">
                                                            <div className="flex items-center justify-between mb-1">
                                                                <h3 className="text-sm font-bold" style={{ color: COLORS.danger }}>Behavioral Anomalies Detected</h3>
                                                                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.cardBg, color: COLORS.danger, border: `1px solid ${COLORS.danger}` }}>High Priority</span>
                                                            </div>
                                                            <p className="text-xs leading-relaxed mb-2" style={{ color: COLORS.textSecondary }}>
                                                                {displayData.metric_explanations?.behavioral_consistency || "System has detected patterns that may indicate external tool usage or multi-tasking."}
                                                            </p>
                                                            <div className="flex flex-wrap gap-2">
                                                                {displayData.metrics.paste_count > 0 && (
                                                                    <span className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold" style={{ backgroundColor: COLORS.danger + '15', color: COLORS.danger }}>
                                                                        <Clipboard className="w-3 h-3" /> {displayData.metrics.paste_count}x Paste
                                                                    </span>
                                                                )}
                                                                {displayData.metrics.copy_count > 0 && (
                                                                    <span className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold" style={{ backgroundColor: COLORS.danger + '15', color: COLORS.danger }}>
                                                                        <Copy className="w-3 h-3" /> {displayData.metrics.copy_count}x Copy
                                                                    </span>
                                                                )}
                                                                {displayData.metrics.focus_loss_count > 0 && (
                                                                    <span className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold" style={{ backgroundColor: COLORS.danger + '15', color: COLORS.danger }}>
                                                                        <EyeOff className="w-3 h-3" /> {displayData.metrics.focus_loss_count}x Tab Switch
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* ─── Behavioral: grade + metrics (only when candidate has started) ─── */}
                                                <div className="p-6 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 30%, ${COLORS.cardBg} 100%)`, borderColor: COLORS.border }}>
                                                    {hasStarted ? (
                                                        <>
                                                            <div className="flex items-center gap-2 mb-4">
                                                                <Brain className="w-4 h-4" style={{ color: COLORS.purple }} />
                                                                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>From assessment</span>
                                                                <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.purpleLight + '80', color: COLORS.purple }}>Based on questions</span>
                                                            </div>
                                                            <div className="flex flex-wrap items-center gap-6 mb-4">
                                                                {/* Grade hero */}
                                                                {(() => {
                                                                    const gc = displayData.overall_fit.grade_color;
                                                                    const ringColor = gc === 'gold' ? '#F59E0B' : gc === 'green' ? COLORS.success : gc === 'blue' ? COLORS.accent : gc === 'yellow' ? COLORS.warning : gc === 'red' ? COLORS.danger : COLORS.textMuted;
                                                                    return (
                                                                        <div className="flex items-center gap-4">
                                                                            <div style={{ position: 'relative', width: '72px', height: '72px' }}>
                                                                                <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                                                                                    <circle cx="50" cy="50" r="42" fill="none" stroke={COLORS.border} strokeWidth="6" opacity="0.2" />
                                                                                    <circle cx="50" cy="50" r="42" fill="none" stroke={ringColor} strokeWidth="6" strokeLinecap="round"
                                                                                        strokeDasharray={`${(displayData.overall_fit.score / 100) * 264} 264`}
                                                                                    />
                                                                                </svg>
                                                                                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                                                                    <span className="text-2xl font-black" style={{ color: ringColor }}>{displayData.overall_fit.grade}</span>
                                                                                    <span className="text-[10px] font-semibold" style={{ color: COLORS.textMuted }}>{displayData.overall_fit.score}</span>
                                                                                </div>
                                                                            </div>
                                                                            <div>
                                                                                <div className="text-xs font-semibold uppercase tracking-wider mb-0.5" style={{ color: COLORS.textMuted }}>Overall fit</div>
                                                                                <div className="text-lg font-bold" style={{ color: COLORS.textPrimary }}>{displayData.overall_fit.grade_label}</div>
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                })()}
                                                                {/* Behavioral metrics row */}
                                                                <div className="flex flex-wrap gap-3 flex-1 min-w-0">
                                                                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border" style={{ backgroundColor: displayData.metrics.cheating_resilience > 80 ? COLORS.successLight : displayData.metrics.cheating_resilience > 50 ? COLORS.warningLight : COLORS.dangerBg, borderColor: COLORS.border }}>
                                                                        <ShieldAlert className="w-4 h-4 shrink-0" style={{ color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger }} />
                                                                        <div>
                                                                            <div className="text-[10px] font-medium uppercase" style={{ color: COLORS.textMuted }}>Behavioral alignment</div>
                                                                            <div className="text-lg font-bold" style={{ color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger }}>{displayData.metrics.cheating_resilience}%</div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border" style={{ backgroundColor: COLORS.cardBgAlt, borderColor: COLORS.border }}>
                                                                        <Shield className="w-4 h-4 shrink-0" style={{ color: COLORS.purple }} />
                                                                        <div>
                                                                            <div className="text-[10px] font-medium uppercase" style={{ color: COLORS.textMuted }}>Answer stability</div>
                                                                            <div className="text-lg font-bold" style={{ color: COLORS.purple }}>{displayData.metrics.decision_firmness}%</div>
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex items-center gap-2 px-4 py-2 rounded-xl border" style={{ backgroundColor: COLORS.cardBgAlt, borderColor: COLORS.border }}>
                                                                        <Zap className="w-4 h-4 shrink-0" style={{ color: COLORS.warning }} />
                                                                        <div>
                                                                            <div className="text-[10px] font-medium uppercase" style={{ color: COLORS.textMuted }}>Selection speed</div>
                                                                            <div className="text-sm font-bold" style={{ color: COLORS.textPrimary }}>{displayData.metrics.decision_speed}</div>
                                                                        </div>
                                                                    </div>

                                                                </div>
                                                            </div>

                                                            {/* Recruiter psychology: verdict + takeaway + strength/consideration + confidence */}
                                                            {(() => {
                                                                const grade = displayData.overall_fit.grade;
                                                                const score = displayData.overall_fit.score ?? 0;
                                                                const verdict = grade === 'S' || grade === 'A' ? 'Strong match — consider shortlisting' : score >= 70 ? 'Worth a closer look' : score >= 50 ? 'Review with caution' : 'Limited data or low fit';
                                                                const qDone = displayData.progress?.current ?? 0;
                                                                const qTotal = displayData.progress?.total ?? 5;
                                                                const confidenceNote = qTotal > 0 ? `Based on ${qDone} of ${qTotal} questions` : 'Waiting for responses';
                                                                const firmness = displayData.metrics.decision_firmness ?? 0;
                                                                const behavioralAlignment = displayData.metrics.cheating_resilience ?? 100;
                                                                const strength = firmness >= 80 ? 'Stable choices' : behavioralAlignment >= 90 ? 'Consistent behavior' : 'Engaged with all options';
                                                                const consideration = behavioralAlignment < 80 ? 'Note: some tab or paste activity' : firmness < 60 ? 'Changed answers frequently' : qDone < 3 ? 'Early data — more questions add confidence' : null;
                                                                return (
                                                                    <>
                                                                        <div className="pt-3 border-t" style={{ borderColor: COLORS.border }}>
                                                                            <p className="text-sm font-semibold" style={{ color: COLORS.accent }}>
                                                                                {verdict}
                                                                            </p>
                                                                            <p className="text-xs mt-1.5" style={{ color: COLORS.textSecondary }}>
                                                                                Takeaway: {[displayData.behavioral_summary?.approach_pattern, displayData.behavioral_summary?.approach].filter(Boolean).join(' · ') || 'Analyzing...'}
                                                                                {displayData.behavioral_summary?.under_pressure ? `; ${displayData.behavioral_summary.under_pressure} under pressure.` : '.'}
                                                                            </p>
                                                                            <div className="mt-2 flex flex-wrap gap-3 text-xs">
                                                                                <span style={{ color: COLORS.success }}>✓ {strength}</span>
                                                                                {consideration && <span style={{ color: COLORS.textMuted }}>· {consideration}</span>}
                                                                            </div>
                                                                            <p className="text-[11px] mt-1.5" style={{ color: COLORS.textMuted }}>{confidenceNote}</p>
                                                                        </div>
                                                                    </>
                                                                );
                                                            })()}

                                                            <div className="mt-3 flex items-center gap-3 flex-wrap">
                                                                <button
                                                                    onClick={() => setActiveTab('profile')}
                                                                    className="text-sm font-semibold flex items-center gap-2 px-3 py-2 rounded-xl transition-colors hover:opacity-90"
                                                                    style={{ backgroundColor: COLORS.accentLight, color: COLORS.accent }}
                                                                >
                                                                    <Brain className="w-4 h-4" /> View full behavioral profile
                                                                </button>
                                                                <span className="text-[11px]" style={{ color: COLORS.textMuted }}>
                                                                    All metrics computed from behavior; expand Full Profile for radar, per-question stats & evidence.
                                                                </span>
                                                            </div>

                                                            {/* AI Behavioral Insights (Traits only, success is in Hero) */}
                                                            {(predictionsLoading || (behavioralTraits && behavioralTraits.predicted_traits && behavioralTraits.predicted_traits.length > 0)) && (
                                                                <div className="mt-4 p-4 rounded-xl border" style={{ backgroundColor: COLORS.cardBgAlt, borderColor: COLORS.border }}>
                                                                    <h4 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: COLORS.textMuted }}>AI Behavioral Insights</h4>
                                                                    {predictionsLoading ? (
                                                                        <div className="flex items-center gap-2 text-sm" style={{ color: COLORS.textMuted }}>
                                                                            <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }} />
                                                                            Analyzing patterns...
                                                                        </div>
                                                                    ) : (
                                                                        <div className="p-3 rounded-lg border" style={{ backgroundColor: COLORS.cardBg, borderColor: COLORS.border }}>
                                                                            <div className="text-[10px] font-medium uppercase mb-2" style={{ color: COLORS.textMuted }}>Predicted traits</div>
                                                                            <ul className="text-xs space-y-1" style={{ color: COLORS.textSecondary }}>
                                                                                {behavioralTraits.predicted_traits.slice(0, 5).map((t, i) => (
                                                                                    <li key={i} className="flex items-center gap-2">
                                                                                        <span style={{ color: COLORS.success }}>•</span> {t}
                                                                                    </li>
                                                                                ))}
                                                                            </ul>
                                                                            <div className="text-[11px] mt-1.5" style={{ color: COLORS.textMuted }}>Confidence: {behavioralTraits.confidence}</div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </>
                                                    ) : (
                                                        <div className="flex flex-col items-center justify-center py-12 gap-4">
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Brain className="w-5 h-5" style={{ color: COLORS.purple }} />
                                                                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>From assessment</span>
                                                            </div>
                                                            <div className="w-14 h-14 rounded-full border-2 border-dashed flex items-center justify-center" style={{ borderColor: COLORS.border }}>
                                                                <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }} />
                                                            </div>
                                                            <p className="text-sm font-medium text-center max-w-[280px]" style={{ color: COLORS.textPrimary }}>
                                                                Waiting for candidate to answer questions
                                                            </p>
                                                            <p className="text-xs text-center max-w-[260px]" style={{ color: COLORS.textMuted }}>
                                                                Grade, integrity, and other behavioral metrics will appear here once they respond.
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* === FULL PROFILE TAB === */}
                                        {activeTab === 'profile' && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>


                                                {/* Spider Chart + Live Metrics */}
                                                <div className="p-5 rounded-2xl border shadow-sm flex-1" style={{ background: `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 40%, ${COLORS.purpleLight} 100%)`, borderColor: COLORS.accent, boxShadow: '0 12px 28px rgba(59, 130, 246, 0.12)' }}>
                                                    <div className="mb-4">
                                                        <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.accentDark }}>
                                                            <span className="px-2.5 py-1 rounded-full" style={{ backgroundColor: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}>Behavioral Profile</span>
                                                        </h4>
                                                    </div>

                                                    {hasStarted ? (
                                                        <>
                                                            {/* Bigger Spider Chart */}
                                                            <div style={{ height: '280px', padding: '10px', borderRadius: '16px', background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 45%, ${COLORS.purpleLight} 100%)`, border: `1px solid ${COLORS.border}` }}>
                                                                <ResponsiveContainer width="100%" height="100%">
                                                                    <RadarChart data={getRadarData()} cx="50%" cy="50%" outerRadius="85%">
                                                                        <defs>
                                                                            <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                                                                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.5" />
                                                                                <stop offset="20%" stopColor="#6366F1" stopOpacity="0.5" />
                                                                                <stop offset="40%" stopColor="#8B5CF6" stopOpacity="0.5" />
                                                                                <stop offset="60%" stopColor="#F59E0B" stopOpacity="0.45" />
                                                                                <stop offset="80%" stopColor="#10B981" stopOpacity="0.45" />
                                                                                <stop offset="100%" stopColor="#0EA5E9" stopOpacity="0.5" />
                                                                            </linearGradient>
                                                                            <linearGradient id="radarStroke" x1="0%" y1="0%" x2="100%" y2="0%">
                                                                                <stop offset="0%" stopColor="#2563EB" />
                                                                                <stop offset="25%" stopColor="#7C3AED" />
                                                                                <stop offset="50%" stopColor="#F59E0B" />
                                                                                <stop offset="75%" stopColor="#10B981" />
                                                                                <stop offset="100%" stopColor="#0EA5E9" />
                                                                            </linearGradient>
                                                                        </defs>
                                                                        <PolarGrid stroke="rgba(148, 163, 184, 0.6)" />
                                                                        <PolarAngleAxis dataKey="skill" tick={{ fill: COLORS.textSecondary, fontSize: 11, fontWeight: 600 }} />
                                                                        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                                                                        <Radar
                                                                            dataKey="value"
                                                                            stroke="url(#radarStroke)"
                                                                            fill="url(#radarGradient)"
                                                                            fillOpacity={0.85}
                                                                            strokeWidth={2.5}
                                                                            dot={({ cx, cy, index }) => {
                                                                                const dotColors = ['#3B82F6', '#7C3AED', '#F59E0B', '#10B981', '#0EA5E9', '#EF4444'];
                                                                                const color = dotColors[index % dotColors.length];
                                                                                return <circle cx={cx} cy={cy} r={5.5} fill={color} stroke="#FFFFFF" strokeWidth={2} />;
                                                                            }}
                                                                        />
                                                                    </RadarChart>
                                                                </ResponsiveContainer>
                                                            </div>

                                                            {/* Skill Legend with Tooltips */}
                                                            <div className="mt-4 flex flex-wrap gap-2 justify-center">
                                                                {getRadarData().map((item, i) => (
                                                                    <TermTooltip
                                                                        key={i}
                                                                        term={item.termKey}
                                                                        dynamicExplanation={displayData.metric_explanations?.[radarExplanationKey[item.termKey]]}
                                                                    >
                                                                        <span className="px-2 py-1 text-xs rounded-full" style={{
                                                                            background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`,
                                                                            color: COLORS.textSecondary,
                                                                            border: `1px solid ${COLORS.border}`,
                                                                            cursor: 'help',
                                                                        }}>
                                                                            {item.skill}: {item.value}%
                                                                        </span>
                                                                    </TermTooltip>
                                                                ))}
                                                            </div>

                                                            {/* Live Metrics - 2 Column Grid with better spacing */}
                                                            <div className="mt-6 pt-5" style={{ borderTop: `1px solid ${COLORS.border}` }}>
                                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                                                    {/* Avg Response */}
                                                                    <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.tealLight} 100%)`, borderColor: COLORS.teal }}>
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            <Timer className="w-4 h-4" style={{ color: COLORS.teal }} />
                                                                            <TermTooltip
                                                                                term="avgResponse"
                                                                                dynamicExplanation={displayData.metric_explanations?.avg_response_time}
                                                                            >
                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Avg Response</span>
                                                                            </TermTooltip>
                                                                        </div>
                                                                        <span className="font-mono text-xl font-bold" style={{ color: COLORS.textPrimary }}>{displayData.metrics.avg_response_time}s</span>
                                                                    </div>

                                                                    {/* Decision Speed */}
                                                                    <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.warningLight} 100%)`, borderColor: COLORS.warning }}>
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            <Zap className="w-4 h-4" style={{ color: COLORS.warning }} />
                                                                            <TermTooltip
                                                                                term="selectionSpeed"
                                                                                dynamicExplanation={displayData.metric_explanations?.selection_speed}
                                                                            >
                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Selection Speed</span>
                                                                            </TermTooltip>
                                                                        </div>
                                                                        <span className="px-2.5 py-1 text-sm font-semibold rounded-full" style={{
                                                                            backgroundColor: displayData.metrics.decision_speed === 'Fast' ? COLORS.successBg : displayData.metrics.decision_speed === 'Slow' ? COLORS.dangerBg : COLORS.warningBg,
                                                                            color: displayData.metrics.decision_speed === 'Fast' ? COLORS.success : displayData.metrics.decision_speed === 'Slow' ? COLORS.danger : COLORS.warning
                                                                        }}>{displayData.metrics.decision_speed}</span>
                                                                    </div>

                                                                    {/* Session Continuity */}
                                                                    <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.accent }}>
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            <Target className="w-4 h-4" style={{ color: COLORS.accent }} />
                                                                            <TermTooltip
                                                                                term="sessionContinuity"
                                                                                dynamicExplanation={displayData.metric_explanations?.session_continuity}
                                                                            >
                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Session Continuity</span>
                                                                            </TermTooltip>
                                                                        </div>
                                                                        <span className="text-xl font-bold" style={{ color: COLORS.accent }}>
                                                                            {displayData.metrics.session_continuity !== null ? `${displayData.metrics.session_continuity}%` : '—'}
                                                                        </span>
                                                                    </div>

                                                                    {/* Decision Firmness */}
                                                                    <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.purpleLight} 100%)`, borderColor: COLORS.purple }}>
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            <Shield className="w-4 h-4" style={{ color: COLORS.purple }} />
                                                                            <TermTooltip
                                                                                term="decisionFirmness"
                                                                                dynamicExplanation={displayData.metric_explanations?.decision_firmness}
                                                                            >
                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Answer Stability</span>
                                                                            </TermTooltip>
                                                                        </div>
                                                                        <span className="text-xl font-bold" style={{ color: COLORS.purple }}>{displayData.metrics.decision_firmness}%</span>
                                                                    </div>

                                                                    {/* Cheating Resilience (New) */}
                                                                    <div className="p-3 rounded-lg border" style={{
                                                                        background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${displayData.metrics.cheating_resilience > 80 ? COLORS.successLight : displayData.metrics.cheating_resilience > 50 ? COLORS.warningLight : COLORS.dangerBg} 100%)`,
                                                                        borderColor: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger
                                                                    }}>
                                                                        <div className="flex items-center gap-2 mb-1">
                                                                            <ShieldAlert className="w-4 h-4" style={{
                                                                                color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger
                                                                            }} />
                                                                            <TermTooltip
                                                                                term="behavioralConsistency"
                                                                                dynamicExplanation={displayData.metric_explanations?.behavioral_consistency}
                                                                            >
                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Behavioral Consistency</span>
                                                                            </TermTooltip>
                                                                        </div>
                                                                        <span className="text-xl font-bold" style={{
                                                                            color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger
                                                                        }}>{displayData.metrics.cheating_resilience}%</span>
                                                                    </div>
                                                                </div>

                                                                {/* Show/Hide detailed metrics */}
                                                                <div className="mt-3">
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setShowDetailedMetrics(!showDetailedMetrics)}
                                                                        className="flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
                                                                        style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.accent, border: `1px solid ${COLORS.border}` }}
                                                                    >
                                                                        {showDetailedMetrics ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                                                        {showDetailedMetrics ? 'Hide' : 'Show'} detailed metrics
                                                                    </button>
                                                                </div>
                                                                {showDetailedMetrics && (
                                                                    <div className="mt-3 p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`, borderColor: COLORS.border }}>
                                                                        <div className="flex items-center gap-2 mb-2">
                                                                            <Activity className="w-4 h-4" style={{ color: COLORS.teal }} />
                                                                            <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>Per-Question Stats</span>
                                                                        </div>
                                                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                                                                            {(() => {
                                                                                const completedTasks = (displayData.per_task_metrics || []).filter(t => t.is_completed);
                                                                                return completedTasks.length > 0 ? (
                                                                                    completedTasks.map((task, idx) => (
                                                                                        <div key={idx} className="flex items-center justify-between py-1.5 px-2 rounded text-xs transition-colors hover:bg-opacity-80" style={{ backgroundColor: COLORS.cardBg }}>
                                                                                            <div className="flex items-center gap-2">
                                                                                                <span className="font-medium" style={{ color: COLORS.textSecondary }}>Q{idx + 1}</span>
                                                                                                {task.focus_loss_count > 0 && <EyeOff size={11} className="text-red-500" title={`Focus Lost: ${task.focus_loss_count}x`} />}
                                                                                            </div>
                                                                                            <div className="flex items-center gap-1.5">
                                                                                                <span className="font-mono" style={{ color: COLORS.teal }}>{Math.round(task.time_spent_seconds) || 0}s</span>
                                                                                                <span style={{ color: task.decision_changes > 2 ? COLORS.warning : COLORS.textMuted }}>{task.decision_changes || 0}Δ</span>
                                                                                            </div>
                                                                                        </div>
                                                                                    ))
                                                                                ) : (
                                                                                    <div className="col-span-2 text-xs text-center py-2" style={{ color: COLORS.textMuted }}>No questions completed yet</div>
                                                                                );
                                                                            })()}
                                                                        </div>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </>
                                                    ) : (
                                                        <div className="flex flex-col items-center justify-center py-16 gap-4">
                                                            <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }}></div>
                                                            <span className="text-sm" style={{ color: COLORS.textMuted }}>Waiting for candidate to start...</span>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Behavioral Labels Grid - Progressive Analysis (only when detailed metrics expanded) */}
                                                {showDetailedMetrics && (
                                                    <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 35%, ${COLORS.tealLight} 100%)`, borderColor: COLORS.accent, boxShadow: '0 12px 26px rgba(13, 148, 136, 0.12)' }}>
                                                        {hasStarted ? (
                                                            <>
                                                                {/* Confidence Indicator Bar */}
                                                                {showDetailedBehavior && (
                                                                    <>
                                                                        {displayData.behavioral_summary?.confidence_level !== undefined && (
                                                                            <div className="mb-3 pb-3 border-b" style={{ borderColor: COLORS.border }}>
                                                                                <div className="flex items-center justify-between mb-1.5">
                                                                                    <TermTooltip
                                                                                        term="analysisConfidence"
                                                                                        dynamicExplanation={displayData.metric_explanations?.analysis_confidence}
                                                                                    >
                                                                                        <span className="text-xs font-medium" style={{ color: COLORS.textMuted }}>
                                                                                            Analysis Confidence ({displayData.behavioral_summary.questions_analyzed || 0} questions)
                                                                                        </span>
                                                                                    </TermTooltip>
                                                                                    <span className="text-xs font-semibold" style={{
                                                                                        color: displayData.behavioral_summary.confidence_level >= 75 ? COLORS.success :
                                                                                            displayData.behavioral_summary.confidence_level >= 50 ? COLORS.warning : COLORS.textMuted
                                                                                    }}>
                                                                                        {displayData.behavioral_summary.confidence_level}%
                                                                                    </span>
                                                                                </div>
                                                                                <div className="h-2 rounded-full overflow-hidden" style={{ background: `linear-gradient(135deg, ${COLORS.cardBgAlt} 0%, ${COLORS.cardBg} 100%)` }}>
                                                                                    <div
                                                                                        className="h-full rounded-full transition-all duration-500"
                                                                                        style={{
                                                                                            width: `${displayData.behavioral_summary.confidence_level}%`,
                                                                                            background: displayData.behavioral_summary.confidence_level >= 75
                                                                                                ? `linear-gradient(90deg, ${COLORS.teal}, ${COLORS.success})`
                                                                                                : displayData.behavioral_summary.confidence_level >= 50
                                                                                                    ? `linear-gradient(90deg, ${COLORS.warning}, ${COLORS.accent})`
                                                                                                    : `linear-gradient(90deg, ${COLORS.textMuted}, ${COLORS.border})`
                                                                                        }}
                                                                                    />
                                                                                </div>
                                                                                {displayData.metric_explanations?.analysis_confidence && (
                                                                                    <div className="mt-2 text-[11px]" style={{ color: COLORS.textMuted }}>
                                                                                        {summarizeExplanation(displayData.metric_explanations.analysis_confidence)}
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        <div className="grid grid-cols-3 gap-3">
                                                                            {[
                                                                                { label: 'Selection Speed', termKey: 'selectionSpeed', explainKey: 'selection_speed', value: displayData.metrics.decision_speed || '—', icon: Zap, color: COLORS.warning },
                                                                                { label: 'Idle Time', termKey: 'idleTime', explainKey: 'idle_time', value: displayData.metrics.idle_time < 30 ? 'Low' : displayData.metrics.idle_time < 60 ? 'Moderate' : 'High', icon: Timer, color: COLORS.teal },
                                                                                { label: 'Approach Pattern', termKey: 'approachPattern', explainKey: 'approach_pattern', value: displayData.behavioral_summary?.approach_pattern || 'Analyzing...', icon: Brain, color: COLORS.purple },
                                                                                { label: 'Approach', termKey: 'approach', explainKey: 'approach', value: displayData.behavioral_summary?.approach || 'Analyzing...', icon: Activity, color: COLORS.success },
                                                                                { label: 'Under Pressure', termKey: 'underPressure', explainKey: 'under_pressure', value: displayData.behavioral_summary?.under_pressure || 'Observing...', icon: Shield, color: COLORS.danger },
                                                                                { label: 'Correctness', termKey: 'correctness', explainKey: 'correctness_rate', value: displayData.behavioral_summary?.correctness_rate !== undefined ? `${displayData.behavioral_summary.correctness_rate}%` : '—', icon: CheckCircle2, color: displayData.behavioral_summary?.correctness_rate >= 70 ? COLORS.success : displayData.behavioral_summary?.correctness_rate >= 50 ? COLORS.warning : COLORS.danger },
                                                                            ].map((item, i) => {
                                                                                const explanationSummary = summarizeExplanation(displayData.metric_explanations?.[item.explainKey]);
                                                                                return (
                                                                                    <div
                                                                                        key={i}
                                                                                        className="p-3 rounded-lg border"
                                                                                        style={{
                                                                                            background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${item.color === COLORS.warning ? COLORS.warningLight :
                                                                                                item.color === COLORS.teal ? COLORS.tealLight :
                                                                                                    item.color === COLORS.purple ? COLORS.purpleLight :
                                                                                                        item.color === COLORS.success ? COLORS.successLight : COLORS.dangerLight
                                                                                                } 100%)`,
                                                                                            borderColor: item.color
                                                                                        }}
                                                                                    >
                                                                                        <div className="flex items-center gap-1.5 mb-1.5">
                                                                                            <item.icon className="w-3.5 h-3.5" style={{ color: item.color }} />
                                                                                            <TermTooltip
                                                                                                term={item.termKey}
                                                                                                dynamicExplanation={displayData.metric_explanations?.[item.explainKey]}
                                                                                            >
                                                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>{item.label}</span>
                                                                                            </TermTooltip>
                                                                                        </div>
                                                                                        <span className="text-sm font-semibold" style={{ color: COLORS.textPrimary }}>
                                                                                            {item.value}
                                                                                            {typeof item.value === 'string' && item.value.includes('*') && (
                                                                                                <span className="text-xs ml-1" style={{ color: COLORS.textMuted }}>(tentative)</span>
                                                                                            )}
                                                                                        </span>
                                                                                        {explanationSummary && (
                                                                                            <div className="mt-1 text-[10px]" style={{ color: COLORS.textMuted }}>
                                                                                                {explanationSummary}
                                                                                            </div>
                                                                                        )}
                                                                                    </div>
                                                                                );
                                                                            })}
                                                                        </div>
                                                                    </>
                                                                )}

                                                            </>
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center py-6 gap-3">
                                                                <div className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }}></div>
                                                                <span className="text-sm" style={{ color: COLORS.textMuted }}>Waiting for first completed answer...</span>
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Behavioral patterns require actual responses to analyze</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Population Intelligence */}
                                                <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, rgba(20, 184, 166, 0.05) 100%)`, borderColor: COLORS.teal, boxShadow: '0 12px 26px rgba(13, 148, 136, 0.08)' }}>
                                                    <PopulationIntelligence data={displayData.population_intelligence} />
                                                </div>

                                            </div>
                                        )}

                                        {/* Evidence tab removed - use Overview + Full Profile instead */}
                                        {false && activeTab === 'evidence' && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

                                                <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)`, borderColor: COLORS.accent, boxShadow: '0 12px 26px rgba(59, 130, 246, 0.08)' }}>
                                                    <h4 className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: COLORS.accentDark }}>
                                                        <span className="px-2.5 py-1 rounded-full" style={{ backgroundColor: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}>Key Metrics</span>
                                                    </h4>
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                                                        <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.tealLight} 100%)`, borderColor: COLORS.teal }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Timer className="w-4 h-4" style={{ color: COLORS.teal }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Avg Response</span>
                                                            </div>
                                                            <span className="font-mono text-xl font-bold" style={{ color: COLORS.textPrimary }}>{displayData.metrics.avg_response_time}s</span>
                                                        </div>
                                                        <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.warningLight} 100%)`, borderColor: COLORS.warning }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Zap className="w-4 h-4" style={{ color: COLORS.warning }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Selection Speed</span>
                                                            </div>
                                                            <span className="px-2.5 py-1 text-sm font-semibold rounded-full" style={{
                                                                backgroundColor: displayData.metrics.decision_speed === 'Fast' ? COLORS.successBg : displayData.metrics.decision_speed === 'Slow' ? COLORS.dangerBg : COLORS.warningBg,
                                                                color: displayData.metrics.decision_speed === 'Fast' ? COLORS.success : displayData.metrics.decision_speed === 'Slow' ? COLORS.danger : COLORS.warning
                                                            }}>{displayData.metrics.decision_speed}</span>
                                                        </div>
                                                        <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.accent }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Target className="w-4 h-4" style={{ color: COLORS.accent }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Continuity</span>
                                                            </div>
                                                            <span className="text-xl font-bold" style={{ color: COLORS.accent }}>{displayData.metrics.session_continuity !== null ? `${displayData.metrics.session_continuity}%` : '—'}</span>
                                                        </div>
                                                        <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.purpleLight} 100%)`, borderColor: COLORS.purple }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <Shield className="w-4 h-4" style={{ color: COLORS.purple }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Answer Stability</span>
                                                            </div>
                                                            <span className="text-xl font-bold" style={{ color: COLORS.purple }}>{displayData.metrics.decision_firmness}%</span>
                                                        </div>
                                                        <div className="p-3 rounded-lg border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.successLight} 100%)`, borderColor: COLORS.success }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <AlignLeft className="w-4 h-4" style={{ color: COLORS.success }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Reasoning Depth</span>
                                                            </div>
                                                            <span className="text-xl font-bold" style={{ color: COLORS.success }}>{displayData.metrics.reasoning_depth || 0}%</span>
                                                        </div>
                                                        <div className="p-3 rounded-lg border" style={{
                                                            background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${displayData.metrics.cheating_resilience > 80 ? COLORS.successLight : displayData.metrics.cheating_resilience > 50 ? COLORS.warningLight : COLORS.dangerBg} 100%)`,
                                                            borderColor: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger
                                                        }}>
                                                            <div className="flex items-center gap-2 mb-1">
                                                                <ShieldAlert className="w-4 h-4" style={{ color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>Integrity</span>
                                                            </div>
                                                            <span className="text-xl font-bold" style={{ color: displayData.metrics.cheating_resilience > 80 ? COLORS.success : displayData.metrics.cheating_resilience > 50 ? COLORS.warning : COLORS.danger }}>{displayData.metrics.cheating_resilience}%</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Population Intelligence */}
                                                <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, rgba(20, 184, 166, 0.05) 100%)`, borderColor: COLORS.teal, boxShadow: '0 12px 26px rgba(13, 148, 136, 0.08)' }}>
                                                    <PopulationIntelligence data={displayData.population_intelligence} />
                                                </div>

                                            </div>
                                        )}

                                        {/* === LIVE FEED TAB === */}
                                        {activeTab === 'livefeed' && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                                <div style={{ padding: '12px 12px 12px 18px', background: `linear-gradient(180deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 75%)`, boxShadow: '0 10px 26px rgba(15, 23, 42, 0.1)' }}>
                                                    <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(145deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.accent, boxShadow: '0 10px 24px rgba(59, 130, 246, 0.12)' }}>
                                                        <div className="flex items-center justify-between mb-3">
                                                            <div className="flex items-center gap-3">
                                                                <div className="relative flex items-center justify-center w-4 h-4">
                                                                    <div className="absolute w-4 h-4 rounded-full animate-ping" style={{ backgroundColor: COLORS.danger, opacity: 0.25 }}></div>
                                                                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS.danger }}></div>
                                                                </div>
                                                                <div>
                                                                    <div className="text-[9px] font-semibold uppercase tracking-[0.22em]" style={{ color: COLORS.textMuted }}>Live Feed</div>
                                                                    <div className="text-xs font-semibold" style={{ color: COLORS.textPrimary }}>Candidate Activity</div>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full" style={{ backgroundColor: COLORS.accentLight, color: COLORS.accent }}>
                                                                    Q {displayData.progress.current}/{displayData.progress.total}
                                                                </span>
                                                                <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full" style={{ backgroundColor: COLORS.cardBg, color: COLORS.textSecondary }}>
                                                                    {formatTime(displayData.time_remaining_seconds)} left
                                                                </span>
                                                            </div>
                                                        </div>

                                                        {currentQuestion ? (
                                                            <div className="space-y-4">
                                                                <div className="p-3 rounded-xl border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.accent }}>
                                                                    <div className="flex items-start justify-between gap-4">
                                                                        <div className="flex items-start gap-2">
                                                                            <FileText className="w-4 h-4 mt-0.5" style={{ color: COLORS.accent }} />
                                                                            <div>
                                                                                <div className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: COLORS.textMuted }}>Current Question</div>
                                                                                <p className="text-xs leading-relaxed mt-1" style={{ color: COLORS.textPrimary }}>{currentQuestion.scenario}</p>
                                                                            </div>
                                                                        </div>
                                                                        <div className="flex flex-col items-end gap-2">
                                                                            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full" style={{
                                                                                backgroundColor: currentQuestion.difficulty === 'hard' ? COLORS.dangerBg : currentQuestion.difficulty === 'medium' ? COLORS.warningBg : COLORS.successBg,
                                                                                color: currentQuestion.difficulty === 'hard' ? COLORS.danger : currentQuestion.difficulty === 'medium' ? COLORS.warning : COLORS.success
                                                                            }}>
                                                                                {currentQuestion.difficulty} difficulty
                                                                            </span>
                                                                            <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full" style={{ backgroundColor: COLORS.cardBgAlt, color: COLORS.textSecondary }}>
                                                                                {currentQuestion.category || 'general'}
                                                                            </span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="mt-3 flex items-center gap-3">
                                                                        <div className="flex items-center gap-1.5">
                                                                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: currentQuestion.candidate_selection ? COLORS.success : COLORS.warning }}></div>
                                                                            <span className="text-[10px]" style={{ color: COLORS.textSecondary }}>
                                                                                {currentQuestion.candidate_selection ? 'Answer selected' : 'Reading / considering'}
                                                                            </span>
                                                                        </div>
                                                                        <div className="text-[10px]" style={{ color: COLORS.textMuted }}>
                                                                            Pattern: {displayData.behavioral_summary?.approach_pattern || 'Detecting...'}
                                                                        </div>
                                                                        <div className="flex items-center gap-2 ml-auto">
                                                                            {currentQuestion.focus_loss_count > 0 && <EyeOff size={11} className="text-red-500" title="Tab Switch" />}
                                                                            {currentQuestion.paste_count > 0 && <Clipboard size={11} className="text-red-500" title="Paste" />}
                                                                            {currentQuestion.copy_count > 0 && <Copy size={11} className="text-orange-500" title="Copy" />}
                                                                        </div>
                                                                    </div>
                                                                </div>

                                                                <div className="p-3 rounded-xl border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.purpleLight} 100%)`, borderColor: COLORS.purple }}>
                                                                    <div className="flex items-center justify-between mb-3">
                                                                        <div className="flex items-center gap-2">
                                                                            <Eye className="w-4 h-4" style={{ color: COLORS.purple }} />
                                                                            <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.purple }}>Candidate Selection</h4>
                                                                        </div>
                                                                        <span className="text-[10px]" style={{ color: COLORS.textMuted }}>
                                                                            {currentQuestion.candidate_selection ? 'Live answer tracked' : 'Waiting for answer'}
                                                                        </span>
                                                                    </div>
                                                                    <div className="space-y-2">
                                                                        {currentQuestion.options?.map((opt) => {
                                                                            const isSelected = currentQuestion.candidate_selection === opt.id;
                                                                            return (
                                                                                <div
                                                                                    key={opt.id}
                                                                                    className="p-3 rounded-lg border transition-all"
                                                                                    style={{
                                                                                        borderColor: isSelected ? COLORS.accent : COLORS.border,
                                                                                        backgroundColor: isSelected ? COLORS.accentLight : 'transparent',
                                                                                        boxShadow: isSelected ? '0 6px 16px rgba(59, 130, 246, 0.15)' : 'none'
                                                                                    }}
                                                                                >
                                                                                    <div className="flex items-start gap-2">
                                                                                        <div className="w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5" style={{ borderColor: isSelected ? COLORS.accent : COLORS.border }}>
                                                                                            {isSelected && <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS.accent }}></div>}
                                                                                        </div>
                                                                                        <div className="flex-1">
                                                                                            <div className="text-xs" style={{ color: COLORS.textPrimary }}>{opt.text}</div>
                                                                                            <div className="mt-1 flex items-center gap-2">
                                                                                                <span className="text-[10px] px-1.5 py-0.5 rounded" style={{
                                                                                                    backgroundColor: opt.risk_level === 'high' ? COLORS.dangerBg : opt.risk_level === 'medium' ? COLORS.warningBg : COLORS.successBg,
                                                                                                    color: opt.risk_level === 'high' ? COLORS.danger : opt.risk_level === 'medium' ? COLORS.warning : COLORS.success
                                                                                                }}>
                                                                                                    {opt.risk_level} risk
                                                                                                </span>
                                                                                                {opt.is_correct && (
                                                                                                    <span className="flex items-center gap-1 px-1 py-0.5 rounded text-[10px]" style={{ backgroundColor: COLORS.successBg, color: COLORS.success }}>
                                                                                                        <CheckCircle2 className="w-2 h-2" /> Correct
                                                                                                    </span>
                                                                                                )}
                                                                                            </div>
                                                                                        </div>
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </div>

                                                                {currentQuestion.reasoning_text && (
                                                                    <div className="p-3 rounded-xl border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`, borderColor: COLORS.teal }}>
                                                                        <div className="flex items-center gap-2 mb-2">
                                                                            <MessageSquare className="w-3.5 h-3.5" style={{ color: COLORS.teal }} />
                                                                            <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: COLORS.teal }}>Live reasoning</span>
                                                                        </div>
                                                                        <p className="text-[11px] leading-relaxed" style={{ color: COLORS.textSecondary }}>
                                                                            {currentQuestion.reasoning_text}
                                                                        </p>
                                                                    </div>
                                                                )}

                                                                <div className="pt-2">
                                                                    <div className="flex items-center justify-between mb-2">
                                                                        <h4 className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: COLORS.textMuted }}>Question History</h4>
                                                                        <span className="text-[11px]" style={{ color: COLORS.textMuted }}>
                                                                            {(displayData.per_task_metrics || []).filter(t => t.is_completed).length} completed
                                                                        </span>
                                                                    </div>
                                                                    {(() => {
                                                                        const completed = (displayData.per_task_metrics || []).map((t, idx) => ({ task: t, idx })).filter(({ task }) => task.is_completed);
                                                                        if (completed.length === 0) {
                                                                            return <div className="text-xs text-center py-3" style={{ color: COLORS.textMuted }}>No completed questions yet</div>;
                                                                        }
                                                                        return (
                                                                            <div className="space-y-2">
                                                                                {completed.map(({ task, idx }) => (
                                                                                    <button
                                                                                        key={idx}
                                                                                        onClick={() => setViewingQuestionIndex(idx)}
                                                                                        className="w-full text-left p-2.5 rounded-xl border transition-all"
                                                                                        style={{
                                                                                            borderColor: viewingQuestionIndex === idx ? COLORS.accent : COLORS.border,
                                                                                            background: viewingQuestionIndex === idx ? `linear-gradient(135deg, ${COLORS.accentLight} 0%, ${COLORS.cardBg} 100%)` : COLORS.cardBg
                                                                                        }}
                                                                                    >
                                                                                        <div className="flex items-center justify-between">
                                                                                            <div className="flex items-center gap-3">
                                                                                                <div className="flex flex-col items-center">
                                                                                                    <span className="text-[11px] font-semibold" style={{ color: COLORS.textPrimary }}>Q{idx + 1}</span>
                                                                                                    <span className="text-[9px]" style={{ color: COLORS.textMuted }}>{Math.round(task.time_spent_seconds || 0)}s</span>
                                                                                                </div>
                                                                                                <div className="text-[10px]" style={{ color: COLORS.textMuted }}>
                                                                                                    {task.observed_pattern || 'pattern pending'}
                                                                                                </div>
                                                                                            </div>
                                                                                            <div className="flex items-center gap-2">
                                                                                                {task.focus_loss_count > 0 && <EyeOff size={10} className="text-red-500" />}
                                                                                                {task.paste_count > 0 && <Clipboard size={10} className="text-red-500" />}
                                                                                                {task.copy_count > 0 && <Copy size={10} className="text-orange-500" />}
                                                                                                <span className="text-[10px]" style={{ color: task.decision_changes > 2 ? COLORS.warning : COLORS.textMuted }}>
                                                                                                    {task.decision_changes || 0} changes
                                                                                                </span>
                                                                                                <span className="text-[10px]" style={{ color: task.session_continuity_score < 70 ? COLORS.warning : COLORS.success }}>
                                                                                                    {task.session_continuity_score || 100}%
                                                                                                </span>
                                                                                            </div>
                                                                                        </div>
                                                                                    </button>
                                                                                ))}
                                                                            </div>
                                                                        );
                                                                    })()}

                                                                    {viewingQuestionIndex !== null && (() => {
                                                                        const histTask = (displayData.per_task_metrics || [])[viewingQuestionIndex];
                                                                        if (!histTask) return null;
                                                                        return (
                                                                            <div className="mt-3 p-3 rounded-xl border" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`, borderColor: COLORS.accent }}>
                                                                                <div className="flex items-center justify-between mb-2">
                                                                                    <span className="text-[11px] font-semibold" style={{ color: COLORS.textPrimary }}>Question {viewingQuestionIndex + 1} details</span>
                                                                                    <button
                                                                                        onClick={() => setViewingQuestionIndex(null)}
                                                                                        className="text-[10px]"
                                                                                        style={{ color: COLORS.textMuted }}
                                                                                    >
                                                                                        close
                                                                                    </button>
                                                                                </div>
                                                                                <div className="grid grid-cols-2 gap-2 text-[10px]" style={{ color: COLORS.textSecondary }}>
                                                                                    <div>First click: <span style={{ color: COLORS.textPrimary }}>{histTask.initial_selection_seconds?.toFixed(2)}s</span></div>
                                                                                    <div>Idle avg: <span style={{ color: COLORS.textPrimary }}>{histTask.idle_time_seconds?.toFixed(2)}s</span></div>
                                                                                    <div>Continuity: <span style={{ color: COLORS.textPrimary }}>{histTask.session_continuity_score || 100}%</span></div>
                                                                                    <div>Changes: <span style={{ color: COLORS.textPrimary }}>{histTask.decision_changes || 0}</span></div>
                                                                                    <div>Pattern: <span style={{ color: COLORS.textPrimary }}>{histTask.observed_pattern || '—'}</span></div>
                                                                                    <div>Explanation: <span style={{ color: COLORS.textPrimary }}>{histTask.explanation_word_count || 0} words</span></div>
                                                                                    {histTask.focus_loss_count > 0 && <div className="text-red-500 font-bold">Tab switches: {histTask.focus_loss_count}</div>}
                                                                                    {histTask.paste_count > 0 && <div className="text-red-500 font-bold">Pastes detected: {histTask.paste_count}</div>}
                                                                                    {histTask.copy_count > 0 && <div className="text-orange-500 font-bold">Copy events: {histTask.copy_count}</div>}
                                                                                </div>
                                                                                {histTask.scenario && (
                                                                                    <p className="mt-2 text-[10px] leading-relaxed" style={{ color: COLORS.textSecondary }}>
                                                                                        {histTask.scenario}
                                                                                    </p>
                                                                                )}
                                                                            </div>
                                                                        );
                                                                    })()}
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center py-8 gap-2">
                                                                <div className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }}></div>
                                                                <span className="text-sm" style={{ color: COLORS.textMuted }}>Waiting for current question...</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="p-4 rounded-xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.cardBgAlt} 100%)`, borderColor: COLORS.border, boxShadow: '0 8px 20px rgba(15, 23, 42, 0.06)' }}>
                                                    <h4 className="text-xs font-semibold uppercase tracking-wider mb-4" style={{ color: COLORS.textMuted }}>Skills Observed</h4>
                                                    {hasStarted && liveData?.resume_comparison?.observed_skills ? (
                                                        <div className="space-y-3">
                                                            {liveData.resume_comparison.observed_skills.slice(0, 5).map((skill, i) => {
                                                                const score = skill.score || 0;
                                                                // Color based on score
                                                                const getScoreColor = (s) => {
                                                                    if (s >= 80) return COLORS.success;
                                                                    if (s >= 60) return COLORS.teal;
                                                                    if (s >= 40) return COLORS.warning;
                                                                    return COLORS.danger;
                                                                };

                                                                return (
                                                                    <div key={i} className="py-2">
                                                                        <div className="flex justify-between items-center mb-1">
                                                                            <span className="text-xs font-medium" style={{ color: COLORS.textPrimary }}>{skill.skill}</span>
                                                                            <span className="text-xs font-semibold" style={{ color: getScoreColor(score) }}>{score}%</span>
                                                                        </div>
                                                                        <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: COLORS.border }}>
                                                                            <div
                                                                                className="h-1.5 rounded-full transition-all duration-700 ease-out"
                                                                                style={{
                                                                                    width: `${score}%`,
                                                                                    backgroundColor: getScoreColor(score)
                                                                                }}
                                                                            />
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                            {/* Overall Score */}
                                                            {liveData.resume_comparison.overall_score !== undefined && (
                                                                <div className="mt-3 pt-3 border-t" style={{ borderColor: COLORS.border }}>
                                                                    <div className="flex justify-between items-center">
                                                                        <span className="text-xs font-semibold uppercase" style={{ color: COLORS.textMuted }}>Overall</span>
                                                                        <span className="text-lg font-bold" style={{ color: COLORS.accent }}>{liveData.resume_comparison.overall_score}%</span>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center justify-center py-6 gap-3">
                                                            <div className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: COLORS.accent, borderTopColor: 'transparent' }}></div>
                                                            <span className="text-sm" style={{ color: COLORS.textMuted }}>Analyzing skills...</span>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* === REAL-TIME EVENT FEED === */}
                                                <div className="p-5 rounded-2xl border shadow-sm" style={{ background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${COLORS.accentLight} 100%)`, borderColor: COLORS.accent, boxShadow: '0 10px 24px rgba(59, 130, 246, 0.12)' }}>
                                                    <div className="flex items-center justify-between mb-4">
                                                        <div className="flex items-center gap-2">
                                                            <Activity className="w-4 h-4" style={{ color: COLORS.accent }} />
                                                            <h4 className="text-xs font-semibold uppercase tracking-wider" style={{ color: COLORS.accent }}>Real-time Activity Log</h4>
                                                        </div>
                                                        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: COLORS.accentLight, color: COLORS.accent }}>{recentEvents.length} events</span>
                                                    </div>

                                                    <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                                        {recentEvents.length > 0 ? (
                                                            recentEvents.map((event, i) => (
                                                                <div key={event.id || i} className="flex gap-3 py-2 border-b last:border-0" style={{ borderColor: COLORS.borderLight }}>
                                                                    <div className="mt-0.5 shrink-0">
                                                                        {event.type === 'paste_detected' && <Clipboard className="w-3.5 h-3.5 text-red-500" />}
                                                                        {event.type === 'copy_detected' && <FileText className="w-3.5 h-3.5 text-orange-500" />}
                                                                        {event.type === 'focus_lost' && <EyeOff className="w-3.5 h-3.5 text-red-600" />}
                                                                        {event.type === 'focus_gained' && <Eye className="w-3.5 h-3.5 text-green-500" />}
                                                                        {event.type === 'idle_detected' && <Clock className="w-3.5 h-3.5 text-yellow-500" />}
                                                                    </div>
                                                                    <div className="flex-1">
                                                                        <div className="flex justify-between items-start">
                                                                            <span className="text-[11px] font-semibold" style={{ color: COLORS.textPrimary }}>
                                                                                {event.type === 'paste_detected' ? 'Text Pasted' :
                                                                                    event.type === 'copy_detected' ? 'Question Copied' :
                                                                                        event.type === 'focus_lost' ? 'Tab Switched (Focus Lost)' :
                                                                                            event.type === 'focus_gained' ? 'Tab Switched (Focus Gained)' :
                                                                                                event.type === 'idle_detected' ? 'Extended Pause' : event.type}
                                                                            </span>
                                                                            <span className="text-[9px]" style={{ color: COLORS.textMuted }}>{new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                                                                        </div>
                                                                        <p className="text-[10px] mt-0.5" style={{ color: COLORS.textSecondary }}>
                                                                            {event.type === 'paste_detected' && `Pasted ${event.payload.char_count || 0} characters into ${event.payload.source || 'field'}.`}
                                                                            {event.type === 'copy_detected' && `Copied question text (${event.payload.char_count || 0} chars).`}
                                                                            {event.type === 'focus_lost' && 'Candidate switched to another tab or application.'}
                                                                            {event.type === 'focus_gained' && 'Candidate returned to the assessment tab.'}
                                                                            {event.type === 'idle_detected' && `Inactivity detected for ${event.payload.duration || 0} seconds.`}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            ))
                                                        ) : (
                                                            <div className="flex flex-col items-center justify-center py-10 gap-2 opacity-50">
                                                                <Activity className="w-8 h-8" style={{ color: COLORS.textMuted }} />
                                                                <span className="text-xs" style={{ color: COLORS.textMuted }}>No live behavior events detected yet</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                    </div>{/* end tab content */}

                                </div>{/* end middle column */}

                                {/* ═══ RIGHT COLUMN: Kiwi assistant ═══ */}
                                <div className="shrink-0 rounded-xl border overflow-hidden flex flex-col" style={{ width: 380, borderColor: COLORS.border, backgroundColor: COLORS.cardBg }}>
                                    <div className="px-3 py-2 border-b flex items-center gap-2 shrink-0" style={{ borderColor: COLORS.border, backgroundColor: COLORS.cardBgAlt }}>
                                        <MessageSquare className="w-4 h-4" style={{ color: COLORS.accent }} />
                                        <span className="text-sm font-semibold" style={{ color: COLORS.textPrimary }}>Kiwi Assistant</span>
                                    </div>
                                    <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                                        <ReportAssistant inline attemptId={selectedAttemptId} pageContext="live_assessment" />
                                    </div>
                                </div>
                            </>
                        )}
                    </div>{/* end main panel */}
                </div >
            )}
        </div >
    );
};

export default LiveAssessment;

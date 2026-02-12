import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import SkillRadarChart from '../components/charts/SkillRadarChart';
import BehavioralLineChart from '../components/charts/BehavioralLineChart';
import { apiGet, apiPost } from '../api/client';
import {
    ArrowLeft, Mail, Phone, Calendar, FileText, Award,
    Clock, TrendingUp, Activity, Download, Share2, Loader2, AlertCircle,
    Brain, Target, Lightbulb, Zap, ShieldAlert, ListChecks, BarChart3
} from 'lucide-react';

const CandidateOverview = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [candidate, setCandidate] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [predictions, setPredictions] = useState({ interviewSuccess: null, behavioral: null });
    const [atsScore, setAtsScore] = useState(null);
    const [predictionsLoading, setPredictionsLoading] = useState(false);

    useEffect(() => {
        async function fetchCandidate() {
            setLoading(true);
            setError(null);
            try {
                // Fetch attempt details with skills
                const attemptRes = await apiGet(`/attempts/${id}`);
                const skillsRes = await apiGet(`/attempts/${id}/skills`).catch(() => ({ skills: [] }));
                let metricsRes = await apiGet(`/metrics/attempt/${id}`).catch(() => null);

                // Auto-compute metrics if missing and assessment is completed
                if (!metricsRes && (attemptRes.status === 'completed' || attemptRes.status === 'locked')) {
                    try {
                        metricsRes = await apiPost(`/metrics/attempt/${id}/compute`, { force_recompute: false });
                    } catch (err) {
                        console.error('Failed to auto-compute metrics:', err);
                    }
                }

                // Build timeline data from metrics if available
                let timelineData = [];
                let behavioralMetrics = {
                    avgHesitation: 0,
                    avgTimePerQuestion: 0,
                    avgDecisionChanges: 0,
                    idleTimeTotal: 0
                };

                if (metricsRes && metricsRes.per_task_metrics) {
                    // Extract timeline from per-task metrics
                    timelineData = metricsRes.per_task_metrics.map((task, index) => ({
                        task: `Q${index + 1}`,
                        hesitation: task.hesitation_seconds || 0,
                        timeSpent: task.time_spent_seconds || 0,
                        changes: task.decision_change_count || 0
                    }));

                    // Calculate averages for the summary cards
                    const taskCount = metricsRes.per_task_metrics.length;
                    if (taskCount > 0) {
                        behavioralMetrics = {
                            avgHesitation: metricsRes.global_metrics?.hesitation_time_seconds || 0,
                            avgTimePerQuestion: metricsRes.global_metrics?.total_time_seconds / taskCount || 0,
                            avgDecisionChanges: metricsRes.per_task_metrics.reduce((sum, t) => sum + (t.decision_change_count || 0), 0) / taskCount,
                            idleTimeTotal: metricsRes.global_metrics?.hesitation_time_seconds || 0
                        };
                    }
                }

                // Normalize data
                const candidateData = {
                    id: attemptRes.id || attemptRes._id || id,
                    name: attemptRes.candidate_info?.name || 'Unknown Candidate',
                    email: attemptRes.candidate_info?.email || '',
                    phone: attemptRes.candidate_info?.phone || 'N/A',
                    position: attemptRes.candidate_info?.position || 'Candidate',
                    status: attemptRes.status || 'pending',
                    avatar: (attemptRes.candidate_info?.name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(),
                    uploadDate: attemptRes.created_at ? new Date(attemptRes.created_at).toLocaleDateString() : 'N/A',
                    skills: skillsRes.skills || [],
                    behavioralMetrics,
                    timelineData,
                    currentQuestion: attemptRes.current_question || 0,
                    totalQuestions: attemptRes.total_questions || 0,
                    analysisResult: attemptRes.analysis_result || null,
                };
                setCandidate(candidateData);
            } catch (err) {
                console.error('Failed to fetch candidate:', err);
                setError(err.message || 'Failed to load candidate details');
            } finally {
                setLoading(false);
            }
        }
        fetchCandidate();
    }, [id]);

    // Fetch ML predictions + ATS score when candidate is completed
    useEffect(() => {
        const status = candidate?.status;
        const isCompleted = status === 'completed' || status === 'locked';
        if (!id || !isCompleted) {
            setPredictions({ interviewSuccess: null, behavioral: null });
            setAtsScore(null);
            return;
        }
        setPredictionsLoading(true);
        setAtsScore(null);
        Promise.allSettled([
            apiPost('predictions/interview-success', { attempt_id: id, include_resume: true }),
            apiGet(`predictions/behavioral/${id}`),
            apiGet(`resume/ats-by-attempt/${id}`),
        ]).then(([successRes, behavioralRes, atsRes]) => {
            setPredictions({
                interviewSuccess: successRes.status === 'fulfilled' ? successRes.value : null,
                behavioral: behavioralRes.status === 'fulfilled' ? behavioralRes.value : null,
            });
            if (atsRes.status === 'fulfilled') setAtsScore(atsRes.value);
        }).catch(() => {
            setPredictions({ interviewSuccess: null, behavioral: null });
            setAtsScore(null);
        }).finally(() => setPredictionsLoading(false));
    }, [id, candidate?.status]);

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
            case 'locked':
                return 'bg-green-500/20 text-green-400 border-green-500/50';
            case 'in_progress':
            case 'in-progress':
                return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
            case 'pending':
                return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
            default:
                return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
        }
    };

    if (loading) {
        return (
            <div className="flex-1 p-6 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-primary-400 animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Loading candidate details...</p>
                </div>
            </div>
        );
    }

    if (error || !candidate) {
        return (
            <div className="flex-1 p-6">
                <Navbar title="Candidate Not Found" />
                <div className="glass-card p-12 text-center animate-fade-in">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <h3 className="text-2xl font-bold text-white mb-3">
                        {error || 'Candidate not found'}
                    </h3>
                    <p className="text-gray-400 mb-6">
                        The candidate you're looking for doesn't exist or may have been removed.
                    </p>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="btn-gradient mt-4 transition-all hover:scale-105 active:scale-95"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const isCompleted = candidate.status === 'completed' || candidate.status === 'locked';
    const isInProgress = candidate.status === 'in_progress' || candidate.status === 'in-progress';

    return (
        <div className="flex-1 p-6">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={() => navigate(-1)}
                    className="p-2 glass-card hover:bg-white/10 transition-all rounded-lg"
                >
                    <ArrowLeft className="w-5 h-5 text-white" />
                </button>
                <div className="flex-1">
                    <h1 className="text-3xl font-bold text-white">{candidate.name}</h1>
                    <p className="text-gray-400">{candidate.position}</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="btn-outline flex items-center gap-2">
                        <Share2 className="w-4 h-4" />
                        Share
                    </button>
                    <button className="btn-gradient flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Export Report
                    </button>
                </div>
            </div>

            {/* Quick Info & Status */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
                <div className="glass-card p-6 text-center">
                    <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-3xl mb-4">
                        {candidate.avatar}
                    </div>
                    <span className={`inline-block px-4 py-2 rounded-full text-sm font-semibold border ${getStatusColor(candidate.status)}`}>
                        {candidate.status.toUpperCase().replace('_', ' ')}
                    </span>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Mail className="w-5 h-5 text-primary-400" />
                        <span className="text-gray-400 text-sm">Email</span>
                    </div>
                    <p className="text-white font-medium">{candidate.email || 'N/A'}</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Phone className="w-5 h-5 text-primary-400" />
                        <span className="text-gray-400 text-sm">Phone</span>
                    </div>
                    <p className="text-white font-medium">{candidate.phone}</p>
                </div>

                <div className="glass-card p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <Calendar className="w-5 h-5 text-primary-400" />
                        <span className="text-gray-400 text-sm">Created Date</span>
                    </div>
                    <p className="text-white font-medium">{candidate.uploadDate}</p>
                </div>
            </div>

            {isCompleted ? (
                <>
                    {/* Skills & Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        {candidate.skills && candidate.skills.length > 0 && (
                            <SkillRadarChart skills={candidate.skills} candidateName={candidate.name} />
                        )}

                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Behavioral Metrics Summary</h3>
                            <div className="space-y-4">
                                <div className="p-4 glass-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-400 text-sm">Avg Idle Time</span>
                                        <Clock className="w-4 h-4 text-yellow-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-gradient">{candidate.behavioralMetrics.avgHesitation || 0}s</p>
                                    <p className="text-xs text-gray-500 mt-1">Time before first interaction</p>
                                </div>

                                <div className="p-4 glass-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-400 text-sm">Avg Time per Question</span>
                                        <Activity className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-gradient">{candidate.behavioralMetrics.avgTimePerQuestion || 0}s</p>
                                    <p className="text-xs text-gray-500 mt-1">Total engagement time</p>
                                </div>

                                <div className="p-4 glass-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-400 text-sm">Avg Decision Changes</span>
                                        <TrendingUp className="w-4 h-4 text-purple-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-gradient">{candidate.behavioralMetrics.avgDecisionChanges || 0}</p>
                                    <p className="text-xs text-gray-500 mt-1">Answer modifications per question</p>
                                </div>

                                <div className="p-4 glass-card">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-400 text-sm">Total Idle Time</span>
                                        <Clock className="w-4 h-4 text-red-400" />
                                    </div>
                                    <p className="text-3xl font-bold text-gradient">{candidate.behavioralMetrics.idleTimeTotal || 0}s</p>
                                    <p className="text-xs text-gray-500 mt-1">Periods of inactivity</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Resume ATS — from resume only (first for clarity) */}
                    <div className="glass-card p-6 mb-6 border-l-4 border-teal-500/60 bg-gradient-to-br from-teal-500/5 to-transparent">
                        <div className="flex items-center gap-2 mb-3">
                            <FileText className="w-5 h-5 text-teal-400" />
                            <h3 className="text-base font-semibold text-white">Resume ATS score</h3>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-400 font-medium">From resume only</span>
                        </div>
                        {predictionsLoading ? (
                            <div className="flex items-center gap-2 text-gray-400">
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Calculating...</span>
                            </div>
                        ) : atsScore != null ? (
                            <div className="flex flex-wrap items-center gap-6">
                                <div className="flex items-center gap-4">
                                    <div className="relative w-16 h-16">
                                        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                                            <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-gray-700" />
                                            <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" strokeLinecap="round" className="text-teal-400"
                                                strokeDasharray={`${(Math.min(100, atsScore.ats_score || 0) / 100) * 264} 264`}
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <span className="text-xl font-bold text-teal-400">{Math.round(atsScore.ats_score || 0)}</span>
                                            <span className="text-[10px] text-gray-500">%</span>
                                        </div>
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-500">Formatting, sections, contact · Does not depend on assessment</p>
                                        {atsScore.breakdown && (atsScore.breakdown.formatting != null || atsScore.breakdown.sections != null) && (
                                            <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-2 text-[11px] text-gray-500">
                                                {atsScore.breakdown.formatting != null && <span>Format {atsScore.breakdown.formatting}%</span>}
                                                {atsScore.breakdown.sections != null && <span>Sections {atsScore.breakdown.sections}%</span>}
                                                {atsScore.breakdown.contact != null && <span>Contact {atsScore.breakdown.contact}%</span>}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm text-gray-500">No resume text for this candidate.</p>
                        )}
                    </div>

                    {/* ML Predictions — from assessment */}
                    <div className="glass-card p-6 mb-6">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-lg bg-primary-500/20 text-primary-400">
                                <BarChart3 className="w-5 h-5" />
                            </div>
                            <h3 className="text-lg font-semibold text-white">ML Predictions</h3>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary-500/20 text-primary-400 font-medium">From assessment</span>
                        </div>
                        {predictionsLoading ? (
                            <div className="flex items-center gap-2 text-gray-400">
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Loading...</span>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {predictions.interviewSuccess && !predictions.interviewSuccess.message && (
                                    <div className="p-4 rounded-xl border border-primary-500/30 bg-primary-500/5">
                                        <div className="text-xs font-medium text-gray-400 uppercase mb-1">Interview success probability</div>
                                        <p className="text-3xl font-bold text-primary-400">{predictions.interviewSuccess.probability}%</p>
                                        <p className="text-sm text-gray-500 mt-1">Confidence: {predictions.interviewSuccess.confidence}</p>
                                    </div>
                                )}
                                {predictions.behavioral && predictions.behavioral.predicted_traits?.length > 0 && (
                                    <div className="p-4 rounded-xl border border-gray-600/50 bg-white/5 md:col-span-2">
                                        <div className="text-xs font-medium text-gray-400 uppercase mb-2">Predicted behavioral traits</div>
                                        <ul className="space-y-1.5 text-sm text-gray-300">
                                            {predictions.behavioral.predicted_traits.map((t, i) => (
                                                <li key={i} className="flex items-center gap-2">
                                                    <span className="text-primary-400">•</span> {t}
                                                </li>
                                            ))}
                                        </ul>
                                        <p className="text-xs text-gray-500 mt-2">Confidence: {predictions.behavioral.confidence}</p>
                                    </div>
                                )}
                                {predictions.interviewSuccess?.message && !predictions.behavioral?.predicted_traits?.length && (
                                    <p className="text-sm text-gray-500 col-span-2">{predictions.interviewSuccess.message}</p>
                                )}
                                {!predictions.interviewSuccess && !predictions.behavioral?.predicted_traits?.length && (
                                    <p className="text-sm text-gray-500 col-span-2">Complete the assessment to see predictions.</p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Timeline Charts */}
                    {candidate.timelineData && candidate.timelineData.length > 0 && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                            <BehavioralLineChart
                                data={candidate.timelineData.slice(0, 10)}
                                dataKey="hesitation"
                                title="Idle Time Over Time"
                                color="#f59e0b"
                                yAxisLabel="Seconds"
                            />
                            <BehavioralLineChart
                                data={candidate.timelineData.slice(0, 10)}
                                dataKey="timeSpent"
                                title="Time Spent per Question"
                                color="#0ea5e9"
                                yAxisLabel="Seconds"
                            />
                            <BehavioralLineChart
                                data={candidate.timelineData.slice(0, 10)}
                                dataKey="changes"
                                title="Decision Changes"
                                color="#d946ef"
                                yAxisLabel="Changes"
                            />
                        </div>
                    )}

                    {/* AI Analysis Section */}
                    {candidate.analysisResult && (
                        <div className="glass-card p-8 mb-6 border-primary-500/30">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 rounded-xl bg-primary-500/20 text-primary-400">
                                    <Brain className="w-6 h-6" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-white">AI Candidate Analysis</h2>
                                    <p className="text-gray-400">Deep behavioral and technical evaluation</p>
                                </div>
                                <div className="ml-auto px-4 py-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-bold">
                                    VERDICT: {candidate.analysisResult.verdict?.toUpperCase()}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                                    <div className="flex items-center gap-2 mb-4 text-primary-400 font-semibold">
                                        <Target className="w-5 h-5" />
                                        Recommendation
                                    </div>
                                    <p className="text-gray-200 leading-relaxed">
                                        {candidate.analysisResult.recommendation}
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="p-5 rounded-2xl bg-green-500/10 border border-green-500/20">
                                        <div className="flex items-center gap-2 mb-3 text-green-400 font-semibold">
                                            <Zap className="w-4 h-4" />
                                            Key Strengths
                                        </div>
                                        <ul className="space-y-2">
                                            {candidate.analysisResult.strengths?.map((s, i) => (
                                                <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                                                    <span className="text-green-500 mt-1">•</span> {s}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div className="p-5 rounded-2xl bg-yellow-500/10 border border-yellow-500/20">
                                        <div className="flex items-center gap-2 mb-3 text-yellow-400 font-semibold">
                                            <Lightbulb className="w-4 h-4" />
                                            Areas to Improve
                                        </div>
                                        <ul className="space-y-2">
                                            {candidate.analysisResult.improvements?.map((s, i) => (
                                                <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                                                    <span className="text-yellow-500 mt-1">•</span> {s}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>

                            {candidate.analysisResult.per_question_analysis && candidate.analysisResult.per_question_analysis.length > 0 && (
                                <div className="border-t border-white/10 pt-8">
                                    <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                        <ListChecks className="w-5 h-5 text-indigo-400" />
                                        Question-by-Question Analysis
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {candidate.analysisResult.per_question_analysis.map((q, i) => {
                                            // Fallback score calculation if backend doesn't provide it
                                            let displayScore = q.score;
                                            if (displayScore === undefined || displayScore === null) {
                                                const base = q.correctness === 'Correct' ? 70 : 30;
                                                const bonus = q.analytical_depth === 'High' ? 30 : q.analytical_depth === 'Medium' ? 15 : 0;
                                                displayScore = base + bonus;
                                            }

                                            return (
                                                <div key={i} className="p-5 rounded-xl bg-white/5 border border-white/5 hover:border-white/20 transition-all">
                                                    <div className="flex items-center justify-between mb-3 text-sm">
                                                        <span className="text-indigo-400 font-bold">Q{i + 1} Assessment</span>
                                                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${displayScore >= 70 ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                                                            SCORE: {displayScore}%
                                                        </span>
                                                    </div>
                                                    <p className="text-white font-medium text-sm mb-2">{q.analysis || q.reasoning_feedback}</p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {q.cognitive_traits?.map((trait, ti) => (
                                                            <span key={ti} className="px-2 py-0.5 rounded-full bg-white/10 text-gray-400 text-[10px]">
                                                                {trait}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            ) : isInProgress ? (
                <div className="glass-card p-12 text-center">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
                        <Activity className="w-10 h-10 text-yellow-400 animate-pulse" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">Assessment In Progress</h3>
                    <p className="text-gray-400 mb-6">
                        {candidate.name} is currently taking the assessment.
                        {candidate.totalQuestions > 0 && (
                            <> Progress: {candidate.currentQuestion}/{candidate.totalQuestions} questions</>
                        )}
                    </p>
                    <button
                        onClick={() => navigate('/live-assessment')}
                        className="btn-gradient"
                    >
                        Monitor Live
                    </button>
                </div>
            ) : (
                <div className="glass-card p-12 text-center">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-700/50 flex items-center justify-center">
                        <Clock className="w-10 h-10 text-gray-500" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">Assessment Pending</h3>
                    <p className="text-gray-400 mb-6">
                        {candidate.name} has been added but hasn't started the assessment yet.
                    </p>
                    <button className="btn-gradient">
                        Send Assessment Link
                    </button>
                </div>
            )}
        </div >
    );
};

export default CandidateOverview;

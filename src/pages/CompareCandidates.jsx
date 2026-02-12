import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeftRight, Download, Loader2, Users, AlertCircle, CalendarDays, Plus, X, UserPlus, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { apiGet } from '../api/client';
import TopNav from '../components/layout/TopNav';
import ReportAssistant from '../components/chat/ReportAssistant';

// Slot colors — cycles through these for unlimited slots
const SLOT_COLORS = [
    { name: 'A', bg: 'from-blue-500 to-indigo-600', accent: '#3b82f6', light: 'blue', ring: 'ring-blue-300 dark:ring-blue-700', border: 'border-blue-400 dark:border-blue-600', bgFill: 'bg-blue-50/60 dark:bg-blue-900/15', badge: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400', pillBg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800', pillText: 'text-blue-700 dark:text-blue-300', removeHover: 'text-blue-400 hover:text-blue-600', btnBg: 'bg-blue-500 hover:bg-blue-600', removeBtnBg: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50' },
    { name: 'B', bg: 'from-orange-500 to-red-500', accent: '#f97316', light: 'orange', ring: 'ring-orange-300 dark:ring-orange-700', border: 'border-orange-400 dark:border-orange-600', bgFill: 'bg-orange-50/60 dark:bg-orange-900/15', badge: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400', pillBg: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800', pillText: 'text-orange-700 dark:text-orange-300', removeHover: 'text-orange-400 hover:text-orange-600', btnBg: 'bg-orange-500 hover:bg-orange-600', removeBtnBg: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50' },
    { name: 'C', bg: 'from-emerald-500 to-teal-600', accent: '#10b981', light: 'emerald', ring: 'ring-emerald-300 dark:ring-emerald-700', border: 'border-emerald-400 dark:border-emerald-600', bgFill: 'bg-emerald-50/60 dark:bg-emerald-900/15', badge: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400', pillBg: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800', pillText: 'text-emerald-700 dark:text-emerald-300', removeHover: 'text-emerald-400 hover:text-emerald-600', btnBg: 'bg-emerald-500 hover:bg-emerald-600', removeBtnBg: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-200 dark:hover:bg-emerald-900/50' },
    { name: 'D', bg: 'from-purple-500 to-violet-600', accent: '#8b5cf6', light: 'purple', ring: 'ring-purple-300 dark:ring-purple-700', border: 'border-purple-400 dark:border-purple-600', bgFill: 'bg-purple-50/60 dark:bg-purple-900/15', badge: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400', pillBg: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800', pillText: 'text-purple-700 dark:text-purple-300', removeHover: 'text-purple-400 hover:text-purple-600', btnBg: 'bg-purple-500 hover:bg-purple-600', removeBtnBg: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50' },
    { name: 'E', bg: 'from-pink-500 to-rose-600', accent: '#ec4899', light: 'pink', ring: 'ring-pink-300 dark:ring-pink-700', border: 'border-pink-400 dark:border-pink-600', bgFill: 'bg-pink-50/60 dark:bg-pink-900/15', badge: 'bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400', pillBg: 'bg-pink-50 dark:bg-pink-900/20 border-pink-200 dark:border-pink-800', pillText: 'text-pink-700 dark:text-pink-300', removeHover: 'text-pink-400 hover:text-pink-600', btnBg: 'bg-pink-500 hover:bg-pink-600', removeBtnBg: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 hover:bg-pink-200 dark:hover:bg-pink-900/50' },
];

const getSlotColor = (index) => SLOT_COLORS[index % SLOT_COLORS.length];
const getSlotLabel = (index) => String.fromCharCode(65 + index); // A, B, C, D...

const CompareCandidates = () => {
    const navigate = useNavigate();

    // ── Date picker ──
    const todayStr = new Date().toISOString().split('T')[0];
    const [selectedDate, setSelectedDate] = useState(todayStr);

    // ── Candidate pool (filtered by date) ──
    const [candidates, setCandidates] = useState([]);
    const [loadingPool, setLoadingPool] = useState(true);
    const [poolError, setPoolError] = useState(null);

    // ── Dynamic comparison slots ──
    // Each slot: { id, data: null | { ...candidateDetails } }
    const [slots, setSlots] = useState([]);
    const [loadingSlots, setLoadingSlots] = useState({});

    // ── Fetch completed candidates for selected date ──
    useEffect(() => {
        async function fetchPool() {
            setLoadingPool(true);
            setPoolError(null);
            try {
                const res = await apiGet(`/attempts?page_size=50&status=completed&completed_date=${selectedDate}`);
                const list = (res.candidates || res.attempts || []).map(c => ({
                    id: c.id || c._id || c.attempt_id,
                    name: c.name || c.candidate_info?.name || c.candidate_name || 'Unknown',
                    position: c.position || c.candidate_info?.position || 'Candidate',
                    email: c.email || c.candidate_info?.email || c.candidate_email || '',
                    initials: (c.name || c.candidate_info?.name || c.candidate_name || 'U')
                        .split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(),
                }));
                setCandidates(list);
            } catch (err) {
                console.error('Failed to fetch candidates:', err);
                setPoolError(err.message || 'Failed to load candidates');
            } finally {
                setLoadingPool(false);
            }
        }
        fetchPool();
    }, [selectedDate]);

    // Reset slots when date changes
    useEffect(() => {
        setSlots([]);
        setLoadingSlots({});
    }, [selectedDate]);

    // ── Fetch live-assessment stats for a candidate ──
    const fetchStatsForSlot = useCallback(async (candidateId, slotIndex) => {
        setLoadingSlots(prev => ({ ...prev, [slotIndex]: true }));
        try {
            const statsRes = await apiGet(`/live-assessment/${candidateId}/stats`);
            const candidate = candidates.find(c => c.id === candidateId);

            // Build skill data from live-assessment skill_profile
            const sp = statsRes.skill_profile || {};
            const skills = [
                { name: 'Task Completion', score: sp.task_completion || sp.problem_solving || 0 },
                { name: 'Selection Speed', score: sp.selection_speed || sp.decision_speed || 0 },
                { name: 'Deliberation', score: sp.deliberation_pattern || sp.analytical_thinking || 0 },
                { name: 'Option Exploration', score: sp.option_exploration || sp.creativity || 0 },
                { name: 'Risk Preference', score: sp.risk_preference || sp.risk_assessment || 0 },
            ].filter(s => s.score > 0);

            const data = {
                id: candidateId,
                name: statsRes.candidate?.name || candidate?.name || 'Unknown',
                position: statsRes.candidate?.position || candidate?.position || 'Candidate',
                initials: statsRes.candidate?.avatar || candidate?.initials || 'U',
                skills,
                overallFit: statsRes.overall_fit || null,
                behavioralSummary: statsRes.behavioral_summary || null,
                roleFit: statsRes.role_fit || null,
                resumeComparison: statsRes.resume_comparison || null,
                metrics: statsRes.metrics || null,
                progress: statsRes.progress || null,
            };

            setSlots(prev => prev.map((s, i) => i === slotIndex ? { ...s, data } : s));
        } catch (err) {
            console.error(`Failed to fetch stats for ${candidateId}:`, err);
            // Fallback: still show basic info
            const candidate = candidates.find(c => c.id === candidateId);
            setSlots(prev => prev.map((s, i) => i === slotIndex ? { ...s, data: { id: candidateId, name: candidate?.name || 'Unknown', position: candidate?.position || 'Candidate', initials: candidate?.initials || 'U', skills: [], overallFit: null, behavioralSummary: null, roleFit: null, resumeComparison: null, metrics: null, progress: null } } : s));
        } finally {
            setLoadingSlots(prev => ({ ...prev, [slotIndex]: false }));
        }
    }, [candidates]);

    // ── Slot management ──
    const addCandidateToSlot = (candidateId) => {
        const newIndex = slots.length;
        setSlots(prev => [...prev, { id: candidateId, data: null }]);
        fetchStatsForSlot(candidateId, newIndex);
    };

    const removeSlot = (index) => {
        setSlots(prev => prev.filter((_, i) => i !== index));
    };

    const isInAnySlot = (candidateId) => slots.some(s => s.id === candidateId);
    const getSlotIndex = (candidateId) => slots.findIndex(s => s.id === candidateId);

    // ── Helpers ──
    const formatDisplayDate = (dateStr) => {
        const d = new Date(dateStr + 'T00:00:00');
        return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    };

    const shiftDate = (days) => {
        const d = new Date(selectedDate + 'T00:00:00');
        d.setDate(d.getDate() + days);
        setSelectedDate(d.toISOString().split('T')[0]);
    };

    const getRadarData = () => {
        // Merge all slots into one radar chart dataset
        const dimensions = ['Task Completion', 'Selection Speed', 'Deliberation', 'Option Exploration', 'Risk Preference'];
        return dimensions.map(dim => {
            const entry = { subject: dim };
            slots.forEach((slot, i) => {
                if (slot.data) {
                    const sk = slot.data.skills?.find(s => s.name === dim);
                    entry[`slot_${i}`] = sk ? Math.round(sk.score * 100) / 100 : 0;
                }
            });
            return entry;
        });
    };

    const getGradeColor = (grade) => {
        if (!grade) return 'text-gray-400';
        if (grade === 'A+' || grade === 'A') return 'text-emerald-500';
        if (grade === 'B+' || grade === 'B') return 'text-blue-500';
        if (grade === 'C+' || grade === 'C') return 'text-yellow-500';
        return 'text-red-500';
    };

    // ── Render ──
    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black transition-colors duration-300">
            <TopNav />

            <div className="p-8 max-w-[1400px] mx-auto">
                <div className="max-w-7xl mx-auto">

                    {/* ── Header ── */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
                            Compare <span className="text-gray-600 dark:text-gray-400">Candidates</span>
                        </h1>
                        <p className="text-gray-600 dark:text-gray-400">
                            Select a date, then add candidates to comparison slots. Add as many as you need.
                        </p>
                    </div>

                    {/* ── Date Picker + Candidate Pool ── */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6 mb-6 transition-colors duration-300">

                        {/* Date selector row */}
                        <div className="flex items-center gap-4 mb-5 flex-wrap">
                            <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                                <CalendarDays className="w-5 h-5 text-blue-500" />
                                <span className="font-semibold text-sm">Assessment Date</span>
                            </div>

                            <div className="flex items-center gap-1">
                                <button onClick={() => shiftDate(-1)} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500 dark:text-gray-400 transition-colors" title="Previous day">
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <input
                                    type="date"
                                    value={selectedDate}
                                    max={todayStr}
                                    onChange={(e) => setSelectedDate(e.target.value)}
                                    className="bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200 cursor-pointer"
                                />
                                <button onClick={() => shiftDate(1)} disabled={selectedDate >= todayStr} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500 dark:text-gray-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors" title="Next day">
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>

                            <span className="text-xs text-gray-500 dark:text-gray-500">
                                {formatDisplayDate(selectedDate)}
                                {selectedDate === todayStr && <span className="ml-1.5 px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold uppercase tracking-wide">Today</span>}
                            </span>

                            {/* Active slot pills */}
                            <div className="ml-auto flex items-center gap-2 flex-wrap">
                                {slots.map((slot, i) => {
                                    const color = getSlotColor(i);
                                    return (
                                        <div key={i} className={`flex items-center gap-2 ${color.pillBg} border rounded-xl px-3 py-1.5 transition-all duration-200`}>
                                            <div className={`w-6 h-6 rounded-full bg-gradient-to-br ${color.bg} flex items-center justify-center`}>
                                                <span className="text-white text-[10px] font-bold">{slot.data?.initials || '...'}</span>
                                            </div>
                                            <span className={`text-xs font-semibold ${color.pillText}`}>Slot {getSlotLabel(i)}</span>
                                            <button onClick={() => removeSlot(i)} className={`${color.removeHover} transition-colors`}><X className="w-3.5 h-3.5" /></button>
                                        </div>
                                    );
                                })}
                                {slots.length > 0 && (
                                    <span className="text-xs text-gray-400 dark:text-gray-500">{slots.length} selected</span>
                                )}
                            </div>
                        </div>

                        {/* Candidate pool */}
                        {loadingPool ? (
                            <div className="flex items-center justify-center py-10">
                                <Loader2 className="w-7 h-7 text-blue-500 animate-spin" />
                                <span className="ml-3 text-gray-500 dark:text-gray-400 text-sm">Loading candidates...</span>
                            </div>
                        ) : poolError ? (
                            <div className="flex items-center gap-3 py-6 justify-center">
                                <AlertCircle className="w-5 h-5 text-red-500" />
                                <span className="text-red-600 dark:text-red-400 text-sm">{poolError}</span>
                            </div>
                        ) : candidates.length === 0 ? (
                            <div className="text-center py-10 animate-fade-in">
                                <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-neutral-800 flex items-center justify-center">
                                    <Users className="w-7 h-7 text-gray-400 dark:text-gray-500" />
                                </div>
                                <p className="font-semibold text-gray-700 dark:text-gray-300 mb-1">No completed assessments</p>
                                <p className="text-sm text-gray-500 dark:text-gray-500">
                                    No candidates completed their assessment on {formatDisplayDate(selectedDate)}.
                                    <br />Try selecting a different date.
                                </p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                {candidates.map(c => {
                                    const inSlot = isInAnySlot(c.id);
                                    const slotIdx = getSlotIndex(c.id);
                                    const color = inSlot ? getSlotColor(slotIdx) : null;

                                    return (
                                        <div
                                            key={c.id}
                                            className={`relative rounded-xl border p-4 transition-all duration-200 ${inSlot
                                                ? `${color.border} ${color.bgFill} ring-2 ${color.ring}`
                                                : 'border-gray-200 dark:border-neutral-700 bg-gray-50/50 dark:bg-neutral-900/50 hover:border-gray-300 dark:hover:border-neutral-600 hover:shadow-md'
                                                }`}
                                        >
                                            {inSlot && (
                                                <span className={`absolute -top-2 -right-2 w-6 h-6 rounded-full bg-gradient-to-br ${color.bg} text-white text-[10px] font-bold flex items-center justify-center shadow-md`}>
                                                    {getSlotLabel(slotIdx)}
                                                </span>
                                            )}

                                            <div className="flex items-center gap-3 mb-3">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${inSlot ? `bg-gradient-to-br ${color.bg}` : 'bg-gradient-to-br from-gray-400 to-gray-500 dark:from-gray-600 dark:to-gray-700'
                                                    }`}>
                                                    <span className="text-white text-xs font-bold">{c.initials}</span>
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="font-semibold text-sm text-gray-800 dark:text-white truncate">{c.name}</p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{c.position}</p>
                                                </div>
                                            </div>

                                            {inSlot ? (
                                                <button
                                                    onClick={() => removeSlot(slotIdx)}
                                                    className={`w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${color.removeBtnBg}`}
                                                >
                                                    <X className="w-3 h-3" /> Remove from Slot {getSlotLabel(slotIdx)}
                                                </button>
                                            ) : (
                                                <button
                                                    onClick={() => addCandidateToSlot(c.id)}
                                                    className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-sm"
                                                >
                                                    <Plus className="w-3.5 h-3.5" /> Add to Slot {getSlotLabel(slots.length)}
                                                </button>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* ── Comparison Section ── */}
                    {slots.length >= 2 ? (
                        <>
                            {/* ── Combined Radar Chart ── */}
                            <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6 mb-6 transition-colors duration-300">
                                <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-4">Skill Profile Comparison</h2>
                                <ResponsiveContainer width="100%" height={320}>
                                    <RadarChart data={getRadarData()}>
                                        <PolarGrid stroke="#e5e7eb" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} />
                                        {slots.map((slot, i) => (
                                            <Radar
                                                key={i}
                                                name={slot.data?.name || `Slot ${getSlotLabel(i)}`}
                                                dataKey={`slot_${i}`}
                                                stroke={getSlotColor(i).accent}
                                                fill={getSlotColor(i).accent}
                                                fillOpacity={0.15}
                                                strokeWidth={2}
                                            />
                                        ))}
                                        <Legend />
                                        <Tooltip />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* ── Individual Report Cards ── */}
                            <div className={`grid gap-6 mb-6 ${slots.length === 2 ? 'grid-cols-2' : slots.length === 3 ? 'grid-cols-3' : 'grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'}`}>
                                {slots.map((slot, i) => {
                                    const color = getSlotColor(i);
                                    const d = slot.data;
                                    const isLoading = loadingSlots[i];

                                    return (
                                        <div key={i} className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-5 transition-colors duration-300">
                                            {isLoading || !d ? (
                                                <div className="h-[300px] flex items-center justify-center">
                                                    <Loader2 className="w-8 h-8 animate-spin" style={{ color: color.accent }} />
                                                </div>
                                            ) : (
                                                <>
                                                    {/* Header */}
                                                    <div className="flex items-center gap-3 mb-4">
                                                        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${color.bg} flex items-center justify-center flex-shrink-0`}>
                                                            <span className="text-white text-lg font-bold">{d.initials}</span>
                                                        </div>
                                                        <div className="min-w-0 flex-1">
                                                            <h3 className="font-bold text-gray-800 dark:text-white truncate">{d.name}</h3>
                                                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{d.position}</p>
                                                        </div>
                                                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${color.badge}`}>Slot {getSlotLabel(i)}</span>
                                                    </div>

                                                    {/* Overall Fit Score */}
                                                    {d.overallFit && (
                                                        <div className="mb-4 p-3 rounded-xl bg-gray-50 dark:bg-neutral-900 border border-gray-100 dark:border-neutral-800">
                                                            <div className="flex items-center justify-between mb-1.5">
                                                                <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">Overall Fit Score</span>
                                                                <span className={`text-lg font-black ${getGradeColor(d.overallFit.grade)}`}>
                                                                    {d.overallFit.grade || '—'}
                                                                </span>
                                                            </div>
                                                            <div className="w-full bg-gray-200 dark:bg-neutral-700 rounded-full h-2">
                                                                <div
                                                                    className="h-2 rounded-full transition-all duration-500"
                                                                    style={{
                                                                        width: `${Math.min(100, d.overallFit.score || 0)}%`,
                                                                        backgroundColor: color.accent,
                                                                    }}
                                                                />
                                                            </div>
                                                            <p className="text-[11px] text-gray-500 dark:text-gray-500 mt-1">
                                                                {d.overallFit.score || 0}% — {d.overallFit.grade_label || 'N/A'}
                                                            </p>
                                                        </div>
                                                    )}

                                                    {/* Behavioral Summary */}
                                                    {d.behavioralSummary && (
                                                        <div className="mb-4 space-y-2">
                                                            <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Behavioral Insights</h4>
                                                            {d.behavioralSummary.approach && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[10px] font-medium text-gray-500 dark:text-gray-500 w-20 flex-shrink-0">Approach</span>
                                                                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">{d.behavioralSummary.approach}</span>
                                                                </div>
                                                            )}
                                                            {d.behavioralSummary.decision_style && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[10px] font-medium text-gray-500 dark:text-gray-500 w-20 flex-shrink-0">Decision</span>
                                                                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">{d.behavioralSummary.decision_style}</span>
                                                                </div>
                                                            )}
                                                            {d.behavioralSummary.strength && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[10px] font-medium text-gray-500 dark:text-gray-500 w-20 flex-shrink-0">Strength</span>
                                                                    <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{d.behavioralSummary.strength}</span>
                                                                </div>
                                                            )}
                                                            {d.behavioralSummary.improvement_area && (
                                                                <div className="flex items-center gap-2">
                                                                    <span className="text-[10px] font-medium text-gray-500 dark:text-gray-500 w-20 flex-shrink-0">Improve</span>
                                                                    <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">{d.behavioralSummary.improvement_area}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Role Fit */}
                                                    {d.roleFit && d.roleFit.recommendation && (
                                                        <div className="mb-3 p-2.5 rounded-lg border border-gray-100 dark:border-neutral-800 bg-gray-50/50 dark:bg-neutral-900/50">
                                                            <span className="text-[10px] font-medium text-gray-500 dark:text-gray-500">Recommendation</span>
                                                            <p className="text-xs font-bold text-gray-700 dark:text-gray-300">{d.roleFit.recommendation}</p>
                                                        </div>
                                                    )}

                                                    {/* Key Metrics */}
                                                    {d.metrics && (
                                                        <div className="grid grid-cols-2 gap-2 mt-3">
                                                            <div className="text-center p-2 rounded-lg bg-gray-50 dark:bg-neutral-900">
                                                                <p className="text-lg font-black text-gray-800 dark:text-white">{d.metrics.avg_response_time || 0}s</p>
                                                                <p className="text-[10px] text-gray-500 dark:text-gray-500">Avg Response</p>
                                                            </div>
                                                            <div className="text-center p-2 rounded-lg bg-gray-50 dark:bg-neutral-900">
                                                                <p className="text-lg font-black text-gray-800 dark:text-white">{d.metrics.decision_firmness || 0}%</p>
                                                                <p className="text-[10px] text-gray-500 dark:text-gray-500">Decision Firmness</p>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Remove button */}
                                                    <button
                                                        onClick={() => removeSlot(i)}
                                                        className="w-full mt-4 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium text-gray-500 dark:text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200 border border-transparent hover:border-red-200 dark:hover:border-red-800"
                                                    >
                                                        <Trash2 className="w-3 h-3" /> Remove
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Download Report */}
                            <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6 transition-colors duration-300">
                                <div className="flex justify-end">
                                    <button className="bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white font-semibold py-3 px-8 rounded-xl transition-all shadow-md flex items-center gap-2">
                                        <Download className="w-5 h-5" />
                                        Download Comparison Report
                                    </button>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-12 text-center transition-colors duration-300 animate-fade-in">
                            <div className="w-16 h-16 mx-auto mb-5 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 flex items-center justify-center">
                                <UserPlus className="w-8 h-8 text-blue-500 dark:text-blue-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
                                {slots.length === 0
                                    ? 'Select Candidates to Compare'
                                    : `Add ${2 - slots.length} more candidate${2 - slots.length > 1 ? 's' : ''} to start comparing`}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                                Pick a date above and click <strong>Add to Slot</strong> on candidate cards. You can compare 2 or more candidates at once.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <ReportAssistant pageContext="compare" />
        </div>
    );
};

export default CompareCandidates;
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import StatCard from '../components/cards/StatCard';
import { apiGet } from '../api/client';
import { Users, Activity, TrendingUp, Award, Clock, CheckCircle, Upload, GitCompare, Loader2, AlertCircle, ArrowRight, BarChart3 } from 'lucide-react';

const RecruiterDashboard = () => {
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [activity, setActivity] = useState([]);
    const [topCandidates, setTopCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchDashboardData() {
            setLoading(true);
            setError(null);
            try {
                const [statsRes, activityRes, candidatesRes] = await Promise.all([
                    apiGet('/dashboard/stats'),
                    apiGet('/dashboard/activity?limit=5'),
                    apiGet('/candidates?page=1&page_size=3&status=completed').catch(() => ({ candidates: [] }))
                ]);
                setStats(statsRes);
                setActivity(activityRes.activities || []);
                setTopCandidates(candidatesRes.candidates || []);
            } catch (err) {
                console.error('Dashboard fetch error:', err);
                setError(err.message || 'Failed to load dashboard data');
            } finally {
                setLoading(false);
            }
        }
        fetchDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="flex-1 p-6 flex items-center justify-center" role="status" aria-label="Loading dashboard">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-primary-400 animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex-1 p-6">
                <Navbar title="Dashboard" subtitle="Welcome back!" />
                <div className="glass-card p-8 text-center animate-fade-in" role="alert">
                    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-white text-lg mb-2">Failed to load dashboard</p>
                    <p className="text-gray-400 mb-6">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="btn-primary transition-all hover:scale-105 active:scale-95"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    const getStatusBadge = (type) => {
        const badges = {
            success: { label: 'Completed', className: 'bg-green-500/20 text-green-400 border border-green-500/30' },
            info: { label: 'In Progress', className: 'bg-blue-500/20 text-blue-400 border border-blue-500/30' },
            warning: { label: 'Pending', className: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' },
        };
        return badges[type] || badges.info;
    };

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return '';
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return timestamp;
        }
    };

    return (
        <main className="flex-1 p-6 space-y-8" aria-label="Recruiter Dashboard">
            {/* Page Header */}
            <Navbar
                title="Dashboard"
                subtitle="Welcome back! Here's what's happening with your candidates today."
            />

            {/* ──────────────────────────────────────────────────────── */}
            {/* SECTION 1: Overview Statistics                          */}
            {/* ──────────────────────────────────────────────────────── */}
            <section aria-labelledby="stats-heading">
                <h2 id="stats-heading" className="text-lg font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-primary-400" />
                    Overview
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" role="list" aria-label="Dashboard statistics">
                    <div role="listitem">
                        <StatCard
                            icon={Users}
                            label="Total Candidates"
                            value={stats?.total_candidates || 0}
                            color="primary"
                        />
                    </div>
                    <div role="listitem">
                        <StatCard
                            icon={Activity}
                            label="Active Assessments"
                            value={stats?.active_assessments || 0}
                            color="warning"
                        />
                    </div>
                    <div role="listitem">
                        <StatCard
                            icon={CheckCircle}
                            label="Completed Today"
                            value={stats?.completed_today || 0}
                            color="success"
                        />
                    </div>
                    <div role="listitem">
                        <StatCard
                            icon={Award}
                            label="Completion Rate"
                            value={`${stats?.completion_rate || 0}%`}
                            color="secondary"
                        />
                    </div>
                </div>
            </section>

            {/* ──────────────────────────────────────────────────────── */}
            {/* SECTION 2: Quick Actions                                */}
            {/* ──────────────────────────────────────────────────────── */}
            <section aria-labelledby="actions-heading">
                <h2 id="actions-heading" className="text-lg font-semibold text-gray-300 uppercase tracking-wider mb-4">
                    Quick Actions
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4" role="list" aria-label="Quick action buttons">
                    <button
                        role="listitem"
                        onClick={() => navigate('/upload-resume')}
                        className="glass-card-hover p-6 text-left group relative overflow-hidden"
                        aria-label="Upload New Resume — Add a new candidate and generate assessment"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-primary-500/20 text-primary-400 group-hover:bg-primary-500/30 group-hover:scale-110 transition-all duration-300">
                                    <Upload className="w-6 h-6" />
                                </div>
                                <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-primary-400 group-hover:translate-x-1 transition-all duration-300" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">Upload New Resume</h3>
                            <p className="text-sm text-gray-400 leading-relaxed">Add a new candidate and generate a personalized assessment</p>
                        </div>
                    </button>

                    <button
                        role="listitem"
                        onClick={() => navigate('/live-assessment')}
                        className="glass-card-hover p-6 text-left group relative overflow-hidden"
                        aria-label="Monitor Live Assessments — Track candidates in real-time"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-green-500/20 text-green-400 group-hover:bg-green-500/30 group-hover:scale-110 transition-all duration-300">
                                    <Activity className="w-6 h-6" />
                                </div>
                                <div className="flex items-center gap-2">
                                    {stats?.active_assessments > 0 && (
                                        <span className="px-2.5 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-bold border border-green-500/30 animate-pulse">
                                            {stats.active_assessments} LIVE
                                        </span>
                                    )}
                                    <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-green-400 group-hover:translate-x-1 transition-all duration-300" />
                                </div>
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">Monitor Live Assessments</h3>
                            <p className="text-sm text-gray-400 leading-relaxed">Watch candidates take assessments in real-time</p>
                        </div>
                    </button>

                    <button
                        role="listitem"
                        onClick={() => navigate('/compare-candidates')}
                        className="glass-card-hover p-6 text-left group relative overflow-hidden"
                        aria-label="Compare Candidates — Analyze side-by-side behavioral comparisons"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-secondary-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        <div className="relative">
                            <div className="flex items-center justify-between mb-4">
                                <div className="p-3 rounded-xl bg-secondary-500/20 text-secondary-400 group-hover:bg-secondary-500/30 group-hover:scale-110 transition-all duration-300">
                                    <GitCompare className="w-6 h-6" />
                                </div>
                                <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-secondary-400 group-hover:translate-x-1 transition-all duration-300" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">Compare Candidates</h3>
                            <p className="text-sm text-gray-400 leading-relaxed">Analyze side-by-side behavioral comparisons</p>
                        </div>
                    </button>
                </div>
            </section>

            {/* ──────────────────────────────────────────────────────── */}
            {/* SECTION 3: Activity & Top Performers                    */}
            {/* ──────────────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Activity */}
                <section className="lg:col-span-2" aria-labelledby="activity-heading">
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-5">
                            <h2 id="activity-heading" className="text-xl font-semibold text-white flex items-center gap-2">
                                <Clock className="w-5 h-5 text-gray-400" />
                                Recent Activity
                            </h2>
                            <span className="text-xs text-gray-500 uppercase tracking-wider">Last 5 events</span>
                        </div>
                        {activity.length === 0 ? (
                            <div className="text-center py-12 text-gray-400">
                                <Clock className="w-14 h-14 mx-auto mb-4 opacity-30" />
                                <p className="text-lg font-medium text-gray-500">No recent activity</p>
                                <p className="text-sm text-gray-600 mt-1">Activity will appear here once candidates start assessments</p>
                            </div>
                        ) : (
                            <div className="space-y-2" role="list" aria-label="Recent activity log">
                                {activity.map((item) => {
                                    const badge = getStatusBadge(item.type);
                                    return (
                                        <article
                                            key={item.id}
                                            role="listitem"
                                            className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.05] hover:border-white/[0.1] transition-all duration-200 cursor-pointer group"
                                            aria-label={`${item.candidate_name} — ${item.action}`}
                                        >
                                            <div className="flex items-center gap-4">
                                                {/* Avatar */}
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${item.type === 'success'
                                                        ? 'bg-gradient-to-br from-green-500/30 to-emerald-600/30 text-green-300 border border-green-500/20'
                                                        : 'bg-gradient-to-br from-blue-500/30 to-indigo-600/30 text-blue-300 border border-blue-500/20'
                                                    }`}>
                                                    {(item.candidate_name || 'C').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                                                </div>

                                                <div>
                                                    <p className="text-white font-medium leading-tight">{item.candidate_name}</p>
                                                    <p className="text-sm text-gray-400 mt-0.5">{item.action}</p>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-3 shrink-0">
                                                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${badge.className}`}>
                                                    {badge.label}
                                                </span>
                                                <span className="text-xs text-gray-500 min-w-[50px] text-right">
                                                    {formatTimestamp(item.timestamp)}
                                                </span>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </section>

                {/* Top Performers */}
                <section aria-labelledby="performers-heading">
                    <div className="glass-card p-6 h-full flex flex-col">
                        <div className="flex items-center justify-between mb-5">
                            <h2 id="performers-heading" className="text-lg font-semibold text-white flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-green-400" />
                                Top Performers
                            </h2>
                            <Award className="w-5 h-5 text-yellow-400/50" />
                        </div>
                        {topCandidates.length === 0 ? (
                            <div className="text-center py-12 text-gray-400 flex-1 flex flex-col items-center justify-center">
                                <Users className="w-14 h-14 mx-auto mb-4 opacity-30" />
                                <p className="text-lg font-medium text-gray-500">No results yet</p>
                                <p className="text-sm text-gray-600 mt-1">Completed assessments will rank here</p>
                            </div>
                        ) : (
                            <div className="space-y-3 flex-1" role="list" aria-label="Top performing candidates">
                                {topCandidates.map((candidate, index) => {
                                    const rankColors = [
                                        'from-yellow-500/30 to-amber-600/30 text-yellow-300 border-yellow-500/30',
                                        'from-gray-400/20 to-slate-500/20 text-gray-300 border-gray-400/20',
                                        'from-orange-700/20 to-amber-800/20 text-orange-300 border-orange-500/20',
                                    ];
                                    return (
                                        <article
                                            key={candidate.id || candidate._id}
                                            role="listitem"
                                            className="flex items-center gap-3 p-3.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.05] hover:border-white/[0.1] transition-all duration-200 cursor-pointer group"
                                            onClick={() => navigate(`/candidate/${candidate.attempt_id || candidate.id}`)}
                                            aria-label={`Rank ${index + 1}: ${candidate.name || candidate.candidate_info?.name} — ${candidate.position || candidate.candidate_info?.position || 'Candidate'}`}
                                        >
                                            {/* Rank Badge */}
                                            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${rankColors[index] || rankColors[2]} flex items-center justify-center text-sm font-bold border shrink-0`}>
                                                {index + 1}
                                            </div>
                                            {/* Avatar */}
                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-semibold text-sm shrink-0 group-hover:scale-105 transition-transform duration-200">
                                                {(candidate.name || candidate.candidate_info?.name || 'C').split(' ').map(n => n[0]).join('').slice(0, 2)}
                                            </div>
                                            {/* Details */}
                                            <div className="flex-1 min-w-0">
                                                <p className="text-white font-medium text-sm truncate">{candidate.name || candidate.candidate_info?.name}</p>
                                                <p className="text-xs text-gray-400 truncate">{candidate.position || candidate.candidate_info?.position || 'Candidate'}</p>
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-primary-400 group-hover:translate-x-1 transition-all duration-200 shrink-0" />
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                        <button
                            onClick={() => navigate('/candidates')}
                            className="w-full mt-4 btn-outline text-sm py-2.5 flex items-center justify-center gap-2 group"
                            aria-label="View all candidates"
                        >
                            View All Candidates
                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                </section>
            </div>
        </main>
    );
};

export default RecruiterDashboard;

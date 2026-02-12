import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Download, ChevronRight, ChevronDown, ChevronLeft, Loader2, Users, AlertCircle } from 'lucide-react';
import { apiGet } from '../api/client';
import TopNav from '../components/layout/TopNav';
import ReportAssistant from '../components/chat/ReportAssistant';

const AllCandidates = () => {
    const navigate = useNavigate();

    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [statusFilter, setStatusFilter] = useState('all');
    const [positionFilter, setPositionFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [totalCount, setTotalCount] = useState(0);
    const [candidateDecisions, setCandidateDecisions] = useState({});

    // Load recruiter decisions from localStorage
    useEffect(() => {
        const stored = localStorage.getItem('candidateDecisions');
        if (stored) {
            try {
                setCandidateDecisions(JSON.parse(stored));
            } catch (e) {
                console.error('Failed to parse candidate decisions:', e);
            }
        }
    }, []);

    // Fetch candidates from API
    const fetchCandidates = async (showLoading = true) => {
        if (showLoading) setLoading(true);
        setError(null);
        try {
            const params = new URLSearchParams({
                page: currentPage.toString(),
                page_size: rowsPerPage.toString()
            });
            if (statusFilter !== 'all') params.append('status', statusFilter);
            if (searchQuery) params.append('search', searchQuery);

            const res = await apiGet(`/attempts?${params.toString()}`);
            // Normalize the data from API
            const normalizedCandidates = (res.candidates || res.attempts || []).map(c => {
                // Extract name from multiple possible locations
                const candidateName = c.candidate_info?.name || c.name || c.candidate_name || 'Unknown';
                const candidateEmail = c.candidate_info?.email || c.email || c.candidate_email || '';
                const candidatePosition = c.candidate_info?.position || c.position || c.role || 'Candidate';

                return {
                    id: c.id || c._id,
                    attempt_id: c.attempt_id || c.id || c._id,
                    name: candidateName,
                    subtitle: candidatePosition,
                    role: candidatePosition,
                    status: c.status || 'pending',
                    email: candidateEmail,
                    avatar: candidateName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(),
                    score: c.overall_score,
                    grade: c.overall_grade
                };
            });
            setCandidates(normalizedCandidates);
            setTotalCount(res.total || res.total_count || normalizedCandidates.length);
        } catch (err) {
            console.error('Failed to fetch candidates:', err);
            setError(err.message || 'Failed to load candidates');
        } finally {
            if (showLoading) setLoading(false);
        }
    };

    useEffect(() => {
        fetchCandidates(true);

        // Polling for real-time status updates every 10s
        const interval = setInterval(() => {
            fetchCandidates(false);
        }, 10000);

        return () => clearInterval(interval);
    }, [currentPage, rowsPerPage, statusFilter, searchQuery]);

    // Get unique roles for filter
    const uniqueRoles = ['all', ...new Set(candidates.map(c => c.role).filter(Boolean))];

    // Filter candidates locally by position (status/search is done server-side)
    const filteredCandidates = candidates.filter(candidate => {
        const matchesPosition = positionFilter === 'all' || candidate.role === positionFilter;
        return matchesPosition;
    });

    // Pagination
    const totalPages = Math.max(1, Math.ceil(totalCount / rowsPerPage));

    const getDecisionBadge = (attemptId) => {
        const decision = candidateDecisions[attemptId];
        if (!decision) return null;

        const decisionConfig = {
            'shortlist': { label: 'Shortlisted', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-300 dark:border-green-700' },
            'reject': { label: 'Rejected', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-300 dark:border-red-700' },
            'hold': { label: 'On Hold', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700' }
        };

        const config = decisionConfig[decision.decision];
        if (!config) return null;

        return (
            <span className={`${config.color} px-3 py-1 rounded-full text-xs font-semibold border`}>
                {config.label}
            </span>
        );
    };

    const getStatusBadge = (status) => {
        const isCompleted = status === 'completed' || status === 'locked';

        if (isCompleted) {
            return (
                <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold">
                    Completed
                </span>
            );
        }

        return (
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">
                Running
            </span>
        );
    };

    // Removed getActionButton - Actions column no longer needed


    const handleExportCSV = () => {
        const headers = ['Name', 'Role', 'Status', 'Email'];
        const rows = filteredCandidates.map(c => [
            c.name,
            c.role,
            c.status,
            c.email
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'candidates.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    if (loading && candidates.length === 0) {
        return (
            <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black flex items-center justify-center transition-colors duration-300">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">Loading candidates...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black transition-colors duration-300">
            {/* Top Navigation */}
            <TopNav />

            {/* Main Content */}
            <div className="p-8 max-w-[1400px] mx-auto">
                <div className="max-w-7xl mx-auto">
                    {/* Header */}
                    <div className="mb-6">
                        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
                            Candidates <span className="text-gray-600 dark:text-gray-400">Overview</span>
                        </h1>
                        <p className="text-gray-600 dark:text-gray-400">
                            Manage and review all candidate assessments.
                        </p>
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-3">
                            <AlertCircle className="w-5 h-5 text-red-500" />
                            <p className="text-red-700">{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="ml-auto text-sm text-red-600 hover:text-red-800 font-medium"
                            >
                                Retry
                            </button>
                        </div>
                    )}

                    {/* Filters and Actions */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6 mb-6 transition-colors duration-300">
                        <div className="flex items-center gap-4 mb-4">
                            {/* Status Filter */}
                            <div className="relative">
                                <select
                                    value={statusFilter}
                                    onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
                                    className="appearance-none bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-2 pr-10 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-colors duration-300"
                                >
                                    <option value="all">Status: All</option>
                                    <option value="completed">Completed</option>
                                    <option value="in_progress">In Progress</option>
                                    <option value="pending">Pending</option>
                                    <option value="expired">Expired</option>
                                </select>
                                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                            </div>

                            {/* Position Filter */}
                            <div className="relative">
                                <select
                                    value={positionFilter}
                                    onChange={(e) => setPositionFilter(e.target.value)}
                                    className="appearance-none bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-2 pr-10 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-colors duration-300"
                                >
                                    <option value="all">Position: All Roles</option>
                                    {uniqueRoles.filter(r => r !== 'all').map(role => (
                                        <option key={role} value={role}>{role}</option>
                                    ))}
                                </select>
                                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                            </div>

                            {/* Search */}
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    placeholder="Search Candidates"
                                    value={searchQuery}
                                    onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                                    className="w-full bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-2 pl-10 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300"
                                />
                                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                            </div>

                            {/* Export CSV */}
                            <button
                                onClick={handleExportCSV}
                                disabled={filteredCandidates.length === 0}
                                className="bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 disabled:opacity-50 text-white font-semibold px-6 py-2 rounded-xl text-sm transition-all shadow-md flex items-center gap-2"
                            >
                                Export CSV
                            </button>
                        </div>

                        {/* Summary */}
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                            <span className="font-semibold text-gray-800 dark:text-white">{totalCount} Candidates</span>
                            {loading && <span className="ml-2 text-blue-500">(updating...)</span>}
                        </div>
                    </div>

                    {/* Candidates Table */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 overflow-hidden transition-colors duration-300">
                        {filteredCandidates.length === 0 && !loading ? (
                            <div className="py-16 text-center animate-fade-in">
                                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center animate-float">
                                    <Users className="w-10 h-10 text-blue-600 dark:text-blue-400" />
                                </div>
                                <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">No candidates found</h3>
                                <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                                    {searchQuery || statusFilter !== 'all' || positionFilter !== 'all'
                                        ? 'Try adjusting your filters to see more results.'
                                        : 'Upload a resume to create your first assessment and start tracking candidates.'}
                                </p>
                                <div className="flex gap-3 justify-center">
                                    <button
                                        onClick={() => navigate('/upload-resume')}
                                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-xl text-sm transition-all duration-300 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
                                    >
                                        Upload Resume
                                    </button>
                                    {(searchQuery || statusFilter !== 'all' || positionFilter !== 'all') && (
                                        <button
                                            onClick={() => { setSearchQuery(''); setStatusFilter('all'); setPositionFilter('all'); }}
                                            className="bg-gray-100 dark:bg-neutral-800 hover:bg-gray-200 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300 font-semibold px-6 py-3 rounded-xl text-sm transition-all duration-300 hover:scale-105 active:scale-95"
                                        >
                                            Clear Filters
                                        </button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead className="bg-gray-50 dark:bg-neutral-900 border-b border-gray-200 dark:border-neutral-700">
                                            <tr>
                                                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 dark:text-gray-200">
                                                    <div className="flex items-center gap-1">
                                                        Name
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </div>
                                                </th>
                                                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 dark:text-gray-200">
                                                    <div className="flex items-center gap-1">
                                                        Role
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </div>
                                                </th>
                                                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 dark:text-gray-200">Score</th>
                                                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 dark:text-gray-200">Status</th>
                                                <th className="text-left py-4 px-6 text-sm font-semibold text-gray-700 dark:text-gray-200">Decision</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredCandidates.map((candidate, index) => (
                                                <tr
                                                    key={candidate.id}
                                                    onClick={() => navigate(`/candidate/${candidate.attempt_id || candidate.id}`)}
                                                    className={`border-b border-gray-100 dark:border-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-800/50 transition-all duration-200 cursor-pointer group ${index === filteredCandidates.length - 1 ? 'border-b-0' : ''}`}
                                                >
                                                    <td className="py-4 px-6">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                                                                <span className="text-white text-sm font-bold">{candidate.avatar}</span>
                                                            </div>
                                                            <div>
                                                                <p className="font-semibold text-gray-800 dark:text-white">{candidate.name}</p>
                                                                <p className="text-xs text-gray-500 dark:text-gray-400">{candidate.email}</p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        <p className="font-medium text-gray-700 dark:text-gray-300">{candidate.role}</p>
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        {candidate.score ? (
                                                            <div className="flex items-center gap-2">
                                                                <div className="w-12 bg-gray-200 dark:bg-neutral-700 rounded-full h-1.5 overflow-hidden">
                                                                    <div
                                                                        className="bg-blue-500 h-full rounded-full"
                                                                        style={{ width: `${Math.min(100, candidate.score)}%` }}
                                                                    />
                                                                </div>
                                                                <span className="text-sm font-bold text-gray-700 dark:text-gray-300">{candidate.score}%</span>
                                                                {candidate.grade && (
                                                                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${['A+', 'A', 'A-'].some(g => candidate.grade.includes(g)) ? 'bg-green-100 text-green-700' :
                                                                        ['B+', 'B', 'B-'].some(g => candidate.grade.includes(g)) ? 'bg-blue-100 text-blue-700' :
                                                                            'bg-yellow-100 text-yellow-700'
                                                                        }`}>{candidate.grade}</span>
                                                                )}
                                                            </div>
                                                        ) : (
                                                            <span className="text-xs text-gray-400 italic">N/A</span>
                                                        )}
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        {getStatusBadge(candidate.status)}
                                                    </td>
                                                    <td className="py-4 px-6">
                                                        {getDecisionBadge(candidate.attempt_id || candidate.id) || (
                                                            <span className="text-xs text-gray-400 dark:text-gray-500 italic">No decision</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* Pagination */}
                                <div className="border-t border-gray-200 dark:border-neutral-800 px-6 py-4 flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-gray-600 dark:text-gray-400">Rows per page:</span>
                                        <div className="relative">
                                            <select
                                                value={rowsPerPage}
                                                onChange={(e) => {
                                                    setRowsPerPage(Number(e.target.value));
                                                    setCurrentPage(1);
                                                }}
                                                className="appearance-none bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-lg px-3 py-1 pr-8 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-colors duration-300"
                                            >
                                                <option value={5}>5</option>
                                                <option value={10}>10</option>
                                                <option value={20}>20</option>
                                                <option value={50}>50</option>
                                            </select>
                                            <ChevronDown className="w-4 h-4 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                            disabled={currentPage === 1}
                                            className="px-3 py-1 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1"
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                            Prev
                                        </button>

                                        <div className="flex items-center gap-1">
                                            {[...Array(Math.min(totalPages, 5))].map((_, i) => {
                                                const pageNum = i + 1;
                                                return (
                                                    <button
                                                        key={pageNum}
                                                        onClick={() => setCurrentPage(pageNum)}
                                                        className={`min-w-[32px] h-8 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-110 active:scale-95 ${currentPage === pageNum
                                                            ? 'bg-blue-600 text-white shadow-md'
                                                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800'
                                                            }`}
                                                    >
                                                        {pageNum}
                                                    </button>
                                                );
                                            })}
                                            {totalPages > 5 && <span className="text-gray-400 px-2">...</span>}
                                        </div>

                                        <button
                                            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                            disabled={currentPage === totalPages}
                                            className="px-3 py-1 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1"
                                        >
                                            Next
                                            <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Kiwi AI Assistant */}
            <ReportAssistant pageContext="all_candidates" />
        </div>
    );
};

export default AllCandidates;

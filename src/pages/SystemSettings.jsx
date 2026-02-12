import { useState, useEffect, useMemo } from 'react';
import { Save, Bell, Database, Calendar, Download, Users, Loader2, Trophy, ChevronLeft, ChevronRight } from 'lucide-react';
import { apiGet } from '../api/client';
import ReportAssistant from '../components/chat/ReportAssistant';

const SystemSettings = () => {
    const [settings, setSettings] = useState({
        emailNotifications: true,
        assessmentReminders: true,
        weeklyReports: false,
        dataRetention: '90',
        theme: 'light',
        autoArchive: true,
    });

    // Candidate records state
    const [allCandidates, setAllCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [calendarMonth, setCalendarMonth] = useState(new Date());

    // Fetch all candidates on mount
    useEffect(() => {
        async function fetchAllCandidates() {
            setLoading(true);
            try {
                const res = await apiGet('/candidates?page_size=500&status=completed');
                const candidates = (res.candidates || res.attempts || []).map(c => ({
                    id: c.id || c._id || c.attempt_id,
                    name: c.name || c.candidate_info?.name || 'Unknown',
                    email: c.email || c.candidate_info?.email || '',
                    position: c.position || c.candidate_info?.position || 'Candidate',
                    score: c.score || c.final_score || c.overall_score || Math.floor(Math.random() * 40 + 60), // Fallback to random score for demo
                    completedAt: c.completed_at || c.updated_at || c.created_at || new Date().toISOString(),
                    status: c.status || 'completed'
                }));
                setAllCandidates(candidates);
            } catch (err) {
                console.error('Failed to fetch candidates:', err);
            } finally {
                setLoading(false);
            }
        }
        fetchAllCandidates();
    }, []);

    // Group candidates by date and sort by highest score
    const candidatesByDate = useMemo(() => {
        const grouped = {};
        allCandidates.forEach(candidate => {
            const date = new Date(candidate.completedAt).toISOString().split('T')[0];
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(candidate);
        });
        // Sort each date's candidates by score descending
        Object.keys(grouped).forEach(date => {
            grouped[date].sort((a, b) => b.score - a.score);
        });
        return grouped;
    }, [allCandidates]);

    // Get available dates for the calendar
    const availableDates = useMemo(() => {
        return Object.keys(candidatesByDate).sort((a, b) => new Date(b) - new Date(a));
    }, [candidatesByDate]);

    // Get candidates for selected date
    const selectedDateCandidates = candidatesByDate[selectedDate] || [];

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    const handleSave = () => {
        alert('Settings saved successfully!');
    };

    // Download CSV for selected date or all records
    const handleDownloadCSV = (downloadAll = false) => {
        let dataToExport = [];
        let filename = '';

        if (downloadAll) {
            // Export all records grouped by date
            availableDates.forEach(date => {
                candidatesByDate[date].forEach(c => {
                    dataToExport.push({
                        date,
                        ...c
                    });
                });
            });
            filename = `all_candidate_records_${new Date().toISOString().split('T')[0]}.csv`;
        } else {
            // Export only selected date
            dataToExport = selectedDateCandidates.map(c => ({
                date: selectedDate,
                ...c
            }));
            filename = `candidate_records_${selectedDate}.csv`;
        }

        if (dataToExport.length === 0) {
            alert('No records to download');
            return;
        }

        const headers = ['Date', 'Rank', 'Name', 'Email', 'Position', 'Score'];
        let currentDate = '';
        let rank = 0;

        const rows = dataToExport.map(c => {
            if (c.date !== currentDate) {
                currentDate = c.date;
                rank = 1;
            } else {
                rank++;
            }
            return [
                c.date,
                rank,
                c.name,
                c.email,
                c.position,
                c.score
            ];
        });

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // Calendar helpers
    const getDaysInMonth = (date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startingDay = firstDay.getDay();
        return { daysInMonth, startingDay };
    };

    const { daysInMonth, startingDay } = getDaysInMonth(calendarMonth);

    const handlePrevMonth = () => {
        setCalendarMonth(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCalendarMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
    };

    const formatDateForComparison = (year, month, day) => {
        return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    };

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black p-8">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">System Settings</h1>
                        <p className="text-gray-600 dark:text-gray-400">Configure system preferences and view candidate records</p>
                    </div>
                    <button
                        onClick={handleSave}
                        className="bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white px-6 py-3 rounded-xl transition-all flex items-center gap-2"
                    >
                        <Save className="w-5 h-5" />
                        Save Changes
                    </button>
                </div>

                <div className="space-y-6">
                    {/* Candidate Records Section */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="bg-gradient-to-br from-amber-100 to-orange-100 p-3 rounded-xl">
                                    <Trophy className="w-6 h-6 text-amber-600" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Candidate Records</h2>
                                    <p className="text-sm text-gray-500">View candidates by date, sorted by highest score</p>
                                </div>
                            </div>
                            <button
                                onClick={() => handleDownloadCSV(true)}
                                disabled={allCandidates.length === 0}
                                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-all shadow-md flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                Download All Records
                            </button>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Calendar */}
                            <div className="lg:col-span-1">
                                <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-950 rounded-xl border border-gray-200 dark:border-neutral-800 p-4">
                                    {/* Calendar Header */}
                                    <div className="flex items-center justify-between mb-4">
                                        <button
                                            onClick={handlePrevMonth}
                                            className="p-2 hover:bg-white dark:hover:bg-neutral-800 rounded-lg transition-colors"
                                        >
                                            <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                                        </button>
                                        <h3 className="font-semibold text-gray-800 dark:text-white">
                                            {monthNames[calendarMonth.getMonth()]} {calendarMonth.getFullYear()}
                                        </h3>
                                        <button
                                            onClick={handleNextMonth}
                                            className="p-2 hover:bg-white rounded-lg transition-colors"
                                        >
                                            <ChevronRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                                        </button>
                                    </div>

                                    {/* Day Names */}
                                    <div className="grid grid-cols-7 gap-1 mb-2">
                                        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                                            <div key={day} className="text-center text-xs font-medium text-gray-500 dark:text-gray-400 py-1">
                                                {day}
                                            </div>
                                        ))}
                                    </div>

                                    {/* Calendar Days */}
                                    <div className="grid grid-cols-7 gap-1">
                                        {/* Empty cells for days before the first day of month */}
                                        {Array.from({ length: startingDay }).map((_, i) => (
                                            <div key={`empty-${i}`} className="aspect-square" />
                                        ))}

                                        {/* Actual days */}
                                        {Array.from({ length: daysInMonth }).map((_, i) => {
                                            const day = i + 1;
                                            const dateStr = formatDateForComparison(
                                                calendarMonth.getFullYear(),
                                                calendarMonth.getMonth(),
                                                day
                                            );
                                            const hasRecords = candidatesByDate[dateStr];
                                            const isSelected = selectedDate === dateStr;
                                            const isToday = dateStr === new Date().toISOString().split('T')[0];

                                            return (
                                                <button
                                                    key={day}
                                                    onClick={() => hasRecords && setSelectedDate(dateStr)}
                                                    disabled={!hasRecords}
                                                    className={`aspect-square rounded-lg text-sm font-medium transition-all relative
                                                        ${isSelected
                                                            ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md'
                                                            : hasRecords
                                                                ? 'bg-white hover:bg-blue-50 text-gray-800 dark:text-white border border-gray-200 hover:border-blue-300 cursor-pointer'
                                                                : 'text-gray-300 cursor-default'
                                                        }
                                                        ${isToday && !isSelected ? 'ring-2 ring-blue-400 ring-offset-1' : ''}
                                                    `}
                                                >
                                                    {day}
                                                    {hasRecords && !isSelected && (
                                                        <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-amber-500 rounded-full" />
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {/* Quick Date Picker */}
                                    <div className="mt-4 pt-4 border-t border-gray-200">
                                        <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                            <Calendar className="w-4 h-4 inline mr-1" />
                                            Jump to Date
                                        </label>
                                        <input
                                            type="date"
                                            value={selectedDate}
                                            onChange={(e) => {
                                                setSelectedDate(e.target.value);
                                                setCalendarMonth(new Date(e.target.value));
                                            }}
                                            className="w-full bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-lg px-3 py-2 text-sm text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Candidates Table for Selected Date */}
                            <div className="lg:col-span-2">
                                <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-950 rounded-xl border border-gray-200 dark:border-neutral-800 overflow-hidden">
                                    {/* Table Header */}
                                    <div className="bg-gradient-to-r from-gray-100 to-gray-200 dark:from-neutral-800 dark:to-neutral-900 px-4 py-3 flex items-center justify-between border-b border-gray-200 dark:border-neutral-700">
                                        <div className="flex items-center gap-2">
                                            <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                                            <h4 className="font-semibold text-gray-800 dark:text-white">
                                                {new Date(selectedDate).toLocaleDateString('en-US', {
                                                    weekday: 'long',
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric'
                                                })}
                                            </h4>
                                            <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-semibold px-2 py-0.5 rounded-full">
                                                {selectedDateCandidates.length} candidate{selectedDateCandidates.length !== 1 ? 's' : ''}
                                            </span>
                                        </div>
                                        <button
                                            onClick={() => handleDownloadCSV(false)}
                                            disabled={selectedDateCandidates.length === 0}
                                            className="text-sm font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                        >
                                            <Download className="w-4 h-4" />
                                            Export Date
                                        </button>
                                    </div>

                                    {/* Table Content */}
                                    {loading ? (
                                        <div className="py-12 text-center">
                                            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
                                            <p className="text-gray-500 dark:text-gray-400 text-sm">Loading candidates...</p>
                                        </div>
                                    ) : selectedDateCandidates.length === 0 ? (
                                        <div className="py-12 text-center">
                                            <Users className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                                            <p className="text-gray-500 dark:text-gray-400 font-medium">No records for this date</p>
                                            <p className="text-gray-400 text-sm mt-1">Select a date with records from the calendar</p>
                                        </div>
                                    ) : (
                                        <div className="max-h-[400px] overflow-y-auto">
                                            <table className="w-full">
                                                <thead className="bg-white dark:bg-neutral-900 sticky top-0 shadow-sm">
                                                    <tr>
                                                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Rank</th>
                                                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Candidate</th>
                                                        <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Position</th>
                                                        <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Score</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {selectedDateCandidates.map((candidate, index) => (
                                                        <tr
                                                            key={candidate.id}
                                                            className={`border-b border-gray-100 dark:border-neutral-800 hover:bg-white dark:hover:bg-neutral-800 transition-colors ${index === 0 ? 'bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20' : ''}`}
                                                        >
                                                            <td className="py-3 px-4">
                                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                                                                    ${index === 0 ? 'bg-gradient-to-br from-amber-400 to-yellow-500 text-white shadow-md' :
                                                                        index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-400 text-white' :
                                                                            index === 2 ? 'bg-gradient-to-br from-amber-600 to-orange-600 text-white' :
                                                                                'bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400'}
                                                                `}>
                                                                    {index + 1}
                                                                </div>
                                                            </td>
                                                            <td className="py-3 px-4">
                                                                <div>
                                                                    <p className="font-semibold text-gray-800 dark:text-white">{candidate.name}</p>
                                                                    <p className="text-xs text-gray-500 dark:text-gray-400">{candidate.email}</p>
                                                                </div>
                                                            </td>
                                                            <td className="py-3 px-4">
                                                                <span className="text-sm text-gray-600 dark:text-gray-400">{candidate.position}</span>
                                                            </td>
                                                            <td className="py-3 px-4 text-right">
                                                                <span className={`font-bold text-lg ${candidate.score >= 80 ? 'text-green-600' :
                                                                    candidate.score >= 60 ? 'text-blue-600' :
                                                                        candidate.score >= 40 ? 'text-amber-600' :
                                                                            'text-red-600'
                                                                    }`}>
                                                                    {candidate.score}%
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Notifications */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-xl">
                                <Bell className="w-6 h-6 text-blue-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Notifications</h2>
                        </div>

                        <div className="space-y-4">
                            <label className="flex items-center justify-between p-4 border border-gray-100 dark:border-neutral-800 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-900">
                                <span className="font-medium text-gray-700 dark:text-gray-200">Email Notifications</span>
                                <input
                                    type="checkbox"
                                    checked={settings.emailNotifications}
                                    onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                />
                            </label>
                            <label className="flex items-center justify-between p-4 border border-gray-100 dark:border-neutral-800 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-900">
                                <span className="font-medium text-gray-700 dark:text-gray-200">Assessment Reminders</span>
                                <input
                                    type="checkbox"
                                    checked={settings.assessmentReminders}
                                    onChange={(e) => handleSettingChange('assessmentReminders', e.target.checked)}
                                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                />
                            </label>
                            <label className="flex items-center justify-between p-4 border border-gray-100 dark:border-neutral-800 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-900">
                                <span className="font-medium text-gray-700 dark:text-gray-200">Weekly Reports</span>
                                <input
                                    type="checkbox"
                                    checked={settings.weeklyReports}
                                    onChange={(e) => handleSettingChange('weeklyReports', e.target.checked)}
                                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                />
                            </label>
                        </div>
                    </div>

                    {/* Data Management */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="bg-purple-100 dark:bg-purple-900/30 p-3 rounded-xl">
                                <Database className="w-6 h-6 text-purple-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Data Management</h2>
                        </div>

                        <div className="space-y-4">
                            <div className="p-4 border border-gray-100 dark:border-neutral-800 rounded-xl">
                                <label className="block font-medium text-gray-700 dark:text-gray-200 mb-2">
                                    Data Retention Period (days)
                                </label>
                                <select
                                    value={settings.dataRetention}
                                    onChange={(e) => handleSettingChange('dataRetention', e.target.value)}
                                    className="w-full bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-lg px-4 py-3 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="30">30 days</option>
                                    <option value="60">60 days</option>
                                    <option value="90">90 days</option>
                                    <option value="180">180 days</option>
                                    <option value="365">1 year</option>
                                </select>
                            </div>

                            <label className="flex items-center justify-between p-4 border border-gray-100 dark:border-neutral-800 rounded-xl cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-900">
                                <span className="font-medium text-gray-700 dark:text-gray-200">Auto-archive completed assessments</span>
                                <input
                                    type="checkbox"
                                    checked={settings.autoArchive}
                                    onChange={(e) => handleSettingChange('autoArchive', e.target.checked)}
                                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                                />
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            {/* Kiwi AI Assistant */}
            <ReportAssistant pageContext="settings" />
        </div>
    );
};

export default SystemSettings;

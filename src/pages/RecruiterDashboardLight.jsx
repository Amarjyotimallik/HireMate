import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Upload,
    Link2,
    BarChart3,
    TrendingUp,
    FileText,
    Users,
    Settings,
    Eye,
    ChevronRight,
    LogOut,
    User,
    Moon,
    Sun
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import ReportAssistant from '../components/chat/ReportAssistant';

const RecruiterDashboardLight = () => {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const [showUserMenu, setShowUserMenu] = useState(false);
    const menuRef = useRef(null);

    // Get user data from auth context or fallback
    const userData = user || { full_name: 'Recruiter Admin', email: 'admin@company.com' };
    const displayName = userData.full_name || userData.name || 'Recruiter Admin';
    const userInitials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowUserMenu(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const featureCards = [
        {
            id: 'assessment',
            title: 'Candidate Assessment',
            icon: FileText,
            iconBg: 'bg-blue-100',
            iconColor: 'text-blue-600',
            subtitle: 'Upload Resume',
            description: 'Create & manage assessments for candidates.',
            actions: [
                {
                    icon: Upload,
                    label: 'Upload Resume',
                    path: '/upload-resume',
                    iconColor: 'text-blue-600'
                },
                {
                    icon: Link2,
                    label: 'Assessment Link',
                    path: '/assessment-link',
                    iconColor: 'text-blue-600'
                },
                {
                    icon: BarChart3,
                    label: 'Live Session',
                    path: '/live-assessment',
                    iconColor: 'text-blue-600'
                },
            ]
        },
        {
            id: 'monitoring',
            title: 'Monitoring & Insights',
            icon: Eye,
            iconBg: 'bg-indigo-100',
            iconColor: 'text-indigo-600',
            subtitle: 'Live Metrics',
            description: 'Track assessment performance and insights.',
            actions: [
                {
                    icon: TrendingUp,
                    label: 'Live Metrics',
                    path: '/live-metrics',
                    iconColor: 'text-indigo-600'
                },
                {
                    icon: FileText,
                    label: 'Skill Reports',
                    path: '/skill-reports',
                    iconColor: 'text-indigo-600'
                },
                {
                    icon: Users,
                    label: 'Compare Candidates',
                    path: '/compare-candidates',
                    iconColor: 'text-indigo-600'
                },
            ]
        },
        {
            id: 'comparison',
            title: 'Candidate Comparison',
            icon: Users,
            iconBg: 'bg-blue-100',
            iconColor: 'text-blue-600',
            subtitle: 'Compare Side-By-Side',
            description: 'Compare and evaluate candidates side-by-side.',
            isPrimary: true,
            primaryAction: {
                label: 'Compare Side-By-Side',
                path: '/compare-candidates'
            }
        },
        {
            id: 'settings',
            title: 'System Configuration',
            icon: Settings,
            iconBg: 'bg-indigo-100',
            iconColor: 'text-indigo-600',
            subtitle: 'Manage Settings',
            description: 'Define skills importance and system preferences.',
            actions: [
                {
                    icon: Settings,
                    label: 'Manage Settings',
                    path: '/settings',
                    iconColor: 'text-indigo-600'
                },
            ]
        }
    ];

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black transition-colors duration-300">
            {/* Top Navigation */}
            <nav className="bg-white dark:bg-neutral-950 border-b border-gray-200 dark:border-neutral-800 px-8 py-4 transition-colors duration-300">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-2">
                            <img
                                src="/hiremate-logo.svg"
                                alt="HireMate Logo"
                                className="w-9 h-9"
                            />
                            <span className="text-xl font-bold text-gray-800 dark:text-white">HireMate</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-8">
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white font-medium transition-colors"
                        >
                            Dashboard
                        </button>
                        <button
                            onClick={() => navigate('/candidates')}
                            className="text-gray-700 dark:text-gray-200 hover:text-gray-900 dark:hover:text-white font-medium transition-colors"
                        >
                            Candidates
                        </button>

                        {/* Dark Mode Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg bg-gray-100 dark:bg-neutral-900 hover:bg-gray-200 dark:hover:bg-neutral-700 transition-all duration-300 group"
                            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {isDark ? (
                                <Sun className="w-5 h-5 text-yellow-500 group-hover:rotate-45 transition-transform duration-300" />
                            ) : (
                                <Moon className="w-5 h-5 text-neutral-600 group-hover:-rotate-12 transition-transform duration-300" />
                            )}
                        </button>

                        {/* User Menu with Dropdown */}
                        <div className="relative" ref={menuRef}>
                            <button
                                onClick={() => setShowUserMenu(!showUserMenu)}
                                className="flex items-center gap-3 pl-6 border-l border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800 py-2 px-3 rounded-lg transition-colors"
                            >
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                                    <span className="text-white text-sm font-semibold">{userInitials}</span>
                                </div>
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{displayName}</span>
                                <ChevronRight className={`w-4 h-4 text-gray-400 dark:text-gray-500 transition-transform duration-200 ${showUserMenu ? 'rotate-90' : 'rotate-90'}`} />
                            </button>

                            {/* Dropdown Menu */}
                            {showUserMenu && (
                                <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-neutral-950 rounded-xl shadow-lg border border-gray-200 dark:border-neutral-800 py-2 z-50 animate-fade-in">
                                    <div className="px-4 py-3 border-b border-gray-100 dark:border-neutral-800">
                                        <p className="text-sm font-semibold text-gray-800 dark:text-white">{displayName}</p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">{userData.email}</p>
                                    </div>
                                    <div className="py-1">
                                        <button
                                            onClick={() => {
                                                setShowUserMenu(false);
                                                navigate('/settings');
                                            }}
                                            className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
                                        >
                                            <User className="w-4 h-4" />
                                            <span className="text-sm">Profile Settings</span>
                                        </button>
                                        <button
                                            onClick={handleLogout}
                                            className="w-full flex items-center gap-3 px-4 py-2.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                        >
                                            <LogOut className="w-4 h-4" />
                                            <span className="text-sm">Sign Out</span>
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <div className="px-8 py-10 max-w-[1400px] mx-auto">
                {/* Header */}
                <div className="mb-10">
                    <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
                        Recruiter <span className="text-gray-600 dark:text-gray-400">Dashboard</span>
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Manage and analyze candidate assessments and system preferences.
                    </p>
                </div>

                {/* Feature Cards Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {featureCards.map((card) => (
                        <div
                            key={card.id}
                            className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 overflow-hidden hover:shadow-medium transition-all duration-300 hover:scale-[1.02] animate-fade-in group"
                        >
                            <div className="p-8">
                                {/* Card Header */}
                                <div className="mb-6">
                                    <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">
                                        {card.title}
                                    </h3>
                                    <div className="flex flex-col items-center mb-4">
                                        <div className={`${card.iconBg} dark:bg-opacity-20 p-4 rounded-2xl mb-4`}>
                                            <card.icon className={`w-8 h-8 ${card.iconColor}`} />
                                        </div>
                                        <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
                                            {card.subtitle}
                                        </h4>
                                        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                                            {card.description}
                                        </p>
                                    </div>
                                </div>

                                {/* Card Actions */}
                                {card.isPrimary ? (
                                    <button
                                        onClick={() => navigate(card.primaryAction.path)}
                                        className="w-full bg-gradient-to-r from-accent-500 to-accent-600 text-white font-semibold py-3 px-6 rounded-xl hover:from-accent-600 hover:to-accent-700 transition-all duration-300 flex items-center justify-center gap-2 shadow-md hover:shadow-lg hover:scale-105 active:scale-95"
                                    >
                                        <span>{card.primaryAction.label}</span>
                                        <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                    </button>
                                ) : (
                                    <div className="space-y-2">
                                        {card.actions.map((action, index) => (
                                            <button
                                                key={index}
                                                onClick={() => navigate(action.path)}
                                                className="w-full bg-blue-50/50 dark:bg-neutral-900/50 hover:bg-blue-100/80 dark:hover:bg-neutral-700/80 text-gray-700 dark:text-gray-200 font-medium py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-between group hover:scale-[1.02] active:scale-95"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <action.icon className={`w-5 h-5 ${action.iconColor}`} />
                                                    <span>{action.label}</span>
                                                </div>
                                                <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300 group-hover:translate-x-1 transition-all" />
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Kiwi AI Assistant */}
            <ReportAssistant pageContext="dashboard" />
        </div>
    );
};

export default RecruiterDashboardLight;

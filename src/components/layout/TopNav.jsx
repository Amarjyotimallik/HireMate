import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, LogOut, User, Moon, Sun } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';

const TopNav = ({ showBackButton = false, backPath = '/dashboard' }) => {
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

    return (
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
    );
};

export default TopNav;

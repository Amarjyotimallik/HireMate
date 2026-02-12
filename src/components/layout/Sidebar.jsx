import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Upload,
    Activity,
    Users,
    GitCompare,
    ChevronRight,
    TrendingUp
} from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();

    const navItems = [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/upload-resume', icon: Upload, label: 'Upload Resume' },
        { path: '/live-assessment', icon: Activity, label: 'Live Assessment' },
        { path: '/compare-candidates', icon: GitCompare, label: 'Compare Candidates' },
        { path: '/candidates', icon: Users, label: 'All Candidates' },
    ];

    const isActive = (path) => location.pathname === path;

    return (
        <aside className="w-64 glass-card m-4 p-6 flex flex-col h-[calc(100vh-2rem)] sticky top-4">
            {/* Logo */}
            <div className="mb-8">
                <Link to="/dashboard" className="flex items-center gap-3 group">
                    <img
                        src="/hiremate-logo.svg"
                        alt="HireMate Logo"
                        className="w-10 h-10"
                    />
                    <div>
                        <h1 className="text-xl font-bold text-gradient">HireMate</h1>
                        <p className="text-xs text-gray-400">Recruiter Portal</p>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-2">
                {navItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={isActive(item.path) ? 'nav-link-active' : 'nav-link'}
                    >
                        <item.icon className="w-5 h-5" />
                        <span className="flex-1">{item.label}</span>
                        {isActive(item.path) && <ChevronRight className="w-4 h-4" />}
                    </Link>
                ))}
            </nav>

            {/* Footer */}
            <div className="mt-auto pt-6 border-t border-white/10">
                <div className="glass-card p-4 bg-gradient-to-br from-primary-600/20 to-secondary-600/20">
                    <p className="text-xs font-semibold text-gray-300 mb-1">Need Help?</p>
                    <p className="text-xs text-gray-400 mb-3">Check our documentation</p>
                    <button className="w-full text-xs btn-gradient py-2">
                        View Docs
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;

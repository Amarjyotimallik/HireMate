import { Bell, Search, User } from 'lucide-react';

const Navbar = ({ title, subtitle }) => {
    return (
        <header className="glass-card mb-6 p-4 flex items-center justify-between">
            <div>
                <h2 className="text-2xl font-bold text-white">{title}</h2>
                {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
            </div>

            <div className="flex items-center gap-4">
                {/* Search */}
                <div className="relative hidden md:block">
                    <input
                        type="text"
                        placeholder="Search candidates..."
                        className="input-field w-64 pl-10 py-2"
                    />
                    <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                </div>

                {/* Notifications */}
                <button className="relative p-2 glass-card hover:bg-white/10 transition-all rounded-lg">
                    <Bell className="w-5 h-5 text-gray-300" />
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
                        3
                    </span>
                </button>

                {/* Profile */}
                <button className="flex items-center gap-3 glass-card px-3 py-2 hover:bg-white/10 transition-all rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
                        <User className="w-5 h-5 text-white" />
                    </div>
                    <div className="hidden lg:block text-left">
                        <p className="text-sm font-semibold text-white">Alex Morgan</p>
                        <p className="text-xs text-gray-400">Recruiter</p>
                    </div>
                </button>
            </div>
        </header>
    );
};

export default Navbar;

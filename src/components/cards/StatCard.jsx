import { TrendingUp, TrendingDown } from 'lucide-react';

const StatCard = ({ icon: Icon, label, value, trend, trendValue, color = "primary" }) => {
    const colorClasses = {
        primary: "from-primary-600/30 to-primary-700/30 border-primary-500/50",
        secondary: "from-secondary-600/30 to-secondary-700/30 border-secondary-500/50",
        success: "from-green-600/30 to-green-700/30 border-green-500/50",
        warning: "from-yellow-600/30 to-yellow-700/30 border-yellow-500/50",
    };

    const iconColors = {
        primary: "text-primary-400",
        secondary: "text-secondary-400",
        success: "text-green-400",
        warning: "text-yellow-400",
    };

    return (
        <div className={`glass-card p-6 bg-gradient-to-br ${colorClasses[color]} hover:scale-[1.02] transition-all duration-300 cursor-pointer`}>
            <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg bg-white/10 ${iconColors[color]}`}>
                    <Icon className="w-6 h-6" />
                </div>
                {trend && (
                    <div className={`flex items-center gap-1 text-sm ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                        {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        <span>{trendValue}</span>
                    </div>
                )}
            </div>
            <div>
                <p className="text-gray-400 text-sm mb-1">{label}</p>
                <p className="text-3xl font-bold text-white">{value}</p>
            </div>
        </div>
    );
};

export default StatCard;

import { TrendingUp, Users, Clock, Award, Activity } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const LiveMetrics = () => {
    // Mock data for charts
    const performanceData = [
        { time: '9:00', assessments: 4, avgScore: 75 },
        { time: '10:00', assessments: 8, avgScore: 78 },
        { time: '11:00', assessments: 12, avgScore: 82 },
        { time: '12:00', assessments: 10, avgScore: 80 },
        { time: '13:00', assessments: 15, avgScore: 85 },
        { time: '14:00', assessments: 18, avgScore: 88 },
    ];

    const stats = [
        { icon: Users, label: 'Active Assessments', value: '12', change: '+3', color: 'blue' },
        { icon: Clock, label: 'Avg. Completion Time', value: '24m', change: '-2m', color: 'green' },
        { icon: Award, label: 'Avg. Score', value: '82%', change: '+5%', color: 'purple' },
        { icon: Activity, label: 'Completion Rate', value: '94%', change: '+2%', color: 'orange' },
    ];

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">Live Metrics</h1>
                    <p className="text-gray-600 dark:text-gray-400">Real-time assessment performance and insights</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {stats.map((stat, index) => (
                        <div key={index} className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className={`bg-${stat.color}-100 p-3 rounded-xl`}>
                                    <stat.icon className={`w-6 h-6 text-${stat.color}-600`} />
                                </div>
                                <span className="text-sm font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                                    {stat.change}
                                </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{stat.label}</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{stat.value}</p>
                        </div>
                    ))}
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Performance Trend */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6">
                        <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-6">Performance Trend</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={performanceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="time" stroke="#6b7280" />
                                <YAxis stroke="#6b7280" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'white',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '0.75rem'
                                    }}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="avgScore"
                                    stroke="#3b82f6"
                                    strokeWidth={3}
                                    name="Average Score"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Assessment Activity */}
                    <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6">
                        <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-6">Assessment Activity</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={performanceData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="time" stroke="#6b7280" />
                                <YAxis stroke="#6b7280" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'white',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '0.75rem'
                                    }}
                                />
                                <Legend />
                                <Bar
                                    dataKey="assessments"
                                    fill="#f97316"
                                    name="Assessments"
                                    radius={[8, 8, 0, 0]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Live Status Indicator */}
                <div className="mt-6 bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-6">
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-gray-700 dark:text-gray-200 font-medium">Live Updates Active</span>
                        <span className="text-gray-500 text-sm">Last updated: just now</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LiveMetrics;

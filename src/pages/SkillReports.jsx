import { FileText, Download, Filter, TrendingUp } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';
import ReportAssistant from '../components/chat/ReportAssistant';

const SkillReports = () => {
    const skillData = [
        { skill: 'JavaScript', score: 85, benchMark: 70 },
        { skill: 'React', score: 90, benchmark: 75 },
        { skill: 'Node.js', score: 75, benchmark: 70 },
        { skill: 'TypeScript', score: 80, benchmark: 65 },
        { skill: 'Problem Solving', score: 88, benchmark: 80 },
        { skill: 'Communication', score: 92, benchmark: 75 },
    ];

    const reports = [
        { id: 1, name: 'Frontend Developer Skills Analysis', date: '2026-01-28', candidates: 15 },
        { id: 2, name: 'Backend Developer Assessment Report', date: '2026-01-27', candidates: 12 },
        { id: 3, name: 'Full Stack Developer Comparison', date: '2026-01-26', candidates: 8 },
        { id: 4, name: 'Quarterly Hiring Trends', date: '2026-01-25', candidates: 45 },
    ];

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">Skill Reports</h1>
                        <p className="text-gray-600 dark:text-gray-400">Analyze and compare candidate skills across assessments</p>
                    </div>
                    <button className="bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white px-6 py-3 rounded-xl transition-all flex items-center gap-2">
                        <Download className="w-5 h-5" />
                        Export All
                    </button>
                </div>

                {/* Skill Overview Chart */}
                <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8 mb-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Overall Skill Performance</h2>
                        <button className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium">
                            <Filter className="w-4 h-4" />
                            Filter
                        </button>
                    </div>
                    <div className="flex justify-center">
                        <ResponsiveContainer width="100%" height={400}>
                            <RadarChart data={skillData}>
                                <PolarGrid stroke="#e5e7eb" />
                                <PolarAngleAxis
                                    dataKey="skill"
                                    tick={{ fill: '#6b7280', fontSize: 12 }}
                                />
                                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                                <Radar
                                    name="Average Score"
                                    dataKey="score"
                                    stroke="#3b82f6"
                                    fill="#3b82f6"
                                    fillOpacity={0.6}
                                />
                                <Radar
                                    name="Benchmark"
                                    dataKey="benchmark"
                                    stroke="#f97316"
                                    fill="#f97316"
                                    fillOpacity={0.3}
                                />
                                <Legend />
                            </RadarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Reports List */}
                <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8">
                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">Recent Reports</h2>
                    <div className="space-y-3">
                        {reports.map((report) => (
                            <div
                                key={report.id}
                                className="flex items-center justify-between p-4 border border-gray-100 dark:border-neutral-800 rounded-xl hover:bg-gray-50 dark:hover:bg-neutral-900 transition-colors cursor-pointer"
                            >
                                <div className="flex items-center gap-4">
                                    <div className="bg-indigo-100 dark:bg-indigo-900/30 p-3 rounded-xl">
                                        <FileText className="w-5 h-5 text-indigo-600" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-800 dark:text-white">{report.name}</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">
                                            {report.date} • {report.candidates} candidates
                                        </p>
                                    </div>
                                </div>
                                <button className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium px-4 py-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
                                    <Download className="w-4 h-4" />
                                    Download
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Insights Section */}
                <div className="mt-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl shadow-soft p-8 text-white">
                    <div className="flex items-start gap-4">
                        <div className="bg-white/20 p-3 rounded-xl">
                            <TrendingUp className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold mb-2">Key Insights</h3>
                            <ul className="space-y-2 text-blue-50">
                                <li>• React skills are 20% above benchmark across all candidates</li>
                                <li>• Communication scores have improved by 15% this quarter</li>
                                <li>• Node.js proficiency needs attention - consider additional training</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Kiwi AI Assistant */}
            <ReportAssistant pageContext="skill_reports" />
        </div>
    );
};

export default SkillReports;

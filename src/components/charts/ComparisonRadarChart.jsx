import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const ComparisonRadarChart = ({ candidates }) => {
    // Transform data for comparison
    const skills = ['problemSolving', 'decisionConfidence', 'analyticalThinking', 'speedVsAccuracy', 'communication'];
    const skillLabels = {
        problemSolving: 'Task Completion',
        decisionConfidence: 'Decision Firmness',
        analyticalThinking: 'Deliberation',
        speedVsAccuracy: 'Speed vs Accuracy',
        communication: 'Explanation Style'
    };

    const data = skills.map(skill => {
        const dataPoint = { skill: skillLabels[skill], fullMark: 100 };
        candidates.forEach((candidate, index) => {
            dataPoint[`candidate${index + 1}`] = candidate.skills[skill];
        });
        return dataPoint;
    });

    const colors = ['#0ea5e9', '#d946ef', '#10b981', '#f59e0b'];

    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Skill Comparison</h3>
            <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis
                        dataKey="skill"
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: '#9ca3af', fontSize: 10 }}
                    />
                    {candidates.map((candidate, index) => (
                        <Radar
                            key={candidate.id}
                            name={candidate.name}
                            dataKey={`candidate${index + 1}`}
                            stroke={colors[index % colors.length]}
                            fill={colors[index % colors.length]}
                            fillOpacity={0.25}
                        />
                    ))}
                    <Legend wrapperStyle={{ color: '#9ca3af' }} />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px',
                            color: '#fff'
                        }}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default ComparisonRadarChart;

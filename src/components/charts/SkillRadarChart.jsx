import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const SkillRadarChart = ({ skills, candidateName }) => {
    const data = [
        { skill: 'Task Completion', value: skills.problemSolving, fullMark: 100 },
        { skill: 'Decision Firmness', value: skills.decisionConfidence, fullMark: 100 },
        { skill: 'Deliberation', value: skills.analyticalThinking, fullMark: 100 },
        { skill: 'Speed vs Accuracy', value: skills.speedVsAccuracy, fullMark: 100 },
        { skill: 'Explanation Style', value: skills.communication, fullMark: 100 },
    ];

    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
                {candidateName ? `${candidateName}'s Skill Profile` : 'Skill Profile'}
            </h3>
            <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis
                        dataKey="skill"
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: '#9ca3af', fontSize: 10 }}
                    />
                    <Radar
                        name={candidateName || 'Candidate'}
                        dataKey="value"
                        stroke="#0ea5e9"
                        fill="#0ea5e9"
                        fillOpacity={0.5}
                    />
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

export default SkillRadarChart;

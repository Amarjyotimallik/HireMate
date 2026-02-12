import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const BehavioralLineChart = ({ data, dataKey, title, color = "#0ea5e9", yAxisLabel }) => {
    return (
        <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis
                        dataKey="question"
                        label={{ value: 'Question #', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                    />
                    <YAxis
                        label={{ value: yAxisLabel, angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px',
                            color: '#fff'
                        }}
                    />
                    <Legend wrapperStyle={{ color: '#9ca3af' }} />
                    <Line
                        type="monotone"
                        dataKey={dataKey}
                        stroke={color}
                        strokeWidth={2}
                        dot={{ fill: color, r: 4 }}
                        activeDot={{ r: 6 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};

export default BehavioralLineChart;

import { useNavigate } from 'react-router-dom';
import { Eye, Calendar, Award, Mail, Phone } from 'lucide-react';

const CandidateCard = ({ candidate }) => {
    const navigate = useNavigate();

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/50';
            case 'in-progress': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
            case 'pending': return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
        }
    };

    const getStatusLabel = (status) => {
        switch (status) {
            case 'completed': return 'Completed';
            case 'in-progress': return 'In Progress';
            case 'pending': return 'Pending';
            default: return status;
        }
    };

    return (
        <div className="glass-card-hover p-6 cursor-pointer" onClick={() => navigate(`/candidate/${candidate.id}`)}>
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-lg">
                        {candidate.avatar}
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">{candidate.name}</h3>
                        <p className="text-sm text-gray-400">{candidate.position}</p>
                    </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(candidate.status)}`}>
                    {getStatusLabel(candidate.status)}
                </span>
            </div>

            <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Mail className="w-4 h-4" />
                    <span>{candidate.email}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Phone className="w-4 h-4" />
                    <span>{candidate.phone}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Calendar className="w-4 h-4" />
                    <span>Uploaded: {candidate.uploadDate}</span>
                </div>
            </div>

            {candidate.status === 'completed' && (
                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <div className="flex items-center gap-2">
                        <Award className="w-5 h-5 text-yellow-400" />
                        <span className="text-sm text-gray-400">Overall Score:</span>
                    </div>
                    <span className="text-2xl font-bold text-gradient">{candidate.overallScore}%</span>
                </div>
            )}

            {candidate.status === 'in-progress' && (
                <div className="pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-400">Progress</span>
                        <span className="text-white font-semibold">{candidate.currentQuestion}/{candidate.totalQuestions}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                            className="bg-gradient-to-r from-primary-500 to-secondary-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${(candidate.currentQuestion / candidate.totalQuestions) * 100}%` }}
                        />
                    </div>
                </div>
            )}

            <button className="w-full mt-4 flex items-center justify-center gap-2 btn-outline py-2">
                <Eye className="w-4 h-4" />
                View Details
            </button>
        </div>
    );
};

export default CandidateCard;

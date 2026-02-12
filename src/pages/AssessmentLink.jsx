import { useState } from 'react';
import { Link2, Copy, Mail, Check, ExternalLink, Loader2 } from 'lucide-react';
import { apiGet, apiPost, assessmentLinkUrl } from '../api/client';

const AssessmentLink = () => {
    const [copied, setCopied] = useState(false);
    const [email, setEmail] = useState('');
    const [assessmentLink, setAssessmentLink] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleGenerateLink = async () => {
        if (!email || !email.includes('@')) {
            setError('Please enter a valid candidate email address');
            return;
        }
        setLoading(true);
        setError('');
        setAssessmentLink('');
        try {
            const tasksRes = await apiGet('tasks?page=1&page_size=10');
            const taskIds = (tasksRes.tasks || []).slice(0, 5).map((t) => t.id);
            if (taskIds.length === 0) {
                setError('No tasks found. Run backend seed: python scripts/seed_tasks.py');
                return;
            }
            const attempt = await apiPost('attempts', {
                candidate_info: {
                    name: email.split('@')[0],
                    email: email,
                    position: 'Software Engineer',
                },
                task_ids: taskIds,
                expires_in_days: 7,
            });
            const link = assessmentLinkUrl(attempt.token);
            setAssessmentLink(link);
        } catch (err) {
            setError(err.json?.detail || err.message || 'Failed to create assessment link. Please ensure you are logged in.');
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        if (!assessmentLink) return;
        navigator.clipboard.writeText(assessmentLink);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleOpenTest = () => {
        if (!assessmentLink) return;
        window.open(assessmentLink, '_blank');
    };

    const handleSendEmail = (e) => {
        e.preventDefault();
        if (!assessmentLink) return;
        alert(`Link copied. Open it in the same browser to take the test: ${assessmentLink}`);
        setEmail('');
    };

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">Assessment Link</h1>
                    <p className="text-gray-600 dark:text-gray-400">Generate and share assessment links with candidates</p>
                </div>

                {/* Main Card */}
                <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8 mb-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-xl">
                            <Link2 className="w-6 h-6 text-blue-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Assessment Link</h2>
                    </div>

                    {error && (
                        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Generate link */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                            Candidate email <span className="text-red-500">*</span>
                        </label>
                        <div className="flex gap-2 mb-4">
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="candidate@example.com"
                                required
                                className="flex-1 bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <button
                                type="button"
                                onClick={handleGenerateLink}
                                disabled={loading}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl transition-colors flex items-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    'Generate link'
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Link Display */}
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                            Share this link with candidates (or open in same browser to take the test)
                        </label>
                        <div className="flex gap-2">
                            <div className="flex-1 bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-700 dark:text-gray-200 font-mono text-sm break-all">
                                {assessmentLink || 'Generate a link above'}
                            </div>
                            <button
                                onClick={handleCopy}
                                disabled={!assessmentLink}
                                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl transition-colors flex items-center gap-2"
                            >
                                {copied ? (
                                    <>
                                        <Check className="w-5 h-5" />
                                        Copied!
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-5 h-5" />
                                        Copy
                                    </>
                                )}
                            </button>
                            <button
                                onClick={handleOpenTest}
                                disabled={!assessmentLink}
                                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-6 py-3 rounded-xl transition-colors flex items-center gap-2"
                            >
                                <ExternalLink className="w-5 h-5" />
                                Open test in new tab
                            </button>
                        </div>
                    </div>

                    {/* Email Form */}
                    <div className="border-t border-gray-200 dark:border-neutral-700 pt-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Send via Email</h3>
                        <form onSubmit={handleSendEmail} className="flex gap-3">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
                                    Candidate Email
                                </label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="candidate@example.com"
                                    className="w-full bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <button
                                type="submit"
                                className="self-end bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white px-6 py-3 rounded-xl transition-all flex items-center gap-2"
                            >
                                <Mail className="w-5 h-5" />
                                Send Link
                            </button>
                        </form>
                    </div>

                    {/* Instructions */}
                    <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-4">
                        <h4 className="font-semibold text-gray-800 dark:text-white mb-2 flex items-center gap-2">
                            <ExternalLink className="w-4 h-4" />
                            How it works
                        </h4>
                        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 ml-6 list-disc">
                            <li>Click &quot;Generate link&quot; to create a real assessment (uses current URL, e.g. localhost:5173)</li>
                            <li>Copy the link or click &quot;Open test in new tab&quot; to take the assessment as a candidate in the same browser</li>
                            <li>Backend must be running and seeded (python scripts/seed_tasks.py). Use DEV_MODE=true to skip login</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AssessmentLink;

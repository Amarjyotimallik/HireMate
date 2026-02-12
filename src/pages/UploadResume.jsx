import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, Copy, ChevronRight, ArrowLeft, Loader2, ExternalLink, Mail, Users } from 'lucide-react';
import { apiGet, apiPost, assessmentLinkUrl } from '../api/client';
import TopNav from '../components/layout/TopNav';

const UploadResume = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1); // 1: Upload, 2: Confirm Email, 3: Success
    const [file, setFile] = useState(null);
    const [email, setEmail] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [assessmentLink, setAssessmentLink] = useState('');
    const [candidateData, setCandidateData] = useState({
        name: '',
        position: '',
        email: '',
        skills: [],
        resume_text: ''
    });
    const [linkLoading, setLinkLoading] = useState(false);
    const [linkError, setLinkError] = useState('');
    const [uploadError, setUploadError] = useState('');
    const [emailSending, setEmailSending] = useState(false);
    const [emailSent, setEmailSent] = useState(false);
    const [attemptId, setAttemptId] = useState('');

    // Drag and drop handlers
    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDragIn = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragOut = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileUpload(files[0]);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    };

    const handleFileUpload = async (uploadedFile) => {
        setFile(uploadedFile);
        setIsProcessing(true);
        setUploadError('');

        try {
            const formData = new FormData();
            formData.append('file', uploadedFile);

            // Use backend AI parsing
            const token = localStorage.getItem('hiremate_access_token');
            if (!token) {
                throw new Error('Please log in to upload resumes');
            }
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v1/resume/parse`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Failed to parse resume (${response.status}). Please ensure the file is a valid PDF or text document.`);
            }

            const data = await response.json();
            const extracted = data.candidate_info;

            if (extracted.email && !email) {
                setEmail(extracted.email);
            }

            const resumeText = data.resume_text || extracted.resume_text || '';
            setCandidateData({
                name: extracted.name || '',
                position: extracted.position || '',
                email: extracted.email || email || '',
                skills: extracted.skills || [],
                resume_text: resumeText
            });
            setIsProcessing(false);

            // Fetch and log ATS score right after parse (resume-only, no JD)
            if (resumeText && resumeText.trim()) {
                try {
                    const atsResult = await apiPost('resume/ats-score', {
                        resume_text: resumeText,
                        job_description: ''
                    });
                    console.log('[UploadResume] ATS Score (after parse):', atsResult);
                    console.log('[UploadResume] ATS Score value:', atsResult?.ats_score ?? 'N/A', 'Breakdown:', atsResult?.breakdown ?? {});
                } catch (e) {
                    console.warn('[UploadResume] ATS score request failed:', e);
                }
            } else {
                console.log('[UploadResume] No resume text to score — ATS not calculated.');
            }

            if (!extracted.name) {
                console.warn('AI could not extract name confidently.');
            }
        } catch (error) {
            console.error('Error processing resume:', error);
            let msg = error.message || 'Failed to parse resume. Please try again.';

            // Provide user-friendly error messages
            if (error.message.includes('network') || error.message.includes('fetch')) {
                msg = 'Network error. Please check your internet connection and try again.';
            } else if (error.message.includes('login') || error.message.includes('token')) {
                msg = 'Session expired. Please log in again.';
            } else if (error.message.includes('PDF') || error.message.includes('format')) {
                msg = 'Invalid file format. Please upload a PDF or text document.';
            }

            setUploadError(msg);
            setIsProcessing(false);
            setFile(null); // Clear file on error
        }
    };

    // Extract text from file based on type
    const extractTextFromFile = async (fileContent, fileType) => {
        if (fileContent == null) return '';
        if (typeof fileContent === 'string') return fileContent;
        try {
            return String(fileContent);
        } catch (_) {
            return '';
        }
    };

    // Parse resume data to extract name, email, position
    const parseResumeData = (text) => {
        const data = { name: '', email: '', position: '' };
        if (!text || typeof text !== 'string') return data;
        const str = String(text);

        // Extract email using regex
        const emailRegex = new RegExp('([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z0-9_-]+)');
        const emailMatch = str.match(emailRegex);
        if (emailMatch) {
            data.email = emailMatch[0];
        }

        // Extract name (usually first line or after "Name:")
        const lines = str.split('\n').filter((line) => line.trim().length > 0);

        // Try to find name
        const namePatterns = [
            new RegExp('Name[:\\s]+([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)', 'i'),
            new RegExp('^([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)\\s*$', 'm')
        ];

        for (const pattern of namePatterns) {
            const nameMatch = str.match(pattern);
            if (nameMatch && nameMatch[1] && nameMatch[1].split(' ').length >= 2) {
                data.name = nameMatch[1].trim();
                break;
            }
        }

        // If no name found via patterns, check first few lines for capitalized names
        if (!data.name && lines.length > 0) {
            const nameLineRegex = new RegExp('^[A-Z][a-z]+(?:\\s+[A-Z][a-z]+){1,3}$');
            const digitRegex = new RegExp('\\d');
            for (let i = 0; i < Math.min(3, lines.length); i++) {
                const line = lines[i].trim();
                if (nameLineRegex.test(line) && !digitRegex.test(line)) {
                    data.name = line;
                    break;
                }
            }
        }

        // Extract position/title
        const positionKeywords = [
            'Developer', 'Engineer', 'Designer', 'Manager', 'Analyst',
            'Architect', 'Consultant', 'Specialist', 'Lead', 'Senior',
            'Junior', 'Full Stack', 'Backend', 'Frontend', 'DevOps'
        ];

        for (const keyword of positionKeywords) {
            const regex = new RegExp(`([\\w\\s]*${keyword}[\\w\\s]*)`, 'i');
            const posMatch = str.match(regex);
            if (posMatch && posMatch[1] && posMatch[1].length < 50) {
                data.position = posMatch[1].trim();
                break;
            }
        }

        return data;
    };

    const handleGenerateAssessment = () => {
        if (!email || !file) return;
        setStep(2);
    };

    const handleConfirmEmail = async () => {
        setLinkLoading(true);
        setLinkError('');
        setAssessmentLink('');
        try {
            const candidateEmail = email || candidateData.email || 'demo@test.com';

            // Call attempt creation (Backend determines if task generation is needed)
            const attempt = await apiPost('attempts', {
                candidate_info: {
                    name: candidateData.name?.trim() || 'Candidate',
                    email: candidateEmail,
                    position: candidateData.position?.trim() || 'General Candidate',
                    skills: candidateData.skills || [],
                    resume_text: candidateData.resume_text || '',
                },
                task_ids: [], // Empty list triggers dynamic generation
                expires_in_days: 7,
            });
            setAssessmentLink(assessmentLinkUrl(attempt.token));
            setAttemptId(attempt.id);
            setStep(3);
        } catch (err) {
            const detail = err && typeof err.json === 'object' ? err.json.detail : undefined;
            const errorMsg = Array.isArray(detail)
                ? (detail[0] && detail[0].msg != null ? detail[0].msg : detail.map((d) => (d && d.msg != null ? d.msg : d)).join(', '))
                : (typeof detail === 'string' ? detail : (err && err.message) || 'Unknown error');
            setLinkError(errorMsg || 'Failed to create assessment link. Is the backend running with DEV_MODE or auth?');
        } finally {
            setLinkLoading(false);
        }
    };

    const handleCopyLink = () => {
        if (!assessmentLink) return;
        navigator.clipboard.writeText(assessmentLink);
        alert('Assessment link copied to clipboard!');
    };

    const handleOpenTest = () => {
        if (!assessmentLink) return;
        window.open(assessmentLink, '_blank');
    };

    const handleSendEmail = async () => {
        if (!attemptId || !email) return;
        setEmailSending(true);
        try {
            const response = await apiPost('email/send-assessment', {
                attempt_id: attemptId,
                to_email: email,
            });
            if (response.success) {
                setEmailSent(true);
                alert(`✅ Email sent successfully to ${email}!`);
            }
        } catch (err) {
            const errorMsg = err?.message || 'Failed to send email';
            alert(`❌ ${errorMsg}`);
        } finally {
            setEmailSending(false);
        }
    };

    const handleCreateAnother = () => {
        setStep(1);
        setFile(null);
        setEmail('');
        setIsProcessing(false);
        setAssessmentLink('');
        setLinkError('');
        setUploadError('');
        setLinkLoading(false);
        setCandidateData({ name: '', position: '', email: '', skills: [], resume_text: '' });
        setEmailSending(false);
        setEmailSent(false);
        setAttemptId('');
    };

    return (
        <div className="flex-1 min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-black dark:via-neutral-950 dark:to-black transition-colors duration-300">
            {/* Top Navigation */}
            <TopNav />

            {/* Main Content */}
            <div className="p-8 max-w-[1400px] mx-auto">
                <div className="max-w-2xl mx-auto">
                    {/* Step 1: Upload Resume */}
                    {step === 1 && (
                        <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8 transition-colors duration-300">
                            {/* Bulk Upload Feature Banner */}
                            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800/30">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
                                            <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-800 dark:text-white">Need to upload multiple resumes?</h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400">Try our new Bulk Upload feature with parallel processing!</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => navigate('/bulk-upload')}
                                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                                    >
                                        <Users className="w-4 h-4" />
                                        Bulk Upload
                                    </button>
                                </div>
                            </div>

                            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-8">Upload Resume</h1>

                            {/* Upload Area */}
                            <div className="mb-8">
                                <div className="flex flex-col items-center mb-6">
                                    <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-2xl mb-4">
                                        <FileText className="w-12 h-12 text-blue-600" />
                                    </div>
                                    <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-2">Upload Resume</h2>
                                </div>

                                <div
                                    className={`border-2 border-dashed rounded-2xl p-12 transition-all text-center ${isDragging
                                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                        : 'border-gray-300 dark:border-neutral-700 hover:border-blue-400 bg-gray-50 dark:bg-neutral-900/50'
                                        }`}
                                    onDragEnter={handleDragIn}
                                    onDragLeave={handleDragOut}
                                    onDragOver={handleDrag}
                                    onDrop={handleDrop}
                                >
                                    {file ? (
                                        <div className="space-y-3">
                                            <div className="w-16 h-16 mx-auto rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                                <CheckCircle className="w-8 h-8 text-green-600" />
                                            </div>
                                            <div>
                                                <p className="text-gray-800 dark:text-white font-semibold">{file.name}</p>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">{(file.size / 1024).toFixed(2)} KB</p>
                                            </div>
                                            {isProcessing && (
                                                <p className="text-sm text-blue-600 animate-pulse font-medium">
                                                    Analyzing resume structure and extracting skills with AI...
                                                </p>
                                            )}
                                            {uploadError && (
                                                <p className="text-sm text-red-600 font-medium">
                                                    {uploadError}
                                                </p>
                                            )}
                                            {!isProcessing && !uploadError && candidateData.name && (
                                                <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                                                    <p className="text-sm font-semibold text-green-800 dark:text-green-300 mb-2">
                                                        ✅ Resume Processed Successfully
                                                    </p>
                                                    <div className="space-y-1 text-sm">
                                                        {candidateData.name && (
                                                            <p className="text-gray-700 dark:text-gray-300">
                                                                <span className="font-medium">Name:</span> {candidateData.name}
                                                            </p>
                                                        )}
                                                        {candidateData.position && (
                                                            <p className="text-gray-700 dark:text-gray-300">
                                                                <span className="font-medium">Position:</span> {candidateData.position}
                                                            </p>
                                                        )}
                                                        {candidateData.email && (
                                                            <p className="text-gray-700 dark:text-gray-300">
                                                                <span className="font-medium">Email:</span> {candidateData.email}
                                                            </p>
                                                        )}
                                                        {candidateData.skills && candidateData.skills.length > 0 && (
                                                            <p className="text-gray-700 dark:text-gray-300">
                                                                <span className="font-medium">Skills:</span> {candidateData.skills.slice(0, 5).join(', ')}{candidateData.skills.length > 5 ? '...' : ''}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            <div className="w-16 h-16 mx-auto rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                                <Upload className="w-8 h-8 text-blue-600" />
                                            </div>
                                            <div>
                                                <p className="text-gray-700 dark:text-gray-300 font-medium mb-1">
                                                    Drag and drop a resume, or
                                                </p>
                                                <label className="inline-block">
                                                    <input
                                                        type="file"
                                                        className="hidden"
                                                        accept=".pdf,.doc,.docx"
                                                        onChange={handleFileChange}
                                                    />
                                                    <span className="text-blue-600 hover:text-blue-700 font-medium cursor-pointer underline">
                                                        upload Doc - micro-resume
                                                    </span>
                                                </label>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Email Input */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    Enter Candidate Email
                                </label>
                                <input
                                    type="email"
                                    value={email || candidateData.email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Candidate@email.com"
                                    className="w-full bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300"
                                />
                            </div>

                            {/* Generate Button */}
                            <button
                                onClick={handleGenerateAssessment}
                                disabled={!file || (!email && !candidateData.email) || isProcessing}
                                className="w-full bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 shadow-md hover:shadow-xl hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                            >
                                Generate Assessment
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    )}

                    {/* Step 2: Confirm Email */}
                    {step === 2 && (
                        <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8 transition-colors duration-300">
                            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-8">Confirm Candidate Email</h1>

                            {linkError && (
                                <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 text-sm">
                                    {linkError}
                                </div>
                            )}

                            {/* Candidate Profile */}
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                                    <span className="text-white text-xl font-bold">
                                        {(candidateData.name || 'DC').split(' ').map(n => n[0]).join('')}
                                    </span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-gray-800 dark:text-white">{candidateData.name || 'Demo Candidate'}</h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">{candidateData.position || 'Software Engineer'}</p>
                                </div>
                            </div>

                            {/* Email Confirmation */}
                            <div className="mb-8">
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                    Is this the candidate's correct email?
                                </label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-gray-50 dark:bg-neutral-900 border border-gray-200 dark:border-neutral-700 rounded-xl px-4 py-3 text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-300"
                                />
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setStep(1)}
                                    className="px-6 py-3 rounded-xl border border-gray-300 dark:border-neutral-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800 font-medium transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-2"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                    Back
                                </button>
                                <button
                                    type="button"
                                    onClick={handleConfirmEmail}
                                    disabled={linkLoading}
                                    className="flex-1 bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 disabled:opacity-50 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 shadow-md hover:shadow-xl hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                                >
                                    {linkLoading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Generating interview questions...
                                        </>
                                    ) : (
                                        'Confirm & Generate'
                                    )}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Assessment Generated */}
                    {step === 3 && (
                        <div className="bg-white dark:bg-neutral-950 rounded-2xl shadow-soft border border-gray-100 dark:border-neutral-800 p-8 transition-colors duration-300">
                            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">Assessment Generated!</h1>

                            {linkError && (
                                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6 text-red-700 dark:text-red-400 text-sm">
                                    {linkError}
                                </div>
                            )}
                            {/* Success Message */}
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 mb-6 flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                                <div>
                                    <p className="text-green-800 dark:text-green-300 font-medium">
                                        Assessment link created. Open it in the same browser to take the test.
                                    </p>
                                    <p className="text-sm text-green-700 dark:text-green-400 mt-1">
                                        Copy the link below or click &quot;Open test in new tab&quot; to take the assessment as the candidate.
                                    </p>
                                </div>
                            </div>

                            {/* Create Another Button */}
                            <button
                                onClick={handleCreateAnother}
                                className="w-full mb-6 bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 shadow-md hover:shadow-xl hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                            >
                                Create Another Assessment
                                <ChevronRight className="w-5 h-5" />
                            </button>

                            {/* Candidate Card */}
                            <div className="border border-gray-200 dark:border-neutral-800 rounded-xl p-6">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                                        <span className="text-white font-bold">
                                            {(candidateData.name || 'DC').split(' ').map(n => n[0]).join('')}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-bold text-gray-800 dark:text-white">{candidateData.name || 'Demo Candidate'}</h3>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">{candidateData.position || 'Software Engineer'}</p>
                                        <p className="text-sm text-blue-600 mt-1">{email || candidateData.email || '—'}</p>
                                    </div>
                                </div>

                                {/* Assessment Link */}
                                <div className="bg-gray-50 dark:bg-neutral-900/50 rounded-lg p-3 mb-3">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <code className="flex-1 min-w-0 text-sm text-gray-700 dark:text-gray-300 break-all">
                                            {assessmentLink}
                                        </code>
                                        <button
                                            onClick={handleCopyLink}
                                            className="bg-white dark:bg-neutral-700 border border-gray-300 dark:border-neutral-600 hover:bg-gray-100 dark:hover:bg-neutral-600 p-2 rounded-lg transition-all duration-200 hover:scale-110 active:scale-95"
                                        >
                                            <Copy className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                                        </button>
                                        <button
                                            onClick={handleOpenTest}
                                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1 text-sm shadow-md hover:shadow-lg"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                            Open test in new tab
                                        </button>
                                        <button
                                            onClick={handleSendEmail}
                                            disabled={emailSending || emailSent}
                                            className={`px-3 py-2 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1 text-sm shadow-md hover:shadow-lg ${emailSent
                                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                                                } disabled:opacity-70`}
                                        >
                                            {emailSending ? (
                                                <><Loader2 className="w-4 h-4 animate-spin" /> Sending...</>
                                            ) : emailSent ? (
                                                <><CheckCircle className="w-4 h-4" /> Email Sent!</>
                                            ) : (
                                                <><Mail className="w-4 h-4" /> Send to Email</>
                                            )}
                                        </button>
                                    </div>
                                </div>

                                {/* Details */}
                                <div className="grid grid-cols-3 gap-3 text-sm">
                                    <div>
                                        <p className="text-gray-500 dark:text-gray-400">Generated</p>
                                        <p className="font-medium text-gray-800 dark:text-white">Just now</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-500 dark:text-gray-400">Questions</p>
                                        <p className="font-medium text-gray-800 dark:text-white">10 Challenges</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-500 dark:text-gray-400">Time Limit</p>
                                        <p className="font-medium text-gray-800 dark:text-white">10 minutes</p>
                                    </div>
                                </div>
                            </div>

                            {/* View All Candidates */}
                            <button
                                onClick={() => navigate('/candidates')}
                                className="w-full mt-6 border border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 font-medium py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                            >
                                View All Candidates
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UploadResume;

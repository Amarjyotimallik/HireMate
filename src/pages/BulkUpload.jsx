import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Upload, FileText, CheckCircle, XCircle, Clock, Mail,
    Copy, ExternalLink, ArrowLeft, Loader2, FolderOpen,
    Trash2, RotateCcw, Download, Send, X, AlertCircle,
    ChevronDown, ChevronUp, Users, Zap, Shield
} from 'lucide-react';
import { getAuthToken, apiUrl, assessmentLinkUrl } from '../api/client';
import TopNav from '../components/layout/TopNav';

const BulkUpload = () => {
    const navigate = useNavigate();

    // ── State ──────────────────────────────────────────────────
    const [phase, setPhase] = useState('upload'); // 'upload' | 'processing' | 'results'
    const [files, setFiles] = useState([]);
    const [isDragging, setIsDragging] = useState(false);
    const [jobId, setJobId] = useState(null);
    const [jobStatus, setJobStatus] = useState(null);
    const [error, setError] = useState('');
    const [selectedResults, setSelectedResults] = useState(new Set());
    const [emailSending, setEmailSending] = useState(false);
    const [emailResults, setEmailResults] = useState(null);
    const [copiedLink, setCopiedLink] = useState(null);
    const [expandedRow, setExpandedRow] = useState(null);

    const fileInputRef = useRef(null);
    const folderInputRef = useRef(null);
    const pollRef = useRef(null);

    // ── Drag & Drop ────────────────────────────────────────────
    const handleDrag = (e) => { e.preventDefault(); e.stopPropagation(); };
    const handleDragIn = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); };
    const handleDragOut = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); };

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        const dropped = Array.from(e.dataTransfer.files);
        addFiles(dropped);
    }, [files]);

    const addFiles = (newFiles) => {
        const validExts = ['.pdf', '.txt', '.docx'];
        const maxSize = 10 * 1024 * 1024;
        const filtered = newFiles.filter(f => {
            const ext = '.' + f.name.split('.').pop().toLowerCase();
            return validExts.includes(ext) && f.size <= maxSize && f.size > 0;
        });
        setFiles(prev => {
            const existing = new Set(prev.map(f => f.name + f.size));
            const unique = filtered.filter(f => !existing.has(f.name + f.size));
            return [...prev, ...unique];
        });
        if (filtered.length < newFiles.length) {
            setError(`${newFiles.length - filtered.length} file(s) skipped (unsupported format or too large).`);
            setTimeout(() => setError(''), 5000);
        }
    };

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const clearFiles = () => setFiles([]);

    // ── Upload ─────────────────────────────────────────────────
    const startBulkUpload = async () => {
        if (files.length === 0) return;
        setError('');
        setPhase('processing');

        try {
            const token = getAuthToken();
            if (!token) throw new Error('Please log in to upload resumes');

            const formData = new FormData();
            files.forEach(f => formData.append('files', f));

            const url = apiUrl('/bulk/create');
            const res = await fetch(url, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Upload failed (${res.status})`);
            }

            const data = await res.json();
            setJobId(data.job_id);

            // Start polling
            startPolling(data.job_id);
        } catch (err) {
            setError(err.message);
            setPhase('upload');
        }
    };

    // ── Polling ────────────────────────────────────────────────
    const startPolling = (id) => {
        if (pollRef.current) clearInterval(pollRef.current);

        const poll = async () => {
            try {
                const token = getAuthToken();
                const url = apiUrl(`/bulk/status/${id}`);
                const res = await fetch(url, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (!res.ok) return;
                const status = await res.json();
                setJobStatus(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setPhase('results');
                }
            } catch (_) { /* ignore */ }
        };

        poll(); // immediate first call
        pollRef.current = setInterval(poll, 2000);
    };

    useEffect(() => {
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, []);

    // ── Bulk Email ─────────────────────────────────────────────
    const sendBulkEmails = async () => {
        const ids = Array.from(selectedResults);
        if (ids.length === 0) return;
        setEmailSending(true);
        setEmailResults(null);

        try {
            const token = getAuthToken();
            const url = apiUrl('/bulk/email');
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ assessment_ids: ids }),
            });
            const data = await res.json();
            setEmailResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setEmailSending(false);
        }
    };

    // ── Copy Link ──────────────────────────────────────────────
    const copyLink = (token) => {
        navigator.clipboard.writeText(assessmentLinkUrl(token));
        setCopiedLink(token);
        setTimeout(() => setCopiedLink(null), 2000);
    };

    // ── Select All / None ──────────────────────────────────────
    const toggleSelectAll = () => {
        if (!jobStatus?.results) return;
        const successIds = jobStatus.results
            .filter(r => r.status === 'success' && r.assessment_id)
            .map(r => r.assessment_id);
        if (selectedResults.size === successIds.length) {
            setSelectedResults(new Set());
        } else {
            setSelectedResults(new Set(successIds));
        }
    };

    // ── Export CSV ─────────────────────────────────────────────
    const exportCSV = () => {
        if (!jobStatus?.results) return;
        const header = 'Filename,Candidate,Email,Position,Status,Assessment Link\n';
        const rows = jobStatus.results.map(r => {
            const link = r.assessment_token ? assessmentLinkUrl(r.assessment_token) : '';
            return `"${r.filename}","${r.candidate_name || ''}","${r.candidate_email || ''}","${r.position || ''}","${r.status}","${link}"`;
        }).join('\n');
        const blob = new Blob([header + rows], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bulk_assessments_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // ── Format Helpers ─────────────────────────────────────────
    const formatSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    const progressPercent = jobStatus
        ? Math.round((jobStatus.processed_count / Math.max(jobStatus.total_files, 1)) * 100)
        : 0;

    // ── Styles ─────────────────────────────────────────────────
    const styles = {
        page: {
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0a12 100%)',
            color: '#e2e8f0',
        },
        container: {
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '32px 24px',
        },
        header: {
            marginBottom: '32px',
        },
        backBtn: {
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            color: '#94a3b8',
            fontSize: '14px',
            cursor: 'pointer',
            marginBottom: '16px',
            background: 'none',
            border: 'none',
            transition: 'color 0.2s',
        },
        title: {
            fontSize: '32px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #818cf8, #a78bfa, #c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0,
        },
        subtitle: {
            color: '#94a3b8',
            fontSize: '16px',
            marginTop: '8px',
        },
        card: {
            background: 'rgba(15, 15, 25, 0.8)',
            border: '1px solid rgba(99, 102, 241, 0.15)',
            borderRadius: '16px',
            backdropFilter: 'blur(20px)',
            overflow: 'hidden',
        },
        cardHeader: {
            padding: '24px',
            borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
        },
        cardBody: {
            padding: '24px',
        },
        dropzone: (active) => ({
            border: `2px dashed ${active ? '#818cf8' : 'rgba(99, 102, 241, 0.25)'}`,
            borderRadius: '12px',
            padding: '48px 24px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.3s',
            background: active
                ? 'rgba(99, 102, 241, 0.08)'
                : 'rgba(15, 15, 25, 0.4)',
            transform: active ? 'scale(1.01)' : 'none',
        }),
        fileList: {
            maxHeight: '320px',
            overflowY: 'auto',
            marginTop: '16px',
        },
        fileItem: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderRadius: '10px',
            background: 'rgba(30, 30, 50, 0.5)',
            marginBottom: '8px',
            transition: 'background 0.2s',
        },
        btn: (variant = 'primary') => ({
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            borderRadius: '12px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: 'pointer',
            border: 'none',
            transition: 'all 0.3s',
            ...(variant === 'primary' ? {
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
            } : variant === 'secondary' ? {
                background: 'rgba(99, 102, 241, 0.1)',
                color: '#a5b4fc',
                border: '1px solid rgba(99, 102, 241, 0.2)',
            } : variant === 'success' ? {
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)',
            } : {
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.2)',
            }),
        }),
        progressBar: {
            width: '100%',
            height: '8px',
            background: 'rgba(99, 102, 241, 0.1)',
            borderRadius: '4px',
            overflow: 'hidden',
        },
        progressFill: (pct) => ({
            width: `${pct}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #6366f1, #a78bfa)',
            borderRadius: '4px',
            transition: 'width 0.5s ease',
        }),
        statsRow: {
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '16px',
            marginBottom: '24px',
        },
        stat: (color) => ({
            padding: '20px',
            borderRadius: '12px',
            background: 'rgba(15, 15, 25, 0.6)',
            border: '1px solid rgba(99, 102, 241, 0.1)',
            textAlign: 'center',
            borderTop: `3px solid ${color}`,
        }),
        statValue: {
            fontSize: '28px',
            fontWeight: 700,
            margin: '4px 0',
        },
        statLabel: {
            color: '#94a3b8',
            fontSize: '13px',
        },
        table: {
            width: '100%',
            borderCollapse: 'separate',
            borderSpacing: 0,
        },
        th: {
            padding: '12px 16px',
            textAlign: 'left',
            fontSize: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            color: '#94a3b8',
            borderBottom: '1px solid rgba(99, 102, 241, 0.1)',
        },
        td: {
            padding: '14px 16px',
            borderBottom: '1px solid rgba(99, 102, 241, 0.05)',
            fontSize: '14px',
            verticalAlign: 'middle',
        },
        statusBadge: (status) => ({
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 10px',
            borderRadius: '999px',
            fontSize: '12px',
            fontWeight: 600,
            ...(status === 'success' ? {
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#34d399',
            } : status === 'failed' ? {
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#f87171',
            } : {
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#a5b4fc',
            }),
        }),
        checkbox: {
            width: '18px',
            height: '18px',
            borderRadius: '4px',
            accentColor: '#6366f1',
            cursor: 'pointer',
        },
        errorBanner: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '14px 20px',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: '#f87171',
            fontSize: '14px',
            marginBottom: '16px',
        },
        actionBar: {
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            flexWrap: 'wrap',
        },
        uploadBtnGroup: {
            display: 'flex',
            gap: '12px',
            justifyContent: 'center',
            marginTop: '20px',
        },
    };

    // ═══════════════════════════════════════════════════════════
    //  Phase 1: Upload
    // ═══════════════════════════════════════════════════════════
    const renderUploadPhase = () => (
        <div style={styles.card}>
            <div style={styles.cardHeader}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: '40px', height: '40px', borderRadius: '12px',
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <Upload size={20} color="#fff" />
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Upload Resumes</h3>
                        <p style={{ margin: 0, color: '#94a3b8', fontSize: '13px' }}>
                            PDF, TXT, or DOCX — up to 100 files
                        </p>
                    </div>
                </div>
                {files.length > 0 && (
                    <button onClick={clearFiles} style={{ ...styles.btn('danger'), padding: '8px 16px' }}>
                        <Trash2 size={14} /> Clear All
                    </button>
                )}
            </div>

            <div style={styles.cardBody}>
                {/* Dropzone */}
                <div
                    style={styles.dropzone(isDragging)}
                    onDragOver={handleDrag}
                    onDragEnter={handleDragIn}
                    onDragLeave={handleDragOut}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                >
                    <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        background: 'rgba(99, 102, 241, 0.1)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 16px',
                    }}>
                        <Upload size={28} color="#818cf8" />
                    </div>
                    <p style={{ fontSize: '16px', fontWeight: 600, margin: '0 0 8px' }}>
                        {isDragging ? 'Drop files here' : 'Drag & drop resumes here'}
                    </p>
                    <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
                        or click to browse • supports PDF, TXT, DOCX
                    </p>

                    <div style={styles.uploadBtnGroup}>
                        <button
                            onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                            style={{ ...styles.btn('secondary'), padding: '10px 20px' }}
                        >
                            <FileText size={16} /> Select Files
                        </button>
                        <button
                            onClick={(e) => { e.stopPropagation(); folderInputRef.current?.click(); }}
                            style={{ ...styles.btn('secondary'), padding: '10px 20px' }}
                        >
                            <FolderOpen size={16} /> Select Folder
                        </button>
                    </div>
                </div>

                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.docx"
                    style={{ display: 'none' }}
                    onChange={(e) => { addFiles(Array.from(e.target.files)); e.target.value = ''; }}
                />
                <input
                    ref={folderInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.txt,.docx"
                    style={{ display: 'none' }}
                    {...{ webkitdirectory: '', directory: '' }}
                    onChange={(e) => { addFiles(Array.from(e.target.files)); e.target.value = ''; }}
                />

                {/* File List */}
                {files.length > 0 && (
                    <>
                        <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            marginTop: '24px', marginBottom: '12px',
                        }}>
                            <span style={{ fontWeight: 600 }}>
                                {files.length} file{files.length > 1 ? 's' : ''} selected
                            </span>
                            <span style={{ color: '#94a3b8', fontSize: '13px' }}>
                                Total: {formatSize(files.reduce((s, f) => s + f.size, 0))}
                            </span>
                        </div>

                        <div style={styles.fileList}>
                            {files.map((f, i) => (
                                <div key={f.name + f.size} style={styles.fileItem}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <FileText size={18} color="#818cf8" />
                                        <div>
                                            <div style={{ fontSize: '14px', fontWeight: 500 }}>{f.name}</div>
                                            <div style={{ fontSize: '12px', color: '#94a3b8' }}>{formatSize(f.size)}</div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => removeFile(i)}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            color: '#94a3b8', padding: '4px',
                                        }}
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
                            <button
                                onClick={startBulkUpload}
                                style={styles.btn('primary')}
                            >
                                <Zap size={16} /> Process {files.length} Resume{files.length > 1 ? 's' : ''}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );

    // ═══════════════════════════════════════════════════════════
    //  Phase 2: Processing
    // ═══════════════════════════════════════════════════════════
    const renderProcessingPhase = () => (
        <div style={styles.card}>
            <div style={styles.cardBody}>
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <div style={{
                        width: '80px', height: '80px', borderRadius: '50%',
                        background: 'rgba(99, 102, 241, 0.1)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 24px',
                        animation: 'pulse 2s ease-in-out infinite',
                    }}>
                        <Loader2 size={36} color="#818cf8" style={{ animation: 'spin 1.5s linear infinite' }} />
                    </div>

                    <h2 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 8px' }}>
                        Processing Resumes...
                    </h2>
                    <p style={{ color: '#94a3b8', fontSize: '16px', margin: '0 0 32px' }}>
                        AI is parsing resumes and generating personalized assessments
                    </p>

                    {/* Progress Bar */}
                    <div style={{ maxWidth: '500px', margin: '0 auto' }}>
                        <div style={{
                            display: 'flex', justifyContent: 'space-between',
                            fontSize: '14px', marginBottom: '8px',
                        }}>
                            <span style={{ color: '#94a3b8' }}>
                                {jobStatus?.current_file || 'Starting...'}
                            </span>
                            <span style={{
                                fontWeight: 700,
                                background: 'linear-gradient(135deg, #818cf8, #a78bfa)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                            }}>
                                {progressPercent}%
                            </span>
                        </div>
                        <div style={styles.progressBar}>
                            <div style={styles.progressFill(progressPercent)} />
                        </div>
                        <div style={{
                            display: 'flex', justifyContent: 'space-between',
                            fontSize: '13px', color: '#94a3b8', marginTop: '8px',
                        }}>
                            <span>
                                {jobStatus?.processed_count || 0} / {jobStatus?.total_files || files.length} files
                            </span>
                            <span>
                                ✓ {jobStatus?.success_count || 0} &nbsp; ✗ {jobStatus?.failed_count || 0}
                            </span>
                        </div>
                    </div>

                    {/* Live Results Preview */}
                    {jobStatus?.results?.length > 0 && (
                        <div style={{
                            marginTop: '32px', textAlign: 'left',
                            maxHeight: '200px', overflowY: 'auto',
                        }}>
                            {jobStatus.results.map((r, i) => (
                                <div key={i} style={{
                                    ...styles.fileItem,
                                    background: r.status === 'success'
                                        ? 'rgba(16, 185, 129, 0.05)'
                                        : r.status === 'failed'
                                            ? 'rgba(239, 68, 68, 0.05)'
                                            : 'rgba(30, 30, 50, 0.5)',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        {r.status === 'success' ? (
                                            <CheckCircle size={18} color="#34d399" />
                                        ) : r.status === 'failed' ? (
                                            <XCircle size={18} color="#f87171" />
                                        ) : (
                                            <Clock size={18} color="#a5b4fc" />
                                        )}
                                        <div>
                                            <div style={{ fontWeight: 500, fontSize: '14px' }}>{r.filename}</div>
                                            <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                                                {r.status === 'success' ? r.candidate_name : r.error_message || 'Processing...'}
                                            </div>
                                        </div>
                                    </div>
                                    <span style={styles.statusBadge(r.status)}>{r.status}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
      `}</style>
        </div>
    );

    // ═══════════════════════════════════════════════════════════
    //  Phase 3: Results Dashboard
    // ═══════════════════════════════════════════════════════════
    const successResults = jobStatus?.results?.filter(r => r.status === 'success') || [];
    const failedResults = jobStatus?.results?.filter(r => r.status === 'failed') || [];

    const renderResultsPhase = () => (
        <>
            {/* Stats Cards */}
            <div style={styles.statsRow}>
                <div style={styles.stat('#818cf8')}>
                    <div style={{ ...styles.statLabel }}>Total Processed</div>
                    <div style={{ ...styles.statValue, color: '#818cf8' }}>{jobStatus?.total_files || 0}</div>
                </div>
                <div style={styles.stat('#34d399')}>
                    <div style={styles.statLabel}>Successful</div>
                    <div style={{ ...styles.statValue, color: '#34d399' }}>{jobStatus?.success_count || 0}</div>
                </div>
                <div style={styles.stat('#f87171')}>
                    <div style={styles.statLabel}>Failed</div>
                    <div style={{ ...styles.statValue, color: '#f87171' }}>{jobStatus?.failed_count || 0}</div>
                </div>
                <div style={styles.stat('#fbbf24')}>
                    <div style={styles.statLabel}>Selected</div>
                    <div style={{ ...styles.statValue, color: '#fbbf24' }}>{selectedResults.size}</div>
                </div>
            </div>

            {/* Action Bar */}
            <div style={{
                ...styles.card,
                marginBottom: '20px',
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px',
            }}>
                <div style={styles.actionBar}>
                    <button onClick={toggleSelectAll} style={styles.btn('secondary')}>
                        <Users size={14} />
                        {selectedResults.size === successResults.length ? 'Deselect All' : 'Select All'}
                    </button>
                    <button
                        onClick={sendBulkEmails}
                        disabled={selectedResults.size === 0 || emailSending}
                        style={{
                            ...styles.btn('success'),
                            opacity: selectedResults.size === 0 || emailSending ? 0.5 : 1,
                            cursor: selectedResults.size === 0 || emailSending ? 'not-allowed' : 'pointer',
                        }}
                    >
                        {emailSending ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                            : <Send size={14} />}
                        Send Emails ({selectedResults.size})
                    </button>
                    <button onClick={exportCSV} style={styles.btn('secondary')}>
                        <Download size={14} /> Export CSV
                    </button>
                </div>

                <button
                    onClick={() => { setPhase('upload'); setFiles([]); setJobId(null); setJobStatus(null); setSelectedResults(new Set()); }}
                    style={styles.btn('secondary')}
                >
                    <Upload size={14} /> New Batch
                </button>
            </div>

            {/* Email Results Banner */}
            {emailResults && (
                <div style={{
                    ...styles.card,
                    marginBottom: '20px',
                    padding: '16px 24px',
                    borderTop: `3px solid ${emailResults.success_count > 0 ? '#34d399' : '#f87171'}`,
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Mail size={18} color={emailResults.success_count > 0 ? '#34d399' : '#f87171'} />
                        <span>
                            Emails sent: <strong style={{ color: '#34d399' }}>{emailResults.success_count}</strong> success
                            {emailResults.failed_count > 0 && (
                                <>, <strong style={{ color: '#f87171' }}>{emailResults.failed_count}</strong> failed</>
                            )}
                        </span>
                        <button
                            onClick={() => setEmailResults(null)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', marginLeft: 'auto' }}
                        >
                            <X size={16} />
                        </button>
                    </div>
                </div>
            )}

            {/* Results Table */}
            <div style={styles.card}>
                <div style={styles.cardHeader}>
                    <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
                        Assessment Results
                    </h3>
                </div>

                <div style={{ overflowX: 'auto' }}>
                    <table style={styles.table}>
                        <thead>
                            <tr>
                                <th style={styles.th}></th>
                                <th style={styles.th}>File</th>
                                <th style={styles.th}>Candidate</th>
                                <th style={styles.th}>Position</th>
                                <th style={styles.th}>Status</th>
                                <th style={styles.th}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobStatus?.results?.map((r, i) => (
                                <tr key={i} style={{
                                    background: selectedResults.has(r.assessment_id) ? 'rgba(99, 102, 241, 0.05)' : 'transparent',
                                    transition: 'background 0.2s',
                                }}>
                                    <td style={{ ...styles.td, width: '40px' }}>
                                        {r.status === 'success' && (
                                            <input
                                                type="checkbox"
                                                checked={selectedResults.has(r.assessment_id)}
                                                onChange={(e) => {
                                                    const next = new Set(selectedResults);
                                                    e.target.checked ? next.add(r.assessment_id) : next.delete(r.assessment_id);
                                                    setSelectedResults(next);
                                                }}
                                                style={styles.checkbox}
                                            />
                                        )}
                                    </td>
                                    <td style={styles.td}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <FileText size={16} color="#818cf8" />
                                            <span style={{ fontWeight: 500, maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {r.filename}
                                            </span>
                                        </div>
                                    </td>
                                    <td style={styles.td}>
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{r.candidate_name || '—'}</div>
                                            <div style={{ fontSize: '12px', color: '#94a3b8' }}>{r.candidate_email || ''}</div>
                                        </div>
                                    </td>
                                    <td style={styles.td}>
                                        <span style={{ color: '#c4b5fd', fontSize: '13px' }}>{r.position || '—'}</span>
                                    </td>
                                    <td style={styles.td}>
                                        <span style={styles.statusBadge(r.status)}>
                                            {r.status === 'success' ? <CheckCircle size={12} /> : <XCircle size={12} />}
                                            {r.status}
                                        </span>
                                    </td>
                                    <td style={styles.td}>
                                        {r.status === 'success' ? (
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                <button
                                                    onClick={() => copyLink(r.assessment_token)}
                                                    title="Copy assessment link"
                                                    style={{
                                                        background: 'rgba(99, 102, 241, 0.1)',
                                                        border: '1px solid rgba(99, 102, 241, 0.2)',
                                                        borderRadius: '8px',
                                                        padding: '6px 10px',
                                                        cursor: 'pointer',
                                                        color: copiedLink === r.assessment_token ? '#34d399' : '#a5b4fc',
                                                        display: 'flex', alignItems: 'center', gap: '4px',
                                                        fontSize: '12px',
                                                    }}
                                                >
                                                    {copiedLink === r.assessment_token ? <CheckCircle size={12} /> : <Copy size={12} />}
                                                    {copiedLink === r.assessment_token ? 'Copied!' : 'Link'}
                                                </button>
                                                <button
                                                    onClick={() => navigate(`/live-assessment?attempt=${r.assessment_id}`)}
                                                    title="View assessment"
                                                    style={{
                                                        background: 'rgba(99, 102, 241, 0.1)',
                                                        border: '1px solid rgba(99, 102, 241, 0.2)',
                                                        borderRadius: '8px',
                                                        padding: '6px 10px',
                                                        cursor: 'pointer',
                                                        color: '#a5b4fc',
                                                        display: 'flex', alignItems: 'center', gap: '4px',
                                                        fontSize: '12px',
                                                    }}
                                                >
                                                    <ExternalLink size={12} /> View
                                                </button>
                                            </div>
                                        ) : (
                                            <span style={{ fontSize: '12px', color: '#f87171' }}>
                                                {r.error_message?.slice(0, 40) || 'Failed'}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );

    // ═══════════════════════════════════════════════════════════
    //  Main Render
    // ═══════════════════════════════════════════════════════════
    return (
        <div style={styles.page}>
            <TopNav />
            <div style={styles.container}>
                <div style={styles.header}>
                    <button onClick={() => navigate('/dashboard')} style={styles.backBtn}>
                        <ArrowLeft size={16} /> Back to Dashboard
                    </button>
                    <h1 style={styles.title}>Bulk Assessment Creator</h1>
                    <p style={styles.subtitle}>
                        {phase === 'upload' && 'Upload multiple resumes to generate assessments in bulk'}
                        {phase === 'processing' && 'AI is processing your resumes — sit back and relax'}
                        {phase === 'results' && `Done! ${successResults.length} assessments created successfully`}
                    </p>
                </div>

                {error && (
                    <div style={styles.errorBanner}>
                        <AlertCircle size={18} />
                        <span>{error}</span>
                        <button onClick={() => setError('')}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#f87171', marginLeft: 'auto' }}>
                            <X size={16} />
                        </button>
                    </div>
                )}

                {phase === 'upload' && renderUploadPhase()}
                {phase === 'processing' && renderProcessingPhase()}
                {phase === 'results' && renderResultsPhase()}
            </div>
        </div>
    );
};

export default BulkUpload;

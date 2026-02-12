import React from 'react';
import {
    Users, TrendingUp, Shield, AlertCircle, ChevronRight, ChevronDown,
    Info, Calculator, BarChart3, Clock, Edit3, Brain, Pause, Eye, EyeOff
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

// Theme-aware color palettes
const LIGHT_COLORS = {
    primary: '#2563EB',      // Blue
    success: '#059669',      // Green
    warning: '#D97706',      // Orange
    danger: '#DC2626',       // Red
    purple: '#7C3AED',       // Purple
    teal: '#0D9488',         // Teal
    cardBg: 'rgba(255, 255, 255, 0.95)',     // White background
    cardBgLight: 'rgba(241, 245, 249, 0.9)', // Light gray
    textMuted: '#374151',    // Dark gray for muted
    text: '#000000',         // Black
    textBright: '#111827',   // Near-black
    border: 'rgba(0, 0, 0, 0.2)',            // Dark border
};

const DARK_COLORS = {
    primary: '#60A5FA',      // Brighter Blue
    success: '#34D399',      // Brighter Green
    warning: '#FBBF24',      // Brighter Orange
    danger: '#F87171',       // Brighter Red
    purple: '#A78BFA',       // Brighter Purple
    teal: '#2DD4BF',         // Brighter Teal
    cardBg: 'rgba(23, 23, 23, 0.95)',        // Dark background
    cardBgLight: 'rgba(38, 38, 38, 0.9)',    // Lighter gray
    textMuted: '#A3A3A3',    // Light gray for muted
    text: '#FAFAFA',         // White
    textBright: '#FFFFFF',   // Pure white
    border: 'rgba(255, 255, 255, 0.1)',      // Light border
};

// Calculation methodology for each check
const METHODOLOGY = {
    uniform_timing: {
        icon: Clock,
        name: "Response Time Consistency",
        formula: "CV = σ / μ × 100",
        explanation: "Coefficient of Variation measures how spread out response times are relative to the average.",
        threshold: "Flagged if CV < 10% (too consistent)",
        normalRange: "Natural CV: 15-60%"
    },
    perfect_pattern: {
        icon: Edit3,
        name: "Decision Revision Pattern",
        formula: "Changes = 0 AND First Decision < 5s",
        explanation: "Checks if candidate never revised any answers AND made all initial selections under 5 seconds.",
        threshold: "Flagged if BOTH conditions are true",
        normalRange: "Most candidates change 1-2 answers"
    },
    identical_explanations: {
        icon: BarChart3,
        name: "Explanation Length Variety",
        formula: "Unique Word Counts / Total Responses",
        explanation: "Counts how many different explanation lengths were used across all questions.",
        threshold: "Flagged if all explanations are exactly the same length",
        normalRange: "Natural: 3-6 different lengths per 5 questions"
    },
    coached_pauses: {
        icon: Pause,
        name: "Pause Pattern Analysis",
        formula: "Count(pause % interval < 0.5s) / Total Pauses",
        explanation: "Checks if pause durations align to regular intervals (5s, 10s, 15s) suggesting coached behavior.",
        threshold: "Flagged if >70% of pauses align to an interval",
        normalRange: "Natural pauses are irregular"
    },
    no_variation: {
        icon: Brain,
        name: "Approach Pattern Variation",
        formula: "Unique Patterns / Total Responses",
        explanation: "Measures whether candidate adapted their approach to different question types.",
        threshold: "Flagged if same pattern on ALL 4+ questions",
        normalRange: "Natural: 2-4 different patterns"
    }
};

/**
 * Get color based on percentile value
 */
const getPercentileColor = (percentile, COLORS) => {
    if (percentile >= 75) return COLORS.success;
    if (percentile >= 50) return COLORS.primary;
    if (percentile >= 25) return COLORS.warning;
    return COLORS.danger;
};

/**
 * Main PopulationIntelligence display
 */
export const PopulationIntelligence = ({ data, className = '' }) => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;
    const [showMethodology, setShowMethodology] = React.useState(false);
    const [showStats, setShowStats] = React.useState(true);

    if (!data) {
        return (
            <div className={`rounded-xl p-5 ${className}`} style={{ background: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}>
                <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg" style={{ background: `${COLORS.teal}20` }}>
                        <Users className="w-5 h-5" style={{ color: COLORS.teal }} />
                    </div>
                    <h3 className="text-base font-semibold" style={{ color: COLORS.text }}>
                        Population Intelligence
                    </h3>
                </div>
                <p className="text-sm" style={{ color: COLORS.textMuted }}>
                    Population data not yet available. Insights will appear after more assessments.
                </p>
            </div>
        );
    }

    const { percentiles, confidence_intervals, authenticity, population_context, has_baseline_data, sample_size } = data;

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Header with Methodology Toggle */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg" style={{ background: `${COLORS.teal}20` }}>
                        <Users className="w-5 h-5" style={{ color: COLORS.teal }} />
                    </div>
                    <div>
                        <h3 className="text-base font-semibold" style={{ color: COLORS.text }}>
                            Population Intelligence
                        </h3>
                        {has_baseline_data && (
                            <span className="text-xs" style={{ color: COLORS.teal }}>
                                ● Baselines Active
                            </span>
                        )}
                    </div>                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowStats(!showStats)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:opacity-80"
                        style={{
                            background: showStats ? `${COLORS.teal}30` : COLORS.cardBgLight,
                            color: showStats ? COLORS.teal : COLORS.textMuted,
                            border: `1px solid ${showStats ? COLORS.teal : COLORS.border}`
                        }}
                    >
                        {showStats ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        {showStats ? 'Hide Stats' : 'Show Stats'}
                    </button>
                    <button
                        onClick={() => setShowMethodology(!showMethodology)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:opacity-80"
                        style={{
                            background: showMethodology ? `${COLORS.primary}30` : COLORS.cardBgLight,
                            color: showMethodology ? COLORS.primary : COLORS.textMuted,
                            border: `1px solid ${showMethodology ? COLORS.primary : COLORS.border}`
                        }}
                    >
                        <Calculator className="w-3.5 h-3.5" />
                        {showMethodology ? 'Hide' : 'How It Works'}
                    </button>
                </div>
            </div>

            {/* Methodology Panel */}
            {showMethodology && (
                <MethodologyPanel />
            )}
            {/* All Stats Sections - Collapsible */}
            {showStats && (
                <>

                    {/* Percentile Cards */}
                    {population_context && Object.keys(population_context).length > 0 && (
                        <div className="space-y-2">
                            <h4 className="text-sm font-bold uppercase tracking-wider" style={{ color: COLORS.text }}>
                                📊 Comparative Context
                            </h4>
                            <div className="grid grid-cols-1 gap-2">
                                {Object.entries(population_context).map(([metric, description]) => (
                                    <PercentileCard
                                        key={metric}
                                        metric={metric}
                                        description={description}
                                        percentile={percentiles?.[metric]}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Confidence Intervals */}
                    {confidence_intervals && Object.keys(confidence_intervals).length > 0 && (
                        <div className="space-y-2">
                            <h4 className="text-sm font-bold uppercase tracking-wider" style={{ color: COLORS.text }}>
                                🎯 Confidence Assessment
                            </h4>
                            <ConfidenceDisplay intervals={confidence_intervals} sampleSize={sample_size} />
                        </div>
                    )}

                    {/* Authenticity Score */}
                    {authenticity && (
                        <div className="space-y-2">
                            <h4 className="text-sm font-bold uppercase tracking-wider" style={{ color: COLORS.text }}>
                                🛡️ Authenticity Analysis
                            </h4>
                            <AuthenticityBadge data={authenticity} />
                        </div>
                    )}
                </>
            )}
        </div>
    );
};


/**
 * Methodology explanation panel
 */
const MethodologyPanel = () => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;

    return (
        <div
            className="rounded-xl p-4 space-y-3 shadow-sm"
            style={{
                background: isDark ? COLORS.cardBgLight : '#f8fafc',
                border: `1px solid ${COLORS.border}`
            }}
        >
            <div className="flex items-center gap-2 mb-3">
                <Info className="w-4 h-4" style={{ color: COLORS.primary }} />
                <span className="text-sm font-semibold" style={{ color: COLORS.text }}>
                    Calculation Methodology
                </span>
            </div>

            <p className="text-xs leading-relaxed" style={{ color: COLORS.textMuted }}>
                The authenticity score starts at 100% and applies deductions based on 5 behavioral checks.
                Each check looks for patterns that are statistically unusual compared to natural test-taking behavior.
            </p>

            <div className="grid gap-2 mt-3">
                {Object.entries(METHODOLOGY).map(([key, method]) => {
                    const IconComponent = method.icon;
                    return (
                        <div
                            key={key}
                            className="p-3 rounded-lg"
                            style={{ background: isDark ? 'rgba(0,0,0,0.2)' : COLORS.cardBgLight }}
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <IconComponent className="w-4 h-4" style={{ color: COLORS.teal }} />
                                <span className="text-xs font-semibold" style={{ color: COLORS.text }}>
                                    {method.name}
                                </span>
                            </div>
                            <div className="space-y-1 text-xs" style={{ color: COLORS.textMuted }}>
                                <div>
                                    <span style={{ color: COLORS.primary, fontWeight: 600 }}>Formula: </span>
                                    <code className="px-2 py-1 rounded border" style={{ background: isDark ? '#000000' : '#f8fafc', color: isDark ? '#f8fafc' : '#1e293b', borderColor: COLORS.border, display: 'inline-block' }}>
                                        {method.formula}
                                    </code>
                                </div>
                                <p>{method.explanation}</p>
                                <div className="flex gap-4 mt-1">
                                    <span style={{ color: COLORS.text }}>
                                        <span style={{ color: COLORS.danger }}>⚠ </span>
                                        {method.threshold}
                                    </span>
                                </div>
                                <span style={{ color: COLORS.text }}><span style={{ color: COLORS.success }}>✓</span> {method.normalRange}</span>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-3 p-3 rounded-lg" style={{ background: isDark ? 'rgba(52, 211, 153, 0.1)' : 'rgba(52, 211, 153, 0.25)', border: `1px solid ${COLORS.success}` }}>
                <p className="text-sm font-semibold" style={{ color: COLORS.text }}>
                    📐 Final Score Formula: 100 - (sum of all applicable deductions)
                </p>
                <p className="text-xs mt-2" style={{ color: COLORS.textMuted }}>
                    <strong style={{ color: COLORS.text }}>Deductions:</strong> Uniform Timing (-15%), Perfect Pattern (-25%), Identical Explanations (-15%), Coached Pauses (-10%), No Variation (-10%)
                </p>
            </div>
        </div>
    );
};


/**
 * Individual percentile card with human-readable context
 */
const PercentileCard = ({ metric, description, percentile }) => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;
    const color = percentile !== undefined ? getPercentileColor(percentile, COLORS) : COLORS.textMuted;

    return (
        <div
            className="flex items-center justify-between p-3 rounded-xl"
            style={{
                background: isDark ? `linear-gradient(135deg, ${COLORS.cardBgLight} 0%, ${color}10 100%)` : `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${color}10 100%)`,
                border: `1px solid ${color}30`,
            }}
        >
            <div className="flex items-center gap-3">
                <div className="p-1.5 rounded-lg" style={{ background: `${color}20` }}>
                    <TrendingUp className="w-4 h-4" style={{ color }} />
                </div>
                <p className="text-sm" style={{ color: COLORS.text }}>
                    {description}
                </p>
            </div>
            {percentile !== undefined && (
                <div className="flex items-center gap-2">
                    <div
                        className="h-1.5 w-16 rounded-full overflow-hidden"
                        style={{ background: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(100, 116, 139, 0.3)' }}
                    >
                        <div
                            className="h-full rounded-full"
                            style={{ width: `${percentile}%`, background: color }}
                        />
                    </div>
                    <span className="text-lg font-bold" style={{ color }}>
                        P{percentile}
                    </span>
                </div>
            )}
        </div>
    );
};


/**
 * Confidence interval display showing uncertainty
 */
const ConfidenceDisplay = ({ intervals, sampleSize }) => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;

    const avgUncertainty = Object.values(intervals).reduce((sum, i) => sum + (i.uncertainty || 0), 0) /
        Math.max(1, Object.keys(intervals).length);

    const uncertaintyLevel = avgUncertainty < 20 ? 'Low' : avgUncertainty < 50 ? 'Moderate' : 'High';
    const uncertaintyColor = avgUncertainty < 20 ? COLORS.success : avgUncertainty < 50 ? COLORS.warning : COLORS.danger;
    const confidencePercent = Math.min(100, Math.max(20, 100 - avgUncertainty));

    return (
        <div
            className="p-4 rounded-xl"
            style={{ background: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}
        >
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-sm" style={{ color: COLORS.text }}>
                        Based on <strong>{sampleSize}</strong> question{sampleSize !== 1 ? 's' : ''}
                    </span>
                </div>
                <span
                    className="text-xs font-semibold px-2.5 py-1 rounded-full"
                    style={{
                        background: `${uncertaintyColor}20`,
                        color: uncertaintyColor,
                    }}
                >
                    {uncertaintyLevel} Uncertainty
                </span>
            </div>

            {/* Confidence bar with gradient */}
            <div className="relative h-3 rounded-full overflow-hidden mb-3" style={{ background: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(100, 116, 139, 0.2)' }}>
                <div
                    className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
                    style={{
                        width: `${confidencePercent}%`,
                        background: `linear-gradient(90deg, ${COLORS.danger} 0%, ${COLORS.warning} 40%, ${COLORS.success} 100%)`,
                    }}
                />
                <div
                    className="absolute inset-y-0 flex items-center justify-end pr-2"
                    style={{ width: `${confidencePercent}%` }}
                >
                    <span className="text-[10px] font-bold text-white drop-shadow">
                        {Math.round(confidencePercent)}%
                    </span>
                </div>
            </div>

            <div className="flex items-start gap-2 p-2 rounded-lg" style={{ background: COLORS.cardBgLight }}>
                <Info className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: COLORS.textMuted }} />
                <p className="text-xs leading-relaxed" style={{ color: COLORS.textMuted }}>
                    {avgUncertainty < 20
                        ? 'High confidence in metrics. Data is sufficient for reliable behavioral assessment.'
                        : avgUncertainty < 50
                            ? 'Moderate confidence. More questions will improve metric accuracy and reduce uncertainty bounds.'
                            : 'Early analysis with limited data. Results are preliminary — interpret with caution.'}
                </p>
            </div>
        </div>
    );
};


/**
 * Authenticity badge with expandable anomaly details
 */
const AuthenticityBadge = ({ data }) => {
    const { isDark } = useTheme();
    const COLORS = isDark ? DARK_COLORS : LIGHT_COLORS;

    const { score, flags, status, confidence_explanation } = data;
    const [expandedFlag, setExpandedFlag] = React.useState(null);

    const statusConfig = {
        natural: { color: COLORS.success, label: 'Natural Behavior', bgGradient: isDark ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.15)' },
        minor_concerns: { color: COLORS.warning, label: 'Minor Anomalies Detected', bgGradient: isDark ? 'rgba(245, 158, 11, 0.1)' : 'rgba(245, 158, 11, 0.15)' },
        review_recommended: { color: COLORS.danger, label: 'Review Recommended', bgGradient: isDark ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.15)' },
        insufficient_data: { color: COLORS.textMuted, label: 'Analyzing...', bgGradient: 'rgba(100, 116, 139, 0.15)' },
    };

    const config = statusConfig[status] || statusConfig.natural;

    const severityConfig = {
        high: { color: COLORS.danger, label: 'High', deduction: '-25%' },
        medium: { color: COLORS.warning, label: 'Medium', deduction: '-15%' },
        low: { color: COLORS.textMuted, label: 'Low', deduction: '-10%' },
    };

    return (
        <div className="space-y-3">
            {/* Main Score Card */}
            <div
                className="p-4 rounded-xl relative overflow-hidden"
                style={{
                    background: `linear-gradient(135deg, ${COLORS.cardBg} 0%, ${config.bgGradient} 100%)`,
                    border: `1px solid ${config.color}30`,
                }}
            >
                {/* Score Circle */}
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <Shield className="w-5 h-5" style={{ color: config.color }} />
                            <span className="text-sm font-semibold" style={{ color: COLORS.text }}>
                                Authenticity Score
                            </span>
                        </div>
                        <span
                            className="text-sm font-medium"
                            style={{ color: config.color }}
                        >
                            {config.label}
                        </span>
                    </div>

                    {/* Circular Score */}
                    <div className="relative w-20 h-20">
                        <svg className="w-20 h-20 transform -rotate-90">
                            <circle
                                cx="40" cy="40" r="35"
                                stroke={isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(100, 116, 139, 0.2)"}
                                strokeWidth="6"
                                fill="none"
                            />
                            <circle
                                cx="40" cy="40" r="35"
                                stroke={config.color}
                                strokeWidth="6"
                                fill="none"
                                strokeDasharray={`${(score / 100) * 220} 220`}
                                strokeLinecap="round"
                            />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-2xl font-bold" style={{ color: config.color }}>
                                {score}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Confidence Explanation */}
                {confidence_explanation && (
                    <div className="mt-4 p-3 rounded-lg" style={{ background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-semibold" style={{ color: COLORS.textMuted }}>
                                ANALYSIS CONFIDENCE
                            </span>
                            <span
                                className="text-xs font-bold px-2 py-0.5 rounded"
                                style={{
                                    background: confidence_explanation.level === 'high' ? `${COLORS.success}20` :
                                        confidence_explanation.level === 'moderate' ? `${COLORS.warning}20` : `${COLORS.danger}20`,
                                    color: confidence_explanation.level === 'high' ? COLORS.success :
                                        confidence_explanation.level === 'moderate' ? COLORS.warning : COLORS.danger
                                }}
                            >
                                {confidence_explanation.level?.toUpperCase()}
                            </span>
                        </div>
                        <p className="text-xs" style={{ color: COLORS.text }}>
                            {confidence_explanation.reason}
                        </p>
                        {confidence_explanation.interpretation && (
                            <p className="text-xs mt-2 italic" style={{ color: COLORS.textMuted }}>
                                "{confidence_explanation.interpretation}"
                            </p>
                        )}

                        {/* Stats Row */}
                        <div className="flex gap-4 mt-3 pt-3" style={{ borderTop: `1px solid ${COLORS.border}` }}>
                            <div className="text-center">
                                <div className="text-lg font-bold" style={{ color: COLORS.text }}>
                                    {confidence_explanation.data_points || 0}
                                </div>
                                <div className="text-[10px]" style={{ color: COLORS.textMuted }}>Questions</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold" style={{ color: (confidence_explanation.anomalies_found || 0) > 0 ? COLORS.warning : COLORS.success }}>
                                    {confidence_explanation.anomalies_found || 0}
                                </div>
                                <div className="text-[10px]" style={{ color: COLORS.textMuted }}>Anomalies</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold" style={{ color: COLORS.danger }}>
                                    -{confidence_explanation.total_deductions || 0}%
                                </div>
                                <div className="text-[10px]" style={{ color: COLORS.textMuted }}>Deductions</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Anomaly Cards */}
            {flags && flags.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold uppercase tracking-wider" style={{ color: COLORS.text }}>
                            ⚠️ Detected Anomalies
                        </h4>
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: COLORS.warning, color: isDark ? '#000000' : '#FFFFFF' }}>
                            {flags.length} found
                        </span>
                    </div>

                    {flags.map((flag, idx) => {
                        const severity = severityConfig[flag.severity] || severityConfig.low;
                        const method = METHODOLOGY[flag.flag];
                        const isExpanded = expandedFlag === idx;

                        return (
                            <div
                                key={idx}
                                className="rounded-xl overflow-hidden transition-all duration-200"
                                style={{
                                    border: `1px solid ${severity.color}30`,
                                    background: isExpanded ? `${severity.color}10` : COLORS.cardBg
                                }}
                            >
                                {/* Header */}
                                <button
                                    className="w-full p-3 flex items-center justify-between text-left"
                                    onClick={() => setExpandedFlag(isExpanded ? null : idx)}
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-2.5 h-2.5 rounded-full animate-pulse"
                                            style={{ background: severity.color }}
                                        />
                                        <span className="text-sm font-medium" style={{ color: COLORS.text }}>
                                            {flag.title || flag.description}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span
                                            className="text-xs font-bold px-2 py-0.5 rounded"
                                            style={{ background: `${severity.color}20`, color: severity.color }}
                                        >
                                            {flag.deduction ? `-${flag.deduction}%` : severity.deduction}
                                        </span>
                                        {isExpanded ? (
                                            <ChevronDown className="w-4 h-4" style={{ color: COLORS.textMuted }} />
                                        ) : (
                                            <ChevronRight className="w-4 h-4" style={{ color: COLORS.textMuted }} />
                                        )}
                                    </div>
                                </button>

                                {/* Expanded Content */}
                                {isExpanded && (
                                    <div className="px-3 pb-3 space-y-3" style={{ borderTop: `1px solid ${COLORS.border}` }}>
                                        {/* Methodology */}
                                        {method && (
                                            <div className="mt-3 p-3 rounded-lg border" style={{ background: isDark ? 'rgba(0,0,0,0.2)' : '#f0f9ff', borderColor: isDark ? COLORS.border : '#e0f2fe' }}>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Calculator className="w-4 h-4" style={{ color: COLORS.primary }} />
                                                    <span className="text-sm font-bold" style={{ color: COLORS.primary }}>
                                                        How This Is Calculated
                                                    </span>
                                                </div>
                                                <code
                                                    className="block text-xs px-2 py-1.5 rounded mb-2 font-bold"
                                                    style={{ background: isDark ? '#000000' : '#ffffff', color: COLORS.textBright, border: `1px solid ${isDark ? COLORS.border : '#bae6fd'}` }}
                                                >
                                                    {method.formula}
                                                </code>
                                                <p className="text-xs font-medium" style={{ color: COLORS.textSecondary }}>
                                                    {method.explanation}
                                                </p>
                                            </div>
                                        )}

                                        {/* Evidence */}
                                        {flag.evidence && (
                                            <div className="space-y-2">
                                                {/* What We Found */}
                                                <div className="p-3 rounded-lg" style={{ background: COLORS.cardBgLight }}>
                                                    <span className="text-xs font-semibold block mb-1" style={{ color: COLORS.teal }}>
                                                        📊 What We Found
                                                    </span>
                                                    <p className="text-sm font-medium" style={{ color: COLORS.text }}>
                                                        {flag.evidence.what_we_found}
                                                    </p>
                                                </div>

                                                {/* Data Grid */}
                                                <div className="grid grid-cols-2 gap-2">
                                                    {Object.entries(flag.evidence)
                                                        .filter(([key]) => !['what_we_found', 'why_this_matters', 'what_is_normal', 'possible_explanations', 'recommendation'].includes(key))
                                                        .map(([key, value]) => (
                                                            <div
                                                                key={key}
                                                                className="p-2 rounded-lg"
                                                                style={{ background: COLORS.cardBgLight }}
                                                            >
                                                                <span className="text-[10px] block" style={{ color: COLORS.textMuted }}>
                                                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                                                </span>
                                                                <span className="text-xs font-mono font-semibold" style={{ color: COLORS.primary }}>
                                                                    {value}
                                                                </span>
                                                            </div>
                                                        ))}
                                                </div>

                                                {/* Why & Normal / Explanations */}
                                                <div className="grid grid-cols-2 gap-2">
                                                    <div className="p-2 rounded-lg" style={{ background: isDark ? 'rgba(217, 119, 6, 0.1)' : `${COLORS.warning}10` }}>
                                                        <span className="text-[10px] font-semibold block mb-1" style={{ color: COLORS.warning }}>
                                                            {flag.evidence.possible_explanations ? '🔍 Possible Explanations' : '⚠️ Why This Matters'}
                                                        </span>
                                                        <div className="text-xs" style={{ color: COLORS.text }}>
                                                            {flag.evidence.possible_explanations ? (
                                                                <ul className="list-disc ml-3 space-y-1">
                                                                    {flag.evidence.possible_explanations.slice(0, 2).map((exp, i) => <li key={i}>{exp}</li>)}
                                                                </ul>
                                                            ) : flag.evidence.why_this_matters}
                                                        </div>
                                                    </div>
                                                    <div className="p-2 rounded-lg" style={{ background: isDark ? 'rgba(5, 150, 105, 0.1)' : `${COLORS.success}10` }}>
                                                        <span className="text-[10px] font-semibold block mb-1" style={{ color: COLORS.success }}>
                                                            ✓ Normal Range
                                                        </span>
                                                        <p className="text-xs" style={{ color: COLORS.text }}>
                                                            {flag.evidence.what_is_normal}
                                                        </p>
                                                    </div>
                                                </div>

                                                {/* Recommendation (if exists) */}
                                                {flag.evidence.recommendation && (
                                                    <div className="p-2 rounded-lg border border-dashed" style={{ borderColor: COLORS.border, background: isDark ? 'rgba(0,0,0,0.2)' : 'rgba(0,0,0,0.02)' }}>
                                                        <span className="text-[10px] font-semibold block mb-1" style={{ color: COLORS.primary }}>
                                                            💡 Recommendation
                                                        </span>
                                                        <p className="text-xs italic" style={{ color: COLORS.textMuted }}>
                                                            {flag.evidence.recommendation}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Factors Analyzed */}
            {confidence_explanation?.factors_analyzed && (
                <div className="p-3 rounded-xl" style={{ background: COLORS.cardBg, border: `1px solid ${COLORS.border}` }}>
                    <span className="text-sm font-bold block mb-3" style={{ color: COLORS.text }}>
                        ⚙️ ANALYSIS FACTORS
                    </span>
                    <div className="grid grid-cols-2 gap-2">
                        {confidence_explanation.factors_analyzed.map((factor, idx) => (
                            <div
                                key={idx}
                                className="flex items-center gap-2 p-2 rounded-lg"
                                style={{ background: factor.analyzed ? isDark ? 'rgba(52, 211, 153, 0.1)' : `${COLORS.success}10` : COLORS.cardBgLight }}
                            >
                                <div
                                    className="w-2 h-2 rounded-full"
                                    style={{ background: factor.analyzed ? COLORS.success : COLORS.textMuted }}
                                />
                                <span
                                    className="text-xs"
                                    style={{ color: factor.analyzed ? COLORS.text : COLORS.textMuted }}
                                >
                                    {factor.name}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};


export default PopulationIntelligence;

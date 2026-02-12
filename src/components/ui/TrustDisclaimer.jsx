/**
 * TrustDisclaimer Component
 * 
 * Prominent disclaimer addressing black-box audit requirement:
 * "Every assessment should include visible, unavoidable disclaimer"
 * 
 * This component makes it clear that HireMate provides behavioral
 * observations, not predictions or final hiring recommendations.
 */

import React from 'react';
import { Info, AlertTriangle, Scale } from 'lucide-react';

// Color palette matching HireMate design
const COLORS = {
    warning: '#F59E0B',
    warningLight: 'rgba(245, 158, 11, 0.1)',
    textMuted: '#94A3B8',
    text: '#F1F5F9',
    border: 'rgba(100, 116, 139, 0.3)',
};

/**
 * Main TrustDisclaimer - shown prominently on assessment view
 */
export const TrustDisclaimer = ({ variant = 'default', className = '' }) => {
    const variants = {
        default: {
            icon: Info,
            title: 'Behavioral Observation Tool',
            message: 'This analysis shows behavioral patterns, not predictions. Use to supplement human judgment, not replace it.',
            style: {
                background: COLORS.warningLight,
                borderColor: COLORS.warning,
            },
        },
        compact: {
            icon: Scale,
            title: null,
            message: 'Observations only — not a hiring recommendation',
            style: {
                background: 'transparent',
                borderColor: COLORS.border,
            },
        },
        prominent: {
            icon: AlertTriangle,
            title: 'Important Disclaimer',
            message: 'HireMate provides behavioral observations based on assessment interactions. These insights should inform, not determine, hiring decisions. Human judgment is required for all employment decisions.',
            style: {
                background: COLORS.warningLight,
                borderColor: COLORS.warning,
            },
        },
    };

    const config = variants[variant] || variants.default;
    const IconComponent = config.icon;

    return (
        <div
            className={`rounded-lg p-4 border flex items-start gap-3 ${className}`}
            style={{
                background: config.style.background,
                borderColor: config.style.borderColor,
            }}
            role="alert"
            aria-label="Disclaimer"
        >
            <IconComponent
                className="w-5 h-5 flex-shrink-0 mt-0.5"
                style={{ color: COLORS.warning }}
            />
            <div>
                {config.title && (
                    <h4
                        className="text-sm font-semibold mb-1"
                        style={{ color: COLORS.text }}
                    >
                        {config.title}
                    </h4>
                )}
                <p
                    className="text-sm"
                    style={{ color: COLORS.textMuted }}
                >
                    {config.message}
                </p>
            </div>
        </div>
    );
};


/**
 * Inline disclaimer for specific metrics
 */
export const MetricDisclaimer = ({ text }) => (
    <p
        className="text-xs italic mt-1"
        style={{ color: COLORS.textMuted }}
    >
        {text}
    </p>
);


/**
 * AI Attribution badge for AI-generated content
 */
export const AIAttribution = ({ className = '' }) => (
    <span
        className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${className}`}
        style={{
            background: 'rgba(139, 92, 246, 0.2)',
            color: '#A78BFA',
            border: '1px solid rgba(139, 92, 246, 0.3)',
        }}
    >
        <span>🤖</span>
        <span>AI-Assisted</span>
    </span>
);


/**
 * Privacy Notice - shown on candidate assessment pages
 * Audit requirement: Explicitly state what we track and DON'T track
 * "Behavior ≠ Identity" messaging
 */
export const PrivacyNotice = ({ className = '' }) => (
    <div
        className={`rounded-lg p-4 border ${className}`}
        style={{
            background: 'rgba(30, 41, 59, 0.5)',
            borderColor: COLORS.border,
        }}
    >
        <h4
            className="text-sm font-semibold mb-3"
            style={{ color: COLORS.text }}
        >
            Privacy & Data Collection
        </h4>
        <div className="grid grid-cols-2 gap-4">
            <div>
                <p className="text-xs font-medium mb-1" style={{ color: '#10B981' }}>
                    ✓ What We Observe
                </p>
                <ul className="text-xs space-y-1" style={{ color: COLORS.textMuted }}>
                    <li>• Time between interactions</li>
                    <li>• Option selections and changes</li>
                    <li>• Text entry patterns (speed only)</li>
                    <li>• Focus changes (tab switches)</li>
                </ul>
            </div>
            <div>
                <p className="text-xs font-medium mb-1" style={{ color: '#EF4444' }}>
                    ✗ What We Don't Track
                </p>
                <ul className="text-xs space-y-1" style={{ color: COLORS.textMuted }}>
                    <li>• Keystroke logging</li>
                    <li>• Screen recording</li>
                    <li>• Personal data inference</li>
                    <li>• Biometric or identity data</li>
                </ul>
            </div>
        </div>
        <p
            className="text-xs mt-3 pt-2 border-t"
            style={{ color: COLORS.textMuted, borderColor: COLORS.border }}
        >
            <strong style={{ color: COLORS.text }}>Behavior ≠ Identity.</strong>{' '}
            This assessment observes problem-solving patterns, not who you are.
        </p>
    </div>
);


export default TrustDisclaimer;

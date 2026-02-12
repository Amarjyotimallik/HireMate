import { useState, useRef, useEffect } from 'react';
import { termDefinitions } from '../../data/termDefinitions';

/**
 * TermTooltip - Hover tooltip component for metric term explanations
 * 
 * Usage:
 * <TermTooltip term="selectionSpeed">
 *   <span>Selection Speed</span>
 * </TermTooltip>
 * 
 * With dynamic evidence:
 * <TermTooltip term="selectionSpeed" dynamicExplanation="Candidate selected in 6.2s avg...">
 *   <span>Selection Speed</span>
 * </TermTooltip>
 */
const TermTooltip = ({ term, children, position = 'top', dynamicExplanation = null }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
    const triggerRef = useRef(null);
    const tooltipRef = useRef(null);

    const definition = termDefinitions[term];

    useEffect(() => {
        if (isVisible && triggerRef.current && tooltipRef.current) {
            const triggerRect = triggerRef.current.getBoundingClientRect();
            const tooltipRect = tooltipRef.current.getBoundingClientRect();

            let top, left;

            // Smart positioning - prefer above, fallback to below if needed
            if (position === 'top' || position === 'auto') {
                top = triggerRect.top - tooltipRect.height - 8;
                // If would go off screen top, position below
                if (top < 10) {
                    top = triggerRect.bottom + 8;
                }
            } else {
                top = triggerRect.bottom + 8;
            }

            // Center horizontally, but keep on screen
            left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
            left = Math.max(10, Math.min(left, window.innerWidth - tooltipRect.width - 10));

            setTooltipPosition({ top, left });
        }
    }, [isVisible, position]);

    // If no definition found and no dynamic explanation, just render children without tooltip
    if (!definition && !dynamicExplanation) {
        return children;
    }

    return (
        <span
            ref={triggerRef}
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
            style={{
                cursor: 'help',
                borderBottom: '1px dotted rgba(148, 163, 184, 0.5)',
            }}
        >
            {children}

            {isVisible && (
                <div
                    ref={tooltipRef}
                    style={{
                        position: 'fixed',
                        top: tooltipPosition.top,
                        left: tooltipPosition.left,
                        backgroundColor: '#1E293B',
                        color: '#E2E8F0',
                        padding: '12px 16px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        lineHeight: '1.5',
                        maxWidth: '380px',
                        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        zIndex: 9999,
                        opacity: isVisible ? 1 : 0,
                        transition: 'opacity 150ms ease-in-out',
                        pointerEvents: 'none',
                    }}
                >
                    {/* Title */}
                    {definition?.title && (
                        <div style={{
                            fontWeight: 600,
                            marginBottom: '6px',
                            color: '#F8FAFC',
                            fontSize: '14px',
                        }}>
                            {definition.title}
                        </div>
                    )}

                    {/* Description */}
                    {definition?.description && (
                        <div style={{
                            color: '#CBD5E1',
                            marginBottom: (definition?.calculation || dynamicExplanation) ? '8px' : 0,
                        }}>
                            {definition.description}
                        </div>
                    )}

                    {/* Dynamic Evidence-Based Explanation (from backend) */}
                    {dynamicExplanation && (
                        <div style={{
                            fontSize: '12px',
                            color: '#A5F3FC',
                            backgroundColor: 'rgba(34, 211, 238, 0.1)',
                            borderRadius: '6px',
                            padding: '8px 10px',
                            marginBottom: definition?.calculation ? '8px' : 0,
                            borderLeft: '3px solid #22D3EE',
                        }}>
                            <div style={{ fontWeight: 600, marginBottom: '4px', color: '#22D3EE', fontSize: '11px', textTransform: 'uppercase' }}>
                                📊 Evidence for this candidate
                            </div>
                            {dynamicExplanation}
                        </div>
                    )}

                    {/* Calculation (if provided) */}
                    {definition?.calculation && (
                        <div style={{
                            fontSize: '12px',
                            color: '#94A3B8',
                            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                            paddingTop: '8px',
                            fontStyle: 'italic',
                        }}>
                            📐 {definition.calculation}
                        </div>
                    )}
                </div>
            )}
        </span>
    );
};

export default TermTooltip;


/**
 * Term Definitions for Metric Tooltips
 * 
 * Each term includes:
 * - title: Display name
 * - description: Plain English explanation (1-2 sentences)
 * - calculation: How it's computed (optional, for transparency)
 */

export const termDefinitions = {
    // ========================
    // LIVE METRICS
    // ========================

    avgResponse: {
        title: 'Avg Response Time',
        description: 'Average time the candidate took to make their first selection after each task appeared.',
        calculation: 'Time from task display to first option click (averaged)',
    },

    selectionSpeed: {
        title: 'Selection Speed',
        description: 'How quickly the candidate made their first choice after each task appeared. Faster or slower speeds may reflect different decision-making approaches.',
        calculation: 'Time from question display to first option click',
    },

    decisionSpeed: {
        title: 'Selection Speed',
        description: 'How quickly the candidate made their first choice after each task appeared. Faster or slower speeds may reflect different decision-making approaches.',
        calculation: 'Time from question display to first option click',
    },

    idleTime: {
        title: 'Idle Time',
        description: 'Time elapsed before first interaction on each question. May indicate reading, thinking, or pause — not inherently good or bad.',
        calculation: 'Seconds elapsed without clicks or typing',
    },

    sessionContinuity: {
        title: 'Session Continuity',
        description: 'Overall consistency of selections across the session. Fewer total revisions yield higher continuity.',
        calculation: '100 − (total selection changes × weight)',
    },

    focusScore: {
        title: 'Session Continuity',
        description: 'Overall consistency of selections across the session. Fewer total revisions yield higher continuity.',
        calculation: '100 − (total selection changes × weight)',
    },

    decisionFirmness: {
        title: 'Answer Stability',
        description: 'How consistently the candidate kept their choice within each question. More changes reduce stability.',
        calculation: '100 − (average selection changes per question × weight)',
    },

    analysisConfidence: {
        title: 'Analysis Confidence',
        description: 'How reliable the behavioral analysis is based on how many completed questions are available.',
        calculation: 'Grows with questions analyzed, with a boost for consistent patterns',
    },

    // ========================
    // SPIDER CHART SKILLS
    // ========================

    problemSolving: {
        title: 'Task Completion',
        description: 'Proportion of tasks the candidate completed out of the total assigned. Does not measure answer quality.',
        calculation: 'Completed tasks ÷ total tasks × 100',
    },

    taskCompletion: {
        title: 'Task Completion',
        description: 'Proportion of tasks the candidate completed out of the total assigned. Does not measure answer quality.',
        calculation: 'Completed tasks ÷ total tasks × 100',
    },

    analyticalThinking: {
        title: 'Deliberation Pattern',
        description: 'Observed depth of consideration based on time spent and explanation detail. Higher values suggest more deliberative behavior.',
        calculation: 'Weighted combination of idle time and explanation length',
    },

    deliberation: {
        title: 'Deliberation Pattern',
        description: 'Observed depth of consideration based on time spent and explanation detail. Higher values suggest more deliberative behavior.',
        calculation: 'Weighted combination of idle time and explanation length',
    },

    creativity: {
        title: 'Option Exploration',
        description: 'How many different options the candidate examined before making a final choice. Higher values suggest broader exploration.',
        calculation: 'Unique options hovered or clicked before final selection',
    },

    optionExploration: {
        title: 'Option Exploration',
        description: 'How many different options the candidate examined before making a final choice. Higher values suggest broader exploration.',
        calculation: 'Unique options hovered or clicked before final selection',
    },

    riskAssessment: {
        title: 'Risk Distribution',
        description: 'Distribution of choices across options tagged as low, medium, or high risk. Shows observed tendency, not evaluation skill.',
        calculation: 'Percentage breakdown of low/medium/high risk selections',
    },

    riskDistribution: {
        title: 'Risk Distribution',
        description: 'Distribution of choices across options tagged as low, medium, or high risk. Shows observed tendency, not evaluation skill.',
        calculation: 'Percentage breakdown of low/medium/high risk selections',
    },

    // ========================
    // BEHAVIORAL LABELS
    // ========================

    approachPattern: {
        title: 'Approach Pattern',
        description: 'The observed approach to tasks — Deliberative (careful, slow), Direct (quick, decisive), or Iterative (explores then refines).',
    },

    underPressure: {
        title: 'Time Pressure Response',
        description: 'How the candidate\'s behavior changed as remaining time decreased. Shows adaptation pattern, not stress tolerance.',
    },

    approach: {
        title: 'Observed Approach',
        description: 'General pattern of how the candidate navigated the assessment based on timing and interaction style.',
    },

    verdict: {
        title: 'AI-Assisted Summary',
        description: 'A synthesized assessment generated by AI based on observed behavioral patterns. Use as a starting point for discussion, not a final judgment.',
        calculation: 'Generated from pattern analysis after assessment completion',
    },
};

export default termDefinitions;

"""
AI Analyzer Service

Uses Groq AI to perform semantic analysis of candidate answers,
providing skill scores, correctness, and analytical quality metrics.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = None

def get_groq_client():
    """Get or create Groq client."""
    global groq_client
    if groq_client is None:
        settings = get_settings()
        api_key = settings.groq_api_key
        if api_key:
            groq_client = Groq(api_key=api_key)
    return groq_client


def analyze_answer_with_ai(
    question_text: str,
    selected_option: str,
    reasoning_text: str,
    skills_to_track: List[str],
    is_correct: bool = None
) -> Dict:
    """
    Analyze a candidate's answer using Groq AI.
    
    Args:
        question_text: The question being answered
        selected_option: The option the candidate selected
        reasoning_text: The candidate's reasoning/explanation
        skills_to_track: List of skills to evaluate (e.g., ["C++", "Arrays", "Problem Solving"])
        is_correct: Whether the answer is correct (if known)
    
    Returns:
        Dict with:
            - skill_scores: { skill_name: 0-100 }
            - correctness: 0.0-1.0
            - analytical_quality: 0.0-1.0
            - confidence_level: 0.0-1.0
            - relevance: 0.0-1.0
    """
    client = get_groq_client()
    
    if not client:
        logger.warning("Groq client not available, returning default scores")
        return get_default_analysis(skills_to_track)
    
    # Build skills string
    skills_str = ", ".join(skills_to_track) if skills_to_track else "Problem Solving, Analytical Thinking"
    
    prompt = f"""Analyze this assessment response and provide a JSON evaluation.

**Question**: {question_text}

**Candidate's Selected Option**: {selected_option}

**Candidate's Reasoning**: {reasoning_text if reasoning_text else "(No reasoning provided)"}

**Skills Being Tested**: {skills_str}

{"**Note**: The answer is " + ("CORRECT" if is_correct else "INCORRECT") if is_correct is not None else ""}

Provide your analysis as a JSON object with these exact keys:
{{
    "skill_scores": {{ 
        // For each skill in [{skills_str}], rate proficiency 0-100
        // Based on: technical accuracy, depth of explanation, practical understanding
    }},
    "correctness": 0.0-1.0,         // How correct is the answer? (1.0 = fully correct)
    "analytical_quality": 0.0-1.0,  // Quality of reasoning structure and logic
    "confidence_level": 0.0-1.0,    // How confident does the candidate seem?
    "relevance": 0.0-1.0            // Is the response on-topic and focused?
}}

Consider:
- Technical accuracy of concepts mentioned
- Depth and clarity of explanation
- Use of logical reasoning
- Practical applicability of approach
- Hedging language ("maybe", "I think") reduces confidence score

Return ONLY the JSON object, no other text."""

    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai_model_70b,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer analyzing candidate responses. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up response - extract JSON if wrapped in markdown
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(result_text)
        
        # Validate and normalize scores
        normalized = {
            "skill_scores": {},
            "correctness": max(0, min(1, float(analysis.get("correctness", 0.5)))),
            "analytical_quality": max(0, min(1, float(analysis.get("analytical_quality", 0.5)))),
            "confidence_level": max(0, min(1, float(analysis.get("confidence_level", 0.5)))),
            "relevance": max(0, min(1, float(analysis.get("relevance", 0.5))))
        }
        
        # Normalize skill scores to 0-100
        raw_skills = analysis.get("skill_scores", {})
        for skill in skills_to_track:
            score = raw_skills.get(skill, 50)
            normalized["skill_scores"][skill] = max(0, min(100, int(score)))
        
        logger.info(f"AI Analysis completed: correctness={normalized['correctness']}, skills={normalized['skill_scores']}")
        return normalized
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return get_default_analysis(skills_to_track)
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return get_default_analysis(skills_to_track)


def get_default_analysis(skills: List[str]) -> Dict:
    """Return default analysis when AI is unavailable."""
    return {
        "skill_scores": {skill: 50 for skill in skills},
        "correctness": 0.5,
        "analytical_quality": 0.5,
        "confidence_level": 0.5,
        "relevance": 0.5
    }


def batch_analyze_answers(answers: List[Dict]) -> List[Dict]:
    """
    Analyze multiple answers in sequence.
    
    Args:
        answers: List of dicts with keys: question_text, selected_option, reasoning_text, skills, is_correct
    
    Returns:
        List of analysis results
    """
    results = []
    for answer in answers:
        result = analyze_answer_with_ai(
            question_text=answer.get("question_text", ""),
            selected_option=answer.get("selected_option", ""),
            reasoning_text=answer.get("reasoning_text", ""),
            skills_to_track=answer.get("skills", ["Problem Solving"]),
            is_correct=answer.get("is_correct")
        )
        results.append(result)

def generate_final_candidate_report(
    candidate_name: str,
    position: str,
    aggregate_metrics: Dict,
    skill_profile: Dict,
    behavioral_summary: Dict
) -> Dict:
    """
    Generate a final executive summary of the candidate's performance using AI.
    """
    client = get_groq_client()
    if not client:
        return {
            "verdict": f"{candidate_name} completed the assessment with {behavioral_summary.get('decision_style', 'Balanced')} style.",
            "recommendation": "Review manually"
        }

    prompt = f"""
    You are a Senior Technical Recruiter. Generate a final assessment report for:
    Candidate: {candidate_name}
    Role: {position}

    Performance Metrics:
    - Decision Speed: {aggregate_metrics.get('avg_decision_speed', 0)}s (Style: {behavioral_summary.get('decision_style')})
    - Reasoning Depth: {aggregate_metrics.get('avg_reasoning_depth', 0)}/100
    - Consistency/Focus: {aggregate_metrics.get('focus_score', 0)}%
    
    Skills Profile: {json.dumps(skill_profile)}
    
    Behavioral Traits:
    - Approach: {behavioral_summary.get('approach')}
    - Under Pressure: {behavioral_summary.get('under_pressure')}
    
    Task:
    Provide a concise, professional "Verdict" (2-3 sentences max) summarizing their fit and capability.
    Sound natural and insightful, not robotic. Avoid stating numbers directly in the text; interpret them.
    
    Return JSON:
    {{
        "verdict": "...",
        "recommendation": "Strong Hire / Hire / Weak Hire / Reject"
    }}
    """
    
    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai_model_70b,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Final report generation failed: {e}")
        return {
            "verdict": f"Assessment completed by {candidate_name}. Please review detailed statistics.",
            "recommendation": "Review Required"
        }


def analyze_full_assessment_batch(
    candidate_name: str,
    position: str,
    answers: List[Dict],
    metrics: Dict = None,
) -> Dict:
    """
    Analyze ALL answers in one go and generate final report.
    metrics: Dict containing behavioral stats (speed, focus, etc.)
    Returns comprehensive report with 'final_verdict'.
    """
    client = get_groq_client()
    if not client:
        return {}

    # concise representation of answers
    answers_text = ""
    for i, ans in enumerate(answers):
        answers_text += f"""
        Q{i+1}: {ans.get('question_text', 'N/A')}
        Selection: {ans.get('selected_option', 'N/A')}
        Reasoning: {ans.get('reasoning_text', 'N/A')}
        Correctness: {'Correct' if ans.get('is_correct') else 'Incorrect'}
        Skills: {', '.join(ans.get('skills', []))}
        ---
        """

    # Format metrics for context
    metrics_text = "N/A"
    if metrics:
        metrics_text = f"""
        Avg Response Time: {metrics.get('avg_response_time')}s
        Decision Speed: {metrics.get('decision_speed')}
        Hesitation Level: {metrics.get('hesitation_level')}/100
        Focus Score: {metrics.get('focus_score')}%
        Revisions: {metrics.get('revision_count')}
        """

    prompt = f"""
    Role: Senior Technical Recruiter.
    Task: Evaluate this full assessment for {candidate_name} ({position}) and provide a comprehensive JSON report.

    BEHAVIORAL MATRICES (During Test):
    {metrics_text}

    TRANSCRIPT OF RESPONSES:
    {answers_text}

    Requirements:
    You MUST return a JSON object with this EXACT structure:
    
    {{
        "per_question_analysis": [
            {{
                "question_title": "Brief title extracted from the question (e.g. 'React State Sync', 'CSS Grid Issue')",
                "correctness": "Correct" or "Incorrect",
                "score": 0-100 (integer, based on correctness and depth),
                "analytical_depth": "High" or "Medium" or "Low",
                "confidence_level": "High" or "Medium" or "Low",
                "reasoning_feedback": "1-2 sentence analysis of their reasoning quality. If they provided explanation text, cite it specifically. If empty, say 'No explanation provided.'"
            }}
        ],
        "final_verdict": {{
            "verdict": "2-3 sentence summary of problem-solving approach and decision style",
            "recommendation": "Strong Hire" or "Hire" or "Weak Hire" or "Reject",
            "strengths": ["strength 1", "strength 2", "strength 3"],
            "improvements": ["area 1", "area 2", "area 3"]
        }}
    }}
    
    CRITICAL: Every field is REQUIRED. Do not omit any field.
    """

    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai_model_70b,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"},
            max_tokens=6000
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        return {}


# ============================================================================
# REPORT ASSISTANT CHATBOT — COMPREHENSIVE KNOWLEDGE BASE
# ============================================================================

ASSISTANT_SYSTEM_PROMPT = """You are Kiwi 🥝, a friendly and knowledgeable AI assistant for HireMate recruiters.

**Your Role:** You help recruiters understand scores, metrics, candidate data, dashboard stats, and how the entire HireMate platform works. You can answer questions about any page they're on.

---

## HireMate Platform Overview

HireMate is a behavior-based hiring intelligence platform. It does NOT score "right or wrong" answers. Instead, it observes HOW candidates solve decision-making tasks — their speed, consistency, reasoning quality, and authenticity. Think of it as a behavioral observation system.

**Assessment Flow:**
1. Recruiter uploads a candidate's resume (auto-extracts name, email, position)
2. Recruiter generates a one-time assessment link (JWT token, expires in configurable days)
3. Candidate opens the link and solves 5 micro-scenarios (decision-making tasks)
4. HireMate captures behavioral events in real time (clicks, timing, option changes, reasoning, focus, pastes)
5. Metrics engine computes 19 behavioral metrics from raw events
6. Skill profile and overall fit grade (S/A/B/C/D) are generated
7. Recruiter views results on dashboard, can compare candidates, and log hiring decisions

---

## 8-Layer Intelligence System

| Layer | Name | Question It Answers |
|-------|------|---------------------|
| 1 | Speed Layer | How fast does the candidate decide? |
| 2 | Firmness Layer | Do they stick with their first choice? |
| 3 | Radar Chart | What's their behavioral profile shape? |
| 4 | Authenticity Layer | Is this a genuine human response? |
| 5 | Anti-GPT Layer | Was AI/copy-paste used? |
| 6 | Confidence Layer | How much of the assessment was completed with commitment? |
| 7 | Stress Layer | Does behavior change under time pressure? |
| 8 | Overall Fit | What's the final hiring grade? |

---

## All Formulas & Scores

### 1. Overall Fit Score
`FitScore = (Task × 0.30) + (Behavioral × 0.35) + (Skill × 0.25) + (Resume × 0.10) - AntiCheatPenalty`

**Grade Mapping:**
- S = 90-100 (Exceptional)
- A = 80-89 (Strong)
- B = 70-79 (Competent)
- C = 60-69 (Developing)
- D = 0-59 (Needs Improvement)

### 2. Authenticity Score
`Authenticity = 100 - deductions`
- Uniform Timing (all answers within 5s of each other): -15
- Perfect Pattern (same option selected every time): -25
- Identical/Similar Explanations across questions: -15
- Coached Pauses (exactly 30s delays between actions): -10
- Zero Revisions (no option changes at all): -10

### 3. Decision Firmness
`Firmness = 100 - min(100, avg_changes_per_question × (100 / high_changes_threshold))`
- High (75%+): Confident, sticks with initial choices
- Medium (50-74%): Deliberate, some revisions
- Low (<50%): Exploratory, frequent revisions

### 4. Speed Thresholds
- Fast (High speed): < 15 seconds for initial selection
- Moderate: 15-45 seconds
- Extended (Low speed): > 45 seconds

### 5. Session Continuity
`Continuity = 100 - min(100, total_changes × 15)`
Measures how much the candidate changes answers overall.

### 6. Reasoning Depth
`Depth = word_score × 0.6 + connector_score × 0.4`
- word_score: based on explanation word count (< 20 = brief, 20-40 = moderate, > 40 = detailed)
- connector_score: presence of logical keywords like "because", "therefore", "however", "considering", etc.

### 7. Confidence Level
Based on sample size of completed questions:
- 1 question = 25% confidence
- 2 questions = 50%
- 3 questions = 75%
- 4+ questions = 75 + 5×(n-3), cap at 95%
- +10% bonus if dominant pattern ≥ 70%

### 8. Stress / Pressure Analysis
Compares first-half vs second-half performance:
- Steady progression: consistent pace throughout
- Variable pacing: significant timing differences between phases
- Frequent revisions: high change rate under time pressure

### 9. Anti-Cheat Penalty Breakdown
- Focus Loss (tab switches): -1 per event, cap -5
- Paste Detected: -2 per event, cap -5
- Copy Detected: -3 per event, cap -3
- Idle/Long Pause: -0.5 per event, cap -2
- Total penalty cap: -15 points

### 10. Radar Chart (Skill Profile) Axes
- **Task Completion**: % of questions answered
- **Selection Speed**: derived from avg first-click time
- **Deliberation Pattern**: explanation depth × completion rate
- **Option Exploration**: options viewed + revision pattern
- **Risk Preference**: timing and choice pattern analysis

---

## Platform Features

- **Resume Parsing**: Supports .txt, .pdf, .docx — auto-extracts name, email, position
- **Candidate Comparison**: Side-by-side skill profiles for up to N candidates
- **WebSocket Live Monitoring**: Real-time event stream during active assessments
- **Hiring Decisions**: Recruiters can log hire/no_hire/pending decisions for calibration
- **Calibration Stats**: Tracks recruiter decisions over time for accuracy analysis
- **Dashboard Stats**: Total candidates, active assessments, completed today, completion rate

---

## How You Should Respond
- Talk like a **friendly colleague**, not a robot. Use simple everyday English.
- Keep it SHORT. 2-4 sentences for simple questions. Max 6-8 sentences even for complex ones.
- Use **bold** for key numbers and metric names.
- Use bullet points only when listing 3+ items. Don't over-format.
- One blank line between different ideas — no walls of text.
- Start with the direct answer. Add a quick "why" if needed.
- Sound natural — use contractions ("you've", "it's", "that's"), casual phrasing.
- Never say "I'm an AI" or "As an AI assistant" — just answer like a knowledgeable teammate.
- If you don't have the data, be honest: "Hmm, I don't have that info right now."

---

## CRITICAL: Anti-Hallucination Rules (MUST FOLLOW)

1. **NEVER fabricate, invent, or guess** candidate explanations, reasoning text, or quotes. If the data says "No responses recorded yet", say exactly that.
2. When asked about candidate explanations/reasoning, you MUST ONLY quote text from the **"Candidate's Actual Responses"** section. Cite these responses directly.
3. **If the candidate provided a URL, random characters, or gibberish** as their explanation, you MUST report that EXACTLY. Do NOT try to interpret a URL as a professional reason. 
   - *Example:* "For Question 1, the candidate simply provided a link: [URL]. They didn't provide a written explanation."
4. **NEVER make up fake professional quotes** to cover for missing or low-quality data. If the explanation is brief or non-existent, state that clearly.
5. Only reference questions the candidate has ACTUALLY completed. Do not guess what they might say for future questions.


**Good example (when data exists):**

For Question 1, they wrote: "A performance-critical module builds a large log string..." — that's a solid technical explanation!

**Good example (when data is missing):**

I don't have the exact text of their explanations right now. I can see their Deliberation score is **21%**, which suggests brief responses.

"""


# ============================================================================
# DYNAMIC KNOWLEDGE BASE
# ============================================================================

def load_system_guide() -> str:
    """Load the comprehensive system guide from disk."""
    try:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_path = os.path.join(base_dir, "system_guide.md")
        
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to load system guide: {e}")
    return ""

def should_inject_guide(query: str) -> bool:
    """Check if the query needs deep architectural knowledge."""
    keywords = [
        "how", "calculate", "formula", "architecture", "anomaly", 
        "score", "why", "explain", "detail", "guide", "system", 
        "layer", "pipeline", "firmness", "radar", "stress"
    ]
    query_lower = query.lower()
    return any(k in query_lower for k in keywords)


# ============================================================================
# DASHBOARD CONTEXT DATA FETCHING
# ============================================================================

async def _fetch_dashboard_context(page_context: str, recruiter_id: str) -> str:
    """
    Fetch real-time data from MongoDB based on which page the recruiter is on.
    Returns a formatted string to inject into the system prompt.
    """
    from datetime import datetime, timedelta
    from bson import ObjectId
    from app.db import get_attempts_collection, get_events_collection
    
    attempts_coll = get_attempts_collection()
    
    try:
        if page_context == "dashboard":
            # Dashboard stats
            total_candidates = await attempts_coll.count_documents({"created_by": recruiter_id})
            active = await attempts_coll.count_documents({"status": "in_progress", "created_by": recruiter_id})
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            completed_today = await attempts_coll.count_documents({
                "status": "completed", "completed_at": {"$gte": today_start}, "created_by": recruiter_id
            })
            total_completed = await attempts_coll.count_documents({"status": "completed", "created_by": recruiter_id})
            started = await attempts_coll.count_documents({
                "status": {"$in": ["in_progress", "completed", "locked"]}, "created_by": recruiter_id
            })
            completion_rate = round((total_completed / started * 100), 1) if started > 0 else 0
            
            # Recent activity
            cursor = attempts_coll.find({"created_by": recruiter_id}).sort("updated_at", -1).limit(5)
            recent = []
            async for a in cursor:
                name = a.get("candidate_info", {}).get("name", "Unknown")
                status = a.get("status", "unknown")
                recent.append(f"  - {name}: {status}")
            recent_text = "\n".join(recent) if recent else "  No recent activity"
            
            return f"""
**Dashboard Stats (Real-Time):**
- Total Candidates: {total_candidates}
- Active Assessments: {active}
- Completed Today: {completed_today}
- Total Completed: {total_completed}
- Completion Rate: {completion_rate}%

**Recent Activity:**
{recent_text}
"""

        elif page_context == "all_candidates":
            # Candidate list with statuses and grades
            cursor = attempts_coll.find({"created_by": recruiter_id}).sort("updated_at", -1).limit(15)
            candidates = []
            async for a in cursor:
                name = a.get("candidate_info", {}).get("name", "Unknown")
                position = a.get("candidate_info", {}).get("position", "N/A")
                status = a.get("status", "unknown")
                grade = a.get("analysis_result", {}).get("recommendation", "") if a.get("analysis_result") else ""
                candidates.append(f"  - {name} | Role: {position} | Status: {status} | Recommendation: {grade or 'Pending'}")
            candidates_text = "\n".join(candidates) if candidates else "  No candidates found"
            
            total = await attempts_coll.count_documents({"created_by": recruiter_id})
            completed = await attempts_coll.count_documents({"status": "completed", "created_by": recruiter_id})
            
            return f"""
**Candidates Overview (Real-Time):**
- Total: {total} | Completed: {completed}

**Recent Candidates:**
{candidates_text}
"""

        elif page_context == "skill_reports":
            # Aggregate skill data
            cursor = attempts_coll.find({
                "created_by": recruiter_id, "status": "completed"
            }).sort("completed_at", -1).limit(10)
            
            skill_summary = []
            async for a in cursor:
                name = a.get("candidate_info", {}).get("name", "Unknown")
                result = a.get("analysis_result", {})
                verdict = result.get("verdict", "Not analyzed") if result else "Not analyzed"
                skill_summary.append(f"  - {name}: {verdict[:80]}...")
            skills_text = "\n".join(skill_summary) if skill_summary else "  No completed assessments yet"
            
            return f"""
**Skill Reports Data (Real-Time):**
{skills_text}
"""

        elif page_context == "compare":
            return """
**Candidate Comparison Mode:**
You can help the recruiter compare candidates. Ask them which candidates they'd like to compare, or answer questions about differences in their behavioral profiles, scores, and fit grades.
"""
        
        elif page_context in ("settings", "general"):
            return """
**General Mode:**
No specific data context. Answer questions about how HireMate works, explain any metric, formula, or feature.
"""
        
        else:
            return ""
            
    except Exception as e:
        logger.error(f"Failed to fetch dashboard context: {e}")
        return "\n(Note: Could not fetch live data at this time.)\n"


def _format_live_answers_for_kiwi(answers: list) -> str:
    """Format the candidate's ACTUAL reasoning text from events for Kiwi context."""
    if not answers:
        return "**Candidate's Actual Responses:** No responses recorded yet."
    
    lines = [f"**Candidate's Actual Responses ({len(answers)} questions answered):**"]
    lines.append("IMPORTANT: These are the candidate's EXACT words. Quote them directly when asked.")
    
    for i, ans in enumerate(answers):
        q_text = ans.get("question_text", f"Question {i+1}")
        if len(q_text) > 120:
            q_text = q_text[:120] + "..."
        
        selected = ans.get("selected_option", "Unknown")
        reasoning = ans.get("reasoning_text", "")
        is_correct = ans.get("is_correct", False)
        
        lines.append(f"\nQ{i+1}: {q_text}")
        lines.append(f"  - Selected: {selected} ({'Correct' if is_correct else 'Incorrect'})")
        lines.append(f'  - Candidate\'s Explanation: "{reasoning if reasoning else "No explanation provided"}"')
    
    return "\n".join(lines)


def _format_ai_analysis_for_kiwi(analysis: Any) -> str:
    """Helper to format the complex AI analysis dictionary into readable Markdown."""
    if not analysis or not isinstance(analysis, dict):
        return "No detailed AI analysis available yet (available after assessment completion)."
    
    lines = []
    
    # Verdict & Recommendation
    if analysis.get("verdict"):
        lines.append(f"**Overall Verdict:** {analysis.get('verdict')}")
    if analysis.get("recommendation"):
        lines.append(f"**Recommendation:** {analysis.get('recommendation')}")
    
    # Per Question Analysis
    qa = analysis.get("per_question_analysis", [])
    if qa:
        lines.append("\n**Detailed Technical Breakdown:**")
        for i, item in enumerate(qa):
            title = item.get("question_title", f"Question {i+1}")
            correct = item.get("correctness", "N/A")
            depth = item.get("analytical_depth", "N/A")
            conf = item.get("confidence_level", "N/A")
            feedback = item.get("reasoning_feedback", "")
            
            lines.append(f"{i+1}. **{title}**")
            lines.append(f"   - Outcome: {correct}")
            lines.append(f"   - Depth: {depth} | Confidence: {conf}")
            if feedback:
                lines.append(f"   - Reasoning Analysis: {feedback}")
    
    # Strengths/Improvements
    if analysis.get("strengths"):
        lines.append(f"\n**Candidate Strengths:** {', '.join(analysis.get('strengths', []))}")
    if analysis.get("improvements"):
        lines.append(f"**Improvement Areas:** {', '.join(analysis.get('improvements', []))}")
        
    return "\n".join(lines)


# ============================================================================
# GLOBAL KIWI CHAT (Dashboard-level, no specific attempt)
# ============================================================================

async def chat_with_dashboard_context(
    query: str,
    page_context: str,
    recruiter_id: str,
    conversation_history: List[Dict] = None
) -> str:
    """
    Generate a chatbot response using dashboard-level context.
    
    This is the global Kiwi mode — works on any page without needing
    a specific attempt_id. Fetches real-time data from MongoDB.
    """
    client = get_groq_client()
    
    if not client:
        return "I'm currently unavailable. Please check that the AI service is configured."
    
    # Fetch dynamic context based on page
    dynamic_context = await _fetch_dashboard_context(page_context, recruiter_id)
    
    # Build the final prompt
    final_system_prompt = ASSISTANT_SYSTEM_PROMPT
    
    # Always inject guide for deeper questions
    if should_inject_guide(query):
        guide_content = load_system_guide()
        if guide_content:
            final_system_prompt += f"\n\n=== SYSTEM ARCHITECTURE & FORMULA GUIDE ===\n{guide_content}\n===========================================\n"
    
    # Append dynamic context
    final_system_prompt += f"\n\n**CURRENT PAGE:** {page_context}\n{dynamic_context}"
    
    # Build messages
    messages = [{"role": "system", "content": final_system_prompt}]
    
    if conversation_history:
        for msg in conversation_history[-6:]:
            messages.append(msg)
    
    messages.append({"role": "user", "content": query})
    
    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai_model_70b,
            messages=messages,
            temperature=0.7,
            max_tokens=1500 if should_inject_guide(query) else 800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Dashboard chat generation failed: {e}")
        return "I encountered an issue processing your question. Please try again."


# ============================================================================
# SINGLE-CANDIDATE CHAT (Live Assessment — existing behavior)
# ============================================================================

def chat_with_candidate_context(
    query: str,
    context_data: Dict,
    conversation_history: List[Dict] = None
) -> str:
    """
    Generate a chatbot response using candidate context.
    
    Args:
        query: The recruiter's question
        context_data: The live metrics data for the current candidate
        conversation_history: Optional list of previous messages
    
    Returns:
        String response from the assistant
    """
    client = get_groq_client()
    
    if not client:
        return "I'm currently unavailable. Please check that the AI service is configured."
    
    # Build context summary for the assistant
    candidate_name = context_data.get("candidate", {}).get("name", "the candidate")
    position = context_data.get("candidate", {}).get("position", "unknown role")
    
    metrics = context_data.get("metrics", {})
    skill_profile = context_data.get("skill_profile", {})
    behavioral = context_data.get("behavioral_summary", {})
    population = context_data.get("population_intelligence", {})
    authenticity = population.get("authenticity", {}) if population else {}
    
    context_summary = f"""
**Current Candidate:** {candidate_name}
**Position:** {position}
**Progress:** {context_data.get('progress', {}).get('current', 0)} / {context_data.get('progress', {}).get('total', 0)} questions

**Live Metrics:**
- Avg Response Time: {metrics.get('avg_response_time', 'N/A')}s
- Decision Speed: {metrics.get('decision_speed', 'N/A')}
- Session Continuity: {metrics.get('session_continuity', 'N/A')}%
- Decision Firmness: {metrics.get('decision_firmness', 'N/A')}%
- Reasoning Depth: {metrics.get('reasoning_depth', 'N/A')}%
- Integrity Score: {metrics.get('cheating_resilience', 'N/A')}%

**Skill Profile:**
- Task Completion: {skill_profile.get('problem_solving', 0)}%
- Selection Speed: {skill_profile.get('decision_speed', 0)}%
- Deliberation: {skill_profile.get('analytical_thinking', 0)}%
- Exploration: {skill_profile.get('creativity', 0)}%
- Risk Distribution: {skill_profile.get('risk_assessment', 0)}%

**Behavioral Summary:**
- Approach: {behavioral.get('approach', 'Analyzing...')}
- Under Pressure: {behavioral.get('under_pressure', 'Observing...')}
- Correctness: {behavioral.get('correctness_rate', 'N/A')}%
- Verdict: {behavioral.get('verdict', 'Pending')}

**Authenticity Analysis:**
- Score: {authenticity.get('score', 'N/A')}%
- Status: {authenticity.get('status', 'N/A')}
- Flags: {len(authenticity.get('flags', []))} anomalies detected

{_format_live_answers_for_kiwi(context_data.get('live_answers', []))}

**AI Reasoning Analysis (70B Tier):**
{_format_ai_analysis_for_kiwi(context_data.get('ai_analysis'))}
"""
    
    # Dynamic Prompt Construction
    final_system_prompt = ASSISTANT_SYSTEM_PROMPT
    
    # Inject comprehensive guide if needed
    if should_inject_guide(query):
        guide_content = load_system_guide()
        if guide_content:
            final_system_prompt += f"\n\n=== SYSTEM ARCHITECTURE & FORMULA GUIDE ===\n{guide_content}\n===========================================\n"
            final_system_prompt += "\nINSTRUCTION: Use the above guide to explain calculations precisely. Quote the formulas."

    # Build messages
    messages = [
        {"role": "system", "content": final_system_prompt + "\n\n**CURRENT CANDIDATE DATA:**\n" + context_summary}
    ]
    
    # Add conversation history if provided
    if conversation_history:
        for msg in conversation_history[-6:]:  # Keep last 6 messages for context
            messages.append(msg)
    
    # Add current query
    messages.append({"role": "user", "content": query})
    
    # DEBUG: Log what context Kiwi receives
    live_answers = context_data.get('live_answers', [])
    print(f"[KIWI-DEBUG] live_answers count: {len(live_answers)}")
    for i, ans in enumerate(live_answers):
        print(f"[KIWI-DEBUG] Q{i+1} reasoning: {ans.get('reasoning_text', 'EMPTY')[:80]}")
    
    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai_model_70b,
            messages=messages,
            temperature=0.3,  # Low temperature to prevent hallucination
            max_tokens=1500 if should_inject_guide(query) else 800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        return "I encountered an issue processing your question. Please try again."


"""
Resume suggestions: keywords, formatting, skills gap, content quality.
Orchestrates keyword extractor, formatting analyzer, skills matcher.
"""

from typing import Dict, Any, List, Optional

from app.utils.keyword_extractor import extract_keywords, keyword_match_score
from app.utils.formatting_analyzer import analyze_formatting
from app.utils.skills_matcher import skills_gap_analysis


def _keyword_suggestions(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Missing keywords from JD that should be added to resume."""
    if not job_description or not job_description.strip():
        return {
            "missing_keywords": [],
            "optimization_score": 100,
        }
    res_kw = set(s.lower().replace("_", " ") for s in extract_keywords(resume_text, max_keywords=100))
    jd_kw = list(dict.fromkeys(s.lower().replace("_", " ") for s in extract_keywords(job_description, max_keywords=80)))
    missing = [k for k in jd_kw if k not in res_kw][:15]
    match = keyword_match_score(list(res_kw), jd_kw)
    opt_score = round(match * 100, 0)
    return {
        "missing_keywords": [
            {"keyword": m, "importance": "high", "suggested_location": "skills"}
            for m in missing
        ],
        "optimization_score": int(opt_score),
    }


def _content_quality_suggestions(resume_text: str) -> Dict[str, Any]:
    """Simple content quality: action verbs, length, metrics hints."""
    suggestions = []
    text_lower = (resume_text or "").lower()
    weak_verbs = ["worked on", "helped with", "did", "made", "was responsible for"]
    strong_verbs = ["Led", "Implemented", "Developed", "Optimized", "Designed", "Built", "Launched"]
    for w in weak_verbs:
        if w in text_lower:
            suggestions.append({
                "type": "use_action_verbs",
                "before": w,
                "after": strong_verbs[0],
                "example": "Use 'Led' or 'Developed' instead of 'worked on'",
            })
            break
    if "%" not in (resume_text or "") and "increased" not in text_lower and "reduced" not in text_lower:
        suggestions.append({
            "type": "add_metrics",
            "example": "Add quantifiable results e.g. 'Increased performance by 30%'",
        })
    word_count = len((resume_text or "").split())
    if word_count < 100:
        suggestions.append({
            "type": "length",
            "example": "Consider adding more detail to experience and achievements",
        })
    quality_score = min(100, 40 + (word_count // 3) + (10 if suggestions else 0))
    return {
        "quality_score": min(100, quality_score),
        "suggestions": suggestions[:5],
    }


def get_suggestions(
    resume_text: str,
    job_description: Optional[str] = None,
    suggestion_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Get resume suggestions. suggestion_types: keywords, formatting, skills, content.
    Default: all.
    """
    resume_text = (resume_text or "").strip()
    types = set(suggestion_types or ["keywords", "formatting", "skills", "content"])
    jd = (job_description or "").strip()

    result = {}
    scores = []

    if "keywords" in types:
        result["keyword_suggestions"] = _keyword_suggestions(resume_text, jd)
        scores.append(result["keyword_suggestions"].get("optimization_score", 0))

    if "formatting" in types:
        fmt_score, issues = analyze_formatting(resume_text)
        result["formatting_suggestions"] = {
            "formatting_issues": issues,
            "ats_readability": fmt_score,
        }
        scores.append(fmt_score)

    if "skills" in types and jd:
        result["skills_analysis"] = skills_gap_analysis(resume_text, jd)
        scores.append(result["skills_analysis"].get("skills_match", 0))
    elif "skills" in types:
        result["skills_analysis"] = {
            "skills_match": 0,
            "missing_skills": [],
            "strengths": [],
            "recommendations": ["Add a job description to get skills gap analysis"],
        }

    if "content" in types:
        result["content_suggestions"] = _content_quality_suggestions(resume_text)
        scores.append(result["content_suggestions"].get("quality_score", 0))

    result["overall_score"] = round(sum(scores) / len(scores), 1) if scores else 0.0
    return result

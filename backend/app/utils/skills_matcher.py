"""
Skills gap analysis: resume vs job description.
"""

from typing import List, Dict, Any

from app.utils.keyword_extractor import extract_keywords, COMMON_SKILLS


def skills_gap_analysis(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Compare resume skills with JD requirements.
    Returns skills_match (0-100), missing_skills, strengths, recommendations.
    """
    resume_kw = set(s.lower().replace("_", " ") for s in extract_keywords(resume_text, max_keywords=100))
    jd_kw = set(s.lower().replace("_", " ") for s in extract_keywords(job_description, max_keywords=100))

    if not jd_kw:
        return {
            "skills_match": 100,
            "missing_skills": [],
            "strengths": list(resume_kw)[:15],
            "recommendations": [],
        }

    overlap = resume_kw & jd_kw
    match_pct = round(100.0 * len(overlap) / len(jd_kw), 1) if jd_kw else 100.0
    missing = list(jd_kw - resume_kw)[:20]
    strengths = list(overlap)[:15]

    # Build recommendations
    recommendations = []
    for m in missing[:10]:
        if m in COMMON_SKILLS or any(m in s for s in COMMON_SKILLS):
            recommendations.append(f"Add '{m}' to skills or experience")
    if match_pct < 50:
        recommendations.append("Consider adding more JD keywords to skills and experience sections")

    return {
        "skills_match": min(100.0, match_pct),
        "missing_skills": [{"skill": s, "importance": "high" if s in COMMON_SKILLS else "medium"} for s in missing],
        "strengths": strengths,
        "recommendations": recommendations[:5],
    }

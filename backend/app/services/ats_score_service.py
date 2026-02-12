"""
ATS score calculation aligned with industry practice.

Industry typical weights:
- With JD: Keyword matching 50%, Semantic/skills relevance 25%, Formatting 15%, Experience 10%
- Resume-only (no JD): Formatting/parseability 30%, Section completeness 25%,
  Contact 20%, Content/skills density 20%, Length 5%
"""

from typing import Dict, Any

from app.services.embedding_service import embed_text, cosine_similarity
from app.utils.keyword_extractor import extract_keywords, keyword_match_score
from app.utils.formatting_analyzer import analyze_formatting, resume_only_ats_breakdown


def calculate_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Compute ATS score (0-100) with breakdown.

    With job description: Keyword match 50%, Semantic 25%, Formatting 15%, Experience 10%.
    Without JD (resume-only): Industry-style resume readability (formatting, sections, contact, content).
    """
    resume_text = (resume_text or "").strip()
    job_description = (job_description or "").strip()

    if not resume_text:
        return {
            "ats_score": 0.0,
            "breakdown": {"keywords": 0.0, "semantic_match": 0.0, "formatting": 0.0, "sections": 0.0, "contact": 0.0, "content": 0.0},
            "formatting_issues": [],
            "message": "No resume text",
        }

    # Resume-only score (no JD): industry-style parseability + sections + contact + content
    if not job_description:
        score, breakdown, issues = resume_only_ats_breakdown(resume_text)
        return {
            "ats_score": score,
            "breakdown": breakdown,
            "formatting_issues": issues[:10],
        }
    # With JD: industry weights
    # 1) Keyword match ~50%
    res_kw = extract_keywords(resume_text)
    jd_kw = extract_keywords(job_description)
    kw_score = keyword_match_score(res_kw, jd_kw) if jd_kw else 0.0
    kw_pct = round(kw_score * 100, 1)

    # 2) Semantic/skills relevance ~25%
    try:
        res_emb = embed_text(resume_text)
        jd_emb = embed_text(job_description)
        sem = cosine_similarity(res_emb, jd_emb)
        semantic_score = max(0.0, min(1.0, (sem + 1) / 2.0))
    except Exception:
        semantic_score = 0.0
    sem_pct = round(semantic_score * 100, 1)

    # 3) Formatting ~15%
    fmt_score_pct, formatting_issues = analyze_formatting(resume_text)
    fmt_pct = round(fmt_score_pct, 1)

    # 4) Experience/skills presence ~10% (resume has experience + skills sections / keywords)
    exp_score = min(100, (len(res_kw) * 2) + 30) if res_kw else 30
    exp_pct = round(min(100.0, exp_score), 1)

    # Industry-style weights
    w_kw, w_sem, w_fmt, w_exp = 0.50, 0.25, 0.15, 0.10
    ats = w_kw * kw_pct + w_sem * sem_pct + w_fmt * (fmt_pct / 100.0) * 100 + w_exp * (exp_pct / 100.0) * 100
    ats = round(min(100.0, max(0.0, ats)), 1)

    return {
        "ats_score": ats,
        "breakdown": {
            "keywords": kw_pct,
            "semantic_match": sem_pct,
            "formatting": fmt_pct,
            "experience": exp_pct,
        },
        "formatting_issues": formatting_issues[:10],
    }

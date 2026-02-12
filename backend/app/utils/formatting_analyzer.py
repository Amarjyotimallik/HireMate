"""
ATS-friendly formatting checks for resume text.
Returns a score 0-100 and list of issues/suggestions.
"""

import re
from typing import List, Tuple, Dict


# Standard section headers ATS systems look for
STANDARD_HEADERS = {
    "experience", "work experience", "employment", "professional experience",
    "education", "academic", "qualification", "qualifications",
    "skills", "technical skills", "core competencies", "expertise",
    "summary", "professional summary", "objective", "profile",
    "certifications", "certification", "projects", "achievements",
    "contact", "contact information", "references",
}


def _normalize_line(s: str) -> str:
    return s.lower().strip()


def analyze_formatting(resume_text: str) -> Tuple[float, List[dict]]:
    """
    Analyze resume text for ATS-friendly formatting.
    Returns (score_0_100, list of issues with severity and fix).
    """
    if not resume_text or not resume_text.strip():
        return 0.0, [{"issue": "Resume is empty", "severity": "high", "fix": "Add resume content"}]

    issues: List[dict] = []
    score_components = []

    # 1) Section headers
    lines = [ln.strip() for ln in resume_text.split("\n") if ln.strip()]
    header_like = []
    for i, line in enumerate(lines):
        # Lines that look like section headers: short, often all caps or title case
        clean = _normalize_line(line)
        if len(clean) < 50 and (line == line.upper() or (len(line) > 2 and line[0].isupper())):
            if not re.match(r"^[\d\.\-\*]+\s*", line):
                header_like.append(clean)
    found_headers = set()
    for h in header_like:
        for std in STANDARD_HEADERS:
            if std in h or h in std:
                found_headers.add(std)
                break
    expected = {"experience", "education", "skills"}
    missing = expected - found_headers
    if missing:
        issues.append({
            "issue": f"Missing or non-standard section headers: {', '.join(missing)}",
            "severity": "high",
            "fix": "Add clear sections: Experience, Education, Skills",
        })
    header_score = 1.0 - (len(missing) / 3.0) * 0.5  # up to 50% penalty
    score_components.append(("sections", max(0, header_score)))

    # 2) Date format consistency (MM/YYYY or YYYY)
    date_patterns = list(re.finditer(r"\b(20\d{2}|19\d{2})\b|\b(\d{1,2})[/\-\.](\d{1,2}|20\d{2})\b", resume_text))
    if not date_patterns and "experience" in resume_text.lower():
        issues.append({
            "issue": "No clear dates found in experience",
            "severity": "medium",
            "fix": "Use MM/YYYY or YYYY for roles",
        })
    date_score = 1.0 if date_patterns else 0.5
    score_components.append(("dates", date_score))

    # 3) Length (not too short)
    word_count = len(resume_text.split())
    if word_count < 50:
        issues.append({
            "issue": "Resume very short; may look incomplete",
            "severity": "medium",
            "fix": "Add more detail to experience and skills",
        })
    length_score = min(1.0, word_count / 200.0)
    score_components.append(("length", length_score))

    # 4) Contact info
    has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text))
    has_phone = bool(re.search(r"\+?[\d\s\-\.\(\)]{10,}", resume_text))
    if not has_email:
        issues.append({
            "issue": "Email not found",
            "severity": "high",
            "fix": "Add email in contact section",
        })
    contact_score = (0.5 if has_email else 0) + (0.5 if has_phone else 0)
    score_components.append(("contact", contact_score))

    # 5) Bullet points (often used in experience)
    bullets = resume_text.count("•") + resume_text.count("*") + resume_text.count("- ")
    bullet_score = min(1.0, bullets / 3.0)  # at least 3 bullets
    score_components.append(("bullets", bullet_score))

    # Weighted total (sections 25%, dates 15%, length 15%, contact 30%, bullets 15%)
    weights = {"sections": 0.25, "dates": 0.15, "length": 0.15, "contact": 0.30, "bullets": 0.15}
    total = sum(weights.get(k, 0.2) * v for k, v in score_components)
    ats_readability = round(min(100.0, total * 100), 1)

    return ats_readability, issues


def resume_only_ats_breakdown(resume_text: str) -> Tuple[float, Dict, List]:
    """
    Industry-style ATS score when no JD is provided.
    Weights: Formatting/parseability 30%, Section completeness 25%, Contact 20%,
             Content/skills density 20%, Length & structure 5%.
    Returns (score_0_100, breakdown_dict, issues_list).
    """
    if not resume_text or not resume_text.strip():
        return 0.0, {}, [{"issue": "Resume is empty", "severity": "high", "fix": "Add content"}]

    fmt_score, issues = analyze_formatting(resume_text)
    # Section completeness: same logic as in analyze_formatting
    lines = [ln.strip() for ln in resume_text.split("\n") if ln.strip()]
    header_like = []
    for line in lines:
        clean = _normalize_line(line)
        if len(clean) < 50 and (line == line.upper() or (len(line) > 2 and line[0].isupper())):
            if not re.match(r"^[\d\.\-\*]+\s*", line):
                header_like.append(clean)
    found = set()
    for h in header_like:
        for std in STANDARD_HEADERS:
            if std in h or h in std:
                found.add(std)
                break
    expected = {"experience", "education", "skills"}
    missing = expected - found
    section_score = max(0, 100 - len(missing) * 25)  # 25 pts per missing core section

    # Contact
    has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text))
    has_phone = bool(re.search(r"\+?[\d\s\-\.\(\)]{10,}", resume_text))
    contact_score = 50.0 * (1 if has_email else 0) + 50.0 * (1 if has_phone else 0)

    # Content/skills density: word count + presence of skill-like tokens (numbers, action verbs, tech terms)
    word_count = len(resume_text.split())
    skill_like = len(re.findall(r"\b(python|java|react|sql|aws|lead|managed|developed|implemented)\b", resume_text.lower()))
    content_score = min(100, 30 + (word_count / 3) + min(40, skill_like * 5))

    # Length (cap so very long resumes don't get 100)
    length_score = min(100, 40 + (word_count / 2))

    # Industry weights for resume-only
    total = (
        0.30 * (fmt_score / 100.0) * 100 +
        0.25 * (section_score / 100.0) * 100 +
        0.20 * (contact_score / 100.0) * 100 +
        0.20 * (content_score / 100.0) * 100 +
        0.05 * (length_score / 100.0) * 100
    )
    score = round(min(100.0, max(0.0, total)), 1)
    breakdown = {
        "formatting": round(fmt_score, 1),
        "sections": round(section_score, 1),
        "contact": round(contact_score, 1),
        "content": round(min(100, content_score), 1),
        "length": round(min(100, length_score), 1),
    }
    return score, breakdown, issues

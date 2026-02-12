"""
Extract keywords (skills, tools, etc.) from job descriptions and resume text.
Used for ATS keyword match and resume suggestions.
"""

import re
from typing import List, Set


# Common tech/role keywords to look for (expand as needed)
COMMON_SKILLS = {
    "python", "javascript", "typescript", "java", "go", "golang", "rust", "c++", "c#", "ruby", "php", "swift", "kotlin",
    "react", "angular", "vue", "node", "nodejs", "express", "django", "flask", "fastapi", "spring", "rails",
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "jenkins", "ci/cd", "devops",
    "sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "machine learning", "ml", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn",
    "rest", "graphql", "api", "microservices", "agile", "scrum", "jira", "git", "linux", "html", "css",
}


def _normalize(s: str) -> str:
    return s.lower().strip()


def _tokenize_for_keywords(text: str) -> Set[str]:
    """Tokenize: words, hyphenated parts, and known multi-word skills."""
    if not text or not text.strip():
        return set()
    text = _normalize(text)
    # Split on non-alphanumeric but keep hyphenated (e.g. ci/cd -> ci, cd)
    tokens = set(re.findall(r"[a-z0-9]+(?:[\/\-][a-z0-9]+)*", text))
    # Add 2-3 word n-grams that match common skills
    words = re.findall(r"[a-z0-9]+", text)
    for i in range(len(words)):
        for n in (2, 3):
            if i + n <= len(words):
                ngram = " ".join(words[i : i + n])
                if ngram in COMMON_SKILLS:
                    tokens.add(ngram.replace(" ", "_"))
    return tokens


def extract_keywords(text: str, max_keywords: int = 80) -> List[str]:
    """
    Extract likely skills/keywords from JD or resume.
    Returns a list of normalized keywords (single + multi-word as one token).
    """
    if not text or not text.strip():
        return []
    tokens = _tokenize_for_keywords(text)
    # Prefer known skills, then longer tokens, then alphabetically
    known = [t for t in tokens if t in COMMON_SKILLS or t.replace("_", " ") in COMMON_SKILLS]
    rest = [t for t in tokens if t not in known]
    rest.sort(key=lambda x: (-len(x), x))
    combined = known + rest[: max_keywords - len(known)]
    return combined[:max_keywords]


def keyword_match_score(resume_keywords: List[str], jd_keywords: List[str]) -> float:
    """
    Jaccard-like match: |intersection| / |jd_keywords|.
    Returns 0.0 to 1.0. Empty jd_keywords -> 1.0.
    """
    if not jd_keywords:
        return 1.0
    rset = {_normalize(k) for k in resume_keywords}
    jset = {_normalize(k) for k in jd_keywords}
    # Normalize multi-word: "machine_learning" vs "machine learning"
    rset = set(s.replace("_", " ") for s in rset)
    jset = set(s.replace("_", " ") for s in jset)
    overlap = len(rset & jset)
    return overlap / len(jset) if jset else 1.0

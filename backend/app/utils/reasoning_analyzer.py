"""
Reasoning Analyzer Utility

Analyzes candidate reasoning text for depth and logical structure.
"""

import re
from typing import Dict, Tuple

# Logical keywords with weights for reasoning depth analysis
LOGICAL_KEYWORDS: Dict[str, float] = {
    # Causal connectors
    "because": 1.0,
    "since": 1.0,
    "therefore": 1.5,
    "thus": 1.5,
    "hence": 1.5,
    "consequently": 1.5,
    "as a result": 1.5,
    
    # Contrast connectors
    "however": 1.2,
    "although": 1.2,
    "whereas": 1.2,
    "but": 0.8,
    "yet": 0.8,
    "despite": 1.2,
    "nevertheless": 1.3,
    "on the other hand": 1.3,
    
    # Conditional connectors
    "if": 0.8,
    "then": 0.8,
    "assuming": 1.3,
    "provided": 1.2,
    "unless": 1.0,
    "in case": 1.0,
    
    # Emphasis connectors
    "moreover": 1.2,
    "furthermore": 1.2,
    "additionally": 1.0,
    "in addition": 1.0,
    "also": 0.5,
    
    # Conclusion connectors
    "finally": 1.0,
    "in conclusion": 1.5,
    "to summarize": 1.5,
    "overall": 1.0,
    
    # Reasoning indicators
    "considering": 1.2,
    "given": 1.0,
    "implies": 1.5,
    "suggests": 1.0,
    "indicates": 1.0,
    "means": 0.8,
    
    # Structure markers
    "firstly": 1.0,
    "first": 0.8,
    "secondly": 1.0,
    "second": 0.8,
    "thirdly": 1.0,
    "third": 0.8,
    "lastly": 1.0,
    
    # Analysis indicators
    "analyze": 1.3,
    "evaluate": 1.3,
    "compare": 1.2,
    "contrast": 1.2,
    "examine": 1.2,
    "consider": 1.0,
    "weigh": 1.2,
    
    # Risk-related words (important for this domain)
    "risk": 1.0,
    "risky": 1.0,
    "safe": 0.8,
    "cautious": 1.0,
    "careful": 0.8,
    "balance": 1.0,
    "trade-off": 1.3,
    "tradeoff": 1.3,
}


def count_words(text: str) -> int:
    """Count words in text."""
    if not text or not text.strip():
        return 0
    
    # Split by whitespace and filter empty strings
    words = [w for w in text.split() if w.strip()]
    return len(words)


def count_logical_keywords(text: str) -> Tuple[int, float]:
    """
    Count logical keywords and calculate weighted score.
    
    Returns:
        Tuple of (keyword_count, weighted_score)
    """
    if not text:
        return 0, 0.0
    
    text_lower = text.lower()
    keyword_count = 0
    weighted_score = 0.0
    
    for keyword, weight in LOGICAL_KEYWORDS.items():
        # Use word boundaries for single words, direct search for phrases
        if " " in keyword:
            count = text_lower.count(keyword)
        else:
            # Use regex for word boundary matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count = len(re.findall(pattern, text_lower))
        
        keyword_count += count
        weighted_score += count * weight
    
    return keyword_count, weighted_score


def calculate_reasoning_depth(text: str) -> float:
    """
    Calculate reasoning depth score (0-1).
    
    Combines word count and logical keyword presence.
    """
    if not text or not text.strip():
        return 0.0
    
    word_count = count_words(text)
    keyword_count, weighted_score = count_logical_keywords(text)
    
    # Word count factor (capped at 100 words for max score)
    word_factor = min(word_count / 100, 1.0)
    
    # Keyword factor (capped at 10 weighted points for max score)
    keyword_factor = min(weighted_score / 10, 1.0)
    
    # Combined score: 40% word count, 60% logical structure
    depth_score = (word_factor * 0.4) + (keyword_factor * 0.6)
    
    return round(depth_score, 3)


def analyze_reasoning(text: str) -> Dict:
    """
    Perform comprehensive reasoning analysis.
    
    Returns dict with:
        - word_count: int
        - character_count: int
        - keyword_count: int
        - weighted_keyword_score: float
        - depth_score: float (0-1)
    """
    if not text:
        return {
            "word_count": 0,
            "character_count": 0,
            "keyword_count": 0,
            "weighted_keyword_score": 0.0,
            "depth_score": 0.0,
        }
    
    word_count = count_words(text)
    character_count = len(text)
    keyword_count, weighted_score = count_logical_keywords(text)
    depth_score = calculate_reasoning_depth(text)
    
    return {
        "word_count": word_count,
        "character_count": character_count,
        "keyword_count": keyword_count,
        "weighted_keyword_score": round(weighted_score, 2),
        "depth_score": depth_score,
    }

# HireMate Audit Action Plan
## Product Owner Response to Truth Audit

---

## Executive Summary

The audit reveals HireMate has strong conceptual foundations but needs critical adjustments in:
1. **Legal/ethical framing** - Safer terminology to avoid liability
2. **False positive protection** - Confidence ranges and human override
3. **Layer-specific improvements** - Ground visualizations in raw data
4. **Privacy safeguards** - Clear messaging about what we DON'T track

---

## Critical Issues & Solutions

### 1. TERMINOLOGY OVERHAUL (Legal Protection)

| Current Phrasing | Safer Alternative | Where to Change |
|-----------------|-------------------|-----------------|
| "Student B cheated" | "Behavioral pattern consistent with external assistance" | All user-facing copy |
| "Human vs robotic" | "Deviation from candidate's baseline" | Layer 4 documentation |
| "We detect ChatGPT" | "Patterns inconsistent with independent reasoning" | Layer 5 messaging |
| "Suspicious activity" | "Anomalous behavioral pattern" | Dashboard, reports |
| "Anti-cheat" | "Integrity indicators" | UI labels, API names |

**Action Items:**
- [ ] Update all user-facing strings in frontend
- [ ] Rewrite API documentation
- [ ] Create legal review checklist for future copy

---

### 2. LAYER 1: Speed Analysis - Add Relative Context

**Audit Finding:** Speed alone is dangerous without context

**Solution:**
```python
# BEFORE (absolute)
speed_label = "Quick" if time < 15 else "Moderate" if time < 45 else "Extended"

# AFTER (relative to candidate's own pattern + population context)
def calculate_speed_context(time_seconds, candidate_history, population_stats):
    """
    Returns speed classification with confidence and context
    """
    # Personal baseline (if candidate has multiple attempts)
    personal_avg = candidate_history.avg_first_decision_time if candidate_history else None
    
    # Population percentile (anonymous aggregate)
    percentile = population_stats.get_percentile(time_seconds)
    
    # Classification with uncertainty
    if personal_avg:
        # Compare to their own baseline
        ratio = time_seconds / personal_avg
        if ratio < 0.5:
            return {
                "classification": "Faster than typical",
                "context": "personal_baseline",
                "confidence": "high",
                "note": "Significantly faster than this candidate's average"
            }
    
    # Fall back to population context
    return {
        "classification": get_speed_label(percentile),
        "context": "population_comparison",
        "percentile": percentile,
        "confidence": "medium" if not personal_avg else "high"
    }
```

**UI Change:**
- Show: "Faster than 73% of candidates" instead of "Quick"
- Add tooltip: "Based on aggregate anonymous data"

---

### 3. LAYER 3: Radar Chart - Ground in Raw Events

**Audit Finding:** Visual sugar unless backed by data

**Solution:**
Every radar chart spike must be drill-downable:

```python
class RadarChartMetrics:
    def __init__(self):
        self.task_completion = {
            "score": 85,
            "evidence": [
                {"type": "event", "event_id": "evt_123", "description": "Task completed in 45s"},
                {"type": "event", "event_id": "evt_124", "description": "Explanation submitted with 42 words"}
            ],
            "raw_events": ["evt_123", "evt_124", "evt_125"]
        }
```

**UI Change:**
- Click any radar axis → Show timeline of events that contributed
- Each metric card has "View Evidence" button
- Export: "Download Raw Event Log" option

---

### 4. LAYER 4: Authenticity - Baseline Comparison

**Audit Finding:** "Human vs robotic" is absolute and risky

**Solution:**
```python
def calculate_authenticity(events, candidate_baseline=None):
    """
    Compare to candidate's own baseline, not population
    """
    if candidate_baseline:
        # Compare to their own history
        variance_ratio = calculate_variance(events) / candidate_baseline.variance
        
        if variance_ratio < 0.3:
            return {
                "assessment": "Significantly more uniform than your baseline",
                "confidence": 0.75,
                "recommendation": "Review session recording",
                "risk_level": "elevated"
            }
    else:
        # First attempt - no baseline, lower confidence
        return {
            "assessment": "First assessment - no baseline comparison available",
            "confidence": 0.4,
            "recommendation": "Consider follow-up assessment",
            "risk_level": "unknown"
        }
```

**Key Change:**
- First-time candidates get "insufficient data" not "suspicious"
- Build baseline across multiple attempts

---

### 5. LAYER 5: Anti-GPT - Reframe to Behavioral Inconsistency

**Audit Finding:** Cannot reliably detect GPT, only behavioral signals

**Solution:**
```python
# Rename service
class BehavioralConsistencyAnalyzer:  # WAS: AntiGPTDetector
    
    def analyze(self, events):
        flags = []
        
        # Detect paste events
        pastes = [e for e in events if e.type == "PASTE_DETECTED"]
        if pastes:
            flags.append({
                "type": "rapid_text_entry",
                "description": f"{len(pastes)} instances of text appearing faster than human typing",
                "possible_explanations": [
                    "Copy-paste from notes",
                    "Auto-fill from browser",
                    "External assistance"
                ],
                "severity": "medium" if len(pastes) <= 2 else "high"
            })
        
        # Detect confidence without exploration
        if self.has_confidence_without_exploration(events):
            flags.append({
                "type": "immediate_commitment",
                "description": "Selected option without viewing alternatives",
                "possible_explanations": [
                    "Prior knowledge of question",
                    "Pre-determined answer",
                    "External guidance"
                ],
                "severity": "low"
            })
        
        return {
            "flags": flags,
            "overall_assessment": "Behavioral patterns noted" if flags else "No anomalies detected",
            "confidence": self.calculate_confidence(events),
            "recommendation": "Review flagged sessions" if flags else "None"
        }
```

**UI Change:**
- Remove "AI Detection" label
- Replace with "Behavioral Consistency Check"
- Show multiple possible explanations, not accusations

---

### 6. LAYER 7: Stress Analysis - Make Optional

**Audit Finding:** Stress tolerance is role-dependent

**Solution:**
```python
class StressAnalysisConfig:
    """Per-assessment configuration"""
    enabled: bool = True  # Can be disabled per role
    weight: float = 0.1   # Reduced from 0.15
    framing: str = "behavioral_shift"  # NOT "stress_response"
    
    def analyze(self, first_half, second_half):
        if not self.enabled:
            return {"status": "not_applicable"}
        
        speed_change = self.calculate_speed_change(first_half, second_half)
        
        return {
            "observation": "Speed increased in second half" if speed_change < -0.3 else "Consistent pacing",
            "interpretation_options": [
                "Candidate found latter questions easier",
                "Candidate was rushing due to time awareness",
                "Candidate warmed up to the format"
            ],
            "recommendation": "Consider role context when interpreting"
        }
```

**UI Change:**
- Add toggle: "Include pacing analysis" when creating assessment
- Default OFF for senior roles, ON for high-pressure roles

---

### 7. LAYER 8: Overall Fit - Add Transparency

**Audit Finding:** Grades feel over-authoritative

**Solution:**
```python
def generate_fit_assessment(scores, flags):
    # Calculate grade
    grade = calculate_grade(scores)
    
    return {
        "grade": grade,
        "grade_context": {
            "calculation_breakdown": scores,
            "confidence": scores.confidence,
            "sample_size": scores.task_count
        },
        "recruiter_controls": {
            "can_override": True,
            "override_reason_required": True,
            "suggested_follow_up": generate_follow_up_questions(scores)
        },
        "disclaimer": {
            "text": "This assessment reflects behavioral patterns during a limited task sample. It should inform, not replace, human judgment.",
            "required_acknowledgment": True
        },
        "explainability": {
            "layer_contributions": scores.layer_breakdown,
            "key_indicators": scores.top_signals,
            "contradictory_signals": scores.conflicts
        }
    }
```

**UI Change:**
- Grade shown with "i" icon explaining calculation
- "Override Grade" button with reason field
- Mandatory disclaimer checkbox before viewing results

---

### 8. FALSE POSITIVE PROTECTION SYSTEM

**Critical Addition:**

```python
class FalsePositiveProtection:
    """
    Built-in safeguards against flagging good candidates
    """
    
    def calculate_confidence(self, metrics):
        """Meta-confidence in our own analysis"""
        factors = {
            "sample_size": min(1.0, metrics.task_count / 5),  # Need at least 5 tasks
            "data_quality": metrics.event_coverage,
            "cross_layer_agreement": self.check_layer_agreement(metrics),
            "baseline_available": metrics.has_baseline
        }
        
        confidence = sum(factors.values()) / len(factors)
        
        return {
            "overall": confidence,
            "factors": factors,
            "recommendation": self.get_recommendation(confidence)
        }
    
    def get_recommendation(self, confidence):
        if confidence < 0.5:
            return {
                "action": "insufficient_data",
                "message": "Low confidence in assessment. Recommend additional tasks or follow-up assessment.",
                "auto_flag": False  # Don't flag, just note
            }
        elif confidence < 0.7:
            return {
                "action": "review_recommended",
                "message": "Moderate confidence. Human review suggested.",
                "auto_flag": False
            }
        else:
            return {
                "action": "proceed",
                "message": "High confidence assessment",
                "auto_flag": True if metrics.has_concerning_patterns else False
            }
```

**UI Changes:**
- Confidence badge on every assessment (High/Medium/Low)
- "Insufficient Data" state instead of premature conclusions
- "Request Additional Assessment" button for low-confidence cases

---

### 9. ETHICAL SAFEGUARDS & PRIVACY

**Add to every assessment page:**

```html
<div class="privacy-notice">
  <h4>What We Track</h4>
  <ul>
    <li>✓ Time between interactions</li>
    <li>✓ Option selections and changes</li>
    <li>✓ Text entry patterns (speed only, not content)</li>
    <li>✓ Focus changes (tab switches)</li>
  </ul>
  
  <h4>What We DON'T Track</h4>
  <ul>
    <li>✗ Keystroke logging</li>
    <li>✗ Screen recording</li>
    <li>✗ Personal data inference</li>
    <li>✗ Content of reasoning (only length and structure)</li>
    <li>✗ Identity or biometric data</li>
  </ul>
  
  <p><strong>Behavior ≠ Identity</strong></p>
  <p>This assessment observes problem-solving patterns, not who you are.</p>
</div>
```

**Required Disclaimers:**
- Pre-assessment: Candidate must acknowledge privacy notice
- Results page: "This is one data point among many"
- Report export: "For informational purposes only"

---

### 10. RECRUITER EDUCATION

**Create:**
1. **"Interpreting HireMate Reports"** guide
2. **False positive examples** with explanations
3. **"When to Override"** decision tree
4. **Legal compliance checklist**

**Sample Guide Section:**
```
## Red Flags vs. False Positives

RED FLAG (Investigate):
- Multiple paste events + immediate submission + no option exploration
- Consistent with external assistance

FALSE POSITIVE (Normal):
- Fast decision + detailed explanation
- Could indicate: Prior knowledge, practiced skill, or genuine expertise
- ACTION: Check explanation quality, consider follow-up question

NEURODIVERSENT CONSIDERATIONS:
- Some candidates may show "robotic" patterns (consistent timing, few changes)
- This is NOT suspicious - it's a valid problem-solving style
- ACTION: Look at explanation depth and logical structure
```

---

## Implementation Priority

### Phase 1: Legal Protection (Week 1)
- [ ] Terminology overhaul
- [ ] Privacy notice implementation
- [ ] Disclaimer additions

### Phase 2: False Positive Protection (Week 2-3)
- [ ] Confidence scoring system
- [ ] Baseline comparison for returning candidates
- [ ] "Insufficient Data" state

### Phase 3: Layer Improvements (Week 4-6)
- [ ] Layer 1: Relative speed
- [ ] Layer 3: Drill-down evidence
- [ ] Layer 4: Baseline-based authenticity
- [ ] Layer 5: Reframed messaging
- [ ] Layer 7: Optional stress analysis
- [ ] Layer 8: Override controls

### Phase 4: Documentation (Week 7)
- [ ] Recruiter training materials
- [ ] Legal review
- [ ] Candidate-facing FAQ

---

## Success Metrics

1. **False Positive Rate** < 5% (track via recruiter overrides)
2. **Confidence Score** shown on 100% of assessments
3. **Override Rate** tracked and analyzed
4. **Candidate Complaints** monitored
5. **Legal Review** passed

---

## Conclusion

HireMate is conceptually strong. These changes transform it from "AI that judges candidates" to "tool that provides behavioral insights with appropriate uncertainty." The key is humility in our claims and transparency in our methods.

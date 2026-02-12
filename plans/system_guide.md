# HireMate Intelligence System - Complete Technical Guide

> **Purpose:** This document is the GROUND TRUTH for understanding how HireMate works.  
> Written for beginners: no prior coding knowledge required.

---

## Table of Contents
1. [What is HireMate?](#1-what-is-hiremate)
2. [The 8-Layer Intelligence System](#2-the-8-layer-intelligence-system)
3. [The 19 Behavioral Metrics](#3-the-19-behavioral-metrics)
4. [How Data Flows Through the Layers](#4-how-data-flows-through-the-layers)
5. [The Math Behind the Scores](#5-the-math-behind-the-scores)
6. [System Architecture](#6-system-architecture)

---

## 1. What is HireMate?

### The Problem We Solve
Traditional hiring tests only check **WHAT** answer you give. But in the age of ChatGPT, anyone can find the "right" answer. HireMate checks **HOW** you arrive at that answer.

### Our Philosophy
- **We don't score answers.** We observe behavior.
- **No black-box AI.** Every score can be explained with hard data.
- **Transparency first.** Recruiters can "drill down" into any metric.

### Simple Analogy
Imagine two students taking a math test:
- **Student A** writes "10" as the answer in 2 seconds.
- **Student B** writes "10" as the answer in 2 seconds, but we saw them paste it from another window.

Both got the right answer. But HireMate knows **Student B cheated**.

---

## 2. The 8-Layer Intelligence System

Think of this like a water filtration system. Raw data enters at Layer 1, and by Layer 8, we have clean, actionable intelligence.

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW EVENT DATA (Clicks, Timing)              │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: SPEED ANALYSIS                                        │
│  "How fast does the candidate process information?"             │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: DECISION FIRMNESS                                     │
│  "How stable are their choices?"                                │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: RADAR CHART DYNAMICS                                  │
│  "What is their behavioral 'shape'?"                            │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: AUTHENTICITY & ANOMALY DETECTION                      │
│  "Is this behavior human or robotic?"                           │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5: ANTI-GPT LAYER                                        │
│  "Are they using external tools like ChatGPT?"                  │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 6: CONFIDENCE & CONSISTENCY                              │
│  "How reliable is our analysis?"                                │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 7: STRESS & PRESSURE                                     │
│  "How does behavior change under time pressure?"                │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 8: OVERALL FIT (RECONCILIATION)                          │
│  "Final hiring recommendation with grade S to D"                │
└─────────────────────────────────────────────────────────────────┘
```

---

### Layer 1: Speed Analysis

**What it measures:** How quickly does the candidate make their first choice?

**Why it matters:** Fast decisions can indicate confidence OR impulsiveness. Slow decisions can indicate deep thinking OR confusion. Context is everything.

**The Metric:** `First Decision Speed`
- Time from when the question appears → to the first click on an option.

**Thresholds (in seconds):**
| Speed | Time | What It Might Mean |
|-------|------|-------------------|
| Fast | < 15 seconds | Intuitive thinker, confident, or impulsive |
| Moderate | 15-45 seconds | Balanced, methodical approach |
| Extended | > 45 seconds | Deep analyzer, or possibly stuck/confused |

**Code Example:**
```python
# How we calculate First Decision Speed
first_click_time = first_option_click_timestamp
question_load_time = task_started_timestamp

first_decision_speed = first_click_time - question_load_time  # in seconds

# Classify the speed
if first_decision_speed < 15:
    speed_label = "Quick"
elif first_decision_speed < 45:
    speed_label = "Moderate"
else:
    speed_label = "Extended"
```

---

### Layer 2: Decision Firmness

**What it measures:** How often does the candidate change their mind?

**Why it matters:** Experts know what they want. Guessers click randomly. This layer separates them.

**The Metric:** `Firmness Score` (0-100)

**The Formula:**
```
Firmness Score = 100 - ((Total Option Changes / Total Questions) × 100)
```

**Example:**
- Candidate answers 5 questions, changes their answer 2 times total.
- Firmness = 100 - ((2 / 5) × 100) = 100 - 40 = **60%**

**Interpretation:**
| Score | Meaning |
|-------|---------|
| 90-100% | Rock solid. Almost never changed answers. |
| 70-89% | Mostly certain. Maybe 1-2 refinements. |
| 50-69% | Some uncertainty. Exploring options. |
| < 50% | High uncertainty. Possibly guessing. |

**Code Example:**
```python
total_changes = count_events(event_type="OPTION_CHANGED")
total_questions = len(task_ids)

firmness_score = 100 - ((total_changes / total_questions) * 100)
firmness_score = max(0, min(100, firmness_score))  # Keep between 0-100
```

---

### Layer 3: Radar Chart Dynamics

**What it measures:** The candidate's "behavioral shape" across 5 dimensions.

**Why it matters:** Some people are fast but sloppy. Others are slow but precise. The radar chart shows the balance.

**The 5 Axes:**

| Axis | What It Measures | Source |
|------|-----------------|--------|
| **Task Completion** | Did they finish and explain well? | Completion rate + explanation detail |
| **Selection Speed** | How fast were their choices? | Average initial selection time |
| **Deliberation Pattern** | Did they think deeply? | Explanation detail + time spent |
| **Option Exploration** | Did they consider alternatives? | Number of option changes |
| **Risk Preference** | Conservative or bold choices? | Risk level of selected options |

**Code Example:**
```python
def compute_skill_profile(metrics):
    return {
        "task_completion": calculate_completion_score(metrics),
        "selection_speed": calculate_speed_score(metrics),
        "deliberation_pattern": calculate_deliberation_score(metrics),
        "option_exploration": calculate_exploration_score(metrics),
        "risk_preference": calculate_risk_score(metrics)
    }
```

---

### Layer 4: Authenticity & Anomaly Detection

**What it measures:** Is this behavior "too perfect" to be human?

**Why it matters:** Bots and scripted behavior follow predictable patterns. Humans are messy.

**Red Flags We Detect:**

| Anomaly | What It Looks Like | Penalty |
|---------|-------------------|---------|
| Uniform Timing | Every answer in exactly 5.0s, 5.1s, 5.0s | -15% |
| Perfect Patterns | Selecting A, B, C, A, B, C in sequence | -25% |
| Identical Explanations | Same text copy-pasted for every question | -15% |
| Coached Pauses | Waiting exactly 30s before every action | -10% |
| Zero Revisions | Never changing a single answer (rare for humans) | -10% |

**The Formula:**
```
Authenticity Score = 100 - Total Deductions
```

**Code Example:**
```python
def compute_authenticity(events):
    deductions = 0
    
    # Check for uniform timing
    time_variance = calculate_timing_variance(events)
    if time_variance < 0.5:  # Very uniform = suspicious
        deductions += 15
    
    # Check for sequential patterns
    if has_sequential_pattern(events):
        deductions += 25
    
    return max(0, 100 - deductions)
```

---

### Layer 5: Anti-GPT Layer (External Integrity)

**What it measures:** Is the candidate using ChatGPT, Google, or another device?

**Why it matters:** In 2026, AI can write perfect answers. We detect when it's being used.

**Detection Methods:**

#### Method 1: Paste Detection
- Human typing speed: ~40 words per minute = ~5 characters per second
- If 200 characters appear in 0.1 seconds → **That's a paste.**

```python
def detect_paste(text_input_event):
    characters = text_input_event.character_count
    time_taken = text_input_event.duration_ms / 1000  # convert to seconds
    
    characters_per_second = characters / time_taken
    
    if characters_per_second > 50:  # Impossible for human typing
        return True  # PASTE DETECTED
    return False
```

#### Method 2: Focus Loss (Tab Switching)
- Every time the candidate leaves the browser tab, we log a `blur` event.
- Coming back = `focus` event.
- High focus loss = likely checking another source.

```python
def count_focus_loss(events):
    return len([e for e in events if e.event_type == "focus_lost"])
```

#### Method 3: Coached Pauses
- If idle time is rhythmically consistent (e.g., exactly 30s every time), it suggests a "script" or external coaching.

---

### Layer 6: Confidence & Consistency

**What it measures:** How reliable is our analysis?

**Why it matters:** We don't make big claims from small data. Confidence grows with more questions answered.

**The Logic:**
```
Analysis Confidence = (Questions Completed / Total Questions) × Pattern Stability
```

**Pattern Stability:** If the candidate's behavior is consistent across questions, stability is high. If they're erratic, it's low.

**Example:**
- Candidate completed 4 out of 5 questions.
- Their speed and firmness were similar across all 4.
- Confidence = (4/5) × 0.9 = **72%**

**Code Example:**
```python
def compute_confidence(per_task_metrics, total_tasks):
    completed = len([t for t in per_task_metrics if t["is_completed"]])
    completion_ratio = completed / total_tasks
    
    # Calculate pattern stability (standard deviation of times)
    times = [t["time_spent_seconds"] for t in per_task_metrics]
    stability = 1 - min(1, calculate_std_dev(times) / 30)  # Normalize
    
    confidence = completion_ratio * stability * 100
    return round(confidence, 1)
```

---

### Layer 7: Stress & Pressure

**What it measures:** Does the candidate "crumple" under pressure?

**Why it matters:** Real jobs have deadlines. We simulate that pressure and observe the change.

**The Logic:** Compare behavior in the **first half** vs. the **second half** of the assessment.

**Signs of "Crumpling":**
| First Half | Second Half | Interpretation |
|-----------|-------------|----------------|
| Moderate speed | Much faster | Rushing due to time pressure |
| High firmness | Low firmness | Panic-clicking, second-guessing |
| Detailed explanations | Short/no explanations | Cutting corners |

**Code Example:**
```python
def compute_pressure_response(per_task_metrics):
    half = len(per_task_metrics) // 2
    first_half = per_task_metrics[:half]
    second_half = per_task_metrics[half:]
    
    # Compare average speed
    first_avg_speed = average([t["initial_selection_seconds"] for t in first_half])
    second_avg_speed = average([t["initial_selection_seconds"] for t in second_half])
    
    # If speed increased dramatically but firmness dropped
    speed_change = (second_avg_speed - first_avg_speed) / first_avg_speed
    
    if speed_change < -0.3:  # 30% faster in second half
        return "Rushed Under Pressure"
    elif speed_change > 0.3:  # 30% slower
        return "Fatigued"
    else:
        return "Consistent"
```

---

### Layer 8: Overall Fit Layer (Reconciliation)

**What it measures:** The final hiring recommendation.

**Why it matters:** This is the number recruiters see. It must be defensible.

**The Master Formula:**
```
Overall Fit Score = (Task × 0.30) + (Behavioral × 0.35) + (Skill × 0.25) + (Resume × 0.10) - Penalties
```

**Breakdown:**

| Component | Weight | What It Includes |
|-----------|--------|------------------|
| **Task Score** | 30% | Completion rate + Accuracy (% correct) |
| **Behavioral Score** | 35% | Firmness + Session Continuity + Response Quality |
| **Skill Score** | 25% | Average of 5 radar chart axes |
| **Resume Alignment** | 10% | How well behavior matches claimed skills |
| **Anti-Cheat Penalty** | Up to -15 | Deductions for focus loss, pastes, copies |

**Grade Mapping:**

| Score | Grade | Label |
|-------|-------|-------|
| 90-100 | S | Exceptional Match |
| 80-89 | A | Strong Match |
| 70-79 | B | Good Match |
| 60-69 | C | Moderate Match |
| 0-59 | D | Low Match |

**Code Example:**
```python
def compute_overall_fit(task_score, behavioral_score, skill_score, resume_score, penalties):
    weighted = (
        task_score * 0.30 +
        behavioral_score * 0.35 +
        skill_score * 0.25 +
        resume_score * 0.10
    )
    
    final_score = max(0, weighted - penalties)
    
    # Assign grade
    if final_score >= 90:
        grade = "S"
    elif final_score >= 80:
        grade = "A"
    elif final_score >= 70:
        grade = "B"
    elif final_score >= 60:
        grade = "C"
    else:
        grade = "D"
    
    return {"score": final_score, "grade": grade}
```

---

## 3. The 18 Behavioral Metrics

We track 18 distinct signals, organized into 4 groups:

### Group A: Execution & Timing (5 Metrics)

| # | Metric Name | What It Measures | Unit |
|---|-------------|-----------------|------|
| 1 | **First Decision Speed** | Time to first click | Seconds |
| 2 | **Total Time Spent** | Duration on question | Seconds |
| 3 | **Idle Time** | Inactive periods (>5s no interaction) | Seconds |
| 4 | **Selection-to-Submit Gap** | Time between last selection and submit | Seconds |
| 5 | **Task Duration Variance** | Consistency of time across questions | Std Dev |

### Group B: Decision Logic (5 Metrics)

| # | Metric Name | What It Measures | Unit |
|---|-------------|-----------------|------|
| 6 | **Option Change Count** | Times answer was changed | Count |
| 7 | **Final Selection Stability** | First choice = Final choice? | Boolean |
| 8 | **Option Coverage** | % of options viewed before deciding | Percentage |
| 9 | **Decision Firmness Ratio** | Normalized stability score | 0-100 |
| 10 | **Pattern Consistency** | Similarity of behavior across questions | 0-1 |

### Group C: Reasoning & Content (3 Metrics)

| # | Metric Name | What It Measures | Unit |
|---|-------------|-----------------|------|
| 11 | **Explanation Word Count** | Length of written reasoning | Words |
| 12 | **Logical Connector Usage** | "because", "therefore", etc. | Count |
| 13 | **Explanation Detail Score** | Quality of reasoning | 0-100 |

### Group D: Integrity & Security (5 Metrics)

| # | Metric Name | What It Measures | Unit |
|---|-------------|-----------------|------|
| 14 | **Focus Loss Count** | Tab switches / window blurs | Count |
| 15 | **Paste Anomaly Flag** | Text appeared faster than typing | Boolean |
| 16 | **Paste Count** | Number of paste events | Count |
| 17 | **Copy Count** | Copying question text (to feed AI?) | Count |
| 18 | **Long Idle Count** | Extended pauses (>30s) | Count |

---

## 4. How Data Flows Through the Layers

Here's the journey of a single click through all 8 layers:

### Step 1: The Click Happens
```
Candidate clicks Option B at 14:32:05.342
```

### Step 2: Event is Captured (Frontend)
```javascript
// JavaScript sensor captures the event
{
  "event_type": "OPTION_SELECTED",
  "option_index": 1,
  "timestamp": "2026-02-08T14:32:05.342Z",
  "task_id": "abc123"
}
```

### Step 3: Event Travels to Server (WebSocket)
```
Browser → WebSocket → FastAPI Server (< 100ms)
```

### Step 4: Event is Stored (MongoDB)
```
behavior_events collection: INSERT (immutable, append-only)
```

### Step 5: Layers Process the Event

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: Calculate first_decision_speed                        │
│          Result: 14.3 seconds → "Quick"                         │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 2: Update firmness tracking                               │
│          Result: This is 2nd change → Firmness drops to 80%     │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 3: Update radar chart values                              │
│          Result: Speed axis = 85, Exploration axis +12          │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 4: Check for anomalies                                    │
│          Result: No uniform timing detected                     │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 5: Check for external tools                               │
│          Result: No paste, no focus loss                        │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 6: Update confidence                                      │
│          Result: 3 questions done → Confidence = 65%            │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 7: (Runs at end) Compare first half vs second half        │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 8: (Runs at end) Calculate final Overall Fit Score        │
└─────────────────────────────────────────────────────────────────┘
```

### Step 6: Recruiter Dashboard Updates (Real-time)
```
WebSocket → Broadcast → Dashboard shows new metrics
```

---

## 5. The Math Behind the Scores

### 5.1 Task Score Calculation

```python
completion_rate = (tasks_completed / total_tasks) * 100
accuracy_rate = (correct_answers / tasks_completed) * 100

task_score = (completion_rate * 0.4) + (accuracy_rate * 0.6)
```

**Example:**
- Completed 4/5 tasks (80%)
- Got 3 correct out of 4 (75%)
- Task Score = (80 × 0.4) + (75 × 0.6) = 32 + 45 = **77**

---

### 5.2 Behavioral Score Calculation

```python
decision_firmness = 100 - (option_changes * 10)  # -10 per change
session_continuity = 100 - (idle_time_percent * 100)
response_quality = 100 - idle_time_level

behavioral_score = (
    decision_firmness * 0.4 +
    session_continuity * 0.3 +
    response_quality * 0.3
)
```

---

### 5.3 Anti-Cheat Penalty Calculation

```python
penalty = 0
penalty += min(5, focus_loss_count * 1)    # -1 per tab switch, max -5
penalty += min(5, paste_count * 2)         # -2 per paste, max -5
penalty += min(3, copy_count * 3)          # -3 per copy, max -3
penalty += min(2, long_idle_count * 0.5)   # -0.5 per long idle, max -2

total_penalty = min(15, penalty)  # Cap at 15 points
```

---

### 5.4 Explanation Detail Score

```python
LOGICAL_KEYWORDS = ["because", "therefore", "however", "although", 
                    "considering", "firstly", "secondly", "finally"]

word_count = len(explanation.split())
connector_count = sum(1 for word in LOGICAL_KEYWORDS if word in explanation.lower())

# Normalize to 0-100
word_score = min(1.0, word_count / 40) * 60  # 40 words = max word contribution
connector_score = min(1.0, connector_count / 3) * 40  # 3 connectors = max

explanation_detail = word_score + connector_score
```

**Example:**
- "I chose this because it balances risk and reward. However, option A was also tempting."
- Word count: 15 words → 15/40 = 0.375 × 60 = **22.5**
- Connectors: "because", "however" = 2 → 2/3 = 0.67 × 40 = **26.8**
- Total: 22.5 + 26.8 = **49.3 / 100**

---

## 6. System Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐   │
│  │ Candidate View  │  │ Recruiter View  │  │ Event Sensors (JS)      │   │
│  │ (Assessment)    │  │ (Dashboard)     │  │ - Click listeners       │   │
│  └────────┬────────┘  └────────┬────────┘  │ - Focus/Blur detection  │   │
│           │                    │           │ - Paste detection       │   │
│           │                    │           └───────────┬─────────────┘   │
└───────────┼────────────────────┼───────────────────────┼─────────────────┘
            │                    │                       │
            ▼                    ▼                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        TRANSPORT LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                    WebSocket (Real-time)                        │     │
│  │              Bi-directional, persistent connection              │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Event       │  │ Metrics     │  │ AI Analyzer │  │ Auth Guard  │     │
│  │ Ingestion   │→ │ Engine      │→ │ (Kiwi)      │  │ (JWT)       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          DATABASE (MongoDB)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │ behavior_events │  │ task_attempts   │  │ computed_metrics│          │
│  │ (Immutable Log) │  │ (Session State) │  │ (Derived Data)  │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `live_metrics_service.py` | All 8-layer calculations |
| `CandidateAssessment.jsx` | Candidate-facing UI + event sensors |
| `LiveAssessment.jsx` | Recruiter dashboard with live updates |
| `event.py` | Event type definitions (schemas) |
| `system_guide.md` | This document (Ground Truth) |

---

## Summary

HireMate's 8-Layer Intelligence System transforms raw clicks into actionable hiring intelligence:

1. **Layer 1-2:** Measure *speed* and *certainty*
2. **Layer 3:** Visualize the *behavioral shape*
3. **Layer 4-5:** Detect *fraud and AI usage*
4. **Layer 6-7:** Measure *reliability* and *pressure response*
5. **Layer 8:** Produce the *final hiring grade*

**Every score is explainable. Every metric is traceable. Every decision is defensible.**

---

*Last Updated: February 2026*
*Version: 2.0 (8-Layer Architecture)*

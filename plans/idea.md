# Project Plan

You are a senior backend systems architect and data instrumentation engineer.
You are working on an existing project where:

- The frontend UI is already built and MUST NOT be modified.
- Your responsibility is ONLY the backend.
- The frontend emits user interaction events (clicks, selections, timing).
- The backend must observe and interpret behavior, not answers.
ABSOLUTE RULE:
❌ Do NOT suggest UI changes
❌ Do NOT modify frontend behavior
❌ Do NOT redesign screens
✅ Assume frontend events already exist

---

## SYSTEM YOU ARE BUILDING

This is NOT a quiz system.
It is a behavior-based skill observation backend where:

- There is no correct or wrong answer.
- The system observes HOW a user solves a task.
- Raw behavior is logged first.
- Interpretation happens only after task completion.
- All logic must be explainable (no black-box ML).

---

## TECH STACK (FIXED – DO NOT CHANGE)

## Backend: FastAPI (Python)
Database: MongoDB (event-based storage)
Auth: JWT + one-time assessment tokens
Realtime: WebSockets (FastAPI)
Deployment: Render

## CORE BACKEND RESPONSIBILITIES

1. Serve micro decision-making tasks
2. Create task attempts using one-time tokens
3. Log all behavioral events directly into MongoDB
4. Broadcast events to frontend in real time
5. After task completion:
    - Compute deterministic behavioral metrics
    - Interpret them using rule-based logic
6. Produce recruiter-readable skill output

---

## BEHAVIOR EVENTS TO SUPPORT

Examples (not limited to):

- task_started
- option_viewed
- option_selected
- option_changed
- reasoning_started
- reasoning_submitted
- task_completed
Each event MUST:
- Be immutable
- Be timestamped server-side
- Be stored immediately in MongoDB
- Be broadcast to connected clients (real-time)

---

## BEHAVIOR METRICS (POST-HOC ONLY)

Derived metrics must include:

- Total time
- Active interaction time
- Hesitation time
(total time − active interaction time)
- First decision speed
- Decision change count
- Reasoning depth
(word count × logical keyword presence)
- Risk behavior
(each option has predefined risk tag:
low / medium / high)
IMPORTANT:
❌ Metrics are NOT computed during the task
✅ Metrics are computed AFTER task completion

---

## SKILL INTERPRETATION RULES

Skill inference must be:

- Deterministic
- Rule-based
- Explainable
- Human-readable
Examples:
- Slow + structured → Analytical thinker
- Fast + many changes → Exploratory thinker
- Low risk preference → Risk-averse
NO machine learning.
NO probabilistic scoring.
NO opaque models.

---

## DATABASE DESIGN REQUIREMENTS

MongoDB must contain:

- users
- tasks
- options (with risk metadata)
- task_attempts
- behavior_events (append-only, core data)
- computed_metrics
- skill_profiles
behavior_events is the source of truth.

---

## REAL-TIME REQUIREMENTS

- Use FastAPI WebSockets
- Broadcast logged events immediately
- Frontend uses this only for live feedback
- Backend remains authoritative

---

## SECURITY REQUIREMENTS

- JWT authentication
- One-time assessment tokens
- Prevent task re-attempts
- Lock attempts after completion

---

## WHAT YOU MUST DO FIRST

BEFORE WRITING ANY CODE:

1. Propose a clean backend architecture
2. Define MongoDB schemas
3. Define REST + WebSocket APIs
4. Define event validation rules
5. Define metric computation formulas
6. Define skill interpretation logic
7. Create a step-by-step execution TODO list

---

## STOP CONDITION

❗ DO NOT WRITE ANY CODE YET ❗
STOP after the architecture + TODO list.
WAIT for explicit user approval before coding.
If anything is ambiguous, make reasonable backend-only assumptions.
Thinking: The user is asking me to design a behavior-based skill observation backend system. This is a comprehensive request that requires careful architectural planning before any code is written.
Let me break down what they need:

1. System Purpose: Observe HOW users solve tasks (not what they answer) - it's behavioral observation, not a quiz
2. Tech Stack: FastAPI, MongoDB, JWT auth, WebSockets, Render deployment
3. Core Flow:
    - Serve micro decision-making tasks
    - Create task attempts with one-time tokens
    - Log behavioral events to MongoDB
    - Broadcast events in real-time via WebSocket
    - After task completion: compute metrics and interpret skills
    Let me design this systematically:
4. Backend Architecture
I need to design:
- Service layers
- API structure
- Event flow
- Data flow
1. MongoDB Schemas
Collections needed:
- users
- tasks
- options (with risk metadata)
- task_attempts
- behavior_events (append-only)
- computed_metrics
- skill_profiles
1. REST + WebSocket APIs
REST endpoints for:
- Auth (login, token generation)
- Tasks (get available tasks)
- Attempts (create, complete)
- Events (log events)
- Metrics/Skills (retrieve results)
WebSocket for:
- Real-time event broadcasting
1. Event Validation Rules
Each event type needs specific validation
2. Metric Computation Formulas
- Total time
- Active interaction time
- Hesitation time
- First decision speed
- Decision change count
- Reasoning depth
- Risk behavior
1. Skill Interpretation Logic
Rule-based, deterministic mapping from metrics to skills
2. TODO List
Step-by-step execution plan
Let me write this out comprehensively.
Behavior-Based Skill Observation Backend
Architecture & Design Document

---

1. Backend Architecture
1.1 High-Level System Overview
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND (EXISTING) │
│ (Emits events, consumes real-time updates) │
└─────────────────────────────────┬───────────────────────────────────────┘
│
┌─────────────▼─────────────┐
│ API Gateway │
│ (JWT + Token Validation)│
└─────────────┬─────────────┘
│
┌─────────────────────────┼─────────────────────────┐
│ │ │
▼ ▼ ▼
┌───────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ REST API │ │ WebSocket Hub │ │ Background │
│ Controllers │ │ (Real-time) │ │ Processors │
└───────┬───────┘ └────────┬────────┘ └────────┬────────┘
│ │ │
└────────────────────────┼─────────────────────────┘
│
┌────────────▼────────────┐
│ Service Layer │
├─────────────────────────┤
│ • AuthService │
│ • TaskService │
│ • AttemptService │
│ • EventService │
│ • MetricService │
│ • SkillInterpreter │
└────────────┬────────────┘
│
┌────────────▼────────────┐
│ Data Access Layer │
│ (MongoDB Repositories)│
└────────────┬────────────┘
│
┌────────────▼────────────┐
│ MongoDB │
│ (Event-Sourced Store) │
└─────────────────────────┘
1.2 Directory Structure
backend/
├── app/
│ ├── **init**.py
│ ├── [main.py](http://main.py/) # FastAPI app entry point
│ ├── [config.py](http://config.py/) # Environment configuration
│ │
│ ├── api/
│ │ ├── **init**.py
│ │ ├── [deps.py](http://deps.py/) # Dependency injection
│ │ ├── routes/
│ │ │ ├── [auth.py](http://auth.py/) # Authentication endpoints
│ │ │ ├── [tasks.py](http://tasks.py/) # Task retrieval endpoints
│ │ │ ├── [attempts.py](http://attempts.py/) # Attempt lifecycle endpoints
│ │ │ ├── [events.py](http://events.py/) # Event ingestion endpoints
│ │ │ ├── [results.py](http://results.py/) # Metrics & skills endpoints
│ │ │ └── [websocket.py](http://websocket.py/) # WebSocket connection handler
│ │ └── middleware/
│ │ ├── [auth.py](http://auth.py/) # JWT validation middleware
│ │ └── rate_limit.py # Rate limiting
│ │
│ ├── core/
│ │ ├── **init**.py
│ │ ├── [security.py](http://security.py/) # JWT, password hashing, tokens
│ │ └── [exceptions.py](http://exceptions.py/) # Custom exception classes
│ │
│ ├── services/
│ │ ├── **init**.py
│ │ ├── auth_service.py
│ │ ├── task_service.py
│ │ ├── attempt_service.py
│ │ ├── event_service.py
│ │ ├── metric_service.py # Post-hoc metric computation
│ │ ├── skill_interpreter.py # Rule-based skill inference
│ │ └── websocket_manager.py # WebSocket connection manager
│ │
│ ├── models/
│ │ ├── **init**.py
│ │ ├── [user.py](http://user.py/)
│ │ ├── [task.py](http://task.py/)
│ │ ├── [option.py](http://option.py/)
│ │ ├── [attempt.py](http://attempt.py/)
│ │ ├── [event.py](http://event.py/)
│ │ ├── [metric.py](http://metric.py/)
│ │ └── skill_profile.py
│ │
│ ├── schemas/
│ │ ├── **init**.py
│ │ ├── [auth.py](http://auth.py/) # Pydantic request/response schemas
│ │ ├── [task.py](http://task.py/)
│ │ ├── [attempt.py](http://attempt.py/)
│ │ ├── [event.py](http://event.py/)
│ │ ├── [metric.py](http://metric.py/)
│ │ └── [skill.py](http://skill.py/)
│ │
│ ├── repositories/
│ │ ├── **init**.py
│ │ ├── [base.py](http://base.py/) # Base repository pattern
│ │ ├── user_repo.py
│ │ ├── task_repo.py
│ │ ├── attempt_repo.py
│ │ ├── event_repo.py
│ │ ├── metric_repo.py
│ │ └── skill_repo.py
│ │
│ └── db/
│ ├── **init**.py
│ ├── [mongodb.py](http://mongodb.py/) # MongoDB connection manager
│ └── [indexes.py](http://indexes.py/) # Index definitions
│
├── tests/
│ ├── **init**.py
│ ├── [conftest.py](http://conftest.py/)
│ ├── test_auth.py
│ ├── test_events.py
│ ├── test_metrics.py
│ └── test_skills.py
│
├── requirements.txt
├── .env.example
└── [README.md](http://readme.md/)

---

1. MongoDB Schema Definitions
2.1 users Collection
{
"_id": ObjectId,
"email": String, // Unique, indexed
"password_hash": String,
"role": String, // "candidate" | "recruiter" | "admin"
"created_at": ISODate,
"updated_at": ISODate,
"is_active": Boolean
}
Indexes:
- { "email": 1 } — unique

---

2.2 tasks Collection
{
"_id": ObjectId,
"task_code": String,                // Unique identifier (e.g., "TASK_001")
"title": String,
"description": String,
"scenario": String,                 // The decision scenario presented
"category": String,                 // "prioritization" | "risk_assessment" | "resource_allocation"
"time_limit_seconds": Number,       // Optional soft limit (null = unlimited)
"option_ids": [ObjectId],           // References to options collection
"requires_reasoning": Boolean,      // Whether reasoning input is expected
"is_active": Boolean,
"created_at": ISODate,
"updated_at": ISODate
}
Indexes:

- { "task_code": 1 } — unique
- { "category": 1, "is_active": 1 }

---

2.3 options Collection
{
"_id": ObjectId,
"task_id": ObjectId,                // Foreign key to tasks
"option_code": String,              // e.g., "A", "B", "C"
"label": String,                    // Display text
"description": String,              // Full option description
"risk_tag": String,                 // "low" | "medium" | "high"
"metadata": {
"trade_off_type": String,         // "speed_vs_quality" | "cost_vs_benefit" | etc.
"domain": String                  // "financial" | "operational" | "strategic"
},
"display_order": Number
}
Indexes:

- { "task_id": 1, "option_code": 1 } — compound unique

---

2.4 task_attempts Collection
{
"_id": ObjectId,
"attempt_token": String,            // One-time token (UUID), unique
"user_id": ObjectId,                // Foreign key to users
"task_id": ObjectId,                // Foreign key to tasks
"status": String,                   // "pending" | "in_progress" | "completed" | "expired"
"started_at": ISODate,              // Set when first event received
"completed_at": ISODate,            // Set on task_completed event
"final_selection": {
"option_id": ObjectId,
"option_code": String
},
"reasoning_text": String,           // Final submitted reasoning (if any)
"is_locked": Boolean,               // True after completion (prevents re-attempts)
"created_at": ISODate,
"expires_at": ISODate               // Token expiration time
}
Indexes:

- { "attempt_token": 1 } — unique
- { "user_id": 1, "task_id": 1 } — compound (for checking re-attempts)
- { "status": 1, "expires_at": 1 } — for cleanup queries

---

2.5 behavior_events Collection (Append-Only, Source of Truth)
{
"_id": ObjectId,
"attempt_id": ObjectId,             // Foreign key to task_attempts
"event_type": String,               // See event types below
"timestamp_client": ISODate,        // Timestamp from frontend (for reference)
"timestamp_server": ISODate,        // Authoritative server timestamp
"sequence_number": Number,          // Auto-incrementing per attempt
"payload": {
// Event-specific data (see section 4)
},
"metadata": {
"client_session_id": String,
"user_agent": String
}
}
Event Types:

| Event Type | Description |
| --- | --- |
| task_started | User began viewing the task |
| option_viewed | User focused/hovered on an option |
| option_selected | User selected an option |
| option_changed | User changed their selection |
| reasoning_started | User began typing reasoning |
| reasoning_updated | Reasoning text changed (debounced) |
| reasoning_submitted | User submitted reasoning |
| task_completed | User finalized the task |
| task_abandoned | User left without completing |
| Indexes: |  |
- { "attempt_id": 1, "sequence_number": 1 } — compound unique
- { "attempt_id": 1, "event_type": 1 }
- { "timestamp_server": 1 } — for time-range queries

---

2.6 computed_metrics Collection
{
"_id": ObjectId,
"attempt_id": ObjectId,             // Foreign key to task_attempts (unique)
"computed_at": ISODate,
"version": String,                  // Metric computation version (e.g., "1.0.0")

"time_metrics": {
"total_time_ms": Number,
"active_interaction_time_ms": Number,
"hesitation_time_ms": Number,
"first_decision_speed_ms": Number
},

"decision_metrics": {
"decision_change_count": Number,
"options_viewed_count": Number,
"unique_options_viewed": Number,
"final_option_view_duration_ms": Number
},

"reasoning_metrics": {
"reasoning_provided": Boolean,
"word_count": Number,
"logical_keyword_count": Number,
"reasoning_depth_score": Number   // Computed: word_count × keyword_multiplier
},

"risk_metrics": {
"final_risk_tag": String,         // "low" | "medium" | "high"
"risk_exposure_pattern": [String] // Ordered list of risk tags viewed/selected
},

"raw_event_count": Number
}
Indexes:

- { "attempt_id": 1 } — unique

---

2.7 skill_profiles Collection
{
"_id": ObjectId,
"attempt_id": ObjectId,             // Foreign key to task_attempts (unique)
"user_id": ObjectId,                // Denormalized for easy querying
"task_id": ObjectId,                // Denormalized for easy querying
"computed_at": ISODate,
"interpreter_version": String,      // Rule engine version (e.g., "1.0.0")

"inferred_skills": [
{
"skill_code": String,           // e.g., "ANALYTICAL_THINKING"
"skill_label": String,          // e.g., "Analytical Thinker"
"confidence": String,           // "strong" | "moderate" | "weak"
"evidence": [String]            // Human-readable explanations
}
],

"behavioral_summary": {
"decision_style": String,         // "analytical" | "intuitive" | "exploratory" | "decisive"
"risk_profile": String,           // "risk_averse" | "risk_neutral" | "risk_seeking"
"reasoning_style": String         // "structured" | "brief" | "none"
},

"recruiter_notes": String           // Auto-generated summary for recruiters
}
Indexes:

- { "attempt_id": 1 } — unique
- { "user_id": 1 }
- { "inferred_skills.skill_code": 1 }

---

1. API Definitions
3.1 REST API Endpoints
Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/auth/register | Register new user | No |
| POST | /api/v1/auth/login | Login, receive JWT | No |
| POST | /api/v1/auth/refresh | Refresh JWT token | Yes |
| GET | /api/v1/auth/me | Get current user info | Yes |
Assessment Tokens
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/tokens/generate | Generate one-time assessment token | Yes (Recruiter) |
| GET | /api/v1/tokens/{token}/validate | Validate token (returns task info) | No |
Tasks
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/tasks | List available tasks | Yes (Admin) |
| GET | /api/v1/tasks/{task_id} | Get task details with options | Yes |
Attempts
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/attempts | Create attempt from token | Token Required |
| GET | /api/v1/attempts/{attempt_id} | Get attempt status | Yes |
| POST | /api/v1/attempts/{attempt_id}/complete | Mark attempt as completed | Yes |
Events
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/v1/events | Log a behavior event | Yes |
| POST | /api/v1/events/batch | Log multiple events (ordered) | Yes |
| GET | /api/v1/attempts/{attempt_id}/events | Get all events for attempt | Yes (Owner/Recruiter) |
Results
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | /api/v1/attempts/{attempt_id}/metrics | Get computed metrics | Yes (Owner/Recruiter) |
| GET | /api/v1/attempts/{attempt_id}/skills | Get skill profile | Yes (Owner/Recruiter) |
| GET | /api/v1/users/{user_id}/profile | Aggregate skill profile | Yes (Recruiter) |

---

## 3.2 REST API Request/Response Schemas
POST /api/v1/events
Request:
{
attempt_id: string (ObjectId),
event_type: option_selected,
timestamp_client: 2025-01-28T10:30:00.000Z,
payload: {
option_id: string (ObjectId),
option_code: B
},
metadata: {
client_session_id: uuid
}
}
Response (201):
{
event_id: string (ObjectId),
sequence_number: 5,
timestamp_server: 2025-01-28T10:30:00.123Z,
acknowledged: true
}
GET /api/v1/attempts/{attempt_id}/skills
Response (200):
{
attempt_id: string,
computed_at: 2025-01-28T10:35:00.000Z,
inferred_skills: [
{
skill_code: ANALYTICAL_THINKING,
skill_label: Analytical Thinker,
confidence: strong,
evidence: [
Spent 45 seconds before first decision (above average),
Viewed all 4 options before selecting,
Provided structured reasoning with 3 logical connectors
]
},
{
skill_code: RISK_AWARENESS,
skill_label: Risk-Aware Decision Maker,
confidence: moderate,
evidence: [
Final selection was low-risk option,
Viewed high-risk options but did not select
]
}
],
behavioral_summary: {
decision_style: analytical,
risk_profile: risk_averse,
reasoning_style: structured
},
recruiter_notes: Candidate demonstrates strong analytical thinking with methodical option evaluation. Shows risk awareness by exploring but avoiding high-risk choices. Reasoning is well-structured with clear logical flow.
}

## 3.3 WebSocket API
Connection
ws://api.example.com/ws/attempts/{attempt_id}?token={jwt_token}
Server → Client Messages
Event Acknowledged:
{
type: event_ack,
data: {
event_id: string,
sequence_number: 5,
timestamp_server: 2025-01-28T10:30:00.123Z
}
}
Attempt Status Update:
{
type: attempt_status,
data: {
status: completed,
completed_at: 2025-01-28T10:35:00.000Z
}
}
Metrics Ready (after completion):
{
type: metrics_ready,
data: {
attempt_id: string,
metrics_url: /api/v1/attempts/{id}/metrics
}
}
Client → Server Messages
Heartbeat:
{
type: ping
}

1. Event Validation Rules
4.1 Common Validation (All Events)
| Field | Rule |
|-------|------|
| attempt_id | Must exist, must be in_progress status, must not be locked |
| event_type | Must be in allowed enum list |
| timestamp_client | Must be valid ISO8601, must not be in future (>5s tolerance) |
| payload | Must conform to event-specific schema |
4.2 Event-Specific Validation
| Event Type | Required Payload | Validation Rules |
|------------|------------------|------------------|
| task_started | {} | Must be first event for attempt; sets started_at |
| option_viewed | { option_id, option_code, duration_ms } | option_id must belong to task; duration_ms ≥ 0 |
| option_selected | { option_id, option_code } | option_id must belong to task |
| option_changed | { from_option_id, to_option_id, from_code, to_code } | Both options must belong to task; must differ |
| reasoning_started | {} | Task must have requires_reasoning: true |
| reasoning_updated | { text_length, word_count } | word_count ≥ 0 |
| reasoning_submitted | { text, word_count } | text length ≤ 5000 chars |
| task_completed | { final_option_id, final_option_code } | Option must be selected; locks the attempt |
4.3 Sequence Rules
ALLOWED SEQUENCES:
- task_started must come first
- option_viewed can occur any number of times
- option_selected must precede option_changed
- option_changed requires prior option_selected
- reasoning_* events must occur after task_started
- task_completed must come last and locks the attempt
REJECTED:
- Any event after task_completed
- task_started appearing twice
- task_completed without option_selected

---

1. Metric Computation Formulas

> All metrics are computed post-hoc from behavior_events after task_completed.
5.1 Time Metrics
> 

# Total Time

total_time_ms = task_completed.timestamp_server - task_started.timestamp_server

# Active Interaction Time

# Sum of all option_viewed durations + reasoning time

active_interaction_time_ms = sum(
event.payload.duration_ms
for event in events
if event.event_type == "option_viewed"
) + reasoning_time_ms

# Where reasoning_time_ms:

reasoning_time_ms = (
reasoning_submitted.timestamp_server - reasoning_started.timestamp_server
if reasoning_submitted exists
else 0
)

# Hesitation Time

hesitation_time_ms = total_time_ms - active_interaction_time_ms

# First Decision Speed

first_decision_speed_ms = (
first_option_selected.timestamp_server - task_started.timestamp_server
)
5.2 Decision Metrics

# Decision Change Count

decision_change_count = count(events where event_type == "option_changed")

# Options Viewed Count (total views, including repeats)

options_viewed_count = count(events where event_type == "option_viewed")

# Unique Options Viewed

unique_options_viewed = count(distinct option_id in option_viewed events)
5.3 Reasoning Metrics

# Reasoning Depth Score

LOGICAL_KEYWORDS = [
"because", "therefore", "however", "although", "considering",
"firstly", "secondly", "finally", "in contrast", "as a result",
"given that", "on the other hand", "weighing", "analyzing"
]
word_count = len(reasoning_text.split())
logical_keyword_count = count(keyword in reasoning_text.lower() for keyword in LOGICAL_KEYWORDS)

# Depth score formula

keyword_multiplier = 1 + (logical_keyword_count * 0.1)  # Max bonus: 1.5x
reasoning_depth_score = word_count * keyword_multiplier
5.4 Risk Metrics

# Risk Exposure Pattern

risk_exposure_pattern = [
get_option_risk_tag(event.payload.option_id)
for event in events
if event.event_type in ["option_viewed", "option_selected", "option_changed"]
]

# Final Risk Tag

## final_risk_tag = get_option_risk_tag(task_completed.payload.final_option_id)

1. Skill Interpretation Logic
6.1 Interpretation Framework
The skill interpreter uses deterministic rule chains. Each rule:
2. Takes computed metrics as input
3. Evaluates boolean conditions
4. Produces skill inferences with confidence levels
6.2 Thresholds Configuration
THRESHOLDS = {
    
    # Time thresholds (in milliseconds)
    
    "fast_decision": 10_000,        # < 10s = fast
    "slow_decision": 30_000,        # > 30s = slow
    "very_slow_decision": 60_000,   # > 60s = very slow
    
    # Hesitation
    
    "low_hesitation_ratio": 0.2,    # < 20% hesitation
    "high_hesitation_ratio": 0.5,   # > 50% hesitation
    
    # Decision changes
    
    "low_changes": 1,
    "high_changes": 3,
    
    # Reasoning
    
    "brief_reasoning": 20,          # < 20 words
    "detailed_reasoning": 50,       # > 50 words
    "structured_reasoning_score": 60,  # depth score threshold
    
    # Coverage
    
    "full_coverage_ratio": 0.8      # Viewed 80%+ of options
    }
    6.3 Skill Inference Rules
    Decision Style Rules
    def infer_decision_style(metrics):
    rules = []
    
    # ANALYTICAL THINKER
    
    if (metrics.first_decision_speed_ms > THRESHOLDS["slow_decision"] and
    metrics.unique_options_viewed >= total_options * THRESHOLDS["full_coverage_ratio"] and
    metrics.reasoning_depth_score >= THRESHOLDS["structured_reasoning_score"]):
    rules.append({
    "skill_code": "ANALYTICAL_THINKING",
    "skill_label": "Analytical Thinker",
    "confidence": "strong",
    "evidence": [
    f"Took {metrics.first_decision_speed_ms/1000:.1f}s before first decision",
    f"Viewed {metrics.unique_options_viewed}/{total_options} options",
    f"Reasoning depth score: {metrics.reasoning_depth_score:.1f}"
    ]
    })
    
    # INTUITIVE/DECISIVE
    
    elif (metrics.first_decision_speed_ms < THRESHOLDS["fast_decision"] and
    metrics.decision_change_count <= THRESHOLDS["low_changes"]):
    rules.append({
    "skill_code": "DECISIVE_THINKING",
    "skill_label": "Decisive Thinker",
    "confidence": "strong" if metrics.decision_change_count == 0 else "moderate",
    "evidence": [
    f"Made first decision in {metrics.first_decision_speed_ms/1000:.1f}s",
    f"Changed decision {metrics.decision_change_count} time(s)"
    ]
    })
    
    # EXPLORATORY
    
    elif (metrics.decision_change_count >= THRESHOLDS["high_changes"] and
    metrics.options_viewed_count > total_options * 2):
    rules.append({
    "skill_code": "EXPLORATORY_THINKING",
    "skill_label": "Exploratory Thinker",
    "confidence": "strong",
    "evidence": [
    f"Changed decision {metrics.decision_change_count} times",
    f"Viewed options {metrics.options_viewed_count} times (high revisit rate)"
    ]
    })
    
    return rules
    Risk Profile Rules
    def infer_risk_profile(metrics):
    final_risk = metrics.final_risk_tag
    pattern = metrics.risk_exposure_pattern
    
    # Count risk tag occurrences in pattern
    
    risk_counts = Counter(pattern)
    total_exposures = len(pattern)
    
    # RISK AVERSE
    
    if final_risk == "low":
    if risk_counts.get("high", 0) > 0:
    # Viewed high risk but chose low
    return {
    "skill_code": "RISK_AWARENESS",
    "skill_label": "Risk-Aware Decision Maker",
    "confidence": "strong",
    "evidence": [
    "Selected low-risk option",
    "Evaluated high-risk alternatives before deciding"
    ]
    }
    else:
    return {
    "skill_code": "RISK_AVERSE",
    "skill_label": "Risk-Averse",
    "confidence": "moderate",
    "evidence": ["Consistently focused on low-risk options"]
    }
    
    # RISK SEEKING
    
    elif final_risk == "high":
    if risk_counts.get("low", 0) > 0:
    return {
    "skill_code": "CALCULATED_RISK_TAKER",
    "skill_label": "Calculated Risk-Taker",
    "confidence": "moderate",
    "evidence": [
    "Selected high-risk option",
    "Evaluated safer alternatives before deciding"
    ]
    }
    else:
    return {
    "skill_code": "RISK_SEEKING",
    "skill_label": "Risk-Seeking",
    "confidence": "strong",
    "evidence": ["Focused primarily on high-risk options"]
    }
    
    # RISK NEUTRAL
    
    return {
    "skill_code": "RISK_NEUTRAL",
    "skill_label": "Balanced Risk Approach",
    "confidence": "moderate",
    "evidence": ["Selected medium-risk option"]
    }
    Reasoning Style Rules
    def infer_reasoning_style(metrics):
    if not metrics.reasoning_provided:
    return {
    "skill_code": "NO_REASONING",
    "reasoning_style": "none",
    "evidence": ["No reasoning provided"]
    }
    
    if metrics.reasoning_depth_score >= THRESHOLDS["structured_reasoning_score"]:
    return {
    "skill_code": "STRUCTURED_REASONING",
    "skill_label": "Structured Communicator",
    "confidence": "strong",
    "reasoning_style": "structured",
    "evidence": [
    f"Word count: {metrics.word_count}",
    f"Used {metrics.logical_keyword_count} logical connectors"
    ]
    }
    
    elif metrics.word_count >= THRESHOLDS["detailed_reasoning"]:
    return {
    "skill_code": "DETAILED_REASONING",
    "skill_label": "Detailed Communicator",
    "confidence": "moderate",
    "reasoning_style": "detailed",
    "evidence": [f"Provided {metrics.word_count} words of explanation"]
    }
    
    else:
    return {
    "skill_code": "CONCISE_REASONING",
    "skill_label": "Concise Communicator",
    "confidence": "moderate",
    "reasoning_style": "brief",
    "evidence": [f"Provided brief explanation ({metrics.word_count} words)"]
    }
    6.4 Recruiter Notes Generation
    def generate_recruiter_notes(skills, summary):
    templates = {
    "analytical": "demonstrates strong analytical thinking with methodical option evaluation",
    "decisive": "shows confident decision-making with quick, committed choices",
    "exploratory": "exhibits exploratory thinking, thoroughly testing multiple approaches",
    
    ```
     "risk_averse": "prefers safe, low-risk options",
     "risk_neutral": "balances risk and reward effectively",
     "risk_seeking": "shows willingness to take calculated risks",
    
     "structured": "communicates with clear, logical reasoning",
     "detailed": "provides thorough explanations",
     "brief": "communicates concisely",
     "none": "did not provide written reasoning"
    
    ```
    
    }
    
    notes = f"Candidate {templates.get(summary.decision_style, 'completed the task')}. "
    notes += f"Shows {templates.get(summary.risk_profile, 'balanced')} risk profile. "
    notes += f"Reasoning style: {templates.get(summary.reasoning_style, 'not assessed')}."
    
    return notes
    

---

1. Execution TODO List
Phase 1: Project Setup & Core Infrastructure
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 1.1 | Initialize FastAPI project structure | High | 30 min |
| 1.2 | Set up configuration management (pydantic-settings) | High | 20 min |
| 1.3 | Configure MongoDB connection with motor (async driver) | High | 30 min |
| 1.4 | Create database index definitions | High | 20 min |
| 1.5 | Set up custom exception handlers | Medium | 15 min |
| 1.6 | Create base repository pattern | Medium | 30 min |
Phase 2: Authentication & Security
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 2.1 | Implement JWT token generation & validation | High | 45 min |
| 2.2 | Create password hashing utilities | High | 15 min |
| 2.3 | Build user registration & login endpoints | High | 45 min |
| 2.4 | Implement one-time assessment token generator | High | 30 min |
| 2.5 | Create auth middleware & dependency injection | High | 30 min |
| 2.6 | Add role-based access control (RBAC) | Medium | 30 min |
Phase 3: Core Data Models & Repositories
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 3.1 | Create Pydantic models for all collections | High | 1 hr |
| 3.2 | Create request/response schemas | High | 45 min |
| 3.3 | Implement UserRepository | High | 30 min |
| 3.4 | Implement TaskRepository | High | 30 min |
| 3.5 | Implement AttemptRepository | High | 45 min |
| 3.6 | Implement EventRepository (append-only pattern) | High | 45 min |
| 3.7 | Implement MetricRepository | Medium | 30 min |
| 3.8 | Implement SkillProfileRepository | Medium | 30 min |
Phase 4: Event Ingestion System
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 4.1 | Create EventService with validation logic | High | 1 hr |
| 4.2 | Implement event-specific payload validators | High | 45 min |
| 4.3 | Implement sequence validation rules | High | 30 min |
| 4.4 | Build POST /events endpoint | High | 30 min |
| 4.5 | Build POST /events/batch endpoint | Medium | 30 min |
| 4.6 | Add server-side timestamping & sequence numbering | High | 20 min |
Phase 5: Task & Attempt Management
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 5.1 | Implement TaskService | High | 30 min |
| 5.2 | Build task retrieval endpoints | High | 30 min |
| 5.3 | Implement AttemptService | High | 45 min |
| 5.4 | Build attempt creation from token | High | 30 min |
| 5.5 | Implement attempt locking on completion | High | 30 min |
| 5.6 | Add re-attempt prevention logic | High | 20 min |
Phase 6: WebSocket Real-time System
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 6.1 | Create WebSocketManager for connection handling | High | 45 min |
| 6.2 | Implement JWT auth for WebSocket connections | High | 30 min |
| 6.3 | Build event broadcast on successful logging | High | 30 min |
| 6.4 | Add heartbeat/ping-pong handling | Medium | 20 min |
| 6.5 | Implement connection cleanup on disconnect | Medium | 20 min |
Phase 7: Metric Computation Engine
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 7.1 | Implement MetricService framework | High | 30 min |
| 7.2 | Build time metric calculators | High | 45 min |
| 7.3 | Build decision metric calculators | High | 30 min |
| 7.4 | Build reasoning metric calculators | High | 45 min |
| 7.5 | Build risk metric calculators | High | 30 min |
| 7.6 | Add metric versioning support | Medium | 20 min |
| 7.7 | Trigger metric computation on task_completed | High | 30 min |
Phase 8: Skill Interpretation Engine
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 8.1 | Create SkillInterpreter framework | High | 30 min |
| 8.2 | Implement decision style rules | High | 45 min |
| 8.3 | Implement risk profile rules | High | 45 min |
| 8.4 | Implement reasoning style rules | High | 30 min |
| 8.5 | Build recruiter notes generator | Medium | 30 min |
| 8.6 | Add interpreter versioning | Medium | 15 min |
| 8.7 | Build GET /attempts/{id}/skills endpoint | High | 30 min |
Phase 9: Results & Reporting APIs
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 9.1 | Build GET /attempts/{id}/metrics endpoint | High | 30 min |
| 9.2 | Build GET /attempts/{id}/events endpoint | Medium | 30 min |
| 9.3 | Build user aggregate profile endpoint | Medium | 45 min |
| 9.4 | Add response caching for computed results | Low | 30 min |
Phase 10: Testing & Quality
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 10.1 | Set up pytest with async support | High | 30 min |
| 10.2 | Write unit tests for metric calculators | High | 1 hr |
| 10.3 | Write unit tests for skill interpreter | High | 1 hr |
| 10.4 | Write integration tests for event flow | High | 1 hr |
| 10.5 | Write API endpoint tests | Medium | 1 hr |
| 10.6 | Add test fixtures and factories | Medium | 30 min |
Phase 11: Deployment Preparation
| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 11.1 | Create requirements.txt with pinned versions | High | 15 min |
| 11.2 | Create .env.example with all config vars | High | 15 min |
| 11.3 | Write Render deployment configuration | High | 30 min |
| 11.4 | Add health check endpoint | High | 15 min |
| 11.5 | Configure CORS for frontend | High | 15 min |
| 11.6 | Write README with setup instructions | Medium | 30 min |

---

Summary

| Component | Status |
| --- | --- |
| Architecture | Defined |
| MongoDB Schemas (7 collections) | Defined |
| REST API (15+ endpoints) | Defined |
| WebSocket API | Defined |
| Event Validation Rules | Defined |
| Metric Formulas (4 categories) | Defined |
| Skill Interpretation Rules | Defined |
| TODO List (50+ tasks) | Defined |

---

Awaiting your approval to begin implementation.
Please review this architecture and let me know:

1. Any modifications needed
2. Priority adjustments for the TODO list
3. Approval to proceed with Phase 1

[](https://www.notion.so/2f8f669fe5f4805685ead5b2a4a02976?pvs=21)
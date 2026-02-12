# HireMate Backend

Behavior-based skill observation system for candidate assessment. This backend powers the HireMate assessment platform, which observes **HOW** candidates solve micro decision-making tasks to generate explainable skill profiles.

## 🎯 Key Features

- **Behavioral Event Logging**: Immutable, append-only event stream capturing all user interactions
- **Real-time WebSockets**: Live event broadcasting for active assessments
- **Post-hoc Metrics**: Behavioral metrics computed AFTER task completion
- **Deterministic Skills**: Rule-based skill interpretation (no ML black boxes)
- **One-time Tokens**: Secure, cryptographically secure assessment access

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB (async with Motor)
- **Authentication**: JWT + One-time assessment tokens
- **Real-time**: WebSockets
- **Validation**: Pydantic v2
- **Deployment**: Render.com

## 📦 Quick Start

### 1. Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- pip

### 2. Installation

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# Required: JWT_SECRET, MONGODB_URL
```

### 4. Seed Database

```bash
python scripts/seed_tasks.py
```

This creates:
- Admin user (`admin@hiremate.com` / `admin123456`)
- 10 sample assessment tasks

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Access API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Run and try it (checklist)

1. **MongoDB** – Running locally (`mongodb://localhost:27017`) or set `MONGODB_URL` in `.env`.
2. **`.env`** – Present in `backend/` with at least `JWT_SECRET` (e.g. copy from `.env.example`).
3. **Dependencies** – From `backend/`: `pip install -r requirements.txt` (includes `pypdf` for resume parse).
4. **Seed** – `python scripts/seed_tasks.py` (creates admin user + 10 tasks).
5. **Start server** – `uvicorn app.main:app --reload --port 8000`.
6. **Optional** – In `.env` set `DEV_MODE=true` to call recruiter endpoints (e.g. resume parse, attempts, dashboard) without a JWT; uses first active user (seeded admin).

Then open http://localhost:8000/docs to try endpoints. No further code changes are required to run.

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_metrics.py -v
```

## 🔄 Project Flow (Resume → Metrics)

The project depends on this pipeline:

1. **Upload resume** → Recruiter uploads a document (PDF or .txt).
2. **System analyses it** → `POST /api/v1/resume/parse` extracts name, email, phone, position and suggests task IDs from the parsed position so questions relate to the resume.
3. **Create attempt** → Recruiter (or frontend) calls `POST /api/v1/attempts` with the parsed `candidate_info` and `task_ids` (use `suggested_task_ids` from parse response, or pick manually).
4. **Candidate does assessment** → Candidate opens the assessment link (token), starts, gets tasks by index, logs behavior events (option viewed/selected, reasoning, etc.), then completes.
5. **Analyse behavior** → Backend logs all events to `behavior_events`; after completion it computes metrics (time, hesitation, decision changes, reasoning depth, risk) and generates a rule-based skill profile.
6. **Show the matrices** → Recruiter uses `GET /api/v1/metrics/attempt/{id}` and `GET /api/v1/skills/attempt/{id}` (or `/generate` first) to view metrics and skill profile.

**Before resume upload:** The backend already did steps 3–6. The recruiter had to **manually** enter candidate name, email, position (and pick task_ids) when creating an attempt. There was no “upload resume → analyse” step. Adding `POST /api/v1/resume/parse` (and optional task suggestion from position) makes the entry point “upload resume → system analyses it → create attempt with that info and related questions → rest of pipeline unchanged.”

## 📡 API Overview

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register recruiter |
| `/api/v1/auth/login` | POST | Login, get JWT |
| `/api/v1/resume/parse` | POST | Upload resume, parse candidate info, get suggested task IDs |
| `/api/v1/resume/files/{file_id}` | GET | Download stored resume file |
| `/api/v1/tasks` | GET/POST | Task CRUD |
| `/api/v1/attempts` | GET/POST | Assessment attempts |
| `/api/v1/assessment/{token}` | GET | Validate assessment token |
| `/api/v1/events` | POST | Log behavior events |
| `/api/v1/metrics/attempt/{id}` | GET/POST | Get/compute metrics |
| `/api/v1/skills/attempt/{id}` | GET/POST | Get/generate skills |
| `/api/v1/dashboard/stats` | GET | Dashboard statistics |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/assessment/{token}` | Candidate real-time event logging |
| `/ws/live/{attempt_id}` | Recruiter live monitoring |

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   ├── v1/        # REST API v1
│   │   └── websocket/ # WebSocket handlers
│   ├── core/          # Security, exceptions
│   ├── db/            # MongoDB connection
│   ├── schemas/       # Pydantic models
│   ├── services/      # Business logic
│   └── utils/         # Utilities
├── scripts/           # Database scripts
├── tests/             # Test suite
├── .env               # Environment config
├── requirements.txt   # Dependencies
└── render.yaml        # Render deployment
```

## 🔐 Authentication Flow

### Recruiters (JWT)
1. Register via `/auth/register`
2. Login via `/auth/login` → receive access + refresh tokens
3. Use `Authorization: Bearer <token>` header

### Candidates (One-time Token)
1. Recruiter creates attempt → generates unique token
2. Candidate accesses via `/assessment/{token}`
3. Token transitions: `pending` → `in_progress` → `completed`
4. Token cannot be reused after completion

## 📊 Behavioral Metrics

Computed from logged events AFTER task completion:

### Time Metrics
- Total time, active time, hesitation time
- Decision speed per task

### Decision Metrics
- Option changes count
- Decision consistency score

### Reasoning Metrics
- Word count, logical keywords
- Reasoning depth score

### Risk Behavior
- Risk choices distribution (low/medium/high)
- Risk preference pattern

## 🧠 Skill Interpretation

All interpretations are **deterministic** and **rule-based**:

| Dimension | Categories |
|-----------|------------|
| Thinking Style | Analytical, Intuitive, Exploratory, Methodical |
| Decision Pattern | Fast/Moderate/Deliberate, Steady/Variable/Improving |
| Risk Orientation | Risk-Averse, Balanced, Risk-Tolerant |
| Communication | Brief/Moderate/Detailed, Informal/Semi-structured/Structured |

## 🚀 Deployment (Render)

1. Connect GitHub repo to Render
2. Set environment variables:
   - `MONGODB_URL`: MongoDB Atlas connection string
   - `JWT_SECRET`: Generated automatically
   - `CORS_ORIGINS`: Frontend URL(s)
3. Deploy!

See `render.yaml` for full configuration.

## 📝 Questions to Resolve

From the implementation plan, these decisions may need user input:

1. **Risk Level Tags**: Manually assigned during task creation (currently implemented)
2. **Reasoning Keywords**: English-only (can extend to multilingual)
3. **Token Expiration**: Default 7 days (configurable via env)

## 📄 License

MIT License - See LICENSE file

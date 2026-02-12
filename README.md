# 🦅 HireMate - The Flight Recorder for Hiring
> **Stop Guessing. Start Observing.**

HireMate is the world’s first **Behavioral Observation Engine** for technical hiring. Instead of just checking if code is *correct*, we analyze **HOW** candidates solve problems.

**It’s Moneyball for Hiring.**

---

## 🚀 Key Features

1.  **Behavioral Flight Recorder**: Captures keystrokes, mouse movements, and decisions to reconstruct thought processes.
2.  **Hybrid ML Architecture**:
    *   **Anomaly Detection**: Pre-trained **Isolation Forest** model detects "unnatural" patterns (copy-pasting, robotic speed).
    *   **LLM Insights**: **Ollama (Llama 3.2)** generates qualitative "Behavioral Fingerprints".
3.  **Live Stream**: Recruiters watch candidates solve problems in real-time.
4.  **Bulk Processing**: **Redis + Celery** used for parallel resume parsing.

---

## ⚙️ Setup Guide (Fast Track)

**Configuration (.env):**
**Configuration (.env):**
Rename `.env.example` to `.env` and fill in the API keys (provided in the submission).
) and included the **trained ML models** and **synthetic dataset** for immediate testing.

### Prerequisites
*   **Node.js** (v18+)
*   **Python** (v3.10+)
*   **MongoDB** (Local port 27017)
*   **Redis** (Required for bulk uploads)
*   **Ollama** (`ollama pull llama3.2`)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd ..  # Return to root
npm install
```

### 3. Running the System

**1. Start Backend (API)**
```bash
# In backend terminal
uvicorn app.main:app --reload
```

**2. Start Frontend**
```bash
# In root terminal
npm run dev
```

**3. Start Celery Worker (For Bulk Uploads)**
*(Must be run in WSL/Linux environment on Windows)*
```bash
cd backend
celery -A app.celery_app worker --loglevel=info -P gevent --concurrency=10 --events
```

---

## 🧪 Testing the "Wow" Features

1.  **Live Assessment**: Login (`admin`/`admin`), go to "Live Dashboard," and open an assessment in Incognito.
2.  **Bulk Upload**: Upload resumes to see parallel processing in action (via Celery).
3.  **ML Insights**: The system uses the pre-loaded **Isolation Forest** model to score candidates instantly.

---
*Built for the Hackathon 2026.**:
    ```bash
    npm run dev
    ```
    The application will launch at `http://localhost:5175`.

---

### 🛠️ Key Features

- **Live Assessment**: Real-time behavioral tracking (Hesitation, Focus, Speed).
- **AI Analysis**: Automated grading and behavioral profiling using Groq AI.
- **Recruiter Dashboard**: Live monitoring of active candidates.
- **Resume Parsing**: AI-based resume extraction.

### 🐛 Troubleshooting

- **Backend fails to start?** Check if Port 8000 is occupied.
- **"Inconclusive" verdict?** Ensure the backend is connected to the internet to reach Groq API.
- **Database errors?** Verify `MONGODB_URL` in `backend/.env`.

---

## 📅 Changelog

### 📅 Latest Updates (Feb 8, 2026 - Afternoon)

**1. Critical Database Fixes**
- **Collection Mismatch Resolved**: Fixed seed script using `db.attempts` while API expected `db.task_attempts`.
- **Events Query Fix**: Resolved ObjectId/string type mismatch in `compute_live_metrics()` preventing behavioral data from loading.
- **Demo Data Verified**: All 3 demo candidates (Sarah Chen, Mike Johnson, Test Candidate) now display correctly with full behavioral profiles.

**2. Email Integration**
- **Send to Email Button**: Added email functionality to the Upload Resume page.
- **Resend API Integration**: Candidates receive polished HTML emails with assessment links.
- **Error Handling**: Improved email service with better status code handling (accepts any 2xx).

**3. Frontend Improvements**
- **Live Assessment Fix**: Fixed empty state logic to show completed assessments when no active ones exist.
- **All Candidates Page**: Corrected API endpoint (`/skills/candidates`) and now returns all completed candidates.

**4. System Audit**
- **Audit Report**: Generated comprehensive system audit documenting all fixes and current data state.
- **Events Verified**: 1,287 behavior events confirmed in database across 3 demo candidates.

---

### 📅 Previous Updates (Feb 8, 2026 - Morning)

**1. The 8-Layer Intelligence System (New Architecture)**

**2. Anti-Cheat & Integrity Upgrades**
- **Copy/Paste Detection:** Monitors clipboard events for "impossible" typing speeds (>50 chars/0.1s).
- **Focus Loss Tracking:** Logs every time a candidate leaves the assessment tab.
- **Idle Detection:** Flags suspicious 30s+ pauses that suggest coaching or external help.

**3. Documentation Overhaul**
- **System Guide:** Completely rewrote `system_guide.md` as the "Ground Truth" documentation, featuring 400+ lines of beginner-friendly explanations, math formulas, and architectural diagrams.

### 📅 Previous Updates (Feb 2026)

**1. Progressive Behavioral Analysis**
- **Confident Data:** Behavioral patterns now require a minimum of 2 questions before displaying definitive labels.
- **Pattern Tracking:** Backend tracks pattern consistency (e.g., "Direct (67%)") across all completed questions.
- **Confidence Levels:** Visual confidence bar increases (25% → 95%) as more data is analyzed.
- **Tentative Indicators:** Preliminary data is marked with asterisks (*) to manage recruiter expectations.

**2. Evidence-Based Tooltips**
- **Dynamic Explanations:** Hovering over metrics now reveals the *why* behind the numbers.
- **Transparent Logic:** Tooltips display raw data values and the thresholds used (e.g., "Selection Speed: High because avg time < 15s").
- **Smart Tooltips:** Explanations adapt based on the specific candidate's performance.

**3. Production Readiness**
- **Demo Mode Removed:** All mock data deleted; system now relies purely on live API data.
- **Security:** Strict JWT authentication enforced across all endpoints.
- **Robustness:** Added comprehensive loading, error, and empty states for all dashboard components.

### 2026-02-05 (Latest Updates)

We have implemented significant improvements to behavioral analytics, data security, and candidate profiling:

1.  **Behavioral Analytics Transparency**
    *   **Formula-Based Explanations**: Updated `live_metrics_service.py` to generate evidence-based explanations for metrics like "Analysis Confidence", "Approach Pattern", and "Under Pressure".
    *   **UI Transparency**: Updated `LiveAssessment.jsx` to display these calculations directly in the UI, showing the exact formula and data points (e.g., "Confidence: 75% from 3 questions") instead of opaque labels.
    *   **Idle Time Logic**: Refined idle time calculations to be more accurate and derived directly from observed pause durations.

2.  **Recruiter Data Isolation**
    *   **Secure Access**: Implemented backend filtering in `live_metrics_service.py` and `live_assessment.py`. Recruiters can now ONLY view active and completed assessments that *they* created.
    *   **API Updates**: Updated endpoints `/active` and `/completed` to enforce `recruiter_id` checks.

3.  **Enhanced Candidate Profiling**
    *   **Smart Position Extraction**: Upgraded the LLM prompt in `resume_parser.py` to specifically extract professional job titles (e.g., "Senior Frontend Engineer") rather than generic fallbacks.
    *   **Accurate Display**: Updated the `Attempt` schema and `LiveAssessment.jsx` to display the specific extracted role, replacing the generic "General Application" or "Not Specified" placeholders.

4.  **UI/UX Improvements**
    *   **Fixed Display Bugs**: Resolved an issue where candidate positions would show as "Not Specified" even when data was available.
### 2026-02-05 00:31 AM (Advanced System Mapping & Privacy Audit)

We have completed the most comprehensive technical update to date, focusing on system transparency and internal data privacy:

1.  **Exhaustive System Documentation**
    *   **Architecture Manual**: Created `system_architecture_and_guide.md`, a high-fidelity guide explaining the 6-layer intelligence pipeline (Speed, Firmness, Radar, Confidence, Skills, and Stress).
    *   **Metric Formulas**: Documented every deterministic formula used by the backend, ensuring Sarah the Recruiter (and our technical team) knows exactly how every pixel on the dashboard is calculated.

2.  **Full-Scale Data Privacy Audit**
    *   **Comprehensive Isolation**: Extended recruiter-specific data isolation to the `AllCandidates` list, dashboard statistics, and activity feeds.
    *   **Secure Backend Querying**: Updated `skill_service.py` and `dashboard.py` to strictly enforce `created_by` filtering based on the authenticated JWT user.

3.  **UI Professionalism & Fallbacks**
    *   **Standardized Roles**: Replaced the "Not Specified" fallback with "General Candidate" in `UploadResume.jsx` to maintain a premium recruiter experience.
    *   **Evidence Tooltips**: Fully integrated the dynamic backend explanations into the frontend `TermTooltip` components across the Live Assessment view.

### 2026-02-06 12:08 AM (Major Intelligence Upgrade)

Today's release marks a significant leap in system intelligence, transparency, and user experience.

1.  **Kiwi Assistant (Formerly Report Assistant)**
    *   **Identity Rebrand**: Renamed generic chatbot to "Kiwi 🥝" with a polished, professional UI (larger window, readable typography, gradient aesthetic).
    *   **Intelligent Prompting**: Backend now dynamically detects complex queries (e.g., "How is firmness calculated?") and injects a 50-line architecture guide into the context window.
    *   **Formula Transparency**: Responses now strictly adhere to the deterministic formulas found in `live_metrics_service.py`.

2.  **Population Intelligence UI Overhaul**
    *   **Visual Redesign**: Replaced standard charts with "Population Intelligence" circular progress indicators and glassmorphism cards.
    *   **Methodology Transparency**: Added a "How It Works" methodology panel detailing the 6-layer intelligence pipeline.
    *   **Drill-Down Capabilities**: Clicking on metrics now opens detailed bottom sheets with historical context and exact formulas.

3.  **System Knowledge Base**
    *   **New Artifact**: Created `backend/app/system_guide.md`, a single source of truth documenting the 6-layer intelligence pipeline (Speed, Firmness, Radar, Confidence, Skills, Stress).
    *   **Anomaly Logic**: Fully documented deduction rules (-15% for uniform timing, -25% for perfect patterns) for recruiter transparency.

4.  **Backend & Parsing Enhancements**
    *   **Resume Parser**: Upgraded AI prompt to extract specific professional job titles (e.g., "Senior React Developer") instead of generic "Not Specified" placeholders.
    *   **Metric Transparency**: `live_metrics_service.py` now generates evidence-based explanations for every score, viewable in the new UI tooltips.
    *   **Security**: Extended strict `recruiter_id` data isolation to all reporting endpoints.

5.  **UI/UX Refinements**
    *   **Visual Access**: Added a floating "Ask Kiwi" action button for immediate access to analysis.
    *   **Accessibility**: Significantly increased font sizes and contrast in the chat interface.
    *   **Cleanliness**: Removed dev-mode text artifacts from the UI production build.
=======
# HireMate
AI- powered recruitment assessment platform 
>>>>>>> 6ba3f5be0b552f81e0f008d3cf4ffce5e8973a25

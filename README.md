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
Rename `.env.example` to `.env`. Update the Keys.

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

# HireMate
AI- powered recruitment assessment platform 
>>>>>>> 6ba3f5be0b552f81e0f008d3cf4ffce5e8973a25

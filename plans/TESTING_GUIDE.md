# HireMate – Step-by-Step Testing Guide

Both **backend** and **frontend** are running. Use this guide to test the full flow.

---

## What’s Running

| Service   | URL                      | Status   |
|----------|---------------------------|----------|
| **Backend**  | http://localhost:8000      | Running  |
| **Frontend** | http://localhost:5174       | Running (5173 was in use) |
| **API Docs** | http://localhost:8000/docs  | Swagger UI |

**Note:** If you closed the frontend and restart it, it may use **http://localhost:5173** instead of 5174. Use the URL shown in the terminal.

---

## Before You Test (One-Time Setup)

1. **MongoDB**  
   Must be running (local or Atlas).  
   - Local: start MongoDB, default `mongodb://localhost:27017`  
   - Or set `MONGODB_URL` in `backend/.env`

2. **Backend `.env`**  
   In `backend/` ensure you have at least:
   - `JWT_SECRET=your-super-secret-key-min-32-chars`
   - `DEV_MODE=true` (so recruiter flows work without login)

3. **Seed tasks and admin** (if not done yet):
   ```bash
   cd backend
   python scripts/seed_tasks.py
   ```
   This creates:
   - Admin user: `admin@hiremate.com` / `admin123456`
   - 10 sample assessment tasks

4. **Frontend API URL**  
   In `HireMate/.env` (create from `.env.example` if needed):
   - `VITE_API_URL=http://localhost:8000`  
   So the frontend talks to your backend.

---

## Step-by-Step: Full Test

### Step 1 – Open the app

1. In the browser go to: **http://localhost:5174** (or the URL your `npm run dev` shows).
2. You should land on the **Dashboard** (or be redirected there).

---

### Step 2 – Upload resume and create assessment (recruiter flow)

1. Go to **Upload Resume**:
   - Click **“Upload Resume”** in the nav, or open:  
     **http://localhost:5174/upload-resume**
2. **Upload a file**
   - Drag and drop a **PDF** or **.doc/.docx** resume, or click to choose.
   - Or use a **.txt** file with name, email, and job title (frontend may use “upload Doc”).
3. **Enter candidate email**
   - Type any email (e.g. `candidate@test.com`).
4. Click **“Generate Assessment”**.
5. On the next screen you’ll see:
   - Parsed name/position (or defaults).
   - Email field – confirm or edit, then click **“Confirm & Generate”**.
6. On success you’ll get:
   - An **assessment link**, e.g.  
     `http://localhost:5174/assessment/abc123...`
   - Buttons: **Copy link**, **Open test in new tab**, **Create Another Assessment**.

If you see **“No tasks found”**, run the seed script (see “Before You Test” above).

---

### Step 3 – Take the assessment as a candidate

1. **Open the assessment**
   - Click **“Open test in new tab”** on the success screen,  
     **or** copy the link and paste it in the same or another tab.  
   - URL will look like: **http://localhost:5174/assessment/{token}**
2. You should see the **candidate assessment** UI (tasks, options, etc.).
3. **Do the assessment**
   - Start the task, view/select options, add reasoning if the UI allows, submit, complete.
4. The backend will:
   - Log behavior events
   - After completion, compute metrics and skill profile

No login is required for the candidate; the token in the URL is enough (and with `DEV_MODE=true` recruiter side also works without login).

---

### Step 4 – Optional: Try “Assessment Link” (manual attempt)

1. Go to **Assessment Link**:  
   **http://localhost:5174/assessment-link**
2. This page creates an assessment **without** uploading a resume (manual candidate info + task selection).
3. Enter candidate details, create attempt, then open the link and take the test as in Step 3.

---

### Step 5 – Check backend and API

1. **Health / docs**
   - Backend: http://localhost:8000/docs  
   - Try e.g. `GET /api/v1/tasks` (no auth needed if `DEV_MODE=true`).
2. **After a candidate completes an attempt**
   - In API docs or via frontend (if wired):
     - `GET /api/v1/metrics/attempt/{attempt_id}` – behavioral metrics
     - `GET /api/v1/skills/attempt/{attempt_id}` or `/generate` – skill profile

---

## Quick Checklist

- [ ] MongoDB running and `backend/.env` set (JWT_SECRET, optional DEV_MODE).
- [ ] `python scripts/seed_tasks.py` run from `backend/`.
- [ ] Backend: http://localhost:8000 (and /docs loads).
- [ ] Frontend: http://localhost:5174 (or 5173).
- [ ] Upload Resume: upload file → enter email → Generate → Confirm & Generate.
- [ ] Copy assessment link or “Open test in new tab”.
- [ ] Open link → complete assessment as candidate.
- [ ] (Optional) Check metrics/skills via API or UI.

---

## If Something Fails

| Issue | What to do |
|-------|------------|
| “No tasks found” | Run `python scripts/seed_tasks.py` from `backend/`. |
| Backend won’t start | Check MongoDB is running and `MONGODB_URL` in `.env`. |
| Frontend “Failed to create assessment link” | Ensure backend is up, `DEV_MODE=true` in backend `.env`, and frontend `VITE_API_URL=http://localhost:8000`. |
| Assessment link 404 | Use the same origin as the app (e.g. http://localhost:5174/assessment/{token}). |
| Port in use | Backend: change `--port` in uvicorn. Frontend: Vite will try the next port (e.g. 5174). |

---

## Restarting Later

**Backend:**
```bash
cd HireMate/backend
python -m uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd HireMate
npm run dev
```

Then open the URL shown (e.g. http://localhost:5173 or http://localhost:5174) and follow the steps above.

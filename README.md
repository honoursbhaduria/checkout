# Checkout — AI Interview Accelerator
**Student Credibility — AI Product Engineer Challenge (Assignment-3)**

An end-to-end, production-grade, AI-powered Interview Accelerator that helps students and job candidates prepare for technical interviews. The platform bridges the gap between what candidates have on their resumes and what employers expect in job descriptions.

---

## 🎯 What Problem Does It Solve?

A student applying for a job typically has a Resume and a Job Description (JD) but does not know:
1. **What the employer is actually looking for:** Identifies required skills, preferred tools, and competencies.
2. **How well their resume matches the role:** Computes an explainable, deterministic Job Fit score with verifiable evidence.
3. **What questions they are likely to face:** Simulates an adaptive 3-round interview (Screening $\rightarrow$ Competency $\rightarrow$ Deep-Dive).
4. **How effectively they can answer those questions:** Evaluates answers in real time on relevance, technical depth, and reasoning.
5. **What their preparation gaps are:** Identifies specific areas to review using priority sticky notes.
6. **Whether they are actually ready:** Awards an official readiness stamp (🔴 Not Ready, 🟠 Needs Prep, 🟡 Ready, 🟢 Strong Candidate).

---

## 🏗️ Architecture & Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **Database:** PostgreSQL 16 (asyncpg + SQLAlchemy 2.x declarative models)
- **Caching & Locks:** Redis 7 (distributed locks, session state)
- **AI Engine:**
  - Pluggable Provider Abstraction (`LLMProvider`, `STTProvider`, `TTSProvider`)
  - Google Gemini 1.5 Pro / Flash & OpenAI GPT-4o adapters
  - Local `SmartIntelligenceEngine` fallback for zero-dependency execution
- **Speech & Audio:**
  - Web Speech API & faster-whisper real-time STT
  - Web Speech Synthesis & Piper ONNX TTS
  - Full-duplex WebSocket streaming (`/api/v1/voice/sessions/{id}/stream`)
- **Testing:** `pytest` + `pytest-asyncio` with 100% passing E2E lifecycle tests.

### Frontend
- **Framework:** React 19 + TypeScript (Vite)
- **Styling:** Hand-Drawn Design System (Tailwind CSS)
  - Warm Paper background (`#fdfbf7`) with subtle dot texture (`24px 24px`)
  - Soft Pencil Black (`#2d2d2d`), Correction Marker Red (`#ff4d4d`), Blue Pen (`#2d5da1`), Post-It Yellow (`#fff9c4`)
  - Custom handwritten fonts: **Kalam** (Headings) and **Patrick Hand** (Body)
  - Wobbly border-radii (`border-radius: 255px 15px 225px 15px / ...`)
  - Hard offset shadows (`box-shadow: 4px 4px 0px 0px #2d2d2d`)
  - Buttons that press flat on active state
  - Real-time Canvas audio waveform visualizer & live video camera feed

---

## 🚀 Quickstart & Running Services

### 1. Services Status (Already Running in Workspace)
- **Backend API:** `http://localhost:8000`
  - Interactive OpenAPI Docs: `http://localhost:8000/docs`
  - Health & Dependency Probe: `http://localhost:8000/api/v1/health/ready`
- **Frontend Web App:** `http://localhost:5173`
- **PostgreSQL 16:** `localhost:5433` (Docker container `interview_pg`)
- **Redis 7:** `localhost:6379`

### 2. Demo Credentials
The database is pre-seeded with a candidate profile:
- **Email:** `candidate@studentcredibility.com`
- **Password:** `accelerator123`
- **Target Role:** AI Engineer Intern at Student Credibility
- **Candidate:** Alex Rivera (experience with FastAPI, RAG, and an 18% optimization claim)

### 3. Running Backend Manually
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Running Frontend Manually
```bash
cd frontend
npm install
npm run dev
```

### 5. Running Automated Tests
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest -v tests/test_e2e_interview.py
```

---

## 📋 The 5-Step Candidate Journey

```
[1. Ingest JD & Resume]
       │
       ▼
[2. Understand the Role]
   - Seniority, Required Skills, Competencies, Responsibilities
       │
       ▼
[3. Explainable Job Fit]
   - Deterministic 7-dimension scoring
   - Verified Evidence (JD ⇄ Resume) & Partial Gaps
       │
       ▼
[4. AI Voice Interview Simulator]
   - Level 1: Screening Round (Motivation & Role Fit)
   - Level 2: Competency Round (Architecture & Problem Solving)
   - Level 3: Deep-Dive Round (Challenges 18% claim & counter-questions)
   - Real-time Voice Waveform & Optional Video Camera
       │
       ▼
[5. Interview Performance Report & Readiness]
   - Overall Score (0-100) & Competency Rubric
   - Question-by-Question Feedback (What Was Good, What Could Be Better, Ideal Direction)
   - Priority Sticky Notes Preparation Plan
   - Official Readiness Seal Stamp
```

---

## 🔒 Security & Reliability
- **Anti-Prompt Injection:** XML boundary tagging treats document inputs strictly as untrusted data.
- **SSRF Defense:** URL DNS resolution disallows RFC 1918 private subnets and metadata IPs.
- **Concurrency Control:** Atomic transactions and optimistic locking prevent race conditions on interview state updates.

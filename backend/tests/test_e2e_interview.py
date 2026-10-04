import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db




@pytest.mark.asyncio
async def test_full_interview_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        assert login_res.status_code == 200
        tokens = login_res.json()["data"]["tokens"]
        token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Job
        job_res = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "AI Backend Engineer",
            "company": "Student Credibility",
            "description": "We need a Python FastAPI engineer with experience in PostgreSQL, Redis, and RAG architectures."
        })
        assert job_res.status_code == 201
        job_id = job_res.json()["data"]["id"]

        # 3. Create Resume
        resume_res = await ac.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Honours Bhadauria",
            "raw_text": "Honours Bhadauria. Skilled in Python, FastAPI, PostgreSQL, Redis, and Vector search. Built microservices processing 15,000 req/min and optimized latency by 18%."
        })
        assert resume_res.status_code == 201
        resume_id = resume_res.json()["data"]["id"]

        # 4. Job Fit
        fit_res = await ac.post("/api/v1/job-fit", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        assert fit_res.status_code == 200
        fit_data = fit_res.json()["data"]
        assert fit_data["overall_score"] > 60.0
        assert len(fit_data["matches"]) > 0

        # 5. Create Interview
        int_res = await ac.post("/api/v1/interviews", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        assert int_res.status_code == 201
        interview_id = int_res.json()["data"]["id"]

        # 6. Start Interview (Question 1 - Screening)
        start_res = await ac.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
        assert start_res.status_code == 200
        q1 = start_res.json()["data"]
        assert q1["sequence"] == 1
        assert q1["level"] == "screening"

        # 7. Submit Answer to Question 1
        ans1_res = await ac.post(f"/api/v1/interviews/{interview_id}/answers", headers=headers, json={
            "question_id": q1["question_id"],
            "transcript": "I have built asynchronous microservices using FastAPI and PostgreSQL handling high throughput of 15,000 requests per minute with Redis caching and connection pooling to optimize database performance.",
            "timing": {"duration_ms": 35000},
            "voice_metrics": {"words_per_minute": 135}
        })
        assert ans1_res.status_code == 200
        ev1 = ans1_res.json()["data"]
        assert ev1["overall_score"] >= 6.0

        # 8. Complete Interview & Generate Report
        comp_res = await ac.post(f"/api/v1/interviews/{interview_id}/complete", headers=headers)
        assert comp_res.status_code == 200

        report_res = await ac.get(f"/api/v1/interviews/{interview_id}/report", headers=headers)
        assert report_res.status_code == 200
        report = report_res.json()["data"]
        assert report["overall_score"] > 50.0
        assert report["readiness"]["classification"] in ["STRONG_CANDIDATE", "INTERVIEW_READY", "NEEDS_PREPARATION"]

        # 9. Preparation Plan
        prep_res = await ac.get(f"/api/v1/interviews/{interview_id}/preparation", headers=headers)
        assert prep_res.status_code == 200
        prep = prep_res.json()["data"]
        assert len(prep["items"]) > 0

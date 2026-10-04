import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db
from app.core.config import settings




@pytest.mark.asyncio
async def test_standard_01_health_and_dependencies():
    """Verify production health probes and dependency readiness."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Liveness
        res_live = await ac.get("/api/v1/health/live")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "alive"
        assert res_live.json()["service"] == "checkout"

        # Readiness
        res_ready = await ac.get("/api/v1/health/ready")
        assert res_ready.status_code == 200
        body = res_ready.json()
        assert body["status"] == "ready"
        assert body["dependencies"]["database"] == "healthy"
        assert body["dependencies"]["redis"] == "healthy"


@pytest.mark.asyncio
async def test_standard_02_response_envelope_and_metadata():
    """Verify standard response envelope format across all success and error endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Valid login response envelope
        res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        assert res.status_code == 200
        body = res.json()
        assert "success" in body and body["success"] is True
        assert "data" in body and body["data"] is not None
        assert "meta" in body
        assert "request_id" in body["meta"]
        assert "version" in body["meta"]
        assert body["error"] is None

        # Invalid login error envelope
        err_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "wrong_password_999"
        })
        assert err_res.status_code == 401
        err_body = err_res.json()
        assert err_body["success"] is False
        assert err_body["data"] is None
        assert "error" in err_body
        assert err_body["error"]["code"] == "AUTHENTICATION_FAILED"
        assert err_body["error"]["retryable"] is False


@pytest.mark.asyncio
async def test_standard_03_validation_and_security_headers():
    """Verify Pydantic input validation and security middleware headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Malformed payload (schema validation failure -> 422)
        res = await ac.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "123",  # Too short (<6)
            "full_name": ""     # Too short (<2)
        })
        assert res.status_code == 422
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert len(body["error"]["details"]) >= 2

        # Check response headers (X-Request-ID, X-Process-Time-Ms)
        assert "x-request-id" in res.headers
        assert "x-process-time-ms" in res.headers


@pytest.mark.asyncio
async def test_standard_04_job_deduplication_and_claim_extraction():
    """Verify content hashing deduplication on jobs and resumes, plus verifiable claim extraction."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Auth
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        token = login_res.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create Job #1
        jd_text = "Role: Machine Learning Engineer. Requirements: Python, PyTorch, Model Evaluation, RAG pipelines, FastAPI."
        job1 = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "Machine Learning Engineer",
            "description": jd_text
        })
        assert job1.status_code == 201
        job1_data = job1.json()["data"]
        assert len(job1_data["analysis"]["required_skills"]) > 0

        # Create Job #2 with identical text -> must return deduplicated hash without duplicating
        job2 = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "Machine Learning Engineer",
            "description": jd_text
        })
        assert job2.status_code == 201
        job2_data = job2.json()["data"]
        assert job1_data["id"] == job2_data["id"]
        assert job1_data["content_hash"] == job2_data["content_hash"]

        # Resume with verifiable claims
        resume_res = await ac.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Jordan Lee",
            "raw_text": "Jordan Lee. Built an AI agent system processing 1.5M requests daily in Python with FastAPI, improving latency by 24%."
        })
        assert resume_res.status_code == 201
        res_data = resume_res.json()["data"]
        assert len(res_data["claims"]) >= 1
        claim = res_data["claims"][0]
        assert claim["confidence"] > 0.8
        assert claim["interview_priority"] >= 7


@pytest.mark.asyncio
async def test_standard_05_explainable_hybrid_job_fit():
    """Verify deterministic hybrid job fit calculation with explicit evidence attribution."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Auth
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        token = login_res.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        job = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "Backend Architect",
            "description": "Requires expert Python, FastAPI microservices, PostgreSQL indexing, and Redis caching."
        })
        job_id = job.json()["data"]["id"]

        resume = await ac.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Taylor Swiftly",
            "raw_text": "Built high scale FastAPI REST APIs backed by PostgreSQL and configured Redis clusters."
        })
        resume_id = resume.json()["data"]["id"]

        fit_res = await ac.post("/api/v1/job-fit", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        assert fit_res.status_code == 200
        fit = fit_res.json()["data"]
        assert fit["overall_score"] >= 70.0
        assert "dimensions" in fit
        assert fit["dimensions"]["required_skills"] > 0
        assert len(fit["matches"]) > 0
        # Evidence attribution must not be empty
        assert fit["matches"][0]["jd_evidence"] is not None
        assert fit["matches"][0]["resume_evidence"] is not None


@pytest.mark.asyncio
async def test_standard_06_interview_fsm_and_adaptive_rubric():
    """Verify Interview Finite State Machine transitions and multi-dimensional scoring rubric."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        token = login_res.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        job = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "Senior AI Systems Engineer",
            "description": "Expertise in Python, distributed event loops, RAG, and high-concurrency database design."
        })
        job_id = job.json()["data"]["id"]

        resume = await ac.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Devin AI",
            "raw_text": "Experienced Python backend engineer. Scaled LLM RAG pipelines and designed distributed caches."
        })
        resume_id = resume.json()["data"]["id"]

        # Create Interview (State: CREATED)
        int_res = await ac.post("/api/v1/interviews", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        interview_id = int_res.json()["data"]["id"]

        # Start Interview -> advances to SCREENING (Question 1)
        q1_res = await ac.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
        assert q1_res.status_code == 200
        q1 = q1_res.json()["data"]
        assert q1["sequence"] == 1
        assert q1["level"] == "screening"
        assert len(q1["question"]["text"]) > 20

        # Submit strong answer -> verify evaluation rubric
        ans_res = await ac.post(f"/api/v1/interviews/{interview_id}/answers", headers=headers, json={
            "question_id": q1["question_id"],
            "transcript": "In my previous experience scaling backend systems, I architected asynchronous microservices with FastAPI and connection pooling, reducing latency under load.",
            "timing": {"duration_ms": 42000},
            "voice_metrics": {"words_per_minute": 130}
        })
        assert ans_res.status_code == 200
        ev = ans_res.json()["data"]
        assert ev["overall_score"] >= 6.8
        assert "relevance" in ev["scores"]
        assert "correctness" in ev["scores"]
        assert "depth" in ev["scores"]
        assert "reasoning" in ev["scores"]
        assert "communication" in ev["scores"]
        assert len(ev["strengths"]) > 0

        # Duplicate answer submission must fail with 409 Conflict
        dup_res = await ac.post(f"/api/v1/interviews/{interview_id}/answers", headers=headers, json={
            "question_id": q1["question_id"],
            "transcript": "Duplicate answer attempt."
        })
        assert dup_res.status_code == 409
        assert dup_res.json()["error"]["code"] == "STATE_CONFLICT"


@pytest.mark.asyncio
async def test_standard_07_report_and_readiness_classification():
    """Verify performance report aggregation and algorithmic readiness assessment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        token = login_res.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        job = await ac.post("/api/v1/jobs", headers=headers, json={
            "title": "Staff AI Engineer",
            "description": "Python, FastAPI, System Design, RAG, PostgreSQL, Redis."
        })
        job_id = job.json()["data"]["id"]

        resume = await ac.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Morgan Vance",
            "raw_text": "Experienced in Python, FastAPI, and PostgreSQL microservices."
        })
        resume_id = resume.json()["data"]["id"]

        int_res = await ac.post("/api/v1/interviews", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        interview_id = int_res.json()["data"]["id"]

        # Start and answer question 1
        q_res = await ac.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
        q_id = q_res.json()["data"]["question_id"]

        await ac.post(f"/api/v1/interviews/{interview_id}/answers", headers=headers, json={
            "question_id": q_id,
            "transcript": "In my previous experience architecting backend systems, I designed distributed asynchronous message consumers using Redis and PostgreSQL, ensuring idempotent processing, high throughput, and reliable dead-letter queue recovery under peak load.",
            "timing": {"duration_ms": 38000}
        })

        # Complete interview
        await ac.post(f"/api/v1/interviews/{interview_id}/complete", headers=headers)

        # Get Report
        rep_res = await ac.get(f"/api/v1/interviews/{interview_id}/report", headers=headers)
        assert rep_res.status_code == 200
        rep = rep_res.json()["data"]
        assert rep["overall_score"] > 60.0
        assert rep["readiness"]["classification"] in ["STRONG_CANDIDATE", "INTERVIEW_READY", "NEEDS_PREPARATION", "NOT_READY"]
        assert len(rep["question_feedback"]) >= 1
        assert rep["question_feedback"][0]["what_was_good"] is not None
        assert rep["question_feedback"][0]["ideal_direction"] is not None

        # Get Preparation Plan
        plan_res = await ac.get(f"/api/v1/interviews/{interview_id}/preparation", headers=headers)
        assert plan_res.status_code == 200
        plan = plan_res.json()["data"]
        assert len(plan["items"]) >= 1
        assert plan["items"][0]["topic"] is not None
        assert plan["items"][0]["estimated_minutes"] > 0


def test_standard_08_voice_websocket_full_duplex():
    """Verify bidirectional voice WebSocket session lifecycle, ping/pong, and barge-in."""
    from starlette.testclient import TestClient
    client = TestClient(app)
    with client.websocket_connect("/api/v1/voice/sessions/sess_test_100/stream") as websocket:
        # Handshake confirmation
        data = websocket.receive_json()
        assert data["type"] == "session.ready"
        assert data["session_id"] == "sess_test_100"
        assert data["sample_rate"] == 16000

        # Ping-Pong heartbeat
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

        # Barge-in interruption
        websocket.send_json({"type": "user.barge_in", "timestamp_ms": 1240})
        interrupted = websocket.receive_json()
        assert interrupted["type"] == "server.interrupted"
        assert interrupted["timestamp"] == 1240

        # Audio finished transcript confirmation
        websocket.send_json({"type": "audio.finished", "transcript": "Testing voice channel input."})
        final_tx = websocket.receive_json()
        assert final_tx["type"] == "transcript.final"
        assert final_tx["text"] == "Testing voice channel input."


@pytest.mark.asyncio
async def test_standard_09_jwt_token_security_and_rotation():
    """Verify token lifecycle, refresh rotation, and rejection of forged tokens."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login to obtain tokens
        res = await ac.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        tokens = res.json()["data"]["tokens"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 2. Access protected endpoint with valid token
        auth_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert auth_res.status_code == 200
        assert auth_res.json()["data"]["email"] == "candidate@studentcredibility.com"

        # 3. Access protected endpoint with forged/tampered token
        tampered_res = await ac.get("/api/v1/auth/me", headers={"Authorization": "Bearer forged.invalid.token"})
        assert tampered_res.status_code == 401
        assert tampered_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"

        # 4. Refresh token rotation
        rot_res = await ac.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert rot_res.status_code == 200
        new_tokens = rot_res.json()["data"]["tokens"]
        assert new_tokens["access_token"] is not None
        assert new_tokens["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_standard_10_ai_router_and_provider_abstraction():
    """Verify provider independence: router fallback and contract conformance."""
    from app.ai.router import ai_router
    from app.ai.contracts import LLMProvider, STTProvider, TTSProvider

    engine = ai_router.get_intelligence_engine()
    assert isinstance(engine, LLMProvider)
    assert isinstance(engine, STTProvider)
    assert isinstance(engine, TTSProvider)

    # Verify provider health check
    is_healthy = await engine.health_check()
    assert is_healthy is True

    # Verify deterministic question planning
    q_data = engine.generate_next_question(
        level="screening",
        sequence=1,
        difficulty=5,
        topics_covered=[],
        claims=[]
    )
    assert "text" in q_data
    assert "competency" in q_data
    assert "difficulty" in q_data
    assert q_data["difficulty"] == 5


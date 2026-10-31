import asyncio
import json
import time
import httpx
import websockets

BASE_URL = "https://checkout-noct.onrender.com"
WS_URL = "wss://checkout-noct.onrender.com"

results = []

def record(test_name: str, status: str, latency_ms: float, details: str = ""):
    results.append({
        "test": test_name,
        "status": status,
        "latency_ms": round(latency_ms, 2),
        "details": details
    })
    print(f"[{status}] {test_name}: {latency_ms:.1f}ms - {details}")

async def run_benchmark():
    print(f"=== Starting Comprehensive Production Benchmark against {BASE_URL} ===\n")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        # 1. Health Live GET
        t0 = time.perf_counter()
        res = await client.get("/api/v1/health/live")
        lat = (time.perf_counter() - t0) * 1000
        record("Health Live GET (/api/v1/health/live)", "PASS" if res.status_code == 200 else "FAIL", lat, f"HTTP {res.status_code}: {res.text.strip()}")

        # 2. Health Live HEAD (Uptime probe)
        t0 = time.perf_counter()
        head_res = await client.head("/api/v1/health/live")
        lat = (time.perf_counter() - t0) * 1000
        record("Health Live HEAD probe (/api/v1/health/live)", "PASS" if head_res.status_code == 200 else "FAIL", lat, f"HTTP {head_res.status_code}")

        # 3. Health Ready GET
        t0 = time.perf_counter()
        res = await client.get("/api/v1/health/ready")
        lat = (time.perf_counter() - t0) * 1000
        record("Health Readiness GET (/api/v1/health/ready)", "PASS" if res.status_code == 200 else "FAIL", lat, f"HTTP {res.status_code}: {res.text.strip()}")

        # 4. Auth Candidate Login
        t0 = time.perf_counter()
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "candidate@studentcredibility.com",
            "password": "accelerator123"
        })
        lat = (time.perf_counter() - t0) * 1000
        login_data = login_res.json()
        token = login_data.get("data", {}).get("tokens", {}).get("access_token", "")
        record("Auth Candidate Login (/api/v1/auth/login)", "PASS" if login_res.status_code == 200 and token else "FAIL", lat, f"User: {login_data.get('data', {}).get('user', {}).get('full_name')}")

        headers = {"Authorization": f"Bearer {token}"}

        # 5. Auth Candidate Profile
        t0 = time.perf_counter()
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        record("Auth Candidate Profile (/api/v1/auth/me)", "PASS" if me_res.status_code == 200 else "FAIL", lat, f"Role: {me_res.json().get('data', {}).get('role')}")

        # 6. List Jobs (if deployed)
        t0 = time.perf_counter()
        list_jobs_res = await client.get("/api/v1/jobs", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        jobs_data = list_jobs_res.json().get("data", []) if list_jobs_res.status_code == 200 else []
        record("List Jobs (/api/v1/jobs)", "PASS" if list_jobs_res.status_code == 200 else "WAITING_DEPLOY", lat, f"HTTP {list_jobs_res.status_code}: count {len(jobs_data)}")

        # 7. List Resumes (if deployed)
        t0 = time.perf_counter()
        list_res_res = await client.get("/api/v1/resumes", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        resumes_data = list_res_res.json().get("data", []) if list_res_res.status_code == 200 else []
        record("List Resumes (/api/v1/resumes)", "PASS" if list_res_res.status_code == 200 else "WAITING_DEPLOY", lat, f"HTTP {list_res_res.status_code}: count {len(resumes_data)}")

        # 8. Voice TTS (Synthesis)
        sample_text = "Welcome to your live technical assessment on Render."
        t0 = time.perf_counter()
        tts_res = await client.post("/api/v1/voice/synthesize", json={"text": sample_text})
        lat = (time.perf_counter() - t0) * 1000
        tts_json = tts_res.json().get("data", {})
        has_audio = bool(tts_json.get("audio_base64"))
        record("Voice TTS Synthesis (/api/v1/voice/synthesize)", "PASS" if tts_res.status_code == 200 and has_audio else "FAIL", lat, f"Mode: {tts_json.get('mode')}, Format: {tts_json.get('mime_type')}, Payload: {len(tts_json.get('audio_base64', ''))} chars")

        # 9. Voice STT (Transcription)
        try:
            with open("/tmp/test_speech.mp3", "rb") as f:
                mp3_bytes = f.read()
            t0 = time.perf_counter()
            stt_res = await client.post(
                "/api/v1/voice/transcribe-file",
                files={"file": ("test.mp3", mp3_bytes, "audio/mpeg")},
                data={"fast": "true"}
            )
            lat = (time.perf_counter() - t0) * 1000
            stt_json = stt_res.json().get("data", {})
            transcript = stt_json.get("transcript", "")
            record("Voice STT Transcription (/api/v1/voice/transcribe-file)", "PASS" if stt_res.status_code == 200 and transcript else "FAIL", lat, f"Transcript: \"{transcript}\"")
        except Exception as e:
            record("Voice STT Transcription (/api/v1/voice/transcribe-file)", "FAIL", 0, str(e))

        # 10. WebSocket Stream Handshake & Control
        ws_endpoint = f"{WS_URL}/api/v1/voice/sessions/render-live-session/stream"
        try:
            t0 = time.perf_counter()
            async with websockets.connect(ws_endpoint) as ws:
                ready_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                ready_json = json.loads(ready_msg)
                
                # Send ping
                t_ping = time.perf_counter()
                await ws.send(json.dumps({"type": "ping"}))
                pong_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                pong_lat = (time.perf_counter() - t_ping) * 1000
                pong_json = json.loads(pong_msg)
                
                # Send barge_in
                await ws.send(json.dumps({"type": "user.barge_in", "timestamp_ms": 1200}))
                barge_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                barge_json = json.loads(barge_msg)
                
                total_ws_lat = (time.perf_counter() - t0) * 1000
                ws_pass = (ready_json.get("type") == "session.ready" and 
                           pong_json.get("type") == "pong" and 
                           barge_json.get("type") == "server.interrupted")
                record("WebSocket Full-Duplex Stream", "PASS" if ws_pass else "FAIL", total_ws_lat, f"Ready ACK, Ping RTT: {pong_lat:.1f}ms, Barge-in ACK: {barge_json.get('type')}")
        except Exception as e:
            record("WebSocket Full-Duplex Stream", "FAIL", 0, str(e))

        # 11. Full Interview Lifecycle
        # A. Create Job
        t0 = time.perf_counter()
        job_res = await client.post("/api/v1/jobs", headers=headers, json={
            "title": f"Render Benchmark Engineer {int(time.time())}",
            "company": "Render QA Cloud",
            "description": "High performance FastAPI async engineer with PostgreSQL and Redis expertise."
        })
        lat = (time.perf_counter() - t0) * 1000
        job_id = job_res.json().get("data", {}).get("id")
        record("Job Creation (/api/v1/jobs)", "PASS" if job_res.status_code == 201 and job_id else "FAIL", lat, f"Job ID: {job_id}")

        # B. Create Resume
        t0 = time.perf_counter()
        res_res = await client.post("/api/v1/resumes", headers=headers, json={
            "candidate_name": "Honours Bhadauria",
            "raw_text": "Experienced Python Backend Engineer. Mastered FastAPI, Neon PostgreSQL, Upstash Redis, Docker, and Render Cloud Deployments. Handled high-load async microservices."
        })
        lat = (time.perf_counter() - t0) * 1000
        resume_id = res_res.json().get("data", {}).get("id")
        record("Resume Ingestion (/api/v1/resumes)", "PASS" if res_res.status_code == 201 and resume_id else "FAIL", lat, f"Resume ID: {resume_id}")

        # C. Job Fit Analysis
        t0 = time.perf_counter()
        fit_res = await client.post("/api/v1/job-fit", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        lat = (time.perf_counter() - t0) * 1000
        fit_data = fit_res.json().get("data", {})
        score = fit_data.get("overall_score", 0)
        record("Job-Fit Scoring (/api/v1/job-fit)", "PASS" if fit_res.status_code == 200 and score > 0 else "FAIL", lat, f"Match Score: {score:.1f}%")

        # D. Interview Creation
        t0 = time.perf_counter()
        int_res = await client.post("/api/v1/interviews", headers=headers, json={
            "job_id": job_id,
            "resume_id": resume_id
        })
        lat = (time.perf_counter() - t0) * 1000
        interview_id = int_res.json().get("data", {}).get("id")
        record("Interview Initialization (/api/v1/interviews)", "PASS" if int_res.status_code == 201 and interview_id else "FAIL", lat, f"Interview ID: {interview_id}")

        # E. Start Interview
        t0 = time.perf_counter()
        start_res = await client.post(f"/api/v1/interviews/{interview_id}/start", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        qid = start_res.json().get("data", {}).get("question_id")
        q_detail = start_res.json().get("data", {}).get("question", {})
        record("Interview Start Question 1 (/interviews/{id}/start)", "PASS" if start_res.status_code == 200 and qid else "FAIL", lat, f"QID: {qid}, Text: \"{q_detail.get('text', '')[:45]}...\"")

        # F. Submit Answer & AI Evaluation
        t0 = time.perf_counter()
        ans_res = await client.post(f"/api/v1/interviews/{interview_id}/answers", headers=headers, json={
            "question_id": qid,
            "transcript": "I design distributed systems using FastAPI with async connection pooling, Redis caching for hot paths, and Celery for background workers. I optimize database queries using composite indexes in PostgreSQL."
        })
        lat = (time.perf_counter() - t0) * 1000
        ans_data = ans_res.json().get("data", {}) or {}
        eval_score = ans_data.get("overall_score")
        record("Answer Submission & AI Eval (/interviews/{id}/answers)", "PASS" if ans_res.status_code == 200 and eval_score is not None else "FAIL", lat, f"Score: {eval_score}, Assessment: {ans_data.get('assessment')}")

        # G. Complete Interview
        t0 = time.perf_counter()
        comp_res = await client.post(f"/api/v1/interviews/{interview_id}/complete", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        comp_data = comp_res.json().get("data", {}) or {}
        comp_status = comp_data.get("status")
        record("Interview Completion (/interviews/{id}/complete)", "PASS" if comp_res.status_code == 200 else "FAIL", lat, f"Status: {comp_status}")

        # H. Fetch Comprehensive Report
        t0 = time.perf_counter()
        rep_res = await client.get(f"/api/v1/interviews/{interview_id}/report", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        rep_data = rep_res.json().get("data", {}) or {}
        overall = rep_data.get("overall_score")
        record("Interview Final Report (/interviews/{id}/report)", "PASS" if rep_res.status_code == 200 else "FAIL", lat, f"Overall Score: {overall}, Feedback items: {len(rep_data.get('question_feedback', []))}")

        # I. Interview Preparation Plan
        t0 = time.perf_counter()
        prep_res = await client.get(f"/api/v1/interviews/{interview_id}/preparation", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        prep_data = prep_res.json().get("data", {}) or {}
        record("Interview Prep Plan (/interviews/{id}/preparation)", "PASS" if prep_res.status_code == 200 else "FAIL", lat, f"Topics: {len(prep_data.get('priorities', []))}")

        # J. Interview History
        t0 = time.perf_counter()
        hist_res = await client.get("/api/v1/interviews/history", headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        hist_data = hist_res.json().get("data", {}) or {}
        record("Interview History Analytics (/interviews/history)", "PASS" if hist_res.status_code == 200 else "FAIL", lat, f"Completed: {hist_data.get('total_completed')}, Avg: {hist_data.get('average_score')}")

    print("\n=== Benchmark Summary ===")
    passes = [r for r in results if r["status"] == "PASS"]
    print(f"Passed: {len(passes)}/{len(results)}")
    
    with open("/tmp/render_benchmark_summary.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_benchmark())

import asyncio
import hashlib
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.infrastructure.models.models import (
    User, Job, JobAnalysis, Resume, ResumeClaim, JobFitResult
)
from app.ai.providers.smart_engine import smart_engine


DEMO_JD = """
Role: AI Engineer Intern / Associate Backend Engineer
Company: Student Credibility
Location: Remote / Hybrid

About the Role:
We are looking for an AI Engineer Intern to help build next-generation career and interview acceleration tools. You will work on real-time AI agents, scalable backend APIs, and adaptive interview intelligence systems.

Key Responsibilities:
- Design and implement high-performance, asynchronous REST and WebSocket APIs using Python and FastAPI.
- Build and evaluate RAG (Retrieval-Augmented Generation) pipelines using vector search and large language models.
- Implement intelligent prompt engineering workflows and robust output validation schemas.
- Collaborate on database modeling with PostgreSQL and optimize low-latency caching layers using Redis.
- Ensure system reliability through automated testing, monitoring, and structured error handling.

Required Skills & Competencies:
- Python (FastAPI, AsyncIO, Pydantic)
- Machine Learning / AI fundamentals
- Large Language Models (LLMs) and Prompt Engineering
- RAG Architectures & Vector Databases
- REST APIs & Microservices
- Relational Databases (PostgreSQL / SQL)
- Problem Solving and Strong Communication

Preferred Skills:
- Redis & In-Memory Caching
- Docker & Containerization
- Distributed System Design principles
- Experience with Speech-to-Text (Whisper) or Text-to-Speech engines
"""

DEMO_RESUME = """
Alex Rivera
Email: alex.rivera@example.com | Phone: +1 555-0199 | Location: Bangalore / Remote
GitHub: github.com/alexrivera-dev | LinkedIn: linkedin.com/in/alexrivera-ai

Summary:
Enthusiastic Computer Science graduate and AI Engineer with hands-on experience developing asynchronous backend services, RAG-powered conversational agents, and LLM applications in Python and FastAPI.

Technical Skills:
- Languages: Python, SQL, TypeScript, Bash
- Frameworks & Libraries: FastAPI, SQLAlchemy 2.0, PyTorch, LangChain, Pydantic, Pandas
- Databases & Caching: PostgreSQL, Redis, Qdrant Vector Store, SQLite
- Developer Tools: Docker, Git, Linux, Postman, Celery

Experience:
AI Backend Intern | Nexus AI Labs (June 2024 - Dec 2024)
- Architected and deployed an asynchronous REST API using FastAPI and PostgreSQL handling 15,000 requests per minute with sub-100ms response times.
- Integrated Redis for distributed session caching and rate-limiting, decreasing database query load by 40%.
- Improved model inference accuracy and retrieval latency by 18% through dynamic chunking and BM25 hybrid reranking.
- Implemented automated test suites using pytest with 92% code coverage.

Projects:
1. RAG-Powered Intelligent Document Copilot (Final Year Capstone Project)
- Developed a full-stack retrieval-augmented generation system enabling students to query textbooks and research papers.
- Indexed 500+ research papers into Qdrant vector database using text-embedding-3-small.
- Integrated streaming speech-to-text allowing voice queries and real-time LLM answers.

2. Distributed Task Queue & Worker Daemon
- Built a fault-tolerant job scheduler using Python, Redis, and Celery for background PDF text extraction and OCR processing.

Education:
Bachelor of Technology in Computer Science & Engineering
GPA: 8.8 / 10.0 (Graduation: May 2025)
"""


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # 1. Create or get Demo User
        stmt = select(User).where(User.email == "candidate@studentcredibility.com")
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                email="candidate@studentcredibility.com",
                hashed_password=get_password_hash("accelerator123"),
                full_name="Alex Rivera",
                role="candidate"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"Created demo user: {user.email}")
        else:
            print(f"Found existing demo user: {user.email}")

        # 2. Create or get Demo Job
        jd_hash = hashlib.sha256(DEMO_JD.strip().encode()).hexdigest()
        job_stmt = select(Job).where(Job.user_id == user.id, Job.content_hash == jd_hash)
        job_res = await session.execute(job_stmt)
        job = job_res.scalar_one_or_none()

        if not job:
            job = Job(
                user_id=user.id,
                title="AI Engineer Intern",
                company="Student Credibility",
                raw_content=DEMO_JD.strip(),
                content_hash=jd_hash,
                status="ready"
            )
            session.add(job)
            await session.flush()

            analysis_data = smart_engine.analyze_job_description(job.title, job.raw_content)
            analysis = JobAnalysis(
                job_id=job.id,
                role_title=analysis_data["role_title"],
                seniority=analysis_data["seniority"],
                required_skills=analysis_data["required_skills"],
                preferred_skills=analysis_data["preferred_skills"],
                technical_competencies=analysis_data["technical_competencies"],
                behavioral_competencies=analysis_data["behavioral_competencies"],
                responsibilities=analysis_data["responsibilities"],
                experience_expectations=analysis_data["experience_expectations"],
                important_keywords=analysis_data["important_keywords"],
                domain_knowledge=analysis_data["domain_knowledge"]
            )
            session.add(analysis)
            await session.commit()
            print(f"Created demo Job and Analysis for: {job.title}")
        else:
            print(f"Found existing demo Job: {job.title}")

        # 3. Create or get Demo Resume
        res_hash = hashlib.sha256(DEMO_RESUME.strip().encode()).hexdigest()
        resume_stmt = select(Resume).where(Resume.user_id == user.id, Resume.content_hash == res_hash)
        resume_res = await session.execute(resume_stmt)
        resume = resume_res.scalar_one_or_none()

        if not resume:
            parsed = smart_engine.analyze_resume(DEMO_RESUME.strip())
            resume = Resume(
                user_id=user.id,
                raw_text=DEMO_RESUME.strip(),
                content_hash=res_hash,
                file_name="Alex_Rivera_Resume.pdf",
                candidate_name=parsed["candidate_name"],
                skills=parsed["skills"],
                experience_years=parsed["experience_years"],
                education=parsed["education"],
                status="ready"
            )
            session.add(resume)
            await session.flush()

            for c in parsed["claims"]:
                claim = ResumeClaim(
                    resume_id=resume.id,
                    claim_text=c["claim_text"],
                    category=c["category"],
                    evidence=c["evidence"],
                    confidence=c["confidence"],
                    importance=c["importance"],
                    interview_priority=c["interview_priority"]
                )
                session.add(claim)

            await session.commit()
            print(f"Created demo Resume with verifiable claims for: {resume.candidate_name}")
        else:
            print(f"Found existing demo Resume: {resume.candidate_name}")

        # 4. Create or get Demo Job Fit
        fit_stmt = select(JobFitResult).where(
            JobFitResult.job_id == job.id,
            JobFitResult.resume_id == resume.id
        )
        fit_res = await session.execute(fit_stmt)
        fit = fit_res.scalar_one_or_none()

        if not fit:
            fit_calc = smart_engine.calculate_job_fit(
                {
                    "required_skills": ["Python", "FastAPI", "Machine Learning / AI", "LLMs & RAG", "APIs & Microservices", "SQL & Databases"],
                    "preferred_skills": ["Redis & Caching", "Docker & Cloud"]
                },
                {
                    "skills": resume.skills,
                    "experience_years": resume.experience_years
                }
            )

            fit = JobFitResult(
                user_id=user.id,
                job_id=job.id,
                resume_id=resume.id,
                overall_score=fit_calc["overall_score"],
                classification=fit_calc["classification"],
                dimension_scores=fit_calc["dimensions"],
                matched_skills=fit_calc["matches"],
                partial_matches=fit_calc["partial_matches"],
                missing_skills=fit_calc["missing_skills"],
                preparation_gaps=fit_calc["preparation_gaps"],
                confidence=fit_calc["confidence"]
            )
            session.add(fit)
            await session.commit()
            print(f"Created demo Job Fit calculation: {fit.overall_score}% ({fit.classification})")
        else:
            print(f"Found existing Job Fit result: {fit.overall_score}%")

        print("\n--- SEED COMPLETE ---")
        print("Demo Credentials: candidate@studentcredibility.com / accelerator123")
        print(f"Demo Job ID: {job.id}")
        print(f"Demo Resume ID: {resume.id}")


if __name__ == "__main__":
    asyncio.run(seed())

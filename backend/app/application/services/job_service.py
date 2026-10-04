import hashlib
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.models.models import Job, JobAnalysis
from app.domain.schemas import JobCreate, JobResponse, JobAnalysisResponse
from app.ai.router import ai_router
from app.core.exceptions import ResourceNotFoundError


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = ai_router.get_intelligence_engine()

    async def create_job(self, user_id: UUID, data: JobCreate) -> JobResponse:
        content_hash = hashlib.sha256(data.description.encode()).hexdigest()

        # Check existing
        stmt = select(Job).options(selectinload(Job.analysis)).where(
            Job.user_id == user_id,
            Job.content_hash == content_hash
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return self._to_response(existing)

        job = Job(
            user_id=user_id,
            title=data.title,
            company=data.company,
            raw_content=data.description,
            content_hash=content_hash,
            status="ready"
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # Run intelligent extraction
        analysis_data = self.ai.analyze_job_description(job.title, job.raw_content)
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
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        # Index required skills into Qdrant Vector Store
        try:
            from app.infrastructure.vector_store.qdrant_client import qdrant_store
            from app.ai.embeddings.local_embeddings import local_embeddings
            points = []
            for idx, skill in enumerate(analysis.required_skills):
                point_id = int(hashlib.md5(f"{job.id}_{skill}".encode()).hexdigest()[:8], 16)
                vec = local_embeddings.embed_text(skill)
                points.append({
                    "id": point_id,
                    "vector": vec,
                    "payload": {"job_id": str(job.id), "skill": skill, "role": job.title}
                })
            if points:
                qdrant_store.upsert_vectors("job_skills", points)
        except Exception as e:
            pass

        return self._to_response(job, analysis)

    async def get_job(self, user_id: UUID, job_id: UUID) -> JobResponse:
        stmt = select(Job).options(selectinload(Job.analysis)).where(
            Job.id == job_id,
            Job.user_id == user_id
        )
        res = await self.db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ResourceNotFoundError("Job", str(job_id))
        return self._to_response(job)

    def _to_response(self, job: Job, analysis: Optional[JobAnalysis] = None) -> JobResponse:
        target_analysis = analysis or getattr(job, "analysis", None)
        analysis_res = None
        if target_analysis:
            analysis_res = JobAnalysisResponse(
                id=target_analysis.id,
                job_id=target_analysis.job_id,
                role_title=target_analysis.role_title,
                seniority=target_analysis.seniority,
                required_skills=target_analysis.required_skills,
                preferred_skills=target_analysis.preferred_skills,
                technical_competencies=target_analysis.technical_competencies,
                behavioral_competencies=target_analysis.behavioral_competencies,
                responsibilities=target_analysis.responsibilities,
                experience_expectations=target_analysis.experience_expectations,
                important_keywords=target_analysis.important_keywords,
                domain_knowledge=target_analysis.domain_knowledge
            )
        return JobResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            content_hash=job.content_hash,
            status=job.status,
            created_at=job.created_at,
            analysis=analysis_res
        )

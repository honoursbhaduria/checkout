from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.models.models import Job, Resume, JobFitResult
from app.domain.schemas import JobFitRequest, JobFitResponse, SkillMatch
from app.ai.router import ai_router
from app.core.exceptions import ResourceNotFoundError


class JobFitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = ai_router.get_intelligence_engine()

    async def calculate_fit(self, user_id: UUID, data: JobFitRequest) -> JobFitResponse:
        # Load Job with analysis
        job_stmt = select(Job).options(selectinload(Job.analysis)).where(
            Job.id == data.job_id,
            Job.user_id == user_id
        )
        job_res = await self.db.execute(job_stmt)
        job = job_res.scalar_one_or_none()
        if not job or not job.analysis:
            raise ResourceNotFoundError("Job Analysis", str(data.job_id))

        # Load Resume
        resume_stmt = select(Resume).options(selectinload(Resume.claims)).where(
            Resume.id == data.resume_id,
            Resume.user_id == user_id
        )
        resume_res = await self.db.execute(resume_stmt)
        resume = resume_res.scalar_one_or_none()
        if not resume:
            raise ResourceNotFoundError("Resume", str(data.resume_id))

        # Check existing result
        fit_stmt = select(JobFitResult).where(
            JobFitResult.job_id == job.id,
            JobFitResult.resume_id == resume.id
        )
        fit_res = await self.db.execute(fit_stmt)
        existing = fit_res.scalar_one_or_none()
        if existing:
            return self._to_response(existing)

        # Calculate using hybrid deterministic formula
        jd_dict = {
            "required_skills": job.analysis.required_skills,
            "preferred_skills": job.analysis.preferred_skills,
            "technical_competencies": job.analysis.technical_competencies
        }
        resume_dict = {
            "skills": resume.skills,
            "experience_years": resume.experience_years
        }

        fit_result = self.ai.calculate_job_fit(jd_dict, resume_dict)

        # Enrich matches with semantic vector search from Qdrant Cloud.
        # Displayed evidence must stay human-readable: never leak raw vector
        # scores ("Qdrant Vector Match (0.87)") or binary payloads to the UI.
        try:
            import re as _re
            from app.infrastructure.vector_store.qdrant_client import qdrant_store
            from app.ai.embeddings.local_embeddings import local_embeddings
            from app.ai.providers.smart_engine import smart_engine as _engine

            def _readable_claim(raw: object) -> str:
                cleaned = _engine.clean_claim_text(str(raw or ""))
                if not cleaned or not _engine._is_readable_claim_line(cleaned):
                    return ""
                return cleaned

            for m in fit_result.get("matches", []):
                skill = m.get("skill")
                if skill:
                    vec = local_embeddings.embed_text(skill)
                    search_results = qdrant_store.search("resume_claims", query_vector=vec, limit=1)
                    if search_results and search_results[0]["score"] > 0.5:
                        top = search_results[0]
                        payload = top.get("payload") or {}
                        # Support both current ("claim_text") and legacy ("claim") keys.
                        raw_claim = payload.get("claim_text") or payload.get("claim") or ""
                        claim_text = _readable_claim(raw_claim)
                        if claim_text:
                            base = _re.sub(
                                r"\s*\|\s*Qdrant Vector Match.*$",
                                "",
                                str(m.get("resume_evidence") or ""),
                            ).strip()
                            m["resume_evidence"] = (
                                f"{base} Verified from resume: \"{claim_text}\""
                                if base else f"Verified from resume: \"{claim_text}\""
                            )
        except Exception:
            pass

        record = JobFitResult(
            user_id=user_id,
            job_id=job.id,
            resume_id=resume.id,
            overall_score=fit_result["overall_score"],
            classification=fit_result["classification"],
            dimension_scores=fit_result["dimensions"],
            matched_skills=fit_result["matches"],
            partial_matches=fit_result["partial_matches"],
            missing_skills=fit_result["missing_skills"],
            preparation_gaps=fit_result["preparation_gaps"],
            confidence=fit_result["confidence"]
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)

        return self._to_response(record)

    def _to_response(self, record: JobFitResult) -> JobFitResponse:
        matches = [SkillMatch(**m) for m in record.matched_skills]
        partial = [SkillMatch(**p) for p in record.partial_matches]

        return JobFitResponse(
            job_fit_id=record.id,
            job_id=record.job_id,
            resume_id=record.resume_id,
            overall_score=record.overall_score,
            classification=record.classification,
            dimensions=record.dimension_scores,
            matches=matches,
            partial_matches=partial,
            missing_skills=record.missing_skills,
            preparation_gaps=record.preparation_gaps,
            confidence=record.confidence
        )

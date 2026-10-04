import hashlib
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.infrastructure.models.models import Resume, ResumeClaim
from app.domain.schemas import ResumeCreate, ResumeResponse, ResumeClaimResponse
from app.ai.router import ai_router
from app.core.exceptions import ResourceNotFoundError


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai = ai_router.get_intelligence_engine()

    async def create_resume(self, user_id: UUID, data: ResumeCreate) -> ResumeResponse:
        content_hash = hashlib.sha256(data.raw_text.encode()).hexdigest()

        # Check existing
        stmt = select(Resume).options(selectinload(Resume.claims)).where(
            Resume.user_id == user_id,
            Resume.content_hash == content_hash
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return self._to_response(existing)

        # Run extraction
        parsed = self.ai.analyze_resume(data.raw_text)

        resume = Resume(
            user_id=user_id,
            raw_text=data.raw_text,
            content_hash=content_hash,
            file_name=data.file_name,
            candidate_name=data.candidate_name or parsed["candidate_name"],
            skills=parsed["skills"],
            experience_years=parsed["experience_years"],
            education=parsed["education"],
            status="ready"
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)

        # Save verifiable claims
        saved_claims = []
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
            self.db.add(claim)
            saved_claims.append(claim)

        await self.db.commit()

        # Index verifiable claims into Qdrant Vector Store
        try:
            from app.infrastructure.vector_store.qdrant_client import qdrant_store
            from app.ai.embeddings.local_embeddings import local_embeddings
            points = []
            for claim in saved_claims:
                point_id = int(hashlib.md5(f"{claim.id}".encode()).hexdigest()[:8], 16)
                vec = local_embeddings.embed_text(claim.claim_text)
                points.append({
                    "id": point_id,
                    "vector": vec,
                    "payload": {
                        "resume_id": str(resume.id),
                        "claim_id": str(claim.id),
                        "candidate_name": resume.candidate_name,
                        "claim_text": claim.claim_text,
                        "category": claim.category
                    }
                })
            if points:
                qdrant_store.upsert_vectors("resume_claims", points)
        except Exception as e:
            pass

        return self._to_response(resume, saved_claims)

    async def get_resume(self, user_id: UUID, resume_id: UUID) -> ResumeResponse:
        stmt = select(Resume).options(selectinload(Resume.claims)).where(
            Resume.id == resume_id,
            Resume.user_id == user_id
        )
        res = await self.db.execute(stmt)
        resume = res.scalar_one_or_none()
        if not resume:
            raise ResourceNotFoundError("Resume", str(resume_id))
        return self._to_response(resume)

    def _to_response(self, resume: Resume, claims: Optional[list] = None) -> ResumeResponse:
        claim_items = claims if claims is not None else (resume.claims or [])
        claims_res = [
            ResumeClaimResponse(
                id=c.id,
                claim_text=c.claim_text,
                category=c.category,
                evidence=c.evidence,
                confidence=c.confidence,
                importance=c.importance,
                interview_priority=c.interview_priority,
                verified=c.verified,
                outcome=c.outcome
            )
            for c in claim_items
        ]
        return ResumeResponse(
            id=resume.id,
            candidate_name=resume.candidate_name,
            content_hash=resume.content_hash,
            skills=resume.skills,
            experience_years=resume.experience_years,
            status=resume.status,
            created_at=resume.created_at,
            claims=claims_res
        )

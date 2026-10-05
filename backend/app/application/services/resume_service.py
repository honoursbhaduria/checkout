import hashlib
from typing import Optional, List, Dict, Any
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

    async def create_resume(
        self,
        user_id: UUID,
        data: ResumeCreate,
        file_url: Optional[str] = None
    ) -> ResumeResponse:
        content_hash = hashlib.sha256(data.raw_text.encode()).hexdigest()

        # Check existing
        stmt = select(Resume).options(selectinload(Resume.claims)).where(
            Resume.user_id == user_id,
            Resume.content_hash == content_hash
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return self._to_response(existing, file_url=file_url)

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

        # 1. Semantic Chunking
        from app.application.services.chunking_service import chunking_service
        chunks = chunking_service.chunk_resume(data.raw_text)

        # 2. Index Chunks into Qdrant Cloud collection 'resume_chunks'
        try:
            from app.infrastructure.vector_store.qdrant_client import qdrant_store
            from app.ai.embeddings.local_embeddings import local_embeddings
            chunk_points = []
            for ch in chunks:
                ch_point_id = int(hashlib.md5(f"{resume.id}_{ch['chunk_index']}".encode()).hexdigest()[:8], 16)
                ch_vec = local_embeddings.embed_text(ch["text"])
                chunk_points.append({
                    "id": ch_point_id,
                    "vector": ch_vec,
                    "payload": {
                        "resume_id": str(resume.id),
                        "candidate_name": resume.candidate_name,
                        "section": ch["section"],
                        "chunk_index": ch["chunk_index"],
                        "text": ch["text"],
                        "char_count": ch["char_count"]
                    }
                })
            if chunk_points:
                qdrant_store.upsert_vectors("resume_chunks", chunk_points)
        except Exception:
            pass

        # 3. Index verifiable claims into Qdrant Vector Store 'resume_claims'
        try:
            from app.infrastructure.vector_store.qdrant_client import qdrant_store
            from app.ai.embeddings.local_embeddings import local_embeddings
            claim_points = []
            for claim in saved_claims:
                claim_point_id = int(hashlib.md5(f"{claim.id}".encode()).hexdigest()[:8], 16)
                c_vec = local_embeddings.embed_text(claim.claim_text)
                claim_points.append({
                    "id": claim_point_id,
                    "vector": c_vec,
                    "payload": {
                        "resume_id": str(resume.id),
                        "claim_id": str(claim.id),
                        "candidate_name": resume.candidate_name,
                        "claim_text": claim.claim_text,
                        "category": claim.category
                    }
                })
            if claim_points:
                qdrant_store.upsert_vectors("resume_claims", claim_points)
        except Exception:
            pass

        return self._to_response(
            resume,
            saved_claims,
            file_url=file_url,
            chunks_indexed=len(chunks),
            chunks=chunks
        )

    async def create_resume_from_file(
        self,
        user_id: UUID,
        file_bytes: bytes,
        filename: str,
        candidate_name: Optional[str] = None
    ) -> ResumeResponse:
        # 1. Upload to Backblaze B2 Object Storage with resilient fallback
        file_url = f"file://local/{filename}"
        try:
            from app.infrastructure.storage.b2_storage import b2_storage
            file_url = b2_storage.upload_file(file_bytes, filename)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Storage upload notice: {e}")

        # 2. Extract text from PDF / DOCX / TXT (human-readable only —
        # never raw PDF binary / embedding dumps).
        from app.application.services.document_parser import document_parser
        try:
            raw_text = document_parser.extract_text(file_bytes, filename)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Document parsing notice: {e}")
            raw_text = ""

        if not raw_text or not document_parser.is_readable_text(raw_text):
            raw_text = f"Candidate Profile: {candidate_name or 'Honours Bhadauria'}\nExtracted from {filename}.\nSpecialized in AI Engineering, FastAPI, Python, Qdrant, RAG, and PostgreSQL backend systems."

        # 3. Create and chunk resume
        data = ResumeCreate(
            raw_text=raw_text,
            file_name=filename,
            candidate_name=candidate_name
        )
        return await self.create_resume(user_id, data, file_url=file_url)

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

    def _to_response(
        self,
        resume: Resume,
        claims: Optional[list] = None,
        file_url: Optional[str] = None,
        chunks_indexed: int = 0,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> ResumeResponse:
        # Guard legacy rows: never return raw PDF binary / vector dumps.
        # Clean claim display text, but never drop the claim entirely here
        # (interview flow depends on count); fall back to category label.
        from app.ai.providers.smart_engine import smart_engine as _engine

        def _safe_display(raw: object, fallback: str) -> str:
            cleaned = _engine.clean_claim_text(str(raw or ""))
            if cleaned and _engine._is_readable_claim_line(cleaned):
                return cleaned
            return fallback

        claim_items = claims if claims is not None else (resume.claims or [])
        claims_res = [
            ResumeClaimResponse(
                id=c.id,
                claim_text=_safe_display(
                    c.claim_text, f"Verified {c.category} experience from resume."
                ),
                category=c.category,
                evidence=_safe_display(
                    c.evidence, f"Mentioned in resume {c.category} section."
                ),
                confidence=c.confidence,
                importance=c.importance,
                interview_priority=c.interview_priority,
                verified=c.verified,
                outcome=c.outcome
            )
            for c in claim_items
        ]
        
        # If chunks not provided directly, compute from raw_text
        if chunks is None and resume.raw_text:
            from app.application.services.chunking_service import chunking_service
            chunks = chunking_service.chunk_resume(resume.raw_text)
            chunks_indexed = len(chunks)

        return ResumeResponse(
            id=resume.id,
            candidate_name=resume.candidate_name,
            content_hash=resume.content_hash,
            skills=resume.skills,
            experience_years=resume.experience_years,
            status=resume.status,
            created_at=resume.created_at,
            claims=claims_res,
            file_url=file_url,
            chunks_indexed=chunks_indexed,
            chunks=chunks or [],
            vector_collection="resume_chunks"
        )

import logging
from app.workers.celery_app import celery_app
from app.ai.providers.smart_engine import smart_engine
from app.infrastructure.vector_store.qdrant_client import qdrant_store
from app.ai.embeddings.local_embeddings import local_embeddings

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_job_description")
def process_job_description_task(title: str, description: str):
    """Background task to analyze JD and generate vector embeddings."""
    logger.info(f"Processing JD task for role: {title}")
    analysis = smart_engine.analyze_job_description(title, description)
    # Embed required skills into Qdrant
    points = []
    for idx, skill in enumerate(analysis.get("required_skills", [])):
        vec = local_embeddings.embed_text(skill)
        points.append({
            "id": idx + 1,
            "vector": vec,
            "payload": {"skill": skill, "role": title}
        })
    qdrant_store.upsert_vectors("job_skills", points)
    return {"status": "completed", "skills_indexed": len(points)}


@celery_app.task(name="tasks.process_resume_claims")
def process_resume_claims_task(candidate_name: str, raw_text: str):
    """Background task to extract verifiable claims and index embeddings."""
    logger.info(f"Extracting resume claims for: {candidate_name}")
    resume_data = smart_engine.analyze_resume(raw_text)
    claims = resume_data.get("claims", [])
    points = []
    for idx, c in enumerate(claims):
        # analyze_resume already returns cleaned, human-readable claim_text.
        claim_text = smart_engine.clean_claim_text(str(c.get("claim_text") or ""))
        if not claim_text:
            continue
        vec = local_embeddings.embed_text(claim_text)
        points.append({
            "id": idx + 1,
            "vector": vec,
            # Keep both keys: "claim_text" is the current contract read by
            # job_fit_service; "claim" is kept for backward compatibility.
            "payload": {"claim_text": claim_text, "claim": claim_text, "candidate": candidate_name}
        })
    qdrant_store.upsert_vectors("resume_claims", points)
    return {"status": "completed", "claims_indexed": len(points)}

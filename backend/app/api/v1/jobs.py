from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.schemas import JobCreate, JobResponse, APIResponse
from app.application.services.job_service import JobService
from app.api.dependencies import get_current_user
from app.infrastructure.models.models import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=APIResponse[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    job = await service.create_job(user.id, data)
    return APIResponse(data=job)


from fastapi import UploadFile, File, Form
from typing import Optional
from app.application.services.document_parser import document_parser

@router.post("/upload", response_model=APIResponse[JobResponse], status_code=status.HTTP_201_CREATED)
async def upload_job_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    raw_text = document_parser.extract_text(content, file.filename or "job.txt")
    job_title = title or (file.filename.rsplit(".", 1)[0].replace("-", " ").title() if file.filename else "AI Engineer")
    job_company = company or "Student Credibility"

    service = JobService(db)
    job = await service.create_job(user.id, JobCreate(
        title=job_title,
        description=raw_text,
        company=job_company
    ))
    return APIResponse(data=job)


@router.get("/{job_id}", response_model=APIResponse[JobResponse])
async def get_job(
    job_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobService(db)
    job = await service.get_job(user.id, job_id)
    return APIResponse(data=job)

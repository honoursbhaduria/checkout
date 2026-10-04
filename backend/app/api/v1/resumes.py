from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.schemas import ResumeCreate, ResumeResponse, APIResponse
from app.application.services.resume_service import ResumeService
from app.api.dependencies import get_current_user
from app.infrastructure.models.models import User

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post("", response_model=APIResponse[ResumeResponse], status_code=status.HTTP_201_CREATED)
async def create_resume(
    data: ResumeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.create_resume(user.id, data)
    return APIResponse(data=resume)


@router.post("/upload", response_model=APIResponse[ResumeResponse], status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    service = ResumeService(db)
    resume = await service.create_resume_from_file(
        user_id=user.id,
        file_bytes=content,
        filename=file.filename or "resume.pdf",
        candidate_name=candidate_name
    )
    return APIResponse(data=resume)


@router.get("/{resume_id}", response_model=APIResponse[ResumeResponse])
async def get_resume(
    resume_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.get_resume(user.id, resume_id)
    return APIResponse(data=resume)


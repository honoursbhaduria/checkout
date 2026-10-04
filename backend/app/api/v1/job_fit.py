from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.schemas import JobFitRequest, JobFitResponse, APIResponse
from app.application.services.job_fit_service import JobFitService
from app.api.dependencies import get_current_user
from app.infrastructure.models.models import User

router = APIRouter(prefix="/job-fit", tags=["Job Fit"])


@router.post("", response_model=APIResponse[JobFitResponse])
async def calculate_job_fit(
    data: JobFitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = JobFitService(db)
    fit_response = await service.calculate_fit(user.id, data)
    return APIResponse(data=fit_response)

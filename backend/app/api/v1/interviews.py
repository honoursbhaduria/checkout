from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.schemas import (
    InterviewCreate, InterviewResponse, QuestionResponse,
    AnswerSubmitRequest, AnswerEvaluationResponse,
    InterviewReportResponse, PreparationPlanResponse, APIResponse,
    InterviewHistorySummary
)
from app.application.services.interview_service import InterviewService
from app.application.services.report_service import ReportService
from app.api.dependencies import get_current_user
from app.infrastructure.models.models import User

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.get("/history", response_model=APIResponse[InterviewHistorySummary])
async def get_interview_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    history = await service.get_interview_history(user.id)
    return APIResponse(data=history)


@router.post("", response_model=APIResponse[InterviewResponse], status_code=status.HTTP_201_CREATED)
async def create_interview(
    data: InterviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    interview = await service.create_interview(user.id, data)
    return APIResponse(data=interview)


@router.post("/{interview_id}/start", response_model=APIResponse[QuestionResponse])
async def start_interview(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    question = await service.start_interview(user.id, interview_id)
    return APIResponse(data=question)


@router.get("/{interview_id}/current-question", response_model=APIResponse[QuestionResponse])
async def get_current_question(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    question = await service.get_current_question(user.id, interview_id)
    return APIResponse(data=question)


@router.post("/{interview_id}/answers", response_model=APIResponse[AnswerEvaluationResponse])
async def submit_answer(
    interview_id: UUID,
    data: AnswerSubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    evaluation = await service.submit_answer(user.id, interview_id, data)
    return APIResponse(data=evaluation)


@router.post("/{interview_id}/complete", response_model=APIResponse[InterviewResponse])
async def complete_interview(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = InterviewService(db)
    interview = await service.complete_interview(user.id, interview_id)
    return APIResponse(data=interview)


@router.get("/{interview_id}/report", response_model=APIResponse[InterviewReportResponse])
async def get_interview_report(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    report = await service.get_or_generate_report(user.id, interview_id)
    return APIResponse(data=report)


@router.get("/{interview_id}/preparation", response_model=APIResponse[PreparationPlanResponse])
async def get_preparation_plan(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    plan = await service.get_or_generate_preparation_plan(user.id, interview_id)
    return APIResponse(data=plan)

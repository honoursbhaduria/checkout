from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.job_fit import router as job_fit_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.voice import router as voice_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(resumes_router)
api_router.include_router(job_fit_router)
api_router.include_router(interviews_router)
api_router.include_router(voice_router)
api_router.include_router(health_router)

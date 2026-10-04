import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import AppException
from app.core.redis import close_redis
from app.api.router import api_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI Interview Accelerator backend...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield
    logger.info("Shutting down backend services...")
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID & Latency Middleware
@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Standard Error Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "meta": {
                "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
                "version": settings.VERSION
            },
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "retryable": exc.retryable
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "meta": {
                "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
                "version": settings.VERSION
            },
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request payload failed schema validation.",
                "details": errors,
                "retryable": False
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "meta": {
                "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
                "version": settings.VERSION
            },
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "details": [],
                "retryable": True
            }
        }
    )


# Include API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs"
    }

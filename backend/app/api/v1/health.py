from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import get_redis_client

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness():
    return {"status": "alive", "service": "ai-interview-accelerator"}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    health_status = {
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check Database
    try:
        await db.execute(text("SELECT 1;"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"unhealthy: {str(e)}"

    is_ready = health_status["database"] == "healthy" and health_status["redis"] == "healthy"
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "dependencies": health_status
        }
    )

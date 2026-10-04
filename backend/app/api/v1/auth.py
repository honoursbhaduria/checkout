from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domain.schemas import (
    UserCreate, UserLogin, TokenResponse, RefreshRequest, 
    APIResponse, UserResponse
)
from app.application.services.auth_service import AuthService
from app.api.dependencies import get_current_user
from app.infrastructure.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token_response = await service.register(data)
    return APIResponse(data=token_response)


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token_response = await service.login(data)
    return APIResponse(data=token_response)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_tokens(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token_response = await service.refresh_tokens(data.refresh_token)
    return APIResponse(data=token_response)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    user_res = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at
    )
    return APIResponse(data=user_res)

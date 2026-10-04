import hashlib
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.models.models import User, RefreshToken
from app.domain.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationError, StateConflictError, ResourceNotFoundError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserCreate) -> TokenResponse:
        # Check if user exists
        stmt = select(User).where(User.email == data.email)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise StateConflictError("An account with this email already exists.")

        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            role="candidate"
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Issue tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        rt_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
        )
        self.db.add(rt_record)
        await self.db.commit()

        return TokenResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                created_at=user.created_at
            ),
            tokens={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }
        )

    async def login(self, data: UserLogin) -> TokenResponse:
        stmt = select(User).where(User.email == data.email)
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        rt_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
        )
        self.db.add(rt_record)
        await self.db.commit()

        return TokenResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                created_at=user.created_at
            ),
            tokens={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid or expired refresh token.")

        user_id = UUID(payload["sub"])
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False)
        )
        res = await self.db.execute(stmt)
        token_record = res.scalar_one_or_none()

        if not token_record:
            raise AuthenticationError("Refresh token was revoked or not found.")

        # Revoke old token
        token_record.revoked = True

        user_stmt = select(User).where(User.id == user_id)
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            raise ResourceNotFoundError("User", str(user_id))

        new_access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()

        new_rt_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=datetime.now(timezone.utc)
        )
        self.db.add(new_rt_record)
        await self.db.commit()

        return TokenResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                created_at=user.created_at
            ),
            tokens={
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600
            }
        )

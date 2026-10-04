from uuid import UUID
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError
from app.infrastructure.models.models import User


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Authorization header missing or invalid format.")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationError("Invalid or expired access token.")

    user_id_str = payload.get("sub")
    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise AuthenticationError("Malformed user identifier in token.")

    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User not found or account deactivated.")

    return user

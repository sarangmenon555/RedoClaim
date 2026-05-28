"""Auth dependencies for FastAPI routes."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    from app.models.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

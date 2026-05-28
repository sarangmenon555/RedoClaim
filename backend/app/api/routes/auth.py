"""Auth routes - JWT-based authentication."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import uuid
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Password hashing (argon2 — no 72-byte limit, more secure than bcrypt) ──
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── Request / Response schemas ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Password helpers ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ──────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        email=req.email,
        full_name=req.full_name,
        phone=req.phone,
        hashed_password=hash_password(req.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    logger.info(f"New user registered: {req.email}")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email + password, return JWT tokens."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account deactivated",
        )

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),   # rotate refresh token too
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(
        __import__("app.api.deps.auth", fromlist=["get_current_user"]).get_current_user
    ),
):
    """Return the currently authenticated user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }
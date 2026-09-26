"""Auth routes - JWT-based authentication."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import secrets
import uuid
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, UserRole
from app.api.deps.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Refresh-token cookie ──────────────────────────────────────────────────────
# The refresh token used to be handed back in the JSON body and stored in
# localStorage on the frontend, which makes it stealable by any XSS anywhere
# on the site. It now goes out ONLY as an httpOnly cookie — JS on the page
# can never read it — and the frontend's /auth/refresh call relies on the
# browser sending it automatically (credentials: "include").
REFRESH_COOKIE_NAME = "redoclaim_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


# ── Login brute-force protection ──────────────────────────────────────────────
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60  # 15 minutes


async def _get_redis():
    try:
        import redis.asyncio as aioredis
        return await aioredis.from_url(settings.REDIS_URL)
    except Exception:
        return None

# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── Request / Response schemas ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # refresh_token is intentionally NOT included here anymore — it is set
    # as an httpOnly cookie instead (see _set_refresh_cookie). Kept optional
    # for any non-browser client that genuinely needs it in-body (e.g. a
    # future mobile app without cookie support); it will be None on web.
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None  # en, hi, ml, ta, te, kn


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

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


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
        phone=req.phone.strip() or None if req.phone else None,
        hashed_password=hash_password(req.password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    logger.info(f"New user registered: {req.email}")

    refresh = create_refresh_token(str(user.id))
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email + password, return JWT tokens."""
    redis = await _get_redis()
    lockout_key = f"login_lockout:{form_data.username.lower()}"
    attempts_key = f"login_attempts:{form_data.username.lower()}"

    if redis:
        try:
            if await redis.get(lockout_key):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Try again in 15 minutes.",
                )
        except HTTPException:
            raise
        except Exception:
            redis = None  # fail open on redis errors, same policy as the rate-limit middleware

    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        if redis:
            try:
                attempts = await redis.incr(attempts_key)
                if attempts == 1:
                    await redis.expire(attempts_key, LOGIN_LOCKOUT_SECONDS)
                if attempts >= MAX_LOGIN_ATTEMPTS:
                    await redis.set(lockout_key, "1", ex=LOGIN_LOCKOUT_SECONDS)
                    logger.warning(f"Login lockout triggered for {form_data.username}")
            except Exception:
                pass
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

    if redis:
        try:
            await redis.delete(attempts_key, lockout_key)
        except Exception:
            pass

    logger.info(f"User logged in: {user.email}")

    refresh = create_refresh_token(str(user.id))
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token (from the httpOnly cookie) for a new access token."""
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    try:
        payload = jwt.decode(
            token,
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

    # Rotate the refresh token on every use so a leaked-but-unused old token
    # stops working the moment the legitimate client refreshes.
    new_refresh = create_refresh_token(user_id)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=create_access_token(user_id))


@router.post("/logout")
async def logout(response: Response):
    """Clear the refresh-token cookie. Access token expires naturally client-side."""
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request a password reset. Always returns a generic success message
    (never reveals whether the email exists) to avoid account enumeration.
    NOTE: no transactional email provider is wired up yet — the reset link
    is logged server-side for now. Plug in an email service (SES/Postmark/
    Resend) and send `reset_url` to the user instead of just logging it.
    """
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        reset_token = jwt.encode(
            {
                "sub": str(user.id),
                "type": "password_reset",
                "exp": datetime.utcnow() + timedelta(minutes=30),
                "jti": secrets.token_hex(8),
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        reset_url = f"/auth/reset-password?token={reset_token}"
        # TODO: send via email provider instead of logging once one is configured.
        logger.info(f"Password reset requested for {user.email}: {reset_url}")

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Complete a password reset using the token from /forgot-password."""
    try:
        payload = jwt.decode(req.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(req.new_password)
    await db.flush()
    logger.info(f"Password reset completed for {user.email}")
    return {"message": "Password has been reset. Please log in with your new password."}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "preferred_language": current_user.preferred_language,
    }


@router.patch("/me")
async def update_profile(
    req: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's full name and/or phone number."""
    if req.full_name is not None:
        full_name = req.full_name.strip()
        if not full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name cannot be empty",
            )
        current_user.full_name = full_name

    if req.phone is not None:
        current_user.phone = req.phone.strip() or None

    if req.preferred_language is not None:
        from app.services.language.sarvam_service import normalize_language
        current_user.preferred_language = normalize_language(req.preferred_language)

    await db.flush()
    logger.info(f"Profile updated: {current_user.email}")

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "preferred_language": current_user.preferred_language,
    }

@router.post("/me/password")
async def change_password(
    req: "ChangePasswordRequest",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )
    current_user.hashed_password = hash_password(req.new_password)
    await db.flush()
    logger.info(f"Password changed: {current_user.email}")
    return {"message": "Password changed successfully"}


@router.delete("/me")
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the current user's account and all associated data.
    Deletes: documents, claims, appeals, then the user record.
    """
    from sqlalchemy import delete as sql_delete
    from app.models.models import Document, Claim, Appeal

    user_id = current_user.id

    # Delete in dependency order: appeals → claims → documents → user
    await db.execute(sql_delete(Appeal).where(Appeal.owner_id == user_id))
    await db.execute(sql_delete(Claim).where(Claim.owner_id == user_id))
    await db.execute(sql_delete(Document).where(Document.owner_id == user_id))
    await db.delete(current_user)
    await db.flush()

    logger.info(f"Account deleted: {current_user.email}")
    return {"message": "Account and all associated data deleted successfully"}
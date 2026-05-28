"""Security middleware - rate limiting, audit logging, prompt injection guard."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import redis.asyncio as aioredis
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

# Prompt injection patterns - block attempts to override system prompts
INJECTION_PATTERNS = [
    r"ignore (previous|all|above|prior) instructions",
    r"you are now",
    r"act as (a different|an unrestricted|jailbreak)",
    r"system prompt",
    r"forget your (instructions|rules|training)",
    r"new persona",
    r"DAN mode",
    r"developer mode",
]
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# JWT token prefix used to extract user identity for per-user rate limiting
_BEARER_PREFIX = "Bearer "


def _extract_rate_limit_key(request: Request) -> str:
    """
    Prefer per-user keying (JWT sub) so that all Docker traffic from the same
    gateway IP (172.19.0.1) is NOT collapsed into a single bucket.
    Falls back to IP when the request is unauthenticated.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith(_BEARER_PREFIX):
        token = auth_header[len(_BEARER_PREFIX):]
        # Use the raw token as the key — no need to decode; we just want a
        # stable per-user identifier, not the claims.
        return f"user:{token[:64]}"  # truncate to keep Redis key sane
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiting per authenticated user (or IP) using Redis."""

    def __init__(self, app):
        super().__init__(app)
        self._redis = None

    async def get_redis(self):
        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(settings.REDIS_URL)
            except Exception:
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        # ── Always pass through ──────────────────────────────────
        # 1. Health check endpoint
        if request.url.path == "/api/health":
            return await call_next(request)

        # 2. OPTIONS preflight — never count against the limit.
        #    Browsers send these automatically; blocking them causes every
        #    real request to fail with a 429 on the *next* attempt.
        if request.method == "OPTIONS":
            return await call_next(request)

        redis = await self.get_redis()

        if redis:
            rate_key = _extract_rate_limit_key(request)
            window = int(time.time() // 60)
            key = f"rl:{rate_key}:{window}"

            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, 60)

                # Default limit from settings (e.g. 60 req/min)
                limit = settings.RATE_LIMIT_PER_MINUTE

                # Stricter limits for heavy endpoints — but still generous
                # enough for normal use (was 10, which is far too tight).
                if "/upload" in request.url.path:
                    limit = 30   # 30 uploads/min per user is plenty
                elif "/audit-rejection" in request.url.path:
                    limit = 20   # LLM-heavy; protect the Ollama instance
                elif "/analyze" in request.url.path:
                    limit = 20

                if count > limit:
                    logger.warning(
                        f"Rate limit hit | key={rate_key} | "
                        f"path={request.url.path} | count={count}/{limit}"
                    )
                    return JSONResponse(
                        {
                            "detail": "Rate limit exceeded. Please wait before retrying.",
                            "retry_after_seconds": 60,
                        },
                        status_code=429,
                        headers={"Retry-After": "60"},
                    )
            except Exception as e:
                logger.warning(f"Rate limit Redis error (failing open): {e}")
                # Fail open — don't block requests if Redis is down

        response = await call_next(request)
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all API calls for security audit trail."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)

        # Log sensitive operations
        sensitive_paths = ["/upload", "/analyze", "/appeals", "/auth", "/audit-rejection"]
        if any(p in request.url.path for p in sensitive_paths):
            logger.info(
                f"AUDIT | {request.method} {request.url.path} | "
                f"IP={request.client.host if request.client else 'unknown'} | "
                f"Status={response.status_code} | {duration}ms"
            )

        return response


def check_prompt_injection(text: str) -> bool:
    """Returns True if prompt injection is detected."""
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """Sanitize text before passing to LLM."""
    if not text:
        return ""
    text = text[:max_length]
    text = text.replace("\x00", "")
    return text.strip()
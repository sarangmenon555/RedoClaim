from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import documents, analysis, appeals, auth, claims, admin, timeline
from app.core.middleware import RateLimitMiddleware, AuditLogMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting RedoClaim API...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down RedoClaim API.")


app = FastAPI(
    title="RedoClaim API",
    description="AI-powered Insurance Rights & Claims Grievance Platform for India",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ─── SECURITY MIDDLEWARES ─────────────────────────────────────────
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditLogMiddleware)

# ─── CORS — added last so it is outermost, runs before everything ─
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ─── ROUTES ───────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(documents.router, prefix="/api/v1/documents",  tags=["Documents"])
app.include_router(analysis.router,  prefix="/api/v1/analysis",   tags=["Analysis"])
app.include_router(appeals.router,   prefix="/api/v1/appeals",    tags=["Appeals"])
app.include_router(claims.router,    prefix="/api/v1/claims",     tags=["Claims"])
app.include_router(timeline.router,  prefix="/api/v1/timeline",   tags=["Timeline"])
app.include_router(admin.router,     prefix="/api/v1/admin",      tags=["Admin"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "redoclaim"}


@app.get("/api/debug-cors")
async def debug_cors():
    return {"allowed_origins": settings.ALLOWED_ORIGINS}
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import json
import logging


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "RedoClaim"

    # Database — required, no default (set in Render env vars)
    DATABASE_URL: str

    # Redis (optional — used for rate limiting; falls back gracefully if absent)
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Groq API (primary LLM) ───────────────────────────────────
    # Required — set in Render env vars, never hardcode
    GROQ_API_KEY: str

    # ── Gemini API (embeddings only) ─────────────────────────────
    # Optional — only needed for RAG embeddings; set in Render env vars
    GEMINI_API_KEY: str = ""

    # Model assignments (free-tier Gemini 2.5 Flash)
    MODEL_EXTRACTION: str = "gemini-2.5-flash"
    MODEL_LEGAL: str = "gemini-2.5-flash"
    MODEL_DRAFTING: str = "gemini-2.5-flash"
    MODEL_SUMMARIZE: str = "gemini-2.5-flash"

    # Qdrant — required, set in Render env vars
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_POLICY_COLLECTION: str = "policy_chunks"
    QDRANT_IRDAI_COLLECTION: str = "irdai_regulations"
    QDRANT_REJECTION_COLLECTION: str = "rejection_patterns"

    # Storage (Supabase via boto3 / MinIO-compatible)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_DOCUMENTS: str = "redoclaim-documents"
    MINIO_BUCKET_REPORTS: str = "redoclaim-reports"
    MINIO_SECURE: bool = False

    # JWT Auth — required, set in Render env vars
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS — accepts a plain URL, comma-separated string, or JSON array
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "https://redoclaim.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip().strip("'\"")
            # Try JSON array first: ["url1", "url2"]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fall back to comma-separated: url1,url2
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # OCR — set PADDLEOCR_ENABLED=true in env only if you want PaddleOCR
    # Leave unset (defaults false) on Render to avoid cold-start model downloads
    # that kill background tasks
    PADDLEOCR_ENABLED: bool = False

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 20

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

logging.getLogger(__name__).info(f"CORS allowed origins: {settings.ALLOWED_ORIGINS}")
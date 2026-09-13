from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import json
import logging


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "RedoClaim"

    # Database — required, set in Render env vars
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── OpenAI API (LLM + embeddings) ──────────────────────────────
    # Required — set in Render env vars. Get one at platform.openai.com
    OPENAI_API_KEY: str

    # ── Sarvam AI (regional language translation) ─────────────────
    # Get your key at: https://dashboard.sarvam.ai/key-management
    # Powers Malayalam, Tamil, Telugu, Kannada, and Hindi support across
    # RedoClaim. Optional — regional language endpoints fall back to
    # returning original English text if unset.
    SARVAM_API_KEY: str = ""
    DEFAULT_LANGUAGE: str = "en"

    # Model assignments (OpenAI) — internal names kept for compatibility,
    # all resolve to gpt-5-nano via _MODEL_MAP in gemini_service.py
    MODEL_EXTRACTION: str = "gpt-5-nano"
    MODEL_LEGAL: str = "gpt-5-nano"
    MODEL_DRAFTING: str = "gpt-5-nano"
    MODEL_SUMMARIZE: str = "gpt-5-nano"

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

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "https://redoclaim.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip().strip("'\"")
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # OCR — leave unset on Render (defaults false) to avoid cold-start model downloads
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
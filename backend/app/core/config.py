from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import json


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "RedoClaim"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://redoclaim:redoclaim_secret@localhost:5432/redoclaim_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Models
    MODEL_EXTRACTION: str = "qwen2.5:7b"
    MODEL_LEGAL: str = "qwen2.5:7b"
    MODEL_DRAFTING: str = "mistral:7b"
    MODEL_SUMMARIZE: str = "qwen2.5:7b"
    MODEL_EMBEDDING: str = "nomic-embed-text"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_POLICY_COLLECTION: str = "policy_chunks"
    QDRANT_IRDAI_COLLECTION: str = "irdai_regulations"
    QDRANT_REJECTION_COLLECTION: str = "rejection_patterns"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_DOCUMENTS: str = "redoclaim-documents"
    MINIO_BUCKET_REPORTS: str = "redoclaim-reports"
    MINIO_SECURE: bool = False

    # JWT Auth
    JWT_SECRET: str = "change_this_to_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS — accepts either a JSON string or a real list
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-app.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip().strip("'\"")   # strip wrapping quotes shells may add
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # Fallback: treat as comma-separated  e.g. "http://a.com,http://b.com"
                return [o.strip() for o in v.split(",") if o.strip()]
        return v

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

# Fail-fast: confirm what's actually loaded at startup
import logging
logging.getLogger(__name__).info(f"CORS allowed origins: {settings.ALLOWED_ORIGINS}")
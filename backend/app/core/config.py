from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import json
import logging


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "RedoClaim"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://redoclaim:redoclaim_secret@localhost:5432/redoclaim_db"

    # Redis (optional — used for rate limiting; falls back gracefully if absent)
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Gemini API ────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # Model assignments (all free-tier Gemini models)
    MODEL_EXTRACTION: str = "gemini-2.0-flash-lite"   # fast + cheap for extraction
    MODEL_LEGAL: str = "gemini-2.0-flash"              # stronger reasoning for audit
    MODEL_DRAFTING: str = "gemini-2.0-flash"           # letter drafting
    MODEL_SUMMARIZE: str = "gemini-2.0-flash-lite"     # summaries

    # Qdrant
    QDRANT_URL: str = "https://09e2dda0-b0a8-4a22-a746-a3f3c297b066.eu-central-1-0.aws.cloud.qdrant.io"
    QDRANT_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NjA5YzNkMjItNjA5Yy00NTBmLWJjYjktNTU5YzM0MGZmYjk1In0.7aUuVhRX0ImCNlImvOE4Pcq9yE515YGgR5F67RTdOOk"
    QDRANT_POLICY_COLLECTION: str = "policy_chunks"
    QDRANT_IRDAI_COLLECTION: str = "irdai_regulations"
    QDRANT_REJECTION_COLLECTION: str = "rejection_patterns"

    # MinIO (file storage — swap for S3/Cloudflare R2 on Render/Vercel)
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
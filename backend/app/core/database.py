from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import ssl
import logging

logger = logging.getLogger(__name__)

# ----------------------------
# Engine
# ----------------------------
# Strip any ?ssl= or ?sslmode= query params from the URL — asyncpg
# requires SSL to be passed as connect_args, not as a URL parameter.
def _clean_db_url(url: str) -> tuple[str, dict]:
    connect_args = {}
    for param in ("?ssl=true", "&ssl=true", "?ssl=require", "&ssl=require",
                  "?sslmode=require", "&sslmode=require"):
        if param in url:
            url = url.replace(param, "")
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_ctx
            break
    return url, connect_args

_db_url, _connect_args = _clean_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    connect_args=_connect_args,
)

# ----------------------------
# Session Factory
# ----------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ----------------------------
# Base Model
# ----------------------------
class Base(DeclarativeBase):
    pass


# ----------------------------
# Initialize DB (create tables)
# ----------------------------
async def init_db():
    """
    Import all models so SQLAlchemy registers them,
    then create all tables.
    """
    import app.models  # noqa: ensures models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified.")


# ----------------------------
# Dependency: DB Session
# ----------------------------
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# ----------------------------
# Engine
# ----------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
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
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            "ALTER TABLE claims ADD COLUMN IF NOT EXISTS translated_reports JSON"
        )
    await engine.dispose()
    print("Done: translated_reports column ensured on claims table.")


if __name__ == "__main__":
    asyncio.run(main())
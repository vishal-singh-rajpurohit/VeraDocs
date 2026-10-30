import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config.settings import settings
from app.model.base import Base

logger = logging.getLogger("veradocs.database")

# Asynchronous engine with asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_pgvector_status() -> dict:
    """Check if PostgreSQL connection and pgvector extension are operational."""
    try:
        async with AsyncSessionLocal() as session:
            # Query pg_extension to check if vector is enabled
            result = await session.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            )
            row = result.first()
            if row:
                return {
                    "connected": True,
                    "pgvector_enabled": True,
                    "version": row[1],
                    "message": f"pgvector v{row[1]} is active and operational",
                }
            return {
                "connected": True,
                "pgvector_enabled": False,
                "version": None,
                "message": "Connected to PostgreSQL, but pgvector extension is not enabled",
            }
    except Exception as exc:
        logger.error(f"Failed to check pgvector status: {exc}")
        return {
            "connected": False,
            "pgvector_enabled": False,
            "version": None,
            "error": str(exc),
        }


async def init_db() -> None:
    """Initialize database extensions and schema tables on application startup."""
    try:
        async with engine.begin() as conn:
            # Ensure pgvector and uuid-ossp extensions exist
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            
            # Create all metadata tables (e.g. document embeddings)
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully with pgvector extension enabled.")
    except Exception as exc:
        logger.warning(
            f"Could not connect to database on startup ({exc}). "
            "Ensure the postgres container is running with pgvector."
        )

from collections.abc import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=10) if settings.database_url else None
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession) if engine else None


async def get_session() -> AsyncIterator[AsyncSession]:
    if SessionFactory is None:
        raise HTTPException(503, 'DATABASE_URL is not configured. Set it in backend/.env.')
    async with SessionFactory() as session:
        yield session


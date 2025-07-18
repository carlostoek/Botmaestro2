from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from .base import Base
from utils.config import Config

_engine = None
_sessionmaker = None

async def init_db():
    global _engine, _sessionmaker
    if _engine is None:
        _engine = create_async_engine(Config.DATABASE_URL, echo=False, poolclass=NullPool)
        async with _engine.begin() as conn:
            # SOLUCIÓN CLAVE: Pasar solo la función sin parámetros adicionales
            await conn.run_sync(Base.metadata.create_all)
    return _engine

async def get_session() -> AsyncSession:
    global _sessionmaker
    if _engine is None:
        await init_db()
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(bind=_engine, expire_on_commit=False)
    return _sessionmaker()

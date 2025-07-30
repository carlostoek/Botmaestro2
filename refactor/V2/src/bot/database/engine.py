"""Configuración del motor de base de datos."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from ..config import settings
from .base import Base

# Configurar el logger
logger = logging.getLogger(__name__)

# Crear el motor de base de datos
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    future=True,
)

# Crear el fabricador de sesiones
async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def init_db() -> None:
    """Inicializar la base de datos."""
    async with engine.begin() as conn:
        # Esto no crea las tablas en producción, sólo en desarrollo
        # En producción, se usarán migraciones Alembic
        if settings.DATABASE_ECHO:
            logger.info("Creating database tables from models...")
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Devuelve una sesión de base de datos."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.exception(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
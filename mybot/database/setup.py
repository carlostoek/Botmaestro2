import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
from .base import Base
from utils.config import Config

# Configuración del logger
logger = logging.getLogger(__name__)

# Variables globales para conexión y sesión
_engine = None
_sessionmaker = None

async def init_db():
    """Inicializa la conexión a la base de datos y crea las tablas si no existen"""
    global _engine, _sessionmaker
    
    try:
        if _engine is None:
            logger.info("Creando motor de base de datos...")
            
            # Verificar formato de la URL de conexión
            if not Config.DATABASE_URL.startswith("postgresql+asyncpg://"):
                logger.warning("Formato de DATABASE_URL puede ser incorrecto. Debe comenzar con 'postgresql+asyncpg://'")
            
            _engine = create_async_engine(
               

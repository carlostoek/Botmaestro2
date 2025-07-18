from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from .base import Base
from utils.config import Config
import logging

# Configurar logger
logger = logging.getLogger(__name__)

_engine = None
_sessionmaker = None

async def init_db():
    global _engine, _sessionmaker
    try:
        if _engine is None:
            logger.info("Creando motor de base de datos...")
            _engine = create_async_engine(
                Config.DATABASE_URL, 
                echo=False, 
                poolclass=NullPool
            )
            
            logger.info("Creando tablas...")
            async with _engine.begin() as conn:
                # Función wrapper para creación segura de tablas
                def create_tables(sync_conn):
                    Base.metadata.create_all(bind=sync_conn)
                
                await conn.run_sync(create_tables)
                logger.info("Tablas creadas exitosamente")
        
        return _engine
    except Exception as e:
        logger.critical(f"Error crítico inicializando DB: {e}")
        # Re-raise para manejo superior
        raise

async def get_session() -> AsyncSession:
    global _sessionmaker
    try:
        if _engine is None:
            await init_db()
        
        if _sessionmaker is None:
            _sessionmaker = async_sessionmaker(
                bind=_engine, 
                expire_on_commit=False,
                class_=AsyncSession
            )
        
        return _sessionmaker()
    except Exception as e:
        logger.error(f"Error obteniendo sesión de DB: {e}")
        raise
        

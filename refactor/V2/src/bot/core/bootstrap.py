"""Bootstrap del bot, inicializa todos los componentes."""

import logging
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from ..config import settings
from ..database import init_db
from .bot import setup_bot
from .middleware import setup_middlewares
from .di import setup_di_container
from .handlers import setup_handlers
from .errors import setup_error_handlers
from .scheduler import setup_scheduler

logger = structlog.get_logger()

async def bootstrap():
    """Inicializa todos los componentes del bot."""
    logger.info("Inicializando componentes del bot")
    
    # Inicializar base de datos
    logger.info("Inicializando base de datos")
    await init_db()
    
    # Crear bot y dispatcher
    logger.info("Creando bot y dispatcher")
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Configurar contenedor de dependencias
    logger.info("Configurando contenedor de dependencias")
    container = await setup_di_container(bot, dp)
    dp["di"] = container
    
    # Configurar bot
    logger.info("Configurando bot")
    await setup_bot(bot)
    
    # Configurar manejadores de errores
    logger.info("Configurando manejadores de errores")
    setup_error_handlers(dp)
    
    # Configurar middlewares
    logger.info("Configurando middlewares")
    setup_middlewares(dp)
    
    # Configurar manejadores
    logger.info("Configurando manejadores")
    setup_handlers(dp)
    
    # Configurar programador de tareas
    logger.info("Configurando programador de tareas")
    scheduler = setup_scheduler()
    
    try:
        # Iniciar programador de tareas
        if settings.ENABLE_BACKGROUND_TASKS:
            logger.info("Iniciando programador de tareas")
            scheduler.start()
        
        # Iniciar polling
        logger.info("Iniciando polling")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Detener programador de tareas
        if settings.ENABLE_BACKGROUND_TASKS:
            logger.info("Deteniendo programador de tareas")
            scheduler.shutdown(wait=True)
        
        # Cerrar sesión del bot
        logger.info("Cerrando sesión del bot")
        await bot.session.close()
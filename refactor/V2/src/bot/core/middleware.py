"""Configuración de middlewares."""

import structlog
from aiogram import Dispatcher

from ..middlewares.database import DatabaseMiddleware
from ..middlewares.user import UserMiddleware
from ..middlewares.throttling import ThrottlingMiddleware
from ..middlewares.emotional import EmotionalMiddleware
from ..middlewares.points import PointsMiddleware

logger = structlog.get_logger()

def setup_middlewares(dp: Dispatcher) -> None:
    """Configura todos los middlewares."""
    
    # Middleware de base de datos (debe ser el primero para proporcionar la sesión)
    dp.update.middleware(DatabaseMiddleware())
    logger.info("Middleware de base de datos configurado")
    
    # Middleware de usuarios (segundo para garantizar que el usuario existe)
    dp.update.middleware(UserMiddleware())
    logger.info("Middleware de usuarios configurado")
    
    # Middleware de throttling (limitar mensajes)
    dp.message.middleware(ThrottlingMiddleware())
    logger.info("Middleware de throttling configurado")
    
    # Middleware de sistema emocional
    dp.message.middleware(EmotionalMiddleware())
    logger.info("Middleware emocional configurado")
    
    # Middleware de puntos (besitos)
    dp.message.middleware(PointsMiddleware())
    logger.info("Middleware de puntos configurado")
    
    logger.info("Todos los middlewares configurados")
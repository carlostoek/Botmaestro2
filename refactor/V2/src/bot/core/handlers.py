"""Configuración de manejadores de eventos."""

import structlog
from aiogram import Dispatcher

from ..handlers.user import register_user_handlers
from ..handlers.admin import register_admin_handlers
from ..handlers.vip import register_vip_handlers

logger = structlog.get_logger()

def setup_handlers(dp: Dispatcher) -> None:
    """Configura todos los manejadores de eventos."""
    
    # Registrar manejadores de usuarios regulares
    register_user_handlers(dp)
    logger.info("Manejadores de usuarios registrados")
    
    # Registrar manejadores de administradores
    register_admin_handlers(dp)
    logger.info("Manejadores de administradores registrados")
    
    # Registrar manejadores de usuarios VIP
    register_vip_handlers(dp)
    logger.info("Manejadores de usuarios VIP registrados")
    
    logger.info("Todos los manejadores configurados")
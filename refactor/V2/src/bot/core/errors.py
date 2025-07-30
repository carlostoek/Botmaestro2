"""Manejo centralizado de errores."""

import structlog
from aiogram import Dispatcher
from aiogram.types import ErrorEvent, Update

logger = structlog.get_logger()

class ErrorHandler:
    """Manejador centralizado de errores."""
    
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        
    async def handle_error(self, event: ErrorEvent):
        """Maneja errores del dispatcher."""
        exception = event.exception
        update = event.update
        
        # Datos para el log
        log_data = {
            "exception_type": type(exception).__name__,
            "exception_msg": str(exception),
            "update_id": getattr(update, "update_id", None) if update else None,
            "chat_id": getattr(update.message, "chat", {}).get("id") if update and update.message else None,
            "user_id": getattr(update.message, "from_user", {}).get("id") if update and update.message else None,
        }
        
        # Registrar el error
        logger.error("Error al procesar update", **log_data, exc_info=exception)
        
        # Manejar tipos específicos de errores
        if isinstance(exception, (ConnectionError, TimeoutError)):
            logger.critical("Error crítico de conexión detectado")
            # Notificar a los administradores, etc.
            
        return True  # Marcar el error como manejado

def setup_error_handlers(dp: Dispatcher) -> None:
    """Configura los manejadores de errores."""
    error_handler = ErrorHandler(dp)
    
    # Registrar manejador de errores
    dp.errors.register(error_handler.handle_error)
    
    logger.info("Manejadores de errores configurados")
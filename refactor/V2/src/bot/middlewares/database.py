"""Middleware para gestionar sesiones de base de datos."""

from typing import Any, Awaitable, Callable, Dict
import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

logger = structlog.get_logger()

class DatabaseMiddleware(BaseMiddleware):
    """Middleware que proporciona una sesión de base de datos a los manejadores."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Ejecuta el middleware."""
        # Crear sesión de base de datos
        async for session in get_session():
            # Añadir sesión a los datos
            data["session"] = session
            
            try:
                # Ejecutar el siguiente middleware o el manejador
                return await handler(event, data)
            except Exception as e:
                # Hacer rollback en caso de error
                await session.rollback()
                logger.exception("Error en el manejador", error=str(e))
                raise
            finally:
                # Cerrar sesión
                await session.close()
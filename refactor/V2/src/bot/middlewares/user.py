"""Middleware para gestionar usuarios."""

from typing import Any, Awaitable, Callable, Dict
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.user import UserService

logger = structlog.get_logger()

class UserMiddleware(BaseMiddleware):
    """Middleware que garantiza que el usuario existe en la base de datos."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Ejecuta el middleware."""
        # Obtener usuario de Telegram
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        # Si hay usuario y sesión de base de datos
        if user and "session" in data:
            session: AsyncSession = data["session"]
            
            # Crear o actualizar usuario
            user_service = UserService()
            user_data = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code
            }
            
            try:
                # Crear o actualizar usuario
                db_user = await user_service.create_or_update_user(
                    session, user.id, user_data
                )
                
                # Añadir usuario a los datos
                data["db_user"] = db_user
                
                # Actualizar última actividad
                await user_service.update(
                    session, user.id, {"last_activity_at": "NOW()"}
                )
                
                # Commit para guardar cambios
                await session.commit()
            except Exception as e:
                logger.error("Error al gestionar usuario", error=str(e), user_id=user.id)
                await session.rollback()
        
        # Ejecutar el siguiente middleware o el manejador
        return await handler(event, data)
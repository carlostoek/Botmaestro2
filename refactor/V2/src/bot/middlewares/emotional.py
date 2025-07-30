"""Middleware para procesar el sistema emocional."""

from typing import Any, Awaitable, Callable, Dict
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.emotional import EmotionalService
from ..config import settings

logger = structlog.get_logger()

class EmotionalMiddleware(BaseMiddleware):
    """Middleware que procesa el sistema emocional para cada mensaje."""
    
    def __init__(self, character_name: str = "Diana"):
        """
        Inicializa el middleware.
        
        Args:
            character_name: Nombre del personaje principal.
        """
        self.character_name = character_name
        self.emotional_service = EmotionalService()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Ejecuta el middleware."""
        # Solo aplicar a mensajes de texto
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)
        
        # Verificar si el sistema emocional está habilitado
        if not settings.ENABLE_EMOTIONAL_SYSTEM:
            return await handler(event, data)
        
        # Obtener usuario y sesión
        user_id = event.from_user.id if event.from_user else None
        session = data.get("session")
        
        # Procesar emoción solo si tenemos usuario y sesión
        if user_id and isinstance(session, AsyncSession):
            try:
                # Procesar mensaje
                emotional_result = await self.emotional_service.process_message(
                    session, user_id, self.character_name, event.text
                )
                
                # Añadir resultado a los datos
                data["emotional_state"] = emotional_result
                
                # Commit para guardar cambios
                await session.commit()
            except Exception as e:
                logger.error(
                    "Error al procesar estado emocional", 
                    error=str(e), 
                    user_id=user_id
                )
                await session.rollback()
        
        # Ejecutar el siguiente middleware o el manejador
        return await handler(event, data)
"""Middleware para gestionar puntos (besitos)."""

from typing import Any, Awaitable, Callable, Dict
import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ReactionTypeUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.gamification import GamificationService
from ..config.constants import (
    DEFAULT_POINTS_PER_MESSAGE,
    DEFAULT_POINTS_PER_REACTION,
    DEFAULT_POINTS_PER_POLL,
    VIP_POINTS_MULTIPLIER
)

logger = structlog.get_logger()

class PointsMiddleware(BaseMiddleware):
    """Middleware que otorga puntos por interacciones."""
    
    def __init__(self):
        """Inicializa el middleware."""
        self.gamification_service = GamificationService()
    
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        """Ejecuta el middleware."""
        # Obtener sesión
        session = data.get("session")
        if not isinstance(session, AsyncSession):
            return await handler(event, data)
        
        # Obtener usuario de la base de datos
        db_user = data.get("db_user")
        
        # Ejecutar el siguiente middleware o el manejador
        result = await handler(event, data)
        
        # Procesar puntos después de manejar el evento
        if db_user:
            try:
                # Determinar tipo de evento y puntos a otorgar
                points = 0
                source = ""
                description = ""
                
                if isinstance(event, Message):
                    # Puntos por mensaje
                    if event.text:
                        points = DEFAULT_POINTS_PER_MESSAGE
                        source = "message"
                        description = "Mensaje enviado"
                    
                    # Puntos por encuesta
                    elif event.poll:
                        points = DEFAULT_POINTS_PER_POLL
                        source = "poll"
                        description = "Encuesta creada"
                
                elif isinstance(event, ReactionTypeUpdated):
                    # Puntos por reacción
                    points = DEFAULT_POINTS_PER_REACTION
                    source = "reaction"
                    description = "Reacción añadida"
                
                # Aplicar multiplicador VIP si corresponde
                if db_user.is_vip:
                    points *= VIP_POINTS_MULTIPLIER
                
                # Otorgar puntos si hay puntos a otorgar
                if points > 0:
                    await self.gamification_service.award_points(
                        session, db_user.id, points, source, description
                    )
                    
                    # Commit para guardar cambios
                    await session.commit()
            except Exception as e:
                logger.error(
                    "Error al otorgar puntos", 
                    error=str(e), 
                    user_id=db_user.id
                )
                await session.rollback()
        
        return result
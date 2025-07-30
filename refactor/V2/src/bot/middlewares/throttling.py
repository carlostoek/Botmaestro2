"""Middleware para limitar la frecuencia de mensajes."""

from typing import Any, Awaitable, Callable, Dict
import structlog
import asyncio
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

logger = structlog.get_logger()

class ThrottlingMiddleware(BaseMiddleware):
    """Middleware para limitar la frecuencia de mensajes de un usuario."""
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Inicializa el middleware.
        
        Args:
            rate_limit: Tiempo mínimo entre mensajes en segundos.
        """
        self.rate_limit = rate_limit
        self.cache = TTLCache(maxsize=10000, ttl=60)  # Cache con TTL de 60 segundos
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Ejecuta el middleware."""
        # Solo aplicar a mensajes
        if not isinstance(event, Message):
            return await handler(event, data)
        
        # Obtener usuario
        user_id = event.from_user.id if event.from_user else None
        
        if user_id:
            # Verificar si el usuario está en el caché
            last_time = self.cache.get(user_id)
            current_time = datetime.now()
            
            if last_time:
                # Calcular tiempo transcurrido
                delta = (current_time - last_time).total_seconds()
                
                # Si no ha pasado suficiente tiempo
                if delta < self.rate_limit:
                    # Esperar el tiempo restante
                    await asyncio.sleep(self.rate_limit - delta)
            
            # Actualizar tiempo en caché
            self.cache[user_id] = current_time
        
        # Ejecutar el siguiente middleware o el manejador
        return await handler(event, data)
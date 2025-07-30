"""Contenedor de inyección de dependencias."""

from typing import Dict, Type, TypeVar, Any, Optional
import structlog
from aiogram import Bot, Dispatcher

from ..services.user import UserService
from ..services.emotional import EmotionalService
from ..services.narrative import NarrativeService
from ..services.gamification import GamificationService

T = TypeVar('T')

logger = structlog.get_logger()

class Container:
    """Contenedor de inyección de dependencias."""
    
    def __init__(self):
        self._services: Dict[Type[Any], Any] = {}
        
    def register(self, service_type: Type[T], instance: T) -> None:
        """Registra una instancia de servicio."""
        self._services[service_type] = instance
        
    def resolve(self, service_type: Type[T]) -> Optional[T]:
        """Resuelve una instancia de servicio."""
        return self._services.get(service_type)

async def setup_di_container(bot: Bot, dp: Dispatcher) -> Container:
    """Configura el contenedor de inyección de dependencias."""
    container = Container()
    
    # Registrar servicios básicos
    container.register(Bot, bot)
    container.register(Dispatcher, dp)
    
    # Crear servicios de aplicación
    user_service = UserService()
    emotional_service = EmotionalService()
    narrative_service = NarrativeService()
    gamification_service = GamificationService()
    
    # Registrar servicios de aplicación
    container.register(UserService, user_service)
    container.register(EmotionalService, emotional_service)
    container.register(NarrativeService, narrative_service)
    container.register(GamificationService, gamification_service)
    
    logger.info("Contenedor de inyección de dependencias configurado")
    
    return container
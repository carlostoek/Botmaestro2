"""Servicio para el sistema narrativo."""

from typing import Optional, Dict, Any, List, Tuple
import structlog
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, desc, func

from .base import BaseService
from .emotional import EmotionalService
from ..database.models.narrative import (
    StoryFragment,
    NarrativeChoice, 
    UserNarrativeState,
    EmotionalNarrativeTrigger
)

logger = structlog.get_logger()

class NarrativeService:
    """Servicio para gestionar el sistema narrativo."""
    
    def __init__(self):
        self.logger = structlog.get_logger(service="NarrativeService")
        self.fragment_service = StoryFragmentService()
        self.choice_service = NarrativeChoiceService()
        self.state_service = UserNarrativeStateService()
        self.trigger_service = NarrativeTriggerService()
    
    async def get_current_fragment(
        self, session: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Obtiene el fragmento narrativo actual del usuario."""
        self.logger.debug("Obteniendo fragmento actual", user_id=user_id)
        
        # Obtener estado narrativo del usuario
        state = await self.state_service.get_by_user(session, user_id)
        
        # Si no existe, crear uno nuevo y asignar fragmento inicial
        if not state or not state.current_fragment_key:
            self.logger.info("Estado narrativo no encontrado, creando nuevo", user_id=user_id)
            
            # Obtener fragmento inicial
            initial_fragment = await self.fragment_service.get_initial_fragment(session)
            if not initial_fragment:
                self.logger.error("No se encontró fragmento inicial")
                raise ValueError("No se encontró fragmento inicial")
            
            # Crear estado narrativo
            if not state:
                state = await self.state_service.create_initial_state(
                    session, user_id, initial_fragment.key
                )
            else:
                await self.state_service.update_current_fragment(
                    session, state.id, initial_fragment.key
                )
                state = await self.state_service.get_by_user(session, user_id)
            
            # Marcar fragmento como visitado
            await self.state_service.add_visited_fragment(
                session, state.id, initial_fragment.key
            )
        
        # Obtener fragmento actual
        fragment = await self.fragment_service.get_by_key(
            session, state.current_fragment_key
        )
        
        if not fragment:
            self.logger.error(
                "Fragmento no encontrado", 
                user_id=user_id, 
                fragment_key=state.current_fragment_key
            )
            raise ValueError(f"Fragmento {state.current_fragment_key} no encontrado")
        
        # Obtener opciones disponibles
        choices = await self.choice_service.get_by_fragment(
            session, fragment.key, user_id
        )
        
        # Formatear respuesta
        result = {
            "fragment": {
                "key": fragment.key,
                "title": fragment.title,
                "character": fragment.character,
                "text": fragment.text,
                "tags": fragment.tags,
                "reward_besitos": fragment.reward_besitos,
                "reward_items": fragment.reward_items
            },
            "choices": [
                {
                    "id": choice.id,
                    "text": choice.text,
                    "target_fragment_key": choice.target_fragment_key,
                    "points_change": choice.points_change,
                    "relationship_change": choice.relationship_change
                }
                for choice in choices
            ],
            "state": {
                "visited_fragments": state.visited_fragments,
                "narrative_items": state.narrative_items
            }
        }
        
        return result
    
    async def make_choice(
        self, session: AsyncSession, user_id: int, choice_id: int
    ) -> Dict[str, Any]:
        """Procesa la elección del usuario y avanza la narrativa."""
        self.logger.debug("Procesando elección", user_id=user_id, choice_id=choice_id)
        
        # Obtener la elección
        choice = await self.choice_service.get_by_id(session, choice_id)
        if not choice:
            self.logger.error("Elección no encontrada", choice_id=choice_id)
            raise ValueError(f"Elección {choice_id} no encontrada")
        
        # Obtener estado narrativo del usuario
        state = await self.state_service.get_by_user(session, user_id)
        if not state:
            self.logger.error("Estado narrativo no encontrado", user_id=user_id)
            raise ValueError(f"Estado narrativo para usuario {user_id} no encontrado")
        
        # Verificar que la elección corresponde al fragmento actual
        if choice.fragment_key != state.current_fragment_key:
            self.logger.error(
                "La elección no corresponde al fragmento actual",
                choice_fragment=choice.fragment_key,
                current_fragment=state.current_fragment_key
            )
            raise ValueError("La elección no corresponde al fragmento actual")
        
        # Obtener fragmento destino
        target_fragment = await self.fragment_service.get_by_key(
            session, choice.target_fragment_key
        )
        if not target_fragment:
            self.logger.error(
                "Fragmento destino no encontrado", 
                target_key=choice.target_fragment_key
            )
            raise ValueError(f"Fragmento destino {choice.target_fragment_key} no encontrado")
        
        # Registrar decisión
        decisions = state.decisions_made.copy() if state.decisions_made else {}
        decisions[choice.fragment_key] = choice.id
        await self.state_service.update(
            session, state.id, {"decisions_made": decisions}
        )
        
        # Actualizar fragmento actual
        await self.state_service.update_current_fragment(
            session, state.id, target_fragment.key
        )
        
        # Marcar fragmento como visitado
        await self.state_service.add_visited_fragment(
            session, state.id, target_fragment.key
        )
        
        # Procesar efectos emocionales si los hay
        if choice.emotional_impacts:
            # Aquí se integraría con el sistema emocional
            # Esto sería implementado por el EmotionalSystem Agent
            pass
        
        # Procesar disparadores emocionales del fragmento
        triggers = await self.trigger_service.get_by_fragment(
            session, target_fragment.key
        )
        
        # Recargamos el estado después de las actualizaciones
        state = await self.state_service.get_by_user(session, user_id)
        
        # Obtener elecciones para el nuevo fragmento
        new_choices = await self.choice_service.get_by_fragment(
            session, target_fragment.key, user_id
        )
        
        # Formatear respuesta
        result = {
            "fragment": {
                "key": target_fragment.key,
                "title": target_fragment.title,
                "character": target_fragment.character,
                "text": target_fragment.text,
                "tags": target_fragment.tags,
                "reward_besitos": target_fragment.reward_besitos,
                "reward_items": target_fragment.reward_items
            },
            "choices": [
                {
                    "id": c.id,
                    "text": c.text,
                    "target_fragment_key": c.target_fragment_key,
                    "points_change": c.points_change,
                    "relationship_change": c.relationship_change
                }
                for c in new_choices
            ],
            "state": {
                "visited_fragments": state.visited_fragments,
                "narrative_items": state.narrative_items
            },
            "triggers": [
                {
                    "id": t.id,
                    "character_name": t.character_name,
                    "trigger_type": t.trigger_type
                }
                for t in triggers
            ]
        }
        
        return result
    
    async def get_narrative_progress(
        self, session: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Obtiene el progreso narrativo del usuario."""
        self.logger.debug("Obteniendo progreso narrativo", user_id=user_id)
        
        # Obtener estado narrativo del usuario
        state = await self.state_service.get_by_user(session, user_id)
        if not state:
            self.logger.info("Estado narrativo no encontrado, creando nuevo", user_id=user_id)
            # Obtener fragmento inicial
            initial_fragment = await self.fragment_service.get_initial_fragment(session)
            if not initial_fragment:
                self.logger.error("No se encontró fragmento inicial")
                return {"progress": 0, "fragments_visited": 0, "total_fragments": 0}
            
            # Crear estado narrativo
            state = await self.state_service.create_initial_state(
                session, user_id, initial_fragment.key
            )
        
        # Obtener total de fragmentos
        total_fragments = await self.fragment_service.count_fragments(session)
        
        # Calcular progreso
        fragments_visited = len(state.visited_fragments) if state.visited_fragments else 0
        progress = (fragments_visited / total_fragments) * 100 if total_fragments > 0 else 0
        
        # Obtener datos adicionales
        current_fragment = await self.fragment_service.get_by_key(
            session, state.current_fragment_key
        ) if state.current_fragment_key else None
        
        # Formatear respuesta
        result = {
            "progress": progress,
            "fragments_visited": fragments_visited,
            "total_fragments": total_fragments,
            "current_fragment": {
                "key": current_fragment.key,
                "title": current_fragment.title,
                "character": current_fragment.character
            } if current_fragment else None,
            "narrative_items": state.narrative_items or {},
            "visited_fragments": state.visited_fragments or []
        }
        
        return result
    
    async def reset_narrative(
        self, session: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Reinicia la narrativa del usuario."""
        self.logger.debug("Reiniciando narrativa", user_id=user_id)
        
        # Obtener estado narrativo del usuario
        state = await self.state_service.get_by_user(session, user_id)
        
        # Obtener fragmento inicial
        initial_fragment = await self.fragment_service.get_initial_fragment(session)
        if not initial_fragment:
            self.logger.error("No se encontró fragmento inicial")
            raise ValueError("No se encontró fragmento inicial")
        
        # Si existe el estado, actualizarlo
        if state:
            # Guardar elementos narrativos
            narrative_items = state.narrative_items
            
            # Reiniciar estado
            await self.state_service.update(
                session, state.id, {
                    "current_fragment_key": initial_fragment.key,
                    "visited_fragments": [initial_fragment.key],
                    "decisions_made": {},
                    "narrative_variables": {}
                }
            )
        else:
            # Crear nuevo estado
            state = await self.state_service.create_initial_state(
                session, user_id, initial_fragment.key
            )
            narrative_items = {}
        
        # Formatear respuesta
        result = {
            "fragment": {
                "key": initial_fragment.key,
                "title": initial_fragment.title,
                "character": initial_fragment.character,
                "text": initial_fragment.text
            },
            "state": {
                "visited_fragments": [initial_fragment.key],
                "narrative_items": narrative_items
            },
            "message": "Narrativa reiniciada correctamente"
        }
        
        return result
    
    async def add_narrative_item(
        self, session: AsyncSession, user_id: int, item_key: str, quantity: int = 1
    ) -> Dict[str, Any]:
        """Añade un elemento narrativo al inventario del usuario."""
        self.logger.debug("Añadiendo elemento narrativo", user_id=user_id, item_key=item_key)
        
        # Obtener estado narrativo del usuario
        state = await self.state_service.get_by_user(session, user_id)
        if not state:
            self.logger.error("Estado narrativo no encontrado", user_id=user_id)
            raise ValueError(f"Estado narrativo para usuario {user_id} no encontrado")
        
        # Añadir elemento
        items = state.narrative_items.copy() if state.narrative_items else {}
        current_quantity = items.get(item_key, 0)
        items[item_key] = current_quantity + quantity
        
        await self.state_service.update(
            session, state.id, {"narrative_items": items}
        )
        
        # Formatear respuesta
        result = {
            "item_key": item_key,
            "quantity_added": quantity,
            "total_quantity": items[item_key],
            "all_items": items
        }
        
        return result


class StoryFragmentService(BaseService[StoryFragment]):
    """Servicio para gestionar fragmentos de historia."""
    
    def __init__(self):
        super().__init__(StoryFragment)
    
    async def get_by_key(
        self, session: AsyncSession, fragment_key: str
    ) -> Optional[StoryFragment]:
        """Obtiene un fragmento por su clave."""
        self.logger.debug("Obteniendo fragmento por clave", key=fragment_key)
        
        query = select(StoryFragment).where(StoryFragment.key == fragment_key)
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_initial_fragment(
        self, session: AsyncSession
    ) -> Optional[StoryFragment]:
        """Obtiene el fragmento inicial de la narrativa."""
        self.logger.debug("Obteniendo fragmento inicial")
        
        # Por convención, el fragmento inicial tiene la clave "start"
        return await self.get_by_key(session, "start")
    
    async def count_fragments(
        self, session: AsyncSession
    ) -> int:
        """Cuenta el número total de fragmentos."""
        self.logger.debug("Contando fragmentos")
        
        result = await session.execute(select(func.count()).select_from(StoryFragment))
        return result.scalar()
    
    async def get_fragments_by_tag(
        self, session: AsyncSession, tag: str
    ) -> List[StoryFragment]:
        """Obtiene fragmentos por etiqueta."""
        self.logger.debug("Obteniendo fragmentos por etiqueta", tag=tag)
        
        query = select(StoryFragment).where(
            StoryFragment.tags.contains([tag])
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_fragments_by_character(
        self, session: AsyncSession, character: str
    ) -> List[StoryFragment]:
        """Obtiene fragmentos por personaje."""
        self.logger.debug("Obteniendo fragmentos por personaje", character=character)
        
        query = select(StoryFragment).where(
            StoryFragment.character == character
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())


class NarrativeChoiceService(BaseService[NarrativeChoice]):
    """Servicio para gestionar elecciones narrativas."""
    
    def __init__(self):
        super().__init__(NarrativeChoice)
    
    async def get_by_fragment(
        self, session: AsyncSession, fragment_key: str, user_id: Optional[int] = None
    ) -> List[NarrativeChoice]:
        """Obtiene elecciones disponibles para un fragmento."""
        self.logger.debug("Obteniendo elecciones por fragmento", fragment_key=fragment_key)
        
        query = select(NarrativeChoice).where(
            NarrativeChoice.fragment_key == fragment_key
        )
        
        result = await session.execute(query)
        choices = list(result.scalars().all())
        
        # Si se proporciona user_id, podríamos filtrar por requisitos
        # Esto sería implementado por el NarrativeService Agent
        
        return choices


class UserNarrativeStateService(BaseService[UserNarrativeState]):
    """Servicio para gestionar estados narrativos de usuarios."""
    
    def __init__(self):
        super().__init__(UserNarrativeState)
    
    async def get_by_user(
        self, session: AsyncSession, user_id: int
    ) -> Optional[UserNarrativeState]:
        """Obtiene el estado narrativo de un usuario."""
        self.logger.debug("Obteniendo estado narrativo por usuario", user_id=user_id)
        
        query = select(UserNarrativeState).where(
            UserNarrativeState.user_id == user_id
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def create_initial_state(
        self, session: AsyncSession, user_id: int, initial_fragment_key: str
    ) -> UserNarrativeState:
        """Crea un estado narrativo inicial para un usuario."""
        self.logger.debug(
            "Creando estado narrativo inicial", 
            user_id=user_id, 
            fragment_key=initial_fragment_key
        )
        
        state_data = {
            "user_id": user_id,
            "current_fragment_key": initial_fragment_key,
            "visited_fragments": [initial_fragment_key],
            "decisions_made": {},
            "narrative_items": {},
            "narrative_variables": {}
        }
        
        state = await self.create(session, state_data)
        return state
    
    async def update_current_fragment(
        self, session: AsyncSession, state_id: int, fragment_key: str
    ) -> None:
        """Actualiza el fragmento actual de un estado narrativo."""
        self.logger.debug(
            "Actualizando fragmento actual", 
            state_id=state_id, 
            fragment_key=fragment_key
        )
        
        await self.update(session, state_id, {"current_fragment_key": fragment_key})
    
    async def add_visited_fragment(
        self, session: AsyncSession, state_id: int, fragment_key: str
    ) -> None:
        """Añade un fragmento a la lista de fragmentos visitados."""
        self.logger.debug(
            "Añadiendo fragmento visitado", 
            state_id=state_id, 
            fragment_key=fragment_key
        )
        
        state = await self.get_by_id(session, state_id)
        if not state:
            self.logger.error("Estado narrativo no encontrado", state_id=state_id)
            return
        
        visited = state.visited_fragments.copy() if state.visited_fragments else []
        if fragment_key not in visited:
            visited.append(fragment_key)
            await self.update(session, state_id, {"visited_fragments": visited})


class NarrativeTriggerService(BaseService[EmotionalNarrativeTrigger]):
    """Servicio para gestionar disparadores emocionales narrativos."""
    
    def __init__(self):
        super().__init__(EmotionalNarrativeTrigger)
    
    async def get_by_fragment(
        self, session: AsyncSession, fragment_key: str
    ) -> List[EmotionalNarrativeTrigger]:
        """Obtiene disparadores para un fragmento."""
        self.logger.debug("Obteniendo disparadores por fragmento", fragment_key=fragment_key)
        
        query = select(EmotionalNarrativeTrigger).where(
            EmotionalNarrativeTrigger.fragment_key == fragment_key
        ).order_by(EmotionalNarrativeTrigger.priority.desc())
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_character(
        self, session: AsyncSession, character_name: str
    ) -> List[EmotionalNarrativeTrigger]:
        """Obtiene disparadores para un personaje."""
        self.logger.debug("Obteniendo disparadores por personaje", character=character_name)
        
        query = select(EmotionalNarrativeTrigger).where(
            EmotionalNarrativeTrigger.character_name == character_name
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.narrative import NarrativeFragment, UserStoryState
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
import logging

logger = logging.getLogger(__name__)

class NarrativeEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_fragment(self, fragment_id: str) -> NarrativeFragment:
        """Obtiene un fragmento narrativo por su ID"""
        result = await self.session.execute(
            select(NarrativeFragment).filter_by(fragment_id=fragment_id)
        fragment = result.scalars().first()
        if not fragment:
            raise NoResultFound(f"Fragmento {fragment_id} no encontrado")
        return fragment
    
    async def get_user_state(self, user_id: int) -> UserStoryState:
        """Obtiene o crea el estado de historia del usuario"""
        result = await self.session.execute(
            select(UserStoryState).filter_by(user_id=user_id))
        state = result.scalars().first()
        
        if not state:
            # Crear nuevo estado si no existe
            state = UserStoryState(user_id=user_id)
            self.session.add(state)
            await self.session.commit()
            logger.info(f"Nuevo estado de historia creado para usuario {user_id}")
        
        return state
    
    async def start_story(self, user_id: int, start_fragment_id: str = "welcome_1"):
        """Inicia la historia para un usuario"""
        state = await self.get_user_state(user_id)
        fragment = await self.get_fragment(start_fragment_id)
        
        # Establecer fragmento inicial
        state.current_fragment_id = fragment.fragment_id
        if fragment.fragment_id not in state.unlocked_fragments:
            state.unlocked_fragments.append(fragment.fragment_id)
        state.story_progress = max(state.story_progress, 1)  # Empezar al menos en progreso 1
        
        await self.session.commit()
        logger.info(f"Historia iniciada para usuario {user_id} con fragmento {start_fragment_id}")
        return fragment
    
    async def get_current_fragment(self, user_id: int) -> NarrativeFragment:
        """Obtiene el fragmento actual del usuario"""
        state = await self.get_user_state(user_id)
        if not state.current_fragment_id:
            # Iniciar historia si no tiene fragmento actual
            return await self.start_story(user_id)
        
        return await self.get_fragment(state.current_fragment_id)
    
    async def process_decision(self, user_id: int, choice_index: int) -> NarrativeFragment:
        """Procesa una decisión del usuario y avanza en la historia"""
        state = await self.get_user_state(user_id)
        current_fragment = await self.get_fragment(state.current_fragment_id)
        
        # Verificar que la elección sea válida
        if choice_index < 0 or choice_index >= len(current_fragment.decisions):
            raise ValueError("Índice de decisión inválido")
        
        # Obtener la decisión seleccionada
        decision = current_fragment.decisions[choice_index]
        next_fragment_id = decision["next_fragment"]
        
        # Registrar la decisión
        state.decisions[current_fragment.fragment_id] = choice_index
        
        # Cargar siguiente fragmento
        next_fragment = await self.get_fragment(next_fragment_id)
        state.current_fragment_id = next_fragment.fragment_id
        
        # Agregar a fragmentos desbloqueados si es nuevo
        if next_fragment.fragment_id not in state.unlocked_fragments:
            state.unlocked_fragments.append(next_fragment.fragment_id)
        
        # Actualizar progreso (simplificado: cada fragmento cuenta como 1 punto)
        state.story_progress = len(state.unlocked_fragments)
        
        await self.session.commit()
        logger.info(f"Usuario {user_id} tomó decisión {choice_index} en fragmento {current_fragment.fragment_id}. Avanzó a {next_fragment_id}")
        
        return next_fragment
      

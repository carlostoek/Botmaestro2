"""
Motor narrativo principal para DianaBot.
Maneja la lógica de fragmentos, decisiones y progresión de historia.
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import User
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
from services.point_service import PointService
from utils.user_roles import get_user_role

logger = logging.getLogger(__name__)

class NarrativeEngine:
    """Motor principal del sistema narrativo inmersivo."""
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        self.point_service = PointService(session) if session else None
    
    async def get_user_current_fragment(self, user_id: int) -> Optional[StoryFragment]:
        """Obtiene el fragmento actual del usuario o inicia la narrativa."""
        # Obtener o crear estado narrativo del usuario
        user_state = await self._get_or_create_user_state(user_id)
        
        if not user_state.current_fragment_id:
            # Iniciar narrativa desde el fragmento inicial
            start_fragment = await self._get_fragment_by_key("START")
            if start_fragment:
                user_state.current_fragment_id = start_fragment.id
                await self.session.commit()
                return start_fragment
            else:
                logger.error("No se encontró fragmento inicial 'START'")
                return None
        
        # Obtener fragmento actual
        fragment = await self.session.get(StoryFragment, user_state.current_fragment_id)
        return fragment
    
    async def process_user_decision(
        self, 
        user_id: int, 
        choice_index: int
    ) -> Optional[StoryFragment]:
        """Procesa una decisión del usuario y avanza la narrativa."""
        current_fragment = await self.get_user_current_fragment(user_id)
        if not current_fragment:
            return None
        
        # Obtener las opciones disponibles para este fragmento
        choices = await self._get_fragment_choices(current_fragment.id)
        
        if choice_index < 0 or choice_index >= len(choices):
            logger.warning(f"Índice de decisión inválido: {choice_index} para fragmento {current_fragment.key}")
            return None
        
        selected_choice = choices[choice_index]
        
        # Verificar condiciones de acceso
        if not await self._check_access_conditions(user_id, selected_choice.destination_fragment):
            logger.info(f"Usuario {user_id} no cumple condiciones para fragmento {selected_choice.destination_fragment.key}")
            return None
        
        # Registrar la decisión
        user_state = await self._get_or_create_user_state(user_id)
        if not user_state.choices_made:
            user_state.choices_made = []
        
        user_state.choices_made.append({
            "fragment_key": current_fragment.key,
            "choice_index": choice_index,
            "choice_text": selected_choice.text,
            "timestamp": str(datetime.utcnow())
        })
        
        # Avanzar al siguiente fragmento
        next_fragment = selected_choice.destination_fragment
        user_state.current_fragment_id = next_fragment.id
        
        # Procesar recompensas del fragmento
        await self._process_fragment_rewards(user_id, next_fragment)
        
        await self.session.commit()
        
        logger.info(f"Usuario {user_id} avanzó de {current_fragment.key} a {next_fragment.key}")
        return next_fragment
    
    async def start_narrative(self, user_id: int) -> Optional[StoryFragment]:
        """Inicia la narrativa para un usuario nuevo."""
        user_state = await self._get_or_create_user_state(user_id)
        
        # Buscar fragmento inicial
        start_fragment = await self._get_fragment_by_key("START")
        if not start_fragment:
            logger.error("No se encontró fragmento inicial 'START'")
            return None
        
        # Verificar condiciones de acceso
        if not await self._check_access_conditions(user_id, start_fragment):
            return None
        
        # Configurar estado inicial
        user_state.current_fragment_id = start_fragment.id
        user_state.choices_made = []
        
        # Procesar recompensas del fragmento inicial
        await self._process_fragment_rewards(user_id, start_fragment)
        
        await self.session.commit()
        
        logger.info(f"Narrativa iniciada para usuario {user_id}")
        return start_fragment
    
    async def get_user_narrative_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas narrativas del usuario."""
        user_state = await self._get_or_create_user_state(user_id)
        
        # Contar fragmentos visitados
        visited_fragments = len(user_state.choices_made) if user_state.choices_made else 0
        
        # Obtener fragmento actual
        current_fragment = None
        if user_state.current_fragment_id:
            current_fragment = await self.session.get(StoryFragment, user_state.current_fragment_id)
        
        # Calcular progreso aproximado
        total_fragments = await self._count_accessible_fragments(user_id)
        progress_percentage = (visited_fragments / max(total_fragments, 1)) * 100
        
        return {
            "current_fragment": current_fragment.key if current_fragment else None,
            "fragments_visited": visited_fragments,
            "total_accessible": total_fragments,
            "progress_percentage": min(progress_percentage, 100),
            "choices_made": user_state.choices_made or []
        }
    
    async def _get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo del usuario."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                choices_made=[]
            )
            self.session.add(user_state)
            await self.session.commit()
            await self.session.refresh(user_state)
        
        return user_state
    
    async def _get_fragment_by_key(self, key: str) -> Optional[StoryFragment]:
        """Obtiene un fragmento por su clave única."""
        stmt = select(StoryFragment).where(StoryFragment.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_fragment_choices(self, fragment_id: int) -> List[NarrativeChoice]:
        """Obtiene las opciones de decisión para un fragmento."""
        stmt = select(NarrativeChoice).where(
            NarrativeChoice.source_fragment_id == fragment_id
        ).order_by(NarrativeChoice.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def _check_access_conditions(self, user_id: int, fragment: StoryFragment) -> bool:
        """Verifica si el usuario puede acceder a un fragmento."""
        if not fragment:
            return False
        
        # Verificar nivel mínimo de besitos
        if fragment.min_besitos > 0:
            user = await self.session.get(User, user_id)
            if not user or user.points < fragment.min_besitos:
                return False
        
        # Verificar rol requerido
        if fragment.required_role and self.bot:
            from utils.user_roles import get_user_role
            user_role = await get_user_role(self.bot, user_id, session=self.session)
            if user_role != fragment.required_role and user_role != "admin":
                return False
        
        return True
    
    async def _process_fragment_rewards(self, user_id: int, fragment: StoryFragment):
        """Procesa las recompensas de un fragmento."""
        if fragment.reward_besitos > 0 and self.point_service and self.bot:
            await self.point_service.add_points(
                user_id, 
                fragment.reward_besitos, 
                bot=self.bot
            )
            logger.info(f"Usuario {user_id} recibió {fragment.reward_besitos} besitos del fragmento {fragment.key}")
        
        # Procesar logros desbloqueados
        if fragment.unlocks_achievement_id:
            from services.achievement_service import AchievementService
            ach_service = AchievementService(self.session)
            await ach_service._grant(user_id, fragment.unlocks_achievement_id, bot=self.bot)
    
    async def _count_accessible_fragments(self, user_id: int) -> int:
        """Cuenta los fragmentos accesibles para el usuario."""
        user_role = "free"
        if self.bot:
            from utils.user_roles import get_user_role
            user_role = await get_user_role(self.bot, user_id, session=self.session)
        
        user = await self.session.get(User, user_id)
        user_besitos = user.points if user else 0
        
        # Contar fragmentos accesibles según rol y besitos
        stmt = select(StoryFragment)
        if user_role != "admin":
            conditions = [StoryFragment.min_besitos <= user_besitos]
            if user_role != "vip":
                conditions.append(
                    (StoryFragment.required_role.is_(None)) | 
                    (StoryFragment.required_role != "vip")
                )
            stmt = stmt.where(and_(*conditions))
        
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
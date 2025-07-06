# mybot/services/narrative_service.py
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from database.narrative_models import NarrativeState, RelationshipStage, EmotionalState

logger = logging.getLogger(__name__)

class NarrativeService:
    """Servicio para gestionar el estado narrativo de los usuarios"""

    @staticmethod
    async def get_or_create_narrative_state(session: AsyncSession, user_id: int) -> NarrativeState:
        """Obtiene o crea el estado narrativo de un usuario"""
        result = await session.execute(
            select(NarrativeState).where(NarrativeState.user_id == user_id)
        )
        narrative_state = result.scalar_one_or_none()

        if not narrative_state:
            narrative_state = NarrativeState(user_id=user_id)
            session.add(narrative_state)
            await session.commit()
            logger.info(f"Created narrative state for user {user_id}")

        return narrative_state

    @staticmethod
    async def update_trust_level(session: AsyncSession, user_id: int, delta: float):
        """Actualiza el nivel de confianza"""
        narrative_state = await NarrativeService.get_or_create_narrative_state(session, user_id)

        narrative_state.trust_level = max(0.0, min(1.0, narrative_state.trust_level + delta))
        narrative_state.total_interactions += 1

        # Actualizar stage basado en trust
        if narrative_state.trust_level >= 0.8:
            narrative_state.relationship_stage = RelationshipStage.INTIMATE
        elif narrative_state.trust_level >= 0.6:
            narrative_state.relationship_stage = RelationshipStage.CONFIDANT
        elif narrative_state.trust_level >= 0.4:
            narrative_state.relationship_stage = RelationshipStage.TRUSTED
        elif narrative_state.trust_level >= 0.2:
            narrative_state.relationship_stage = RelationshipStage.ACQUAINTANCE
        elif narrative_state.trust_level >= 0.1:
            narrative_state.relationship_stage = RelationshipStage.CURIOUS

        await session.commit()
        logger.info(f"Updated trust level for user {user_id}: {narrative_state.trust_level}")


"""Servicio para el sistema emocional."""

from typing import Optional, Dict, Any, List, Tuple
import structlog
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, desc, func

from .base import BaseService
from ..database.models.emotional import (
    CharacterEmotionalProfile, 
    UserCharacterRelationship,
    UserCharacterEmotionalState,
    EmotionalMemory,
    PersonalityAdaptation,
    RelationshipStatusEnum
)

logger = structlog.get_logger()

class EmotionalService:
    """Servicio para gestionar el sistema emocional."""
    
    def __init__(self):
        self.logger = structlog.get_logger(service="EmotionalService")
        self.profile_service = CharacterProfileService()
        self.relationship_service = RelationshipService()
        self.emotional_state_service = EmotionalStateService()
        self.memory_service = EmotionalMemoryService()
        self.personality_service = PersonalityAdaptationService()
    
    async def process_message(
        self,
        session: AsyncSession,
        user_id: int,
        character_name: str,
        message_text: str,
        context_type: str = "conversation",
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y actualiza el estado emocional del personaje.
        
        Retorna un diccionario con la información emocional actualizada.
        """
        self.logger.debug(
            "Procesando mensaje para estado emocional", 
            user_id=user_id, 
            character=character_name
        )
        
        # Obtener o crear perfil del personaje
        character = await self.profile_service.get_by_name(session, character_name)
        if not character:
            # Si no existe, usar perfil predeterminado
            self.logger.warning("Perfil de personaje no encontrado, usando predeterminado", character=character_name)
            character = await self.profile_service.create_default_profile(session, character_name)
        
        # Obtener o crear relación
        relationship = await self.relationship_service.get_or_create(
            session, user_id, character.id
        )
        
        # Obtener estado emocional actual
        emotional_state = await self.emotional_state_service.get_by_relationship(
            session, relationship.id
        )
        
        # Analizar el mensaje (en una implementación real, aquí habría un análisis de NLP)
        # Por ahora, usamos una implementación simple
        emotional_impact = self._analyze_message_simple(message_text)
        
        # Actualizar estado emocional
        updated_state = await self.emotional_state_service.update_from_impact(
            session, emotional_state.id, emotional_impact
        )
        
        # Crear memoria emocional
        memory_data = {
            "user_id": user_id,
            "character_id": character.id,
            "relationship_id": relationship.id,
            "memory_type": "message",
            "summary": f"El usuario dijo: {message_text[:50]}{'...' if len(message_text) > 50 else ''}",
            "details": message_text,
            "emotional_context": emotional_impact,
            "importance_score": self._calculate_importance(emotional_impact)
        }
        
        memory = await self.memory_service.create(session, memory_data)
        
        # Actualizar contador de interacciones
        await self.relationship_service.increment_interactions(
            session, relationship.id
        )
        
        # Preparar respuesta
        response = {
            "character_name": character.character_name,
            "dominant_emotion": updated_state.dominant_emotion,
            "emotional_state": {
                "joy": updated_state.joy,
                "trust": updated_state.trust,
                "fear": updated_state.fear,
                "sadness": updated_state.sadness,
                "anger": updated_state.anger,
                "surprise": updated_state.surprise,
                "anticipation": updated_state.anticipation,
                "disgust": updated_state.disgust
            },
            "relationship": {
                "status": relationship.relationship_status.value,
                "level": relationship.relationship_level,
                "trust_level": relationship.trust_level
            }
        }
        
        return response
    
    async def get_relationship_summary(
        self, session: AsyncSession, user_id: int, character_name: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un resumen de la relación entre usuario y personaje."""
        self.logger.debug(
            "Obteniendo resumen de relación", 
            user_id=user_id, 
            character=character_name
        )
        
        # Obtener perfil del personaje
        character = await self.profile_service.get_by_name(session, character_name)
        if not character:
            self.logger.warning("Perfil de personaje no encontrado", character=character_name)
            return None
        
        # Obtener relación
        relationship = await self.relationship_service.get_relationship(
            session, user_id, character.id
        )
        
        if not relationship:
            self.logger.warning("Relación no encontrada", user_id=user_id, character=character_name)
            return None
        
        # Obtener estado emocional
        emotional_state = await self.emotional_state_service.get_by_relationship(
            session, relationship.id
        )
        
        # Obtener memorias importantes
        important_memories = await self.memory_service.get_important_memories(
            session, relationship.id, limit=5
        )
        
        # Obtener adaptación de personalidad
        personality = await self.personality_service.get_by_relationship(
            session, relationship.id
        )
        
        # Preparar resumen
        summary = {
            "character_name": character.character_name,
            "relationship": {
                "status": relationship.relationship_status.value,
                "level": relationship.relationship_level,
                "trust_level": relationship.trust_level,
                "interaction_count": relationship.interaction_count,
                "first_interaction": relationship.first_interaction_at.isoformat(),
                "last_interaction": relationship.last_interaction_at.isoformat()
            },
            "emotional_state": {
                "dominant_emotion": emotional_state.dominant_emotion,
                "joy": emotional_state.joy,
                "trust": emotional_state.trust,
                "fear": emotional_state.fear,
                "sadness": emotional_state.sadness,
                "anger": emotional_state.anger,
                "surprise": emotional_state.surprise,
                "anticipation": emotional_state.anticipation,
                "disgust": emotional_state.disgust
            },
            "personality_adaptation": {
                "warmth": personality.warmth,
                "formality": personality.formality,
                "humor": personality.humor,
                "directness": personality.directness,
                "confidence_score": personality.confidence_score
            },
            "important_memories": [
                {
                    "summary": memory.summary,
                    "importance": memory.importance_score,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in important_memories
            ]
        }
        
        return summary
    
    async def create_default_profiles(self, session: AsyncSession) -> None:
        """Crea perfiles predeterminados para los personajes."""
        # Diana
        await self.profile_service.create_default_profile(session, "Diana")
        
        # Lucien
        await self.profile_service.create_default_profile(session, "Lucien")
    
    def _analyze_message_simple(self, message_text: str) -> Dict[str, float]:
        """
        Análisis simple de mensaje (placeholder).
        
        En una implementación real, esto utilizaría NLP para analizar el mensaje.
        """
        # Implementación básica como placeholder
        message = message_text.lower()
        
        emotional_impact = {
            "joy": 0.0,
            "trust": 0.0,
            "fear": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "surprise": 0.0,
            "anticipation": 0.0,
            "disgust": 0.0
        }
        
        # Palabras clave simples (en una implementación real esto sería mucho más sofisticado)
        if any(word in message for word in ["feliz", "contento", "alegre", "divertido"]):
            emotional_impact["joy"] = 0.6
        
        if any(word in message for word in ["confío", "creo", "seguro"]):
            emotional_impact["trust"] = 0.5
            
        if any(word in message for word in ["miedo", "terror", "asustado"]):
            emotional_impact["fear"] = 0.7
            
        if any(word in message for word in ["triste", "deprimido", "dolor"]):
            emotional_impact["sadness"] = 0.6
            
        if any(word in message for word in ["enojado", "furioso", "molesto"]):
            emotional_impact["anger"] = 0.7
            
        if any(word in message for word in ["wow", "increíble", "sorprendente"]):
            emotional_impact["surprise"] = 0.6
            
        if any(word in message for word in ["espero", "ansioso", "pronto"]):
            emotional_impact["anticipation"] = 0.5
            
        if any(word in message for word in ["asco", "repulsivo", "repugnante"]):
            emotional_impact["disgust"] = 0.7
        
        return emotional_impact
    
    def _calculate_importance(self, emotional_impact: Dict[str, float]) -> float:
        """Calcula la importancia de una interacción basada en su impacto emocional."""
        # Suma de valores absolutos de impacto emocional
        importance = sum(abs(value) for value in emotional_impact.values())
        
        # Normalizar al rango 0.1-3.0
        importance = min(3.0, max(0.1, importance / 2))
        
        return importance


class CharacterProfileService(BaseService[CharacterEmotionalProfile]):
    """Servicio para gestionar perfiles emocionales de personajes."""
    
    def __init__(self):
        super().__init__(CharacterEmotionalProfile)
    
    async def get_by_name(self, session: AsyncSession, character_name: str) -> Optional[CharacterEmotionalProfile]:
        """Obtiene un perfil de personaje por su nombre."""
        self.logger.debug("Obteniendo perfil por nombre", character=character_name)
        
        query = select(CharacterEmotionalProfile).where(
            CharacterEmotionalProfile.character_name == character_name
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def create_default_profile(self, session: AsyncSession, character_name: str) -> CharacterEmotionalProfile:
        """Crea un perfil predeterminado para un personaje."""
        self.logger.debug("Creando perfil predeterminado", character=character_name)
        
        # Valores predeterminados basados en el personaje
        if character_name == "Diana":
            profile_data = {
                "character_name": "Diana",
                "base_joy": 60.0,
                "base_trust": 40.0,
                "base_fear": 15.0,
                "base_sadness": 20.0,
                "base_anger": 10.0,
                "base_surprise": 30.0,
                "base_anticipation": 45.0,
                "base_disgust": 5.0,
                "personality_traits": {
                    "introversion": 0.7,
                    "sensitivity": 0.8,
                    "curiosity": 0.9,
                    "creativity": 0.8,
                    "playfulness": 0.6
                }
            }
        elif character_name == "Lucien":
            profile_data = {
                "character_name": "Lucien",
                "base_joy": 45.0,
                "base_trust": 35.0,
                "base_fear": 25.0,
                "base_sadness": 15.0,
                "base_anger": 15.0,
                "base_surprise": 20.0,
                "base_anticipation": 50.0,
                "base_disgust": 10.0,
                "personality_traits": {
                    "formality": 0.9,
                    "loyalty": 1.0,
                    "wisdom": 0.8,
                    "patience": 0.7,
                    "protectiveness": 0.9
                }
            }
        else:
            # Perfil genérico para otros personajes
            profile_data = {
                "character_name": character_name,
                "base_joy": 50.0,
                "base_trust": 30.0,
                "base_fear": 20.0,
                "base_sadness": 15.0,
                "base_anger": 10.0,
                "base_surprise": 25.0,
                "base_anticipation": 40.0,
                "base_disgust": 5.0,
                "personality_traits": {
                    "adaptability": 0.5,
                    "sociability": 0.5,
                    "confidence": 0.5
                }
            }
        
        profile = await self.create(session, profile_data)
        return profile


class RelationshipService(BaseService[UserCharacterRelationship]):
    """Servicio para gestionar relaciones entre usuarios y personajes."""
    
    def __init__(self):
        super().__init__(UserCharacterRelationship)
    
    async def get_relationship(
        self, session: AsyncSession, user_id: int, character_id: int
    ) -> Optional[UserCharacterRelationship]:
        """Obtiene una relación entre usuario y personaje."""
        self.logger.debug("Obteniendo relación", user_id=user_id, character_id=character_id)
        
        query = select(UserCharacterRelationship).where(
            and_(
                UserCharacterRelationship.user_id == user_id,
                UserCharacterRelationship.character_id == character_id
            )
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def get_or_create(
        self, session: AsyncSession, user_id: int, character_id: int
    ) -> UserCharacterRelationship:
        """Obtiene o crea una relación entre usuario y personaje."""
        self.logger.debug("Obteniendo o creando relación", user_id=user_id, character_id=character_id)
        
        relationship = await self.get_relationship(session, user_id, character_id)
        
        if not relationship:
            # Crear nueva relación
            relationship_data = {
                "user_id": user_id,
                "character_id": character_id,
                "relationship_status": RelationshipStatusEnum.INITIAL,
                "relationship_level": 1,
                "trust_level": 0.0,
                "familiarity": 0.0,
                "rapport": 0.0,
                "interaction_count": 0
            }
            
            relationship = await self.create(session, relationship_data)
            
            # Crear estado emocional inicial
            emotional_state_service = EmotionalStateService()
            await emotional_state_service.create_initial_state(
                session, user_id, character_id, relationship.id
            )
            
            # Crear adaptación de personalidad inicial
            personality_service = PersonalityAdaptationService()
            await personality_service.create_initial_adaptation(
                session, user_id, character_id, relationship.id
            )
        
        return relationship
    
    async def increment_interactions(
        self, session: AsyncSession, relationship_id: int, count: int = 1
    ) -> None:
        """Incrementa el contador de interacciones y actualiza la fecha de última interacción."""
        self.logger.debug("Incrementando interacciones", relationship_id=relationship_id, count=count)
        
        await session.execute(
            update(UserCharacterRelationship)
            .where(UserCharacterRelationship.id == relationship_id)
            .values(
                interaction_count=UserCharacterRelationship.interaction_count + count,
                last_interaction_at=datetime.now()
            )
        )
    
    async def update_relationship_status(
        self, session: AsyncSession, relationship_id: int, status: RelationshipStatusEnum
    ) -> Optional[UserCharacterRelationship]:
        """Actualiza el estado de una relación."""
        self.logger.debug("Actualizando estado de relación", relationship_id=relationship_id, status=status)
        
        return await self.update(session, relationship_id, {"relationship_status": status})
    
    async def update_trust_level(
        self, session: AsyncSession, relationship_id: int, change: float
    ) -> Optional[UserCharacterRelationship]:
        """Actualiza el nivel de confianza de una relación."""
        self.logger.debug("Actualizando nivel de confianza", relationship_id=relationship_id, change=change)
        
        relationship = await self.get_by_id(session, relationship_id)
        if relationship:
            new_trust = max(0.0, min(1.0, relationship.trust_level + change))
            return await self.update(session, relationship_id, {"trust_level": new_trust})
        
        return None


class EmotionalStateService(BaseService[UserCharacterEmotionalState]):
    """Servicio para gestionar estados emocionales."""
    
    def __init__(self):
        super().__init__(UserCharacterEmotionalState)
    
    async def get_by_relationship(
        self, session: AsyncSession, relationship_id: int
    ) -> Optional[UserCharacterEmotionalState]:
        """Obtiene el estado emocional asociado a una relación."""
        self.logger.debug("Obteniendo estado emocional por relación", relationship_id=relationship_id)
        
        query = select(UserCharacterEmotionalState).where(
            UserCharacterEmotionalState.relationship_id == relationship_id
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def create_initial_state(
        self, session: AsyncSession, user_id: int, character_id: int, relationship_id: int
    ) -> UserCharacterEmotionalState:
        """Crea un estado emocional inicial para una relación."""
        self.logger.debug(
            "Creando estado emocional inicial", 
            user_id=user_id, 
            character_id=character_id
        )
        
        # Obtener valores base del personaje
        character_service = CharacterProfileService()
        character = await character_service.get_by_id(session, character_id)
        
        # Crear estado emocional inicial
        state_data = {
            "user_id": user_id,
            "character_id": character_id,
            "relationship_id": relationship_id,
            "joy": character.base_joy,
            "trust": character.base_trust,
            "fear": character.base_fear,
            "sadness": character.base_sadness,
            "anger": character.base_anger,
            "surprise": character.base_surprise,
            "anticipation": character.base_anticipation,
            "disgust": character.base_disgust,
            "dominant_emotion": "neutral"
        }
        
        state = await self.create(session, state_data)
        return state
    
    async def update_from_impact(
        self, session: AsyncSession, state_id: int, emotional_impact: Dict[str, float]
    ) -> UserCharacterEmotionalState:
        """Actualiza un estado emocional basado en un impacto emocional."""
        self.logger.debug("Actualizando estado emocional", state_id=state_id)
        
        # Obtener estado actual
        state = await self.get_by_id(session, state_id)
        if not state:
            self.logger.error("Estado emocional no encontrado", state_id=state_id)
            raise ValueError(f"Estado emocional {state_id} no encontrado")
        
        # Aplicar impacto emocional
        update_data = {}
        for emotion, impact in emotional_impact.items():
            if hasattr(state, emotion) and impact != 0:
                # Calcular nuevo valor
                current = getattr(state, emotion)
                new_value = max(0.0, min(100.0, current + impact * 10))  # Escalar impacto
                update_data[emotion] = new_value
        
        # Actualizar solo si hay cambios
        if update_data:
            # Actualizar estado
            state = await self.update(session, state_id, update_data)
            
            # Determinar emoción dominante
            dominant = await self._calculate_dominant_emotion(state)
            if dominant != state.dominant_emotion:
                state = await self.update(session, state_id, {"dominant_emotion": dominant})
        
        return state
    
    async def _calculate_dominant_emotion(
        self, state: UserCharacterEmotionalState
    ) -> str:
        """Calcula la emoción dominante en un estado emocional."""
        emotions = {
            "joy": state.joy,
            "trust": state.trust,
            "fear": state.fear,
            "sadness": state.sadness,
            "anger": state.anger,
            "surprise": state.surprise,
            "anticipation": state.anticipation,
            "disgust": state.disgust
        }
        
        # Encontrar la emoción con mayor valor
        dominant_emotion, max_value = max(emotions.items(), key=lambda x: x[1])
        
        # Si el valor máximo es bajo, la emoción dominante es neutral
        if max_value < 30:
            return "neutral"
        
        return dominant_emotion


class EmotionalMemoryService(BaseService[EmotionalMemory]):
    """Servicio para gestionar memorias emocionales."""
    
    def __init__(self):
        super().__init__(EmotionalMemory)
    
    async def get_important_memories(
        self, session: AsyncSession, relationship_id: int, limit: int = 5
    ) -> List[EmotionalMemory]:
        """Obtiene las memorias más importantes de una relación."""
        self.logger.debug(
            "Obteniendo memorias importantes", 
            relationship_id=relationship_id, 
            limit=limit
        )
        
        query = (
            select(EmotionalMemory)
            .where(
                and_(
                    EmotionalMemory.relationship_id == relationship_id,
                    EmotionalMemory.is_forgotten == False
                )
            )
            .order_by(desc(EmotionalMemory.importance_score))
            .limit(limit)
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_memories(
        self, session: AsyncSession, relationship_id: int, limit: int = 5
    ) -> List[EmotionalMemory]:
        """Obtiene las memorias más recientes de una relación."""
        self.logger.debug(
            "Obteniendo memorias recientes", 
            relationship_id=relationship_id, 
            limit=limit
        )
        
        query = (
            select(EmotionalMemory)
            .where(
                and_(
                    EmotionalMemory.relationship_id == relationship_id,
                    EmotionalMemory.is_forgotten == False
                )
            )
            .order_by(desc(EmotionalMemory.created_at))
            .limit(limit)
        )
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def update_memory_recall(
        self, session: AsyncSession, memory_id: int
    ) -> None:
        """Actualiza la información de recuerdo de una memoria."""
        self.logger.debug("Actualizando recuerdo de memoria", memory_id=memory_id)
        
        await session.execute(
            update(EmotionalMemory)
            .where(EmotionalMemory.id == memory_id)
            .values(
                last_recalled_at=datetime.now(),
                recall_count=EmotionalMemory.recall_count + 1
            )
        )


class PersonalityAdaptationService(BaseService[PersonalityAdaptation]):
    """Servicio para gestionar adaptaciones de personalidad."""
    
    def __init__(self):
        super().__init__(PersonalityAdaptation)
    
    async def get_by_relationship(
        self, session: AsyncSession, relationship_id: int
    ) -> Optional[PersonalityAdaptation]:
        """Obtiene la adaptación de personalidad asociada a una relación."""
        self.logger.debug("Obteniendo adaptación por relación", relationship_id=relationship_id)
        
        query = select(PersonalityAdaptation).where(
            PersonalityAdaptation.relationship_id == relationship_id
        )
        
        result = await session.execute(query)
        return result.scalars().first()
    
    async def create_initial_adaptation(
        self, session: AsyncSession, user_id: int, character_id: int, relationship_id: int
    ) -> PersonalityAdaptation:
        """Crea una adaptación de personalidad inicial para una relación."""
        self.logger.debug(
            "Creando adaptación inicial", 
            user_id=user_id, 
            character_id=character_id
        )
        
        # Crear adaptación inicial
        adaptation_data = {
            "user_id": user_id,
            "character_id": character_id,
            "relationship_id": relationship_id,
            "warmth": 0.5,
            "formality": 0.5,
            "humor": 0.5,
            "directness": 0.5,
            "assertiveness": 0.5,
            "curiosity": 0.5,
            "emotional_expressiveness": 0.5,
            "communication_preferences": {},
            "topic_preferences": {},
            "taboo_topics": [],
            "confidence_score": 0.1  # Baja confianza inicial
        }
        
        adaptation = await self.create(session, adaptation_data)
        return adaptation
    
    async def update_adaptation(
        self, session: AsyncSession, adaptation_id: int, changes: Dict[str, Any]
    ) -> Optional[PersonalityAdaptation]:
        """Actualiza una adaptación de personalidad."""
        self.logger.debug("Actualizando adaptación", adaptation_id=adaptation_id)
        
        # Validar cambios (solo campos permitidos)
        valid_fields = [
            "warmth", "formality", "humor", "directness", 
            "assertiveness", "curiosity", "emotional_expressiveness",
            "communication_preferences", "topic_preferences", "taboo_topics"
        ]
        
        valid_changes = {k: v for k, v in changes.items() if k in valid_fields}
        
        # Incrementar confianza
        adaptation = await self.get_by_id(session, adaptation_id)
        if adaptation:
            # Aumentar ligeramente la confianza con cada actualización
            confidence = min(1.0, adaptation.confidence_score + 0.05)
            valid_changes["confidence_score"] = confidence
        
        return await self.update(session, adaptation_id, valid_changes)
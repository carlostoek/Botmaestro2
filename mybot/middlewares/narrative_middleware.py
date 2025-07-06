# middlewares/narrative_middleware.py
"""
Middleware que inyecta contexto narrativo en todas las interacciones.
Rastrea patrones de comportamiento y actualiza el estado narrativo.
"""

from typing import Callable, Dict, Any, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.narrative_models import NarrativeState, UserArchetype
from database.models import User

class NarrativeContextMiddleware(BaseMiddleware):
    """Middleware que gestiona el contexto narrativo del usuario"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        session: AsyncSession = data.get("session")
        user: User = data.get("user")
        
        if not session or not user:
            return await handler(event, data)
        
        # Obtener o crear estado narrativo
        narrative_state = await session.get(NarrativeState, user.id)
        if not narrative_state:
            narrative_state = NarrativeState(user_id=user.id)
            session.add(narrative_state)
            await session.commit()
        
        # Calcular contexto emocional basado en la hora
        emotional_context = self._calculate_time_based_context()
        
        # Detectar patrones de respuesta si es un mensaje
        if isinstance(event, Message) and event.text:
            await self._analyze_response_pattern(
                session, user, narrative_state, event.text
            )
        
        # Inyectar datos narrativos
        data["narrative_state"] = narrative_state
        data["emotional_context"] = emotional_context
        data["narrative_chapter"] = self._get_chapter(user.narrative_level)
        
        # Procesar handler
        result = await handler(event, data)
        
        # Post-procesamiento
        await self._post_process_interaction(session, user, narrative_state)
        
        return result
    
    def _calculate_time_based_context(self) -> Dict[str, float]:
        """Calcula modificadores emocionales basados en la hora"""
        
        hour = datetime.now().hour
        
        # Contextos por hora del día
        if 23 <= hour or hour < 4:  # Madrugada
            return {
                "vulnerability": 0.8,
                "introspection": 0.9,
                "playfulness": 0.2,
                "formality": 0.1
            }
        elif 5 <= hour < 9:  # Mañana temprano
            return {
                "vulnerability": 0.5,
                "introspection": 0.6,
                "playfulness": 0.4,
                "formality": 0.3
            }
        elif 9 <= hour < 18:  # Día
            return {
                "vulnerability": 0.3,
                "introspection": 0.4,
                "playfulness": 0.7,
                "formality": 0.5
            }
        else:  # Tarde/Noche
            return {
                "vulnerability": 0.6,
                "introspection": 0.7,
                "playfulness": 0.5,
                "formality": 0.2
            }
    
    async def _analyze_response_pattern(
        self,
        session: AsyncSession,
        user: User,
        narrative_state: NarrativeState,
        message_text: str
    ):
        """Analiza patrones en las respuestas del usuario"""
        
        # Métricas básicas
        message_length = len(message_text)
        word_count = len(message_text.split())
        question_marks = message_text.count("?")
        exclamations = message_text.count("!")
        
        # Actualizar patrones de interacción
        patterns = user.interaction_patterns or {}
        
        # Tiempos de respuesta (si hay mensaje previo)
        if narrative_state.last_meaningful_interaction:
            response_time = (datetime.utcnow() - narrative_state.last_meaningful_interaction).seconds
            response_times = patterns.get("response_times", [])[-9:]  # Mantener últimos 10
            response_times.append(response_time)
            patterns["response_times"] = response_times
        
        # Longitudes de mensaje
        lengths = patterns.get("message_lengths", [])[-9:]
        lengths.append(message_length)
        patterns["message_lengths"] = lengths
        
        # Actualizar métricas de estilo
        style_metrics = narrative_state.response_style_metrics or {}
        
        # Detectar estilo poético
        poetic_words = ["alma", "corazón", "sueño", "anhelo", "eternidad", "infinito"]
        if any(word in message_text.lower() for word in poetic_words):
            style_metrics["poetic"] = style_metrics.get("poetic", 0) + 1
        
        # Detectar estilo directo
        if word_count < 10 and question_marks == 0:
            style_metrics["direct"] = style_metrics.get("direct", 0) + 1
        
        # Detectar estilo analítico
        analytical_words = ["porque", "creo que", "pienso", "considero", "analizar"]
        if any(word in message_text.lower() for word in analytical_words):
            style_metrics["analytical"] = style_metrics.get("analytical", 0) + 1
        
        # Detectar emocionalidad
        emotional_words = ["siento", "emoción", "sentimiento", "corazón", "alma"]
        emotional_count = sum(1 for word in emotional_words if word in message_text.lower())
        if emotional_count > 0:
            style_metrics["emotional"] = style_metrics.get("emotional", 0) + emotional_count
            patterns["emotional_words"] = patterns.get("emotional_words", 0) + emotional_count
        
        # Actualizar en BD
        narrative_state.response_style_metrics = style_metrics
        user.interaction_patterns = patterns
        
        # Intentar detectar arquetipo después de suficientes interacciones
        if narrative_state.total_interactions > 10 and narrative_state.user_archetype == UserArchetype.UNKNOWN:
            detected_archetype = self._detect_archetype(style_metrics, patterns)
            if detected_archetype:
                narrative_state.user_archetype = detected_archetype
                narrative_state.archetype_confidence = 0.7
        
        await session.commit()
    
    def _detect_archetype(
        self,
        style_metrics: Dict[str, int],
        patterns: Dict[str, Any]
    ) -> Optional[UserArchetype]:
        """Intenta detectar el arquetipo del usuario"""
        
        # Calcular puntuaciones para cada arquetipo
        scores = {
            UserArchetype.ROMANTIC: 0,
            UserArchetype.DIRECT: 0,
            UserArchetype.ANALYTICAL: 0,
            UserArchetype.EXPLORER: 0,
            UserArchetype.PATIENT: 0,
            UserArchetype.PERSISTENT: 0,
        }
        
        # Romántico: alto en poético y emocional
        scores[UserArchetype.ROMANTIC] = (
            style_metrics.get("poetic", 0) * 2 +
            style_metrics.get("emotional", 0) * 1.5
        )
        
        # Directo: mensajes cortos, sin rodeos
        avg_length = sum(patterns.get("message_lengths", [0])) / max(len(patterns.get("message_lengths", [1])), 1)
        if avg_length < 50:
            scores[UserArchetype.DIRECT] = style_metrics.get("direct", 0) * 3
        
        # Analítico: alto en análisis y mensajes largos
        scores[UserArchetype.ANALYTICAL] = (
            style_metrics.get("analytical", 0) * 2 +
            (1 if avg_length > 100 else 0) * 10
        )
        
        # Paciente: tiempos de respuesta largos
        avg_response_time = sum(patterns.get("response_times", [0])) / max(len(patterns.get("response_times", [1])), 1)
        if avg_response_time > 300:  # Más de 5 minutos promedio
            scores[UserArchetype.PATIENT] = 20
        
        # Determinar arquetipo con mayor puntuación
        max_score = max(scores.values())
        if max_score > 10:  # Umbral mínimo
            for archetype, score in scores.items():
                if score == max_score:
                    return archetype
        
        return None
    
    async def _post_process_interaction(
        self,
        session: AsyncSession,
        user: User,
        narrative_state: NarrativeState
    ):
        """Post-procesamiento después de cada interacción"""
        
        # Actualizar última interacción
        user.last_diana_interaction = datetime.utcnow()
        narrative_state.last_meaningful_interaction = datetime.utcnow()
        
        # Evaluar progresión de relación
        if narrative_state.total_interactions > 5:
            await self._evaluate_relationship_progression(
                session, user, narrative_state
            )
        
        await session.commit()
    
    async def _evaluate_relationship_progression(
        self,
        session: AsyncSession,
        user: User,
        narrative_state: NarrativeState
    ):
        """Evalúa si la relación debe progresar a la siguiente etapa"""
        
        # Criterios por etapa
        progression_criteria = {
            "stranger_to_curious": {
                "interactions": 3,
                "trust": 0.1
            },
            "curious_to_acquaintance": {
                "interactions": 10,
                "trust": 0.3,
                "vulnerabilities": 1
            },
            "acquaintance_to_trusted": {
                "interactions": 25,
                "trust": 0.5,
                "vulnerabilities": 3,
                "meaningful_conversations": 5
            },
            "trusted_to_confidant": {
                "interactions": 50,
                "trust": 0.7,
                "vulnerabilities": 5,
                "meaningful_conversations": 10,
                "boundary_respect": 3
            },
            "confidant_to_intimate": {
                "interactions": 100,
                "trust": 0.85,
                "vulnerabilities": 10,
                "meaningful_conversations": 20,
                "boundary_respect": 5,
                "special_requirement": "chosen_ending_path"
            }
        }
        
        # Determinar siguiente etapa
        current_stage = narrative_state.relationship_stage.value
        next_stage = None
        
        stage_order = ["stranger", "curious", "acquaintance", "trusted", "confidant", "intimate"]
        current_index = stage_order.index(current_stage)
        
        if current_index < len(stage_order) - 1:
            next_stage = stage_order[current_index + 1]
            criteria_key = f"{current_stage}_to_{next_stage}"
            
            if criteria_key in progression_criteria:
                criteria = progression_criteria[criteria_key]
                
                # Verificar todos los criterios
                meets_criteria = True
                
                if narrative_state.total_interactions < criteria.get("interactions", 0):
                    meets_criteria = False
                
                if narrative_state.trust_level < criteria.get("trust", 0):
                    meets_criteria = False
                
                if narrative_state.vulnerabilities_shared < criteria.get("vulnerabilities", 0):
                    meets_criteria = False
                
                if narrative_state.meaningful_conversations < criteria.get("meaningful_conversations", 0):
                    meets_criteria = False
                
                if narrative_state.times_respected_boundaries < criteria.get("boundary_respect", 0):
                    meets_criteria = False
                
                # Requisitos especiales
                special_req = criteria.get("special_requirement")
                if special_req == "chosen_ending_path" and not user.chosen_ending_path:
                    meets_criteria = False
                
                # Si cumple todos los criterios, avanzar
                if meets_criteria:
                    from database.narrative_models import RelationshipStage
                    narrative_state.relationship_stage = RelationshipStage(next_stage)
                    
                    # Notificar al usuario sobre la progresión
                    # (Esto se maneja en otro lugar, solo marcamos el cambio)
                    narrative_state.key_decisions[f"progression_to_{next_stage}"] = datetime.utcnow().isoformat()
    
    def _get_chapter(self, narrative_level: int) -> str:
        """Obtiene el capítulo narrativo según el nivel"""
        
        chapters = {
            0: "prologue",
            1: "the_invitation",
            2: "first_observations",
            3: "the_kinky_revelation",
            4: "beyond_the_wall",
            5: "emotional_depths", 
            6: "ultimate_connection"
        }
        
        return chapters.get(narrative_level, "epilogue")

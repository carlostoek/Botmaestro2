# handlers/narrative/diana_dialogue.py
"""
Handler principal para las interacciones con Diana.
Maneja todos los diálogos y la progresión narrativa.
"""

from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.narrative_models import NarrativeState, RelationshipStage
from database.models import User
from services.narrative.dialogue_manager import DianaDialogueManager
from services.narrative.memory_system import MemoryCallbackSystem
from handlers.utils import check_user_in_vip_channel

router = Router(name="diana_dialogue")
dialogue_manager = DianaDialogueManager()
memory_system = MemoryCallbackSystem()

class DianaStates(StatesGroup):
    """Estados de conversación con Diana"""
    greeting = State()
    conversation = State()
    deep_conversation = State()
    vulnerable_moment = State()
    mission_briefing = State()
    emotional_response = State()

@router.message(Command("diana"))
async def cmd_diana(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
    user: User
):
    """Comando principal para iniciar conversación con Diana"""
    
    # Verificar acceso según nivel
    if user.narrative_level == 0:
        await message.answer(
            "🎩 <b>Lucien:</b> Diana no está disponible en este momento. "
            "Quizás más adelante, cuando hayas progresado más en tu viaje..."
        )
        return
    
    # Obtener o crear estado narrativo
    narrative_state = await session.get(NarrativeState, user.id)
    if not narrative_state:
        narrative_state = NarrativeState(user_id=user.id)
        session.add(narrative_state)
        await session.commit()
    
    # Generar saludo contextual
    greeting = await dialogue_manager.generate_contextual_response(
        session,
        user.id,
        "greeting",
        {"first_interaction": narrative_state.total_interactions == 0}
    )
    
    # Enviar saludo con foto apropiada
    photo_url = await _get_contextual_photo(narrative_state)
    
    await message.answer_photo(
        photo=photo_url,
        caption=f"🌸 <b>Diana:</b> {greeting}"
    )
    
    # Actualizar estado
    narrative_state.total_interactions += 1
    await session.commit()
    
    # Establecer estado de conversación
    await state.set_state(DianaStates.conversation)
    await state.update_data(
        conversation_start=datetime.utcnow(),
        messages_count=0,
        emotional_depth=0
    )

@router.message(DianaStates.conversation)
async def handle_conversation(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
    user: User
):
    """Maneja la conversación general con Diana"""
    
    narrative_state = await session.get(NarrativeState, user.id)
    state_data = await state.get_data()
    
    # Analizar mensaje y generar respuesta
    response, analysis = await dialogue_manager.process_user_response(
        session,
        user.id,
        message.text,
        {
            "chapter": _get_current_chapter(user),
            "conversation_depth": state_data.get("emotional_depth", 0),
            "messages_in_conversation": state_data.get("messages_count", 0)
        }
    )
    
    # Verificar si debemos transicionar a un momento más profundo
    if analysis.get("vulnerability_indicators", 0) > 2:
        await state.set_state(DianaStates.vulnerable_moment)
        response = await _handle_vulnerable_moment(
            session, user, narrative_state, message.text, response
        )
    
    # Buscar memorias relevantes para callback
    if state_data.get("messages_count", 0) > 3:  # Después de algunos mensajes
        relevant_memory = await memory_system.find_relevant_memory(
            session,
            user.id,
            {"emotional_tone": analysis.get("emotional_tone", "neutral")}
        )
        
        if relevant_memory:
            memory_reference = await memory_system.reference_memory(
                session, relevant_memory
            )
            response = f"{memory_reference}\n\n{response}"
    
    # Enviar respuesta con foto apropiada
    photo_url = await _get_contextual_photo(
        narrative_state, 
        emotional_context=analysis.get("emotional_context")
    )
    
    await message.answer_photo(
        photo=photo_url,
        caption=f"🌸 <b>Diana:</b> {response}"
    )
    
    # Actualizar métricas
    await state.update_data(
        messages_count=state_data.get("messages_count", 0) + 1,
        emotional_depth=state_data.get("emotional_depth", 0) + analysis.get("emotional_value", 0)
    )

async def _handle_vulnerable_moment(
    session: AsyncSession,
    user: User,
    narrative_state: NarrativeState,
    user_message: str,
    initial_response: str
) -> str:
    """Maneja momentos de vulnerabilidad especial"""
    
    # Crear memoria si es significativo
    if narrative_state.vulnerability_shown < 0.5:  # Primera vulnerabilidad importante
        memory = await memory_system.create_memory(
            session,
            user.id,
            "vulnerability",
            user_message,
            initial_response,
            {
                "chapter": _get_current_chapter(user),
                "trigger": "user_vulnerability",
                "emotional_tone": "intimate"
            },
            {
                "trust": 0.2,
                "vulnerability": 0.3,
                "relationship": 0.2,
                "is_breakthrough": True
            }
        )
        
        # Actualizar estado narrativo
        narrative_state.vulnerability_shown += 0.1
        narrative_state.trust_level += 0.05
        
        if not user.has_shared_vulnerability:
            user.has_shared_vulnerability = True
            await session.commit()
            
            # Respuesta especial por primera vulnerabilidad
            return (
                f"{initial_response}\n\n"
                "[Diana se acerca un poco más, su expresión suavizándose]\n\n"
                "Gracias por confiar en mí con esto. No muchos se atreven a ser "
                "tan honestos... Significa más de lo que imaginas."
            )
    
    return initial_response

async def _get_contextual_photo(
    narrative_state: NarrativeState,
    emotional_context: Optional[Dict] = None
) -> str:
    """Selecciona foto apropiada según contexto"""
    
    # URLs de placeholder por ahora
    base_url = "https://placehold.co/1080x1350"
    
    # Mapeo de estados a descripciones para alt text
    photo_contexts = {
        RelationshipStage.STRANGER: {
            "default": f"{base_url}?text=Diana+Distant",
            "alt": "Diana de pie junto a una ventana, mirando hacia afuera con expresión contemplativa y distante, vestida elegantemente"
        },
        RelationshipStage.CURIOUS: {
            "default": f"{base_url}?text=Diana+Curious", 
            "alt": "Diana sentada en un sofá, mirando directamente con una sonrisa sutil y curiosa, ambiente cálido pero con cierta reserva"
        },
        RelationshipStage.ACQUAINTANCE: {
            "default": f"{base_url}?text=Diana+Warm",
            "alt": "Diana en una pose más relajada, sonrisa genuina, en un ambiente acogedor con luz suave"
        },
        RelationshipStage.TRUSTED: {
            "default": f"{base_url}?text=Diana+Open",
            "alt": "Diana con expresión abierta y cálida, postura relajada, ambiente íntimo con iluminación dorada"
        },
        RelationshipStage.CONFIDANT: {
            "default": f"{base_url}?text=Diana+Intimate",
            "alt": "Diana en un momento íntimo, expresión vulnerable pero confiada, ambiente muy personal"
        },
        RelationshipStage.INTIMATE: {
            "default": f"{base_url}?text=Diana+Connected",
            "alt": "Diana completamente relajada y auténtica, mirada profunda y significativa, ambiente de total confianza"
        },
    }
    
    # Ajustar según contexto emocional si se proporciona
    if emotional_context:
        if emotional_context.get("vulnerability", 0) > 0.7:
            return f"{base_url}?text=Diana+Vulnerable"
        elif emotional_context.get("playfulness", 0) > 0.7:
            return f"{base_url}?text=Diana+Playful"
        elif emotional_context.get("intensity", 0) > 0.7:
            return f"{base_url}?text=Diana+Intense"
    
    # Retornar según stage de relación
    stage_photos = photo_contexts.get(
        narrative_state.relationship_stage,
        photo_contexts[RelationshipStage.STRANGER]
    )
    
    return stage_photos["default"]

def _get_current_chapter(user: User) -> str:
    """Determina el capítulo narrativo actual basado en el nivel"""
    
    chapters = {
        0: "prologue",
        1: "the_invitation",
        2: "first_observations", 
        3: "the_kinky_revelation",
        4: "beyond_the_wall",
        5: "emotional_depths",
        6: "ultimate_connection"
    }
    
    return chapters.get(user.narrative_level, "unknown")

@router.message(Command("diana_stats"))
async def cmd_diana_stats(
    message: types.Message,
    session: AsyncSession,
    user: User
):
    """Muestra estadísticas de la relación con Diana"""
    
    narrative_state = await session.get(NarrativeState, user.id)
    if not narrative_state:
        await message.answer("Aún no has comenzado tu historia con Diana.")
        return
    
    # Obtener resumen de memorias
    memories_summary = await memory_system.get_shared_memories_summary(
        session, user.id
    )
    
    # Generar estadísticas
    trust_bar = "█" * int(narrative_state.trust_level * 10)
    vulnerability_bar = "█" * int(narrative_state.vulnerability_shown * 10)
    
    stats_text = f"""
📊 <b>Tu Relación con Diana</b>

🤝 <b>Etapa:</b> {narrative_state.relationship_stage.value}
🗨️ <b>Conversaciones:</b> {narrative_state.total_interactions}

<b>Niveles de Conexión:</b>
Confianza: {trust_bar} {narrative_state.trust_level:.0%}
Vulnerabilidad: {vulnerability_bar} {narrative_state.vulnerability_shown:.0%}

<b>Memorias Compartidas:</b> {memories_summary['total_memories']}
├ Momentos Especiales: {memories_summary['breakthrough_moments']}
└ Impacto Promedio: {'⭐' * int(memories_summary.get('average_trust_impact', 0) * 5)}

<b>Tu Perfil:</b> {narrative_state.user_archetype.value if narrative_state.user_archetype else 'Por descubrir'}
"""
    
    if memories_summary.get('most_impactful'):
        stats_text += f"\n<b>Momento más significativo:</b> {memories_summary['most_impactful']['type']}"
    
    await message.answer(stats_text)
        

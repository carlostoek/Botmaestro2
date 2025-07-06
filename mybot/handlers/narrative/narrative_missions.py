# handlers/narrative/narrative_missions.py
"""
Sistema de misiones con contexto narrativo.
Integra las misiones existentes con la narrativa de Diana.
"""

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from typing import Dict, List, Optional, Tuple  # Agrega esta línea

from database.models import Mission, UserMissionEntry, User
from database.narrative_models import NarrativeState, LorePiece, UserLorePiece
from services.narrative.dialogue_manager import DianaDialogueManager

router = Router(name="narrative_missions")
dialogue_manager = DianaDialogueManager()

async def get_narrative_missions(
    session: AsyncSession,
    user: User,
    narrative_state: NarrativeState
) -> List[Mission]:
    """Obtiene misiones disponibles según el estado narrativo"""
    
    # Query base de misiones activas
    query = select(Mission).filter(
        and_(
            Mission.is_active == True,
            Mission.narrative_chapter == _get_current_chapter(user)
        )
    )
    
    # Filtrar por requisitos narrativos
    if narrative_state:
        # Solo mostrar misiones apropiadas para la etapa de relación
        query = query.filter(
            or_(
                Mission.requires_relationship_stage == None,
                Mission.requires_relationship_stage <= narrative_state.relationship_stage.value
            )
        )
    
    result = await session.execute(query)
    missions = result.scalars().all()
    
    # Filtrar misiones ya completadas
    completed_missions = await _get_completed_mission_ids(session, user.id)
    available_missions = [m for m in missions if m.id not in completed_missions]
    
    return available_missions

async def assign_narrative_mission(
    session: AsyncSession,
    user: User,
    mission: Mission,
    narrative_state: NarrativeState
) -> str:
    """Asigna una misión con contexto narrativo"""
    
    # Crear entrada de misión
    mission_entry = UserMissionEntry(
        user_id=user.id,
        mission_id=mission.id,
        progress_value=0,
        completed=False
    )
    session.add(mission_entry)
    
    # Generar diálogo de Diana para la misión
    if mission.diana_intro_dialogue:
        diana_dialogue = mission.diana_intro_dialogue
    else:
        # Generar diálogo contextual
        diana_dialogue = await dialogue_manager.generate_contextual_response(
            session,
            user.id,
            "mission_introduction",
            {
                "mission_name": mission.name,
                "mission_type": mission.type,
                "reward_points": mission.reward_points
            }
        )
    
    await session.commit()
    
    return diana_dialogue

async def complete_narrative_mission(
    session: AsyncSession,
    user: User,
    mission: Mission,
    narrative_state: NarrativeState
) -> Dict:
    """Completa una misión y maneja las recompensas narrativas"""
    
    result = {
        "points_earned": mission.reward_points,
        "diana_response": "",
        "lore_unlocked": None,
        "relationship_impact": 0.0
    }
    
    # Marcar misión como completada
    mission_entry = await session.execute(
        select(UserMissionEntry).filter(
            and_(
                UserMissionEntry.user_id == user.id,
                UserMissionEntry.mission_id == mission.id
            )
        )
    )
    mission_entry = mission_entry.scalar_one()
    mission_entry.completed = True
    mission_entry.completed_at = datetime.utcnow()
    
    # Otorgar puntos
    user.points += mission.reward_points
    
    # Generar respuesta de Diana
    if mission.diana_completion_dialogue:
        result["diana_response"] = mission.diana_completion_dialogue
    else:
        result["diana_response"] = await dialogue_manager.generate_contextual_response(
            session,
            user.id,
            "mission_complete",
            {
                "mission_name": mission.name,
                "points_earned": mission.reward_points
            }
        )
    
    # Desbloquear lore si corresponde
    if mission.unlocks_lore_piece_code:
        lore_piece = await session.get(LorePiece, mission.unlocks_lore_piece_code)
        if lore_piece:
            # Agregar a la mochila del usuario
            user_lore = UserLorePiece(
                user_id=user.id,
                lore_piece_code=lore_piece.code,
                found_context="mission_reward",
                discovery_method=f"Completar misión: {mission.name}"
            )
            session.add(user_lore)
            
            result["lore_unlocked"] = {
                "name": lore_piece.name,
                "description": lore_piece.description,
                "diana_comment": lore_piece.diana_comment_on_find
            }
    
    # Impacto en la relación
    if mission.affects_trust and narrative_state:
        narrative_state.trust_level += mission.trust_impact
        narrative_state.trust_level = max(0.0, min(1.0, narrative_state.trust_level))
        result["relationship_impact"] = mission.trust_impact
    
    await session.commit()
    
    return result

@router.callback_query(F.data.startswith("narrative_mission:"))
async def handle_narrative_mission_selection(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Maneja la selección de misiones narrativas"""
    
    mission_id = callback.data.split(":")[1]
    mission = await session.get(Mission, mission_id)
    
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    
    narrative_state = await session.get(NarrativeState, user.id)
    if not narrative_state:
        narrative_state = NarrativeState(user_id=user.id)
        session.add(narrative_state)
        await session.commit()
    
    # Asignar misión
    diana_dialogue = await assign_narrative_mission(
        session, user, mission, narrative_state
    )
    
    # Mostrar detalles de la misión
    mission_text = f"""
🌸 <b>Diana:</b> {diana_dialogue}

📜 <b>{mission.name}</b>
{mission.description}

🎁 <b>Recompensa:</b> {mission.reward_points} besitos
"""
    
    if mission.unlocks_lore_piece_code:
        mission_text += "🔓 <b>Desbloqueará:</b> Nueva pista para tu mochila\n"
    
    if mission.affects_trust:
        impact_emoji = "📈" if mission.trust_impact > 0 else "📉"
        mission_text += f"{impact_emoji} <b>Impacto en confianza:</b> {'Positivo' if mission.trust_impact > 0 else 'Cuidado'}\n"
    
    # Keyboard con opciones
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="📋 Ver Progreso",
                callback_data=f"mission_progress:{mission.id}"
            )
        ],
        [
            types.InlineKeyboardButton(
                text="↩️ Volver",
                callback_data="narrative_missions_menu"
            )
        ]
    ])
    
    await callback.message.edit_text(mission_text, reply_markup=keyboard)
    await callback.answer()

def _get_current_chapter(user: User) -> str:
    """Determina el capítulo narrativo actual"""
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

async def _get_completed_mission_ids(
    session: AsyncSession,
    user_id: int
) -> List[str]:
    """Obtiene IDs de misiones completadas"""
    result = await session.execute(
        select(UserMissionEntry.mission_id).filter(
            and_(
                UserMissionEntry.user_id == user_id,
                UserMissionEntry.completed == True
            )
        )
    )
    return [row[0] for row in result]
      

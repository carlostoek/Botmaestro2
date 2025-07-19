from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from modules.narrative.story_engine import NarrativeEngine
from keyboards.narrative_kb import get_decision_keyboard

router = Router()

@router.message(Command("start_story"))
async def start_story_command(message: Message, session: AsyncSession):
    """Inicia la historia para el usuario"""
    engine = NarrativeEngine(session)
    fragment = await engine.start_story(message.from_user.id)
    
    await message.answer(
        fragment.content,
        reply_markup=get_decision_keyboard(fragment)
    )

@router.callback_query(F.data.startswith("narrative_choice:"))
async def handle_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Maneja una elección narrativa del usuario"""
    user_id = callback.from_user.id
    _, fragment_id, choice_index = callback.data.split(":")
    choice_index = int(choice_index)
    
    engine = NarrativeEngine(session)
    try:
        next_fragment = await engine.process_decision(user_id, choice_index)
        await callback.message.edit_text(
            next_fragment.content,
            reply_markup=get_decision_keyboard(next_fragment)
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)
        logger.error(f"Error en decisión narrativa: {str(e)}")

@router.message(Command("story_status"))
async def story_status_command(message: Message, session: AsyncSession):
    """Muestra el estado actual de la historia del usuario"""
    engine = NarrativeEngine(session)
    state = await engine.get_user_state(message.from_user.id)
    current_fragment = await engine.get_fragment(state.current_fragment_id)
    
    response = (
        f"📖 **Tu progreso en la historia:**\n"
        f"• Fragmento actual: {current_fragment.fragment_id}\n"
        f"• Progreso total: {state.story_progress}%\n"
        f"• Fragmentos desbloqueados: {len(state.unlocked_fragments)}\n"
        f"\nContenido actual:\n{current_fragment.content}"
    )
    
    await message.answer(
        response,
        reply_markup=get_decision_keyboard(current_fragment)
    )
  

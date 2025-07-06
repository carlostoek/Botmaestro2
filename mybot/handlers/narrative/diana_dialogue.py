# mybot/handlers/narrative/diana_dialogue.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from services.narrative_service import NarrativeService

router = Router(name="diana_dialogue")
logger = logging.getLogger(__name__)

@router.message(Command("diana"))
async def start_diana_dialogue(message: Message, session, bot):
    """Comando para iniciar diálogo con Diana"""
    user_id = message.from_user.id

    # Obtener estado narrativo
    narrative_state = await NarrativeService.get_or_create_narrative_state(session, user_id)

    # Respuesta basada en el nivel de relación
    if narrative_state.relationship_stage.value == "stranger":
        response = "Oh... no esperaba compañía. ¿Quién eres?"
    elif narrative_state.relationship_stage.value == "curious":
        response = "Ah, eres tú otra vez... Interesante."
    else:
        response = f"Hola de nuevo... (Confianza: {narrative_state.trust_level:.1%})"

    await message.answer(response)

    # Actualizar interacciones
    narrative_state.total_interactions += 1
    await session.commit()

@router.message(F.text & F.reply_to_message)
async def diana_response(message: Message, session, bot):
    """Responde a mensajes cuando Diana está activa"""
    # Por ahora, solo registramos la interacción
    if message.reply_to_message.from_user.id == bot.id:
        user_id = message.from_user.id

        # Actualizar confianza ligeramente
        await NarrativeService.update_trust_level(session, user_id, 0.01)

        await message.answer("*Diana te observa con curiosidad*")


from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("ip_"))
async def handle_interactive_post_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    """Handle interactive post reactions with improved error handling."""
    try:
        parts = callback.data.split("_")
        if len(parts) < 3:
            logger.warning(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Formato de datos inválido")
            return
            
        reaction_type = parts[1]  # e.g. 'r0'
        try:
            message_id = int(parts[2])
        except ValueError:
            logger.warning(f"Invalid message ID in callback: {callback.data}")
            await callback.answer("❌ ID de mensaje inválido")
            return

        service = MessageService(session, bot)
        await service.register_reaction(callback.from_user.id, message_id, reaction_type)
        await callback.answer("⚡ ¡Gracias por reaccionar!")
        
    except Exception as e:
        logger.error(f"Error handling interactive post callback: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar la reacción")
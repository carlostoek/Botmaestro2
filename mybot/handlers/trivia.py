import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards import trivia_kb
from services import trivia_service
from utils import messages
from utils.menu_manager import MenuManager

logger = logging.getLogger(__name__)
router = Router()

menu_manager = MenuManager()

@router.message(Command("trivia"))
async def cmd_trivia(message: Message, session: AsyncSession, bot: Bot):
    user_id = message.from_user.id
    mission_id = None
    logger.info(f"Comando /trivia recibido de usuario {user_id}.")
    await _send_trivia_question(message, session, bot, user_id, mission_id)

async def _send_trivia_question(message_or_callback: Message | CallbackQuery, session: AsyncSession, bot: Bot, user_id: int, mission_id: str = None):
    if isinstance(message_or_callback, CallbackQuery):
        chat_id = message_or_callback.message.chat.id
        message_id = message_or_callback.message.message_id
        is_callback = True
    else:
        chat_id = message_or_callback.chat.id
        message_id = None
        is_callback = False

    question = await trivia_service.get_random_trivia_question(session, user_id, mission_id)

    if question:
        options = trivia_service.parse_options_from_db(question.options)
        keyboard = trivia_kb.get_trivia_options_keyboard(options, question.id)
        trivia_text = messages.TRIVIA_QUESTION_TEMPLATE.format(question_text=question.question)

        if is_callback:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=trivia_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await message_or_callback.answer()
        else:
            await menu_manager.send_message(
                message_or_callback,
                trivia_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        logger.info(f"Trivia {question.id} enviada a usuario {user_id}.")
    else:
        response_text = messages.TRIVIA_NO_MORE_AVAILABLE
        reply_markup = trivia_kb.get_generic_back_keyboard()

        if is_callback:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=response_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            await message_or_callback.answer()
        else:
            await menu_manager.send_message(
                message_or_callback,
                response_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        logger.info(f"No hay trivias para mostrar al usuario {user_id}.")

@router.callback_query(F.data.startswith("trivia_answer:"))
async def process_trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback.from_user.id
    message_id = callback.message.message_id
    chat_id = callback.message.chat.id

    parts = callback.data.split(':')
    question_id = int(parts[1])
    selected_option = ":".join(parts[2:])

    logger.info(f"Usuario {user_id} respondió trivia {question_id} con: '{selected_option}'")

    if await trivia_service.check_if_trivia_answered_correctly(session, user_id, question_id):
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=messages.TRIVIA_ALREADY_ANSWERED,
            reply_markup=trivia_kb.get_generic_back_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(messages.TRIVIA_ALREADY_ANSWERED, show_alert=True)
        return

    question = await session.get(TriviaQuestion, question_id)
    if not question:
        logger.error(f"Pregunta {question_id} no encontrada al procesar respuesta.")
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=messages.TRIVIA_NO_MORE_AVAILABLE,
            reply_markup=trivia_kb.get_generic_back_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Error: Trivia no encontrada.", show_alert=True)
        return

    is_correct = (selected_option == question.correct_option)
    response_text = ""
    reply_markup = None

    if is_correct:
        response_text = await trivia_service.handle_correct_answer(session, user_id, question_id, bot)
        reply_markup = trivia_kb.get_generic_back_keyboard()
        await callback.answer("¡Correcto!", show_alert=True)
    else:
        response_text = await trivia_service.handle_incorrect_answer(session, user_id, question_id)
        current_attempts = await trivia_service.get_trivia_attempts(session, user_id, question_id)
        if trivia_service.ALLOW_RETRY_ON_INCORRECT and current_attempts < trivia_service.MAX_INCORRECT_ATTEMPTS:
            reply_markup = trivia_kb.get_trivia_retry_keyboard(question_id)
            await callback.answer("Incorrecto.", show_alert=True)
        else:
            reply_markup = trivia_kb.get_generic_back_keyboard()
            await callback.answer(messages.TRIVIA_NO_RETRY_ALLOWED, show_alert=True)

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=response_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("trivia_retry:"))
async def process_trivia_retry(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback.from_user.id
    logger.info(f"Usuario {user_id} solicitó reintento de trivia.")

    await _send_trivia_question(callback, session, bot, user_id, mission_id=None)
    await callback.answer("Buscando otra trivia...")

@router.callback_query(F.data.startswith("trivia_cancel_retry:"))
async def process_trivia_cancel_retry(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    user_id = callback.from_user.id
    logger.info(f"Usuario {user_id} canceló reintento de trivia.")

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="De acuerdo, el mayordomo comprende. Quizás la próxima vez tu intelecto esté más afilado.",
        reply_markup=trivia_kb.get_generic_back_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Reintento cancelado.")


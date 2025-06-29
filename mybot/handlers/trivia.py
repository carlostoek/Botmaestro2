from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TriviaQuestion

from utils.messages import BOT_MESSAGES
from keyboards.trivia_kb import (
    get_trivia_options_keyboard,
    get_trivia_retry_keyboard,
    get_generic_back_keyboard,
)
from services.trivia_service import TriviaService, parse_options_from_db

router = Router()


@router.message(F.text.regexp("^/trivia$"))
async def command_trivia(message: Message, session: AsyncSession):
    service = TriviaService(session)
    question = await service.get_random_trivia_question(message.from_user.id)
    if not question:
        await message.answer(BOT_MESSAGES.get("trivia_no_questions", "No hay preguntas."))
        return
    options = parse_options_from_db(question.options)
    kb = get_trivia_options_keyboard(question.id, options)
    await message.answer(question.question, reply_markup=kb)


@router.callback_query(F.data.startswith("trivia_answer:"))
async def process_trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    _, qid, index = callback.data.split(":")
    question = await session.get(TriviaQuestion, int(qid))
    options = parse_options_from_db(question.options)
    selected = options[int(index)] if int(index) < len(options) else None
    is_correct = selected == question.correct_option
    service = TriviaService(session)
    if is_correct:
        await service.record_trivia_result(callback.from_user.id, question.id, True)
        await service.handle_correct_answer(callback.from_user.id, question, bot=bot)
        await callback.message.edit_text(
            BOT_MESSAGES.get("trivia_correct_answer", "¡Correcto!").format(points=question.points),
            reply_markup=get_generic_back_keyboard(),
        )
    else:
        await service.record_trivia_result(callback.from_user.id, question.id, False)
        await callback.message.edit_text(
            BOT_MESSAGES.get("trivia_wrong_answer", "Incorrecto"),
            reply_markup=get_trivia_retry_keyboard(question.id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("trivia_retry:"))
async def trivia_retry(callback: CallbackQuery, session: AsyncSession):
    _, qid = callback.data.split(":")
    question = await session.get(TriviaQuestion, int(qid))
    options = parse_options_from_db(question.options)
    kb = get_trivia_options_keyboard(question.id, options)
    await callback.message.edit_text(question.question, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "trivia_cancel")
async def trivia_cancel(callback: CallbackQuery):
    await callback.message.edit_text(BOT_MESSAGES.get("trivia_back", "Volver"))
    await callback.answer()

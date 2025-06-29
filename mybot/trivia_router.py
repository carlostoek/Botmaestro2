# No coloques mybot como módulo, es la raíz del proyecto
from __future__ import annotations

import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from mybot.quests.trivia_quest_integration import TriviaQuestIntegration
from services.trivia_service import TriviaService
from utils.user_roles import get_user_role, is_admin

router = Router()

# Store active trivia per user_id -> {"question_id": int, "start": datetime}
_active_trivia: dict[int, dict] = {}


@router.message(F.text == "🧩 Trivia")
async def start_trivia(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)
    user_access = "vip" if role in {"vip", "admin"} else "free"

    service = TriviaService(session)
    question = await service.get_random_question(user_access=user_access)
    if not question:
        await message.answer("No hay preguntas de trivia disponibles.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"trivia_{question['id']}_{i}")]
            for i, opt in enumerate(question["options"])
        ]
    )
    await message.answer(question["question"], reply_markup=keyboard)
    _active_trivia[user_id] = {"question_id": question["id"], "start": datetime.datetime.utcnow()}


@router.callback_query(F.data.startswith("trivia_"))
async def trivia_response(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    parts = callback.data.split("_")
    if len(parts) != 3:
        await callback.answer("Trivia inválida", show_alert=True)
        return

    _, qid, opt = parts
    try:
        question_id = int(qid)
        option = int(opt)
    except ValueError:
        await callback.answer("Datos de trivia inválidos", show_alert=True)
        return

    user_id = callback.from_user.id
    info = _active_trivia.pop(user_id, None)
    response_time = None
    if info and info.get("question_id") == question_id:
        start: datetime.datetime = info["start"]
        response_time = int((datetime.datetime.utcnow() - start).total_seconds())

    service = TriviaService(session)
    result = await service.save_trivia_answer(user_id, question_id, option, response_time)

    missions_completed = await TriviaQuestIntegration.check_trivia_missions(user_id, result, session, bot)
    stats = await service.get_user_trivia_stats(user_id)
    special_missions = await TriviaQuestIntegration.trigger_special_missions(user_id, stats, session, bot)

    if result["is_correct"]:
        text = (
            f"✅ ¡Correcto! Has ganado {result['points']} puntos.\n"
            f"Bonus por tiempo: {result['time_bonus']} puntos."
        )
        if result.get("lore_piece"):
            text += f"\nHas desbloqueado: {result['lore_piece']}"
    else:
        text = "❌ Respuesta incorrecta."

    stats = await service.get_user_trivia_stats(user_id)
    text += (
        "\n\n📊 Tus estadísticas:\n"
        f"Preguntas respondidas: {stats['total']}\n"
        f"Respuestas correctas: {stats['correct']}\n"
        f"Precisión: {stats['accuracy']*100:.1f}%\n"
        f"Racha actual: {stats['streak']}\n"
        f"Mejor racha: {stats['best_streak']}\n"
        f"Puntos totales: {stats['points']}"
    )

    await callback.message.edit_text(text)

    for mission in missions_completed + special_missions:
        await callback.message.answer(
            f"🎯 *Misión completada:* {mission['description']}\n"
            f"🏆 *Recompensa:* {mission['reward_points']} puntos y {mission['reward_lorepiece']}"
        )
    await callback.answer()
@router.message(F.text == "📊 Mis Estadísticas de Trivia")
async def show_stats(message: Message, session: AsyncSession):
    service = TriviaService(session)
    stats = await service.get_user_trivia_stats(message.from_user.id)
    text = (
        "📊 Estadísticas de Trivia:\n"
        f"Preguntas respondidas: {stats['total']}\n"
        f"Respuestas correctas: {stats['correct']}\n"
        f"Precisión: {stats['accuracy']*100:.1f}%\n"
        f"Racha actual: {stats['streak']}\n"
        f"Mejor racha: {stats['best_streak']}\n"
        f"Puntos totales: {stats['points']}"
    )
    await message.answer(text)


@router.message(F.text.startswith("/add_trivia"))
async def add_trivia(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        await message.answer("Acceso denegado")
        return

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("Formato inválido")
        return

    data = parts[1].split("|")
    if len(data) < 9:
        await message.answer("Faltan parámetros")
        return

    question = data[0]
    options = data[1:5]
    try:
        correct_idx = int(data[5])
    except ValueError:
        await message.answer("Índice de respuesta inválido")
        return

    category = data[6]
    difficulty = data[7]
    access = data[8]
    lore_piece = data[9] if len(data) > 9 else None

    service = TriviaService(session)
    q = await service.add_trivia_question(
        question,
        options,
        correct_idx,
        category,
        difficulty,
        access,
        lore_piece,
    )
    await message.answer(f"Pregunta guardada con ID {q.id}")


@router.message(F.text.startswith("/trivia_admin"))
async def trivia_admin_panel(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        await message.answer("Acceso denegado")
        return

    service = TriviaService(session)
    stats = await service.get_trivia_statistics()
    text = (
        "📊 Estadísticas del Sistema de Trivia:\n"
        f"Preguntas registradas: {stats['total_questions']}\n"
        f"Respuestas registradas: {stats['total_answers']}\n"
        f"Jugadores: {stats['total_players']}"
    )
    await message.answer(text)


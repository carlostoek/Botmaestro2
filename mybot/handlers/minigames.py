from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from services.config_service import ConfigService
from services.point_service import PointService
from services.minigame_service import MiniGameService
from utils.messages import BOT_MESSAGES
from services.reaction_service import ReactionService
import random

router = Router()

TRIVIA = [
    {
        "q": "¿Capital de Francia?",
        "opts": ["Madrid", "París", "Roma"],
        "answer": 1,
    },
    {
        "q": "¿Cuántos días tiene una semana?",
        "opts": ["5", "7", "10"],
        "answer": 1,
    },
    {
        "q": "¿Color resultante de mezclar rojo y azul?",
        "opts": ["Verde", "Morado", "Amarillo"],
        "answer": 1,
    },
]

@router.message(F.text.regexp("/dice"))
async def play_dice(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    dice_msg = await bot.send_dice(message.chat.id)
    score = dice_msg.dice.value
    await PointService(session).add_points(message.from_user.id, score, bot=bot)
    await message.answer(BOT_MESSAGES.get("dice_points", "Ganaste {points} puntos").format(points=score))


@router.message(F.text.regexp("/roulette"))
async def play_roulette(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    mg_service = MiniGameService(session)
    if await mg_service.can_use_free(message.from_user.id, "roulette"):
        await mg_service.use_free(message.from_user.id, "roulette")
    elif not await mg_service.use_extra(message.from_user.id, "roulette"):
        return await message.answer(BOT_MESSAGES.get("roulette_no_free", "Ya usaste tu tiro gratis. Compra giros extra."))
    dice_msg = await bot.send_dice(message.chat.id)
    score = dice_msg.dice.value
    await PointService(session).add_points(message.from_user.id, score, bot=bot)
    await message.answer(BOT_MESSAGES.get("roulette_result", "Resultado {score}, ganaste {points} puntos.").format(score=score, points=score))


@router.message(F.text.regexp("/roulette_buy"))
async def buy_roulette_spin(message: Message, session: AsyncSession, bot: Bot):
    mg_service = MiniGameService(session)
    success = await mg_service.add_extra_uses(message.from_user.id, "roulette", 1, cost=5)
    if success:
        await message.answer(BOT_MESSAGES.get("roulette_bought", "Tiro extra comprado."))
    else:
        await message.answer(BOT_MESSAGES.get("roulette_buy_fail", "No tienes puntos suficientes."))

@router.message(F.text.regexp("/trivia"))
async def send_trivia(message: Message, session: AsyncSession):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    q = random.choice(TRIVIA)
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data="trivia_correct" if i==q["answer"] else "trivia_wrong")]
        for i, opt in enumerate(q["opts"])
    ]
    await message.answer(q["q"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.in_({"trivia_correct", "trivia_wrong"}))
async def trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        return await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
    if callback.data == "trivia_correct":
        await PointService(session).add_points(callback.from_user.id, 5, bot=bot)
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_correct", "¡Correcto! +5 puntos"))
    else:
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_wrong", "Respuesta incorrecta."))
    await callback.answer()


@router.message(F.text.regexp("/reto"))
async def reto_or_recompensa(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    target = 3
    seconds = 30
    await message.answer(
        BOT_MESSAGES.get("reto_start", "Reacciona a {target} publicaciones en {seconds} segundos.").format(
            target=target, seconds=seconds
        )
    )
    reaction_service = ReactionService(session)
    start = datetime.utcnow()
    await asyncio.sleep(seconds)
    count = await reaction_service.get_user_reaction_count(message.from_user.id, since=start)
    if count >= target:
        await PointService(session).add_points(message.from_user.id, 10, bot=bot)
        await message.answer(
            BOT_MESSAGES.get("reto_success", "¡Reto completado!"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=BOT_MESSAGES.get("reto_improve", "Mejorar recompensa (+5 puntos)"),
                            callback_data="reto_improve",
                        )
                    ]
                ]
            ),
        )
    else:
        await message.answer(
            BOT_MESSAGES.get("reto_failed", "No completaste el reto y perdiste puntos."),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=BOT_MESSAGES.get("reto_avoid", "Evitar penalización (5 puntos)"),
                            callback_data="reto_avoid",
                        )
                    ]
                ]
            ),
        )
        await PointService(session).deduct_points(message.from_user.id, 5)


@router.callback_query(F.data == "reto_improve")
async def reto_improve_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Handle reward upgrade purchase."""
    point_service = PointService(session)
    success = await point_service.deduct_points(callback.from_user.id, 5)
    if success:
        await point_service.add_points(callback.from_user.id, 10, bot=bot)
        await callback.message.edit_text(BOT_MESSAGES.get("reto_upgraded", "¡Recompensa mejorada!"))
    else:
        await callback.answer(BOT_MESSAGES.get("reto_no_points", "No tienes puntos suficientes."), show_alert=True)


@router.callback_query(F.data == "reto_avoid")
async def reto_avoid_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Allow user to pay to avoid the penalty."""
    point_service = PointService(session)
    success = await point_service.deduct_points(callback.from_user.id, 5)
    if success:
        await point_service.add_points(callback.from_user.id, 5, bot=None)
        await callback.message.edit_text(BOT_MESSAGES.get("reto_penalty_avoided", "Penalización evitada."))
    else:
        await callback.answer(BOT_MESSAGES.get("reto_no_points", "No tienes puntos suficientes."), show_alert=True)

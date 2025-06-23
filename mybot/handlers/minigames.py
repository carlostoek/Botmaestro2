from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
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
    await message.answer(BOT_MESSAGES.get("reto_start", "Reacciona a {target} publicaciones en {seconds} segundos.").format(target=target, seconds=seconds))
    await asyncio.sleep(seconds)
    reaction_service = ReactionService(session)
    top = await reaction_service.get_weekly_top_users(limit=1)
    count = 0
    if top and top[0][0].id == message.from_user.id:
        count = top[0][1]
    if count >= target:
        await PointService(session).add_points(message.from_user.id, 10, bot=bot)
        await message.answer(BOT_MESSAGES.get("reto_success", "¡Reto completado!") )
    else:
        await PointService(session).deduct_points(message.from_user.id, 5)
        await message.answer(BOT_MESSAGES.get("reto_failed", "No completaste el reto y perdiste puntos."))

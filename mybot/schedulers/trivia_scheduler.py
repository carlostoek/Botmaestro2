# No coloques mybot como módulo, es la raíz del proyecto
import asyncio
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from services.trivia_service import TriviaService
from utils.config import CANAL_KINKYS_ID, CANAL_DIVAN_ID


async def _send_trivia(bot: Bot, session: AsyncSession, chat_id: int):
    service = TriviaService(session)
    question = await service.get_random_question()
    if not question:
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"trivia_{question['id']}_{i}")]
            for i, opt in enumerate(question["options"])
        ]
    )
    await bot.send_message(chat_id, question["question"], reply_markup=keyboard)


async def trivia_scheduler_worker(bot: Bot, session_factory: async_sessionmaker[AsyncSession]):
    """Background task to periodically post trivia questions."""
    logging.info("Trivia scheduler started")
    interval = 3600  # default: every hour
    try:
        while True:
            async with session_factory() as session:
                if CANAL_KINKYS_ID:
                    await _send_trivia(bot, session, CANAL_KINKYS_ID)
                if CANAL_DIVAN_ID and CANAL_DIVAN_ID != CANAL_KINKYS_ID:
                    await _send_trivia(bot, session, CANAL_DIVAN_ID)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logging.info("Trivia scheduler cancelled")
        raise
    except Exception:
        logging.exception("Unhandled error in trivia scheduler")

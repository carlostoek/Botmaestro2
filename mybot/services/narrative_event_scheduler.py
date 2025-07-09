import asyncio
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

async def start_narrative_scheduler(bot: Bot) -> None:
    """Scheduler para eventos narrativos."""
    while True:
        logger.debug("Narrative scheduler tick")
        # Aquí puedes agregar la lógica para manejar eventos narrativos
        await asyncio.sleep(3600)


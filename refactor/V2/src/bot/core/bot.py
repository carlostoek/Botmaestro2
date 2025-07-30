"""Configuración del bot."""

import structlog
from aiogram import Bot
from aiogram.types import BotCommand

from ..config.constants import COMMANDS

logger = structlog.get_logger()

async def setup_bot(bot: Bot) -> None:
    """Configura el bot."""
    # Establecer comandos
    commands = [
        BotCommand(command=command, description=description)
        for command, description in COMMANDS.items()
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Comandos del bot configurados", commands_count=len(commands))
    
    # Obtener información del bot
    bot_info = await bot.get_me()
    logger.info(
        "Bot inicializado", 
        username=bot_info.username,
        id=bot_info.id,
        can_join_groups=bot_info.can_join_groups,
        can_read_all_group_messages=bot_info.can_read_all_group_messages
    )
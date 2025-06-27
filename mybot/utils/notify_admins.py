import logging
from aiogram import Bot
from utils.config import ADMIN_IDS
from utils.text_utils import escape_html


async def notify_admins(bot: Bot, text: str) -> None:
    """Send a notification to all admins escaping HTML characters."""
    safe_text = escape_html(text)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, safe_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

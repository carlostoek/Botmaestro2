import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

logger = logging.getLogger(__name__)

class DebugMiddleware(BaseMiddleware):
    """Middleware para debugging detallado de usuarios normales"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        event_type = type(event).__name__

        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id

        if user_id and user_id != 1280444712:  # Reemplazar con tu admin ID
            if isinstance(event, Message):
                logger.info(f"\N{magnifying glass tilted left} DEBUG USER {user_id}: Message received")
                logger.info(f"   Text: {event.text}")
                logger.info(f"   Command: {event.text.startswith('/') if event.text else False}")
                logger.info(
                    f"   Handler chain: {handler.__name__ if hasattr(handler, '__name__') else 'Unknown'}"
                )

            elif isinstance(event, CallbackQuery):
                logger.info(f"\N{magnifying glass tilted left} DEBUG USER {user_id}: Callback received")
                logger.info(f"   Data: {event.data}")
                logger.info(
                    f"   Handler chain: {handler.__name__ if hasattr(handler, '__name__') else 'Unknown'}"
                )

        try:
            result = await handler(event, data)
            if user_id and user_id != 1280444712:
                logger.info(f"\N{check mark} DEBUG USER {user_id}: Handler executed successfully")
            return result

        except Exception as e:
            if user_id and user_id != 1280444712:
                logger.error(f"\N{cross mark} DEBUG USER {user_id}: Handler failed")
                logger.error(f"   Error: {type(e).__name__}: {e}")
                logger.error(f"   Event: {event_type}")
                if isinstance(event, Message) and event.text:
                    logger.error(f"   Text: {event.text}")
                elif isinstance(event, CallbackQuery):
                    logger.error(f"   Callback: {event.data}")
            raise

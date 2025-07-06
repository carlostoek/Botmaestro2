from typing import Any, Callable, Dict, Awaitable
import logging
from aiogram import BaseMiddleware

logger = logging.getLogger(__name__)

class NarrativeContextMiddleware(BaseMiddleware):
    """Middleware para adjuntar un contexto narrativo a los datos del manejador."""

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        data.setdefault("narrative_context", {})
        logger.info("Narrative context initialized.")
        return await handler(event, data)


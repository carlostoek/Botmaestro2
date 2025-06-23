from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from utils.config import DEFAULT_REACTION_BUTTONS


def get_back_kb(callback_data: str = "admin_back"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_interactive_post_kb(
    message_id: int,
    buttons: list[str] | None = None,
    counts: dict[str, int] | None = None,
    channel_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Return a keyboard with reaction buttons for channel posts.

    The markup is always returned as an ``InlineKeyboardMarkup`` instance even
    when no buttons are provided.
    """
    texts = [t for t in (buttons or DEFAULT_REACTION_BUTTONS) if t]
    builder = InlineKeyboardBuilder()

    for idx, text in enumerate(texts[:10]):
        count = counts.get(f"r{idx}", 0) if counts else 0
        display = f"{text} {count}" if counts else text
        if channel_id is not None:
            cb_data = f"ip_{channel_id}_r{idx}_{message_id}"
        else:
            cb_data = f"ip_r{idx}_{message_id}"
        builder.button(text=display, callback_data=cb_data)

    if texts:
        builder.adjust(min(len(texts[:10]), 5))

    return builder.as_markup()

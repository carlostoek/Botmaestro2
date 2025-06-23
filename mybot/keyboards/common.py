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
    raw_reactions_data: list[str] | None = None,
    counts: dict[str, int] | None = None,
    channel_id: int | None = None,
) -> InlineKeyboardMarkup:
    """Build the inline keyboard for interactive posts."""
    texts = raw_reactions_data if raw_reactions_data else DEFAULT_REACTION_BUTTONS
    builder = InlineKeyboardBuilder()
    for idx, text in enumerate(texts[:10]):
        count = counts.get(f"r{idx}", 0) if counts else 0
        display = f"{text} {count}" if counts else text
        if channel_id is not None:
            cb_data = f"ip_{channel_id}_r{idx}_{message_id}"
        else:
            cb_data = f"ip_r{idx}_{message_id}"
        cb_data = cb_data[:64]
        builder.button(text=display, callback_data=cb_data)
    builder.adjust(len(texts[:10]))
    return builder.as_markup()

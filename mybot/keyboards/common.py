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
    counts: list[int] | None = None,
) -> InlineKeyboardMarkup:
    """Keyboard with reaction buttons for channel posts."""
    texts = buttons if buttons else DEFAULT_REACTION_BUTTONS
    builder = InlineKeyboardBuilder()
    for idx, text in enumerate(texts[:10]):
        count_text = f" ({counts[idx]})" if counts and idx < len(counts) else ""
        builder.button(
            text=f"{text}{count_text}",
            callback_data=f"ip_r{idx}_{message_id}",
        )
    builder.adjust(len(texts[:10]))
    return builder.as_markup()

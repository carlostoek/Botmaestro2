from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_trivia_options_keyboard(question_id: int, options: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idx, option in enumerate(options):
        builder.button(text=option, callback_data=f"trivia_answer:{question_id}:{idx}")
    builder.adjust(1)
    return builder.as_markup()


def get_trivia_retry_keyboard(question_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Intentar de nuevo", callback_data=f"trivia_retry:{question_id}")
    builder.button(text="❌ Cancelar", callback_data="trivia_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_generic_back_keyboard(callback: str = "trivia_back") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Volver", callback_data=callback)
    builder.adjust(1)
    return builder.as_markup()

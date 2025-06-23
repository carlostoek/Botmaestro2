from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_minigames_kb(back_callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Tirar Dado", callback_data="play_dice")
    builder.button(text="❓ Trivia", callback_data="play_trivia")
    builder.button(text="🔙 Volver", callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()

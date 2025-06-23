from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_minigames_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎲 Dados", callback_data="play_dice")
    builder.button(text="❓ Trivia", callback_data="play_trivia")
    builder.button(text="🔙 Volver", callback_data="vip_menu")
    builder.adjust(1)
    return builder.as_markup()

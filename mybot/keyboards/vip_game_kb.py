from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_game_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Mi perfil", callback_data="game_profile")
    builder.button(text="Ganar puntos", callback_data="gain_points")
    builder.button(text="Minijuegos", callback_data="game_minigames")
    builder.adjust(1)
    return builder.as_markup()

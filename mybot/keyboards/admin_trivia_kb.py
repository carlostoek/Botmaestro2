from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def trivia_admin_main_kb():
    buttons = [
        [InlineKeyboardButton(text="📖 Listar Trivias", callback_data="list_trivias")],
        [InlineKeyboardButton(text="✨ Crear Trivia", callback_data="create_trivia")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

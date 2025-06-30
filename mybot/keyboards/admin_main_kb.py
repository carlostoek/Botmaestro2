from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_admin_main_kb():
    """Return the main admin reply keyboard."""
    keyboard = [
        [KeyboardButton(text="📊 Estadísticas"), KeyboardButton(text="🛠️ Administrar Trivias")],
        [KeyboardButton(text="🎒 Mochila Admin"), KeyboardButton(text="⚙️ Configuración")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# mybot/keyboards/user_kb.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

# ... (otras funciones de teclado si ya las tienes) ...

def get_free_user_menu_kb() -> InlineKeyboardMarkup:
    """Teclado para usuarios gratuitos."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Contenido Gratuito", callback_data="free_content")
    builder.button(text="💎 Ver Tarifas VIP", callback_data="show_vip_tariffs")
    builder.button(text="❓ Preguntas Frecuentes", callback_data="faq")
    builder.button(text="📞 Contactar Soporte", callback_data="contact_support")
    builder.adjust(1) # Cada botón en su propia fila para mayor claridad
    return builder.as_markup()

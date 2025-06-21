from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_free_user_menu_kb() -> InlineKeyboardMarkup:
    """Teclado para usuarios gratuitos."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Contenido Gratuito", callback_data="free_content")
    builder.button(text="💎 Ver Tarifas VIP", callback_data="show_vip_tariffs")
    builder.button(text="❓ Preguntas Frecuentes", callback_data="faq")
    builder.button(text="📞 Contactar Soporte", callback_data="contact_support")
    builder.adjust(1)  # Cada botón en su propia fila para mayor claridad
    return builder.as_markup()


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """Teclado principal para usuarios (ej. VIPs o con acceso general)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Mi Suscripción", callback_data="my_subscription")
    builder.button(text="🎁 Mis Recompensas", callback_data="my_rewards")
    builder.button(text="💬 Grupo VIP", url="https://t.me/your_vip_group_link")  # Reemplaza con tu link
    builder.button(text="❓ Ayuda", callback_data="help_menu")
    builder.adjust(1)
    return builder.as_markup()

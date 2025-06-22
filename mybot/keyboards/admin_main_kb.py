from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_kb():
    """Return the main admin inline keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Gestionar Usuarios VIP", callback_data="vip_manage")
    builder.button(text="📺 Gestionar Canales", callback_data="admin_manage_channels")
    builder.button(text="🎮 Configurar Gamificación", callback_data="admin_kinky_game")
    builder.button(text="⚙️ Configuración del Bot", callback_data="admin_bot_config")
    builder.adjust(2)
    return builder.as_markup()

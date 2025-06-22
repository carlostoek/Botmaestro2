from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

# Teclado principal de administración
def get_admin_kb() -> InlineKeyboardMarkup:
    """Main admin menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Gestionar Usuarios VIP", callback_data="vip_manage")
    builder.button(text="📺 Gestionar Canales", callback_data="admin_manage_channels")
    builder.button(text="🎮 Configurar Gamificación", callback_data="admin_kinky_game")
    builder.button(text="⚙️ Configuración del Bot", callback_data="admin_bot_config")
    builder.adjust(2)
    return builder.as_markup()

# Teclado para gestión de canales de administración (ejemplo, si lo necesitas)
def get_admin_channels_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Añadir Canal VIP", callback_data="admin_add_vip_channel")
    builder.button(text="➕ Añadir Canal Gratuito", callback_data="admin_add_free_channel")
    builder.button(text="🔙 Volver al Panel Admin", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()

# Teclado para gestión de gamificación de administración (ejemplo)
def get_admin_gamification_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎯 Misiones", callback_data="admin_missions")
    builder.button(text="🏅 Insignias", callback_data="admin_badges")
    builder.button(text="🎁 Recompensas", callback_data="admin_rewards")
    builder.button(text="📊 Niveles", callback_data="admin_levels")
    builder.button(text="🔙 Volver a Config. Gamificación", callback_data="setup_gamification")
    builder.adjust(2)
    return builder.as_markup()

# Teclado para gestión de tarifas de administración (ejemplo)
def get_admin_tariffs_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💎 Ver Tarifas Existentes", callback_data="admin_view_tariffs")
    builder.button(text="➕ Crear Nueva Tarifa", callback_data="admin_create_tariff")
    builder.button(text="🔙 Volver a Config. Tarifas", callback_data="setup_tariffs")
    builder.adjust(1)
    return builder.as_markup()

# Teclado para gestión de usuarios de administración (ejemplo)
def get_admin_users_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Buscar Usuario", callback_data="admin_search_user")
    builder.button(text="📝 Editar Rol de Usuario", callback_data="admin_edit_user_role")
    builder.button(text="📊 Estadísticas de Usuarios", callback_data="admin_user_stats")
    builder.button(text="🔙 Volver al Panel Admin", callback_data="admin_main")
    builder.adjust(1)
    return builder.as_markup()

# Teclado para solicitar un ID de canal (ejemplo, si es necesario)
def get_admin_channel_id_input_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Cancelar", callback_data="cancel_channel_input")
    return builder.as_markup()

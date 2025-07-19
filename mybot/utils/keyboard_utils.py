# utils/keyboard_utils.py
from typing import List, Optional
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import User
from utils.messages import BOT_MESSAGES


def get_main_menu_keyboard(user_vip: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Construye el menú principal del Diván de Diana con diseño elegante.
    
    Layout optimizado:
    - Fila 1: Estado y acceso VIP
    - Fila 2: Actividades principales (Misiones, Regalo diario)
    - Fila 3: Perfil y colección (Perfil, Mochila)
    - Fila 4: Entretenimiento (Subastas, Ranking)
    - Fila 5: Administración (solo para admins)
    
    Args:
        user_vip (bool): Si el usuario tiene acceso al Diván VIP
        is_admin (bool): Si el usuario es administrador
        
    Returns:
        InlineKeyboardMarkup con la navegación principal estilizada
    """
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Estado VIP y suscripción
    if user_vip:
        builder.row(
            InlineKeyboardButton(text="💎 Mi Diván VIP", callback_data="vip_subscription"),
            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="💎 Únete al Diván", callback_data="vip_subscription"),
            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift")
        )
    
    # Fila 2: Actividades principales
    builder.row(
        InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions"),
        InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile")
    )
    
    # Fila 3: Colección y progreso
    builder.row(
        InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack"),
        InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")
    )
    
    # Fila 4: Entretenimiento y competencia
    builder.row(
        InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main"),
        InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")
    )
    
    # Fila 5: Administración (solo para admins)
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Panel Admin", callback_data="admin_main_menu")
        )
    
    return builder.as_markup()


def get_main_menu_message(username: str, besitos: int, level: int, 
                         streak: int, vip_status: str) -> str:
    """
    Genera el mensaje principal con el estado del usuario en el Diván.
    
    Args:
        username (str): Nombre del usuario
        besitos (int): Cantidad de besitos
        level (int): Nivel actual
        streak (int): Días de racha
        vip_status (str): Estado VIP del usuario
        
    Returns:
        str: Mensaje formateado con el estado del usuario
    """
    level_emoji = get_level_emoji(level)
    vip_badge = get_vip_badge(vip_status)
    
    message = f"""
✨ **¡Hola, {username}!** {vip_badge}

┌─────────────────────────────────┐
│        ESTADO EN EL DIVÁN       │
├─────────────────────────────────┤
│ {level_emoji} Nivel {level}                    │
│ 💋 {besitos:,} besitos             │
│ 🔥 Racha: {streak} días            │
│ 🌟 Progreso diario: {get_daily_progress()}%      │
└─────────────────────────────────┘

💫 **¿Qué haremos hoy en mi Diván?**
"""
    
    return message


def get_level_emoji(level: int) -> str:
    """Retorna el emoji correspondiente al nivel del usuario."""
    if level <= 10:
        return "🌸"  # Principiante
    elif level <= 25:
        return "🌹"  # Intermedio
    elif level <= 50:
        return "💐"  # Avanzado
    elif level <= 100:
        return "👑"  # Experto
    else:
        return "💎"  # Maestro


def get_vip_badge(vip_status: str) -> str:
    """Retorna el badge VIP apropiado para el Diván."""
    badges = {
        "standard": "🤍",
        "vip": "💎",
        "premium": "👑",
        "admin": "✨"
    }
    return badges.get(vip_status, "🤍")


def get_daily_progress() -> int:
    """
    Calcula el progreso diario basado en actividades completadas.
    """
    # Placeholder - implementar lógica real
    return 75


def get_vip_zone_menu(user_vip: bool) -> InlineKeyboardMarkup:
    """Menú específico para la zona VIP del Diván."""
    builder = InlineKeyboardBuilder()
    
    if user_vip:
        # Menú para usuarios VIP del Diván
        builder.row(
            InlineKeyboardButton(text="🏆 Subastas VIP", callback_data="vip_auctions"),
            InlineKeyboardButton(text="🎁 Catálogo VIP", callback_data="vip_rewards")
        )
        builder.row(
            InlineKeyboardButton(text="💌 Contenido Exclusivo", callback_data="vip_content"),
            InlineKeyboardButton(text="👥 Círculo Íntimo", callback_data="vip_community")
        )
        builder.row(
            InlineKeyboardButton(text="💎 Mi Estado VIP", callback_data="vip_status"),
            InlineKeyboardButton(text="↩️ Volver", callback_data="menu_principal")
        )
    else:
        # Menú para usuarios no VIP
        builder.row(
            InlineKeyboardButton(text="💎 Únete al Diván", callback_data="become_vip"),
            InlineKeyboardButton(text="✨ Beneficios VIP", callback_data="vip_benefits")
        )
        builder.row(
            InlineKeyboardButton(text="👀 Vista Previa", callback_data="vip_preview"),
            InlineKeyboardButton(text="↩️ Volver", callback_data="menu_principal")
        )
    
    return builder.as_markup()


def get_missions_keyboard(missions: list, offset: int = 0):
    """Menú de misiones rediseñado con mejor organización."""
    builder = InlineKeyboardBuilder()
    
    # Mostrar hasta 4 misiones por página para mejor legibilidad
    for mission in missions[offset:offset + 4]:
        status_emoji = "✅" if mission.completed else "🎯"
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} {mission.name} ({mission.reward_points} besitos)",
                callback_data=f"mission_{mission.id}"
            )
        )
    
    # Navegación
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"missions_page_{offset - 4}")
        )
    if offset + 4 < len(missions):
        nav_buttons.append(
            InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"missions_page_{offset + 4}")
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Botones de acción
    builder.row(
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="refresh_missions"),
        InlineKeyboardButton(text="🏠 Inicio", callback_data="menu_principal")
    )
    
    return builder.as_markup()


def get_reward_keyboard(rewards: list, claimed_ids: set[int], offset: int = 0) -> InlineKeyboardMarkup:
    """Menú de recompensas rediseñado."""
    builder = InlineKeyboardBuilder()
    
    for reward in rewards[offset:offset + 4]:
        if reward.id in claimed_ids:
            text = f"✅ {reward.title}"
            callback = f"claimed_{reward.id}"
        else:
            text = f"🎁 {reward.title} ({reward.required_points} besitos)"
            callback = f"claim_reward_{reward.id}"
        
        builder.row(
            InlineKeyboardButton(text=text, callback_data=callback)
        )
    
    # Navegación
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"rewards_page_{offset - 4}")
        )
    if offset + 4 < len(rewards):
        nav_buttons.append(
            InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"rewards_page_{offset + 4}")
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="refresh_rewards"),
        InlineKeyboardButton(text="🏠 Inicio", callback_data="menu_principal")
    )
    
    return builder.as_markup()


def format_section_message(title: str, content: str, emoji: str = "💫") -> str:
    """
    Formatea mensajes de sección con estilo del Diván.
    """
    separator = "✨" * 15
    
    return f"""
{emoji} **{title.upper()}**

{separator}

{content}

{separator}
"""


# Mantener funciones existentes para compatibilidad
def get_profile_keyboard():
    """Returns the keyboard for the profile section."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="refresh_profile"),
        InlineKeyboardButton(text="🏠 Inicio", callback_data="menu_principal")
    )
    return builder.as_markup()


def get_ranking_keyboard():
    """Returns the keyboard for the ranking section."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="refresh_ranking"),
        InlineKeyboardButton(text="🏠 Inicio", callback_data="menu_principal")
    )
    return builder.as_markup()


# ... [resto de funciones administrativas sin cambios] ...
                                 

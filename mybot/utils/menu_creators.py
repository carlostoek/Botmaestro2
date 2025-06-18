"""
Menu creators for specific menu types.
Separated to avoid circular imports and improve maintainability.
"""
from typing import Tuple
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from utils.keyboard_utils import (
    get_profile_keyboard,
    get_missions_keyboard,
    get_reward_keyboard,
    get_ranking_keyboard
)
from utils.message_utils import get_profile_message, get_ranking_message
from services.mission_service import MissionService
from services.reward_service import RewardService
from services.point_service import PointService
from keyboards.auction_kb import get_auction_main_kb

async def create_profile_menu(user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the profile menu for a user."""
    user = await session.get(User, user_id)
    if not user:
        return (
            "❌ **Perfil No Encontrado**\n\n"
            "No se pudo cargar tu perfil. Usa /start para registrarte.",
            get_profile_keyboard()
        )
    
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id)
    
    profile_text = await get_profile_message(user, active_missions, session)
    return profile_text, get_profile_keyboard()

async def create_missions_menu(user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the missions menu for a user."""
    mission_service = MissionService(session)
    active_missions = await mission_service.get_active_missions(user_id=user_id, category="standard")
    
    if not active_missions:
        text = (
            "🎯 **Misiones Disponibles**\n\n"
            "No hay misiones activas en este momento.\n"
            "¡Mantente atento! Pronto habrá nuevos desafíos."
        )
    else:
        text = (
            "🎯 **Misiones Disponibles**\n\n"
            "Completa estas misiones para ganar puntos y desbloquear recompensas:"
        )
    
    return text, get_missions_keyboard(active_missions)

async def create_onboarding_missions_menu(user_id: int, user_type: str, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the onboarding missions menu for a user."""
    mission_service = MissionService(session)
    onboarding_missions = await mission_service.get_onboarding_missions(user_type, user_id)
    
    if not onboarding_missions:
        # No onboarding missions or all completed
        user = await session.get(User, user_id)
        if user_type == "vip" and user and user.vip_onboarding_complete:
            text = (
                "✅ **¡Onboarding VIP Completado!**\n\n"
                "Has completado todas las misiones de introducción VIP.\n"
                "¡Ahora puedes acceder a todas las funciones premium!"
            )
        elif user_type == "free" and user and user.free_onboarding_complete:
            text = (
                "✅ **¡Introducción Completada!**\n\n"
                "Has completado todas las misiones de introducción.\n"
                "¡Ahora puedes explorar todo el contenido disponible!"
            )
        else:
            text = (
                f"🎯 **Misiones de {user_type.title()}**\n\n"
                "No hay misiones de onboarding configuradas en este momento."
            )
    else:
        completed_count = 0
        for mission in onboarding_missions:
            # Check if mission is completed
            if user_id in [m.user_id for m in mission.user_missions if m.completed]:
                completed_count += 1
        
        progress_text = f"({completed_count}/{len(onboarding_missions)} completadas)"
        
        if user_type == "vip":
            text = (
                f"🎯 **Misiones VIP de Onboarding** {progress_text}\n\n"
                "Completa estas misiones para familiarizarte con las funciones VIP "
                "y ganar puntos extra:"
            )
        else:
            text = (
                f"🎯 **Misiones de Introducción** {progress_text}\n\n"
                "Completa estas misiones para conocer las funciones básicas "
                "y ganar tus primeros puntos:"
            )
    
    # Create custom keyboard for onboarding
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Add mission buttons
    for mission in onboarding_missions:
        # Check if completed (simplified check)
        status_emoji = "✅" if mission.id in [m.mission_id for m in mission.user_missions if m.completed] else "🎯"
        button_text = f"{status_emoji} {mission.name}"
        builder.button(text=button_text, callback_data=f"mission_{mission.id}")
    
    # Add navigation buttons
    if user_type == "vip":
        builder.button(text="🏠 Menú VIP", callback_data="menu_principal")
    else:
        builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1)
    
    return text, builder.as_markup()

async def create_rewards_menu(user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the rewards menu for a user."""
    reward_service = RewardService(session)
    user = await session.get(User, user_id)
    user_points = int(user.points) if user else 0
    
    available_rewards = await reward_service.get_available_rewards(user_points)
    claimed_ids = await reward_service.get_claimed_reward_ids(user_id)
    
    if not available_rewards:
        text = (
            "🎁 **Recompensas Disponibles**\n\n"
            "No hay recompensas disponibles con tus puntos actuales.\n"
            "¡Sigue participando para desbloquear más recompensas!"
        )
    else:
        text = (
            f"🎁 **Recompensas Disponibles**\n\n"
            f"Tienes **{user_points} puntos** para canjear.\n"
            f"Selecciona una recompensa para reclamarla:"
        )
    
    return text, get_reward_keyboard(available_rewards, set(claimed_ids))

async def create_auction_menu(user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the auction menu for a user."""
    text = (
        "🏛️ **Subastas en Tiempo Real**\n\n"
        "Participa en subastas exclusivas y gana premios únicos.\n"
        "¡Usa tus puntos para pujar por increíbles recompensas!"
    )
    
    return text, get_auction_main_kb()

async def create_ranking_menu(user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    """Create the ranking menu for a user."""
    point_service = PointService(session)
    top_users = await point_service.get_top_users(limit=10)
    
    ranking_text = await get_ranking_message(top_users)
    return ranking_text, get_ranking_keyboard()
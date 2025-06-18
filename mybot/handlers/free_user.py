from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.subscription_kb import (
    get_subscription_kb,
    get_free_info_kb,
    get_free_game_kb,
)
from utils.user_roles import is_admin, get_user_role
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from services.mission_service import MissionService
from database.models import User
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("subscribe"))
async def subscription_menu(message: Message, session: AsyncSession):
    """Enhanced subscription menu with onboarding support."""
    user_id = message.from_user.id
    
    if is_admin(user_id):
        await menu_manager.send_temporary_message(
            message,
            "ℹ️ **Administrador Detectado**\n\nComo administrador, tienes acceso completo al sistema.",
            auto_delete_seconds=5
        )
        return
    
    role = await get_user_role(message.bot, user_id, session=session)
    if role == "vip":
        await menu_manager.send_temporary_message(
            message,
            "✨ **Ya eres VIP**\n\nYa tienes acceso a todas las funciones premium.",
            auto_delete_seconds=5
        )
        return
    
    # Check if user needs onboarding
    user = await session.get(User, user_id)
    if user and not user.free_onboarding_complete:
        # Assign free onboarding missions
        mission_service = MissionService(session)
        await mission_service.assign_onboarding_missions(user_id, "free")
    
    try:
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "main")
    except Exception as e:
        logger.error(f"Error showing subscription menu for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el menú. Intenta nuevamente.",
            auto_delete_seconds=5
        )


@router.callback_query(F.data == "free_info")
async def show_info(callback: CallbackQuery, session: AsyncSession):
    """Display the info section for free users."""
    try:
        await menu_manager.update_menu(
            callback,
            "ℹ️ **Información del Canal Gratuito**\n\n"
            "Aquí encontrarás información sobre las funciones disponibles "
            "para usuarios gratuitos y cómo aprovechar al máximo tu experiencia.\n\n"
            "🎯 **Funciones disponibles:**\n"
            "• Sistema de puntos básico\n"
            "• Misiones de introducción\n"
            "• Acceso al canal gratuito\n"
            "• Perfil y progreso\n\n"
            "💎 **¿Quieres más?**\n"
            "Considera actualizar a VIP para acceder a funciones premium.",
            get_free_info_kb(),
            session,
            "free_info"
        )
    except Exception as e:
        logger.error(f"Error showing free info: {e}")
        await callback.answer("Error al cargar la información", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "free_game")
async def free_game(callback: CallbackQuery, session: AsyncSession):
    """Placeholder mini game for free users."""
    try:
        await menu_manager.update_menu(
            callback,
            "🎮 **Mini Juego Kinky (Versión Gratuita)**\n\n"
            "¡Bienvenido al mini juego! Esta es la versión gratuita con "
            "funciones básicas.\n\n"
            "🎯 **Funciones disponibles:**\n"
            "• Juegos simples\n"
            "• Puntos básicos\n"
            "• Diversión limitada\n\n"
            "💎 **Versión VIP:**\n"
            "Los miembros VIP tienen acceso a juegos avanzados, "
            "multiplicadores de puntos y contenido exclusivo.",
            get_free_game_kb(),
            session,
            "free_game"
        )
    except Exception as e:
        logger.error(f"Error showing free game: {e}")
        await callback.answer("Error al cargar el juego", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.in_("free_info_test", "free_game_test"))
async def dummy_button(callback: CallbackQuery):
    """Handle placeholder buttons in the free user menu."""
    await callback.answer("🎮 Función en desarrollo - ¡Pronto disponible!")
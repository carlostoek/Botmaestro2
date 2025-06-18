"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.user_utils import get_or_create_user
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from utils.user_roles import clear_role_cache, is_admin
from services.tenant_service import TenantService
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """
    Enhanced start command with intelligent routing based on user status.
    Provides seamless experience for new and returning users.
    """
    user_id = message.from_user.id
    
    # Clear any cached role for fresh check
    clear_role_cache(user_id)
    
    # Get or create user safely
    user = await session.get(User, user_id)
    is_new_user = user is None

    if not user:
        user = await get_or_create_user(
            session,
            user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        is_new_user = True
    else:
        # Update user info if changed
        updated = False
        new_username = sanitize_text(message.from_user.username)
        new_first_name = sanitize_text(message.from_user.first_name)
        new_last_name = sanitize_text(message.from_user.last_name)
        
        if user.username != new_username:
            user.username = new_username
            updated = True
        if user.first_name != new_first_name:
            user.first_name = new_first_name
            updated = True
        if user.last_name != new_last_name:
            user.last_name = new_last_name
            updated = True
            
        if updated:
            await session.commit()
            logger.info(f"Updated user info: {user_id}")
    
    # Check if this is an admin and if setup is needed
    if is_admin(user_id):
        tenant_service = TenantService(session)
        tenant_status = await tenant_service.get_tenant_status(user_id)
        
        # If admin hasn't completed basic setup, guide them to setup
        if not tenant_status["basic_setup_complete"]:
            await menu_manager.show_menu(
                message,
                "👋 **¡Hola, Administrador!**\n\n"
                "Parece que es la primera vez que usas este bot. "
                "Te guiaré a través de una configuración rápida para que "
                "esté listo para tus usuarios.\n\n"
                "**¿Quieres configurar el bot ahora?**\n"
                "• ✅ Configuración guiada (recomendado)\n"
                "• ⏭️ Ir directo al panel de administración\n\n"
                "La configuración solo toma unos minutos y puedes "
                "cambiar todo después.",
                menu_factory._create_setup_choice_kb(),
                session,
                "admin_setup_choice"
            )
            return
    
    # Create appropriate menu based on user role and status
    try:
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
        
        # Customize welcome message for new vs returning users
        if is_new_user:
            welcome_prefix = "🌟 **¡Bienvenido!**\n\n"
            if "admin" in text.lower():
                welcome_prefix = "👑 **¡Bienvenido, Administrador!**\n\n"
            elif "vip" in text.lower():
                welcome_prefix = "✨ **¡Bienvenido, Miembro VIP!**\n\n"
            
            text = welcome_prefix + text
        else:
            # Returning user - more concise welcome
            if "admin" in text.lower():
                text = "👑 **Panel de Administración**\n\n" + text.split('\n\n', 1)[-1]
            elif "vip" in text.lower():
                text = "✨ **Bienvenido de vuelta**\n\n" + text.split('\n\n', 1)[-1]
            else:
                text = "🌟 **¡Hola de nuevo!**\n\n" + text.split('\n\n', 1)[-1]
        
        await menu_manager.show_menu(message, text, keyboard, session, "main")
        
    except Exception as e:
        logger.error(f"Error in start command for user {user_id}: {e}")
        # Fallback to basic menu
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\n"
            "Hubo un problema al cargar el menú. Por favor, intenta nuevamente en unos segundos.",
            auto_delete_seconds=5
        )

def _create_setup_choice_kb():
    """Create keyboard for admin setup choice."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Configurar Ahora", callback_data="start_setup")
    builder.button(text="⏭️ Ir al Panel", callback_data="skip_to_admin")
    builder.button(text="📖 Ver Guía", callback_data="show_setup_guide")
    builder.adjust(1)
    return builder.as_markup()

# Add the method to MenuFactory
menu_factory._create_setup_choice_kb = _create_setup_choice_kb


# Callback handlers for guided setup choices

@router.callback_query(F.data == "start_setup")
async def start_setup_callback(callback: CallbackQuery, session: AsyncSession):
    """Launch the guided setup from inline button."""
    from handlers.setup import start_setup

    await start_setup(callback.message, session)
    await callback.answer()


@router.callback_query(F.data == "skip_to_admin")
async def skip_to_admin_callback(callback: CallbackQuery, session: AsyncSession):
    """Directly open the admin menu, skipping setup."""
    from handlers.admin.admin_menu import admin_menu

    await admin_menu(callback.message, session)
    await callback.answer()


@router.callback_query(F.data == "show_setup_guide")
async def show_setup_guide_callback(callback: CallbackQuery):
    """Show a short message pointing to the setup guide."""
    guide_text = (
        "Consulta el README del proyecto para la guía completa de configuración."
    )
    await callback.message.answer(guide_text, disable_web_page_preview=True)
    await callback.answer()

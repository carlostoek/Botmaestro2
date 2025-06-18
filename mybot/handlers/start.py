"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
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
    
    try:
        logger.info(f"Start command received from user {user_id}")
        
        # Clear any cached role for fresh check
        clear_role_cache(user_id)
        
        # Get or create user
        user = await session.get(User, user_id)
        is_new_user = user is None
        
        if not user:
            user = User(
                id=user_id,
                username=sanitize_text(message.from_user.username),
                first_name=sanitize_text(message.from_user.first_name),
                last_name=sanitize_text(message.from_user.last_name),
            )
            session.add(user)
            await session.commit()
            logger.info(f"Created new user: {user_id}")
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
            logger.info(f"Admin user detected: {user_id}")
            try:
                tenant_service = TenantService(session)
                tenant_status = await tenant_service.get_tenant_status(user_id)
                
                # If admin hasn't completed basic setup, guide them to setup
                if not tenant_status["basic_setup_complete"]:
                    await message.answer(
                        "👋 **¡Hola, Administrador!**\n\n"
                        "Parece que es la primera vez que usas este bot. "
                        "Te guiaré a través de una configuración rápida para que "
                        "esté listo para tus usuarios.\n\n"
                        "Usa /setup para comenzar la configuración o /admin_menu para ir directo al panel.",
                        parse_mode="Markdown"
                    )
                    return
            except Exception as e:
                logger.error(f"Error checking tenant status: {e}")
        
        # Simple welcome message based on user type
        if is_admin(user_id):
            welcome_text = "👑 **Panel de Administración**\n\nBienvenido al centro de control del bot."
            try:
                from keyboards.admin_main_kb import get_admin_main_kb
                keyboard = get_admin_main_kb()
            except ImportError:
                keyboard = None
        elif user.role == "vip":
            welcome_text = "✨ **Bienvenido al Diván de Diana**\n\nTu suscripción VIP te da acceso completo."
            try:
                from keyboards.vip_main_kb import get_vip_main_kb
                keyboard = get_vip_main_kb()
            except ImportError:
                keyboard = None
        else:
            welcome_text = "🌟 **Bienvenido a los Kinkys**\n\nExplora nuestro contenido gratuito."
            try:
                from keyboards.subscription_kb import get_subscription_kb
                keyboard = get_subscription_kb()
            except ImportError:
                keyboard = None
        
        if is_new_user:
            welcome_text = "🌟 **¡Bienvenido!**\n\n" + welcome_text
        else:
            welcome_text = "🌟 **¡Hola de nuevo!**\n\n" + welcome_text
        
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        logger.info(f"Start command processed successfully for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in start command for user {user_id}: {e}", exc_info=True)
        # Fallback to basic response
        try:
            await message.answer(
                "❌ **Error Temporal**\n\n"
                "Hubo un problema al cargar el menú. Por favor, intenta nuevamente.",
                parse_mode="Markdown"
            )
        except Exception as e2:
            logger.error(f"Error sending fallback message: {e2}")
            await message.answer("Error al procesar el comando. Intenta nuevamente.")
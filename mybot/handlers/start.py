"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory 
from utils.user_roles import clear_role_cache, is_admin
from services.tenant_service import TenantService
from services.subscription_service import SubscriptionService
from services.config_service import ConfigService
from utils.config import VIP_CHANNEL_ID
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

    # --- Verify VIP channel membership and update role if necessary ---
    config_service = ConfigService(session)
    vip_channel_id = await config_service.get_vip_channel_id()
    if not vip_channel_id:
        vip_channel_id = VIP_CHANNEL_ID

    if vip_channel_id:
        try:
            member = await message.bot.get_chat_member(vip_channel_id, user_id)
            in_channel = member.status in {"member", "administrator", "creator"}
        except Exception as e:
            logger.warning(
                f"Failed VIP membership check for user {user_id}: {e}"
            )
            in_channel = False

        if not in_channel and user.role == "vip":
            sub_service = SubscriptionService(session)
            await sub_service.revoke_subscription(user_id)
            clear_role_cache(user_id)
            logger.info(
                f"User {user_id} removed from VIP role due to missing channel"
            )

    # Check if this is an admin
    if is_admin(user_id):
        tenant_service = TenantService(session)
        
        # Opcional: Asegurarse de que el tenant exista, incluso si no se completará el setup
        # Esto es importante para que el panel de administración funcione correctamente
        init_result = await tenant_service.initialize_tenant(user_id)
        if not init_result["success"]:
            logger.error(f"Failed to initialize tenant for admin {user_id}: {init_result['error']}")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error Crítico**\n\nNo se pudo inicializar la configuración de administrador. Por favor, contacta a soporte.",
                auto_delete_seconds=10
            )
            return

        # *** CAMBIO CLAVE AQUÍ: Siempre ir al panel de administración para admins ***
        text, keyboard = await menu_factory.create_menu("admin_main", user_id, session, message.bot)
        
        # Personalizar mensaje de bienvenida para admin al iniciar
        welcome_prefix = "👑 **¡Bienvenido, Administrador!**\n\n"
        text = welcome_prefix + text.split('\n\n', 1)[-1] # Mantiene el texto del menú, pero reemplaza el saludo inicial

        await menu_manager.show_menu(
            message,
            text,
            keyboard,
            session,
            "admin_main", # Asegúrate de registrar el estado correcto
            delete_origin_message=True
        )
        return # Terminar aquí para el flujo de administración
    
    # Lógica para usuarios no-administradores (VIP, Free)
    try:
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
        
        if is_new_user:
            welcome_prefix = "🌟 **¡Bienvenido!**\n\n"
            if "suscripción vip" in text.lower() or "experiencia premium" in text.lower():
                welcome_prefix = "✨ **¡Bienvenido, Miembro VIP!**\n\n"
            
            text = welcome_prefix + text
        else:
            if "suscripción vip" in text.lower() or "experiencia premium" in text.lower():
                text = "✨ **Bienvenido de vuelta**\n\n" + text.split('\n\n', 1)[-1]
            else:
                text = "🌟 **¡Hola de nuevo!**\n\n" + text.split('\n\n', 1)[-1]
        
        await menu_manager.show_menu(
            message, 
            text, 
            keyboard, 
            session, 
            "main",
            delete_origin_message=True
        )
        
    except Exception as e:
        logger.error(f"Error in start command for user {user_id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\n"
            "Hubo un problema al cargar el menú. Por favor, intenta nuevamente en unos segundos.",
            auto_delete_seconds=5
        )
        

"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User # Asegúrate de que User tiene current_menu_state
from utils.text_utils import sanitize_text
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory 
from utils.user_roles import clear_role_cache, is_admin, get_user_role # Usaremos get_user_role directamente para los no-admins
from services.tenant_service import TenantService
from services.user_service import UserService # Necesario para is_vip_member
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
            current_menu_state="initial" # Establece un estado inicial para nuevos usuarios
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
    
    # Check if this is an admin
    if await is_admin(user_id, session): # Asegúrate de pasar la sesión aquí
        tenant_service = TenantService(session)
        
        # Intenta inicializar o obtener el tenant. Esto es crucial para admins.
        init_result = await tenant_service.initialize_tenant(user_id)
        if not init_result["success"]:
            logger.error(f"Failed to initialize tenant for admin {user_id}: {init_result['error']}")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error Crítico**\n\nNo se pudo inicializar la configuración de administrador. Por favor, contacta a soporte.",
                auto_delete_seconds=10
            )
            return

        # *** Lógica para admins: Elección de configuración o Panel de Administración ***
        if not init_result["status"]["basic_setup_complete"]:
            # Si la configuración no está completa, muestra la elección inicial de setup
            text, keyboard = menu_factory.create_setup_choice_menu() # Llama directamente al método para el menú de elección
            target_menu_state = "admin_setup_choice"
            welcome_prefix = "👋 **¡Hola, Administrador!**\n\n"
            text = welcome_prefix + text # Asegura el saludo
        else:
            # Si la configuración ya está completa, va directo al panel de admin
            text, keyboard = await menu_factory.create_menu("admin_main", user_id, session, message.bot)
            target_menu_state = "admin_main"
            welcome_prefix = "👑 **¡Bienvenido, Administrador!**\n\n"
            # Extrae el contenido principal del texto para evitar duplicar el saludo
            text_parts = text.split('\n\n', 1)
            text = welcome_prefix + (text_parts[1] if len(text_parts) > 1 else text_parts[0])
            
        await menu_manager.show_menu(
            message,
            text,
            keyboard,
            session,
            target_menu_state, # Usar el estado de menú decidido
            delete_origin_message=True
        )
        return # Terminar aquí para el flujo de administración
    
    # Lógica para usuarios no-administradores (VIP o Gratuitos)
    try:
        # Pide el menú "main" al factory. El factory decidirá internamente
        # si debe mostrar "vip_main" o "free_main" basándose en el rol del usuario.
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)
        
        # Ahora, para personalizar el prefijo de bienvenida, inferimos el estado final
        # basado en el contenido del texto devuelto por el factory.
        final_menu_state_for_welcome = "main" # Por defecto
        if "bienvenido al diván de diana" in text.lower() or "experiencia premium" in text.lower():
            final_menu_state_for_welcome = "vip_main"
        elif "bienvenido a los kinkys" in text.lower() or "explora nuestro contenido gratuito" in text.lower():
            final_menu_state_for_welcome = "free_main"

        welcome_prefix = ""
        if is_new_user:
            if final_menu_state_for_welcome == "vip_main":
                welcome_prefix = "✨ **¡Bienvenido, Miembro VIP!**\n\n"
            elif final_menu_state_for_welcome == "free_main":
                welcome_prefix = "👋 **¡Bienvenido!**\n\n"
            else:
                welcome_prefix = "🌟 **¡Bienvenido!**\n\n" # General welcome
        else:
            if final_menu_state_for_welcome == "vip_main":
                welcome_prefix = "✨ **Bienvenido de vuelta**\n\n"
            elif final_menu_state_for_welcome == "free_main":
                welcome_prefix = "👋 **¡Hola de nuevo!**\n\n"
            else:
                welcome_prefix = "🌟 **¡Hola de nuevo!**\n\n" # General welcome

        # Asegúrate de que el prefijo se añada correctamente al texto del menú
        # Esto intenta evitar duplicar saludos si el texto del menú ya tiene uno
        text_parts = text.split('\n\n', 1)
        if len(text_parts) > 1:
            # Si el texto ya tiene un salto de línea doble, asume que la primera parte es un saludo
            text = welcome_prefix + text_parts[1]
        else:
            # Si no hay salto de línea doble, simplemente añade el prefijo
            text = welcome_prefix + text 

        await menu_manager.show_menu(
            message, 
            text, 
            keyboard, 
            session, 
            final_menu_state_for_welcome, # Usar el estado de menú decidido
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
        

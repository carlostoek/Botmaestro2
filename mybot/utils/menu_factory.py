"""
Menu factory for creating consistent menus based on user role and state.
Centralizes menu creation logic for better maintainability.
"""
from typing import Tuple, Optional
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot # Importa Bot aquí

from utils.user_roles import get_user_role, is_admin, is_vip_member # Asegúrate de que estas funciones existan
from keyboards.admin_kb import get_admin_main_kb, get_admin_channels_kb, get_admin_gamification_kb, get_admin_tariffs_kb, get_admin_users_kb, get_admin_channel_id_input_kb
from keyboards.vip_main_kb import get_vip_main_kb # Asumo que tienes este teclado para VIPs
from keyboards.subscription_kb import get_subscription_kb # Asumo que tienes este teclado, si es para usuarios gratuitos
from keyboards.setup_kb import (
    get_setup_main_kb,
    get_setup_channels_kb,
    get_setup_complete_kb,
    get_setup_gamification_kb,
    get_setup_tariffs_kb,
    get_setup_confirmation_kb,
)
from keyboards.user_kb import get_free_user_menu_kb, get_main_menu_kb # Tus nuevos teclados de usuario

from database.models import User # Necesario para get_user_role y UserService
import logging

from aiogram.utils.keyboard import InlineKeyboardBuilder # Importar InlineKeyboardBuilder

# Importar creadores de menú específicos (asegúrate de que estos archivos existen)
# Si no usas estos, puedes comentarlos o eliminarlos.
from utils.menu_creators import (
    create_profile_menu,
    create_missions_menu,
    create_rewards_menu,
    create_auction_menu,
    create_ranking_menu
)
from utils.text_utils import sanitize_text # Asegúrate de que esta importación exista y sea correcta

logger = logging.getLogger(__name__)

class MenuFactory:
    """
    Factory class for creating menus based on user state and role.
    Centralizes menu logic and ensures consistency.
    """
    
    def __init__(self):
        self.menus = {
            # --- Menús de Configuración ---
            "setup_main": {
                "text": "🛠️ **Bienvenido al proceso de configuración de tu bot.**\n\n"
                        "Por favor, completa los siguientes pasos para que tu bot funcione correctamente. "
                        "Puedes omitir cualquier sección y configurarla más tarde desde el panel de administrador.",
                "keyboard_builder": get_setup_main_kb
            },
            "setup_channels": {
                "text": "📢 **Configuración de Canales**\n\n"
                        "Define los canales VIP y/o Gratuito de tu comunidad. "
                        "El bot necesita ser administrador en estos canales para funcionar correctamente.",
                "keyboard_builder": get_setup_channels_kb
            },
            "setup_gamification": {
                "text": "🎮 **Configuración de Gamificación**\n\n"
                        "Establece misiones, insignias y recompensas para incentivar a tus usuarios. "
                        "Puedes usar la configuración por defecto o personalizarla.",
                "keyboard_builder": get_setup_gamification_kb
            },
            "setup_tariffs": {
                "text": "💳 **Configuración de Tarifas VIP**\n\n"
                        "Crea y gestiona las tarifas de suscripción para tu contenido premium. "
                        "Define precios, duraciones y descripciones.",
                "keyboard_builder": get_setup_tariffs_kb
            },
            "setup_complete": {
                "text": "✅ **Configuración Inicial Completada**\n\n"
                        "¡Felicidades! Tu bot ha sido configurado. Ahora puedes acceder al panel de administrador "
                        "para ajustes avanzados y gestión diaria, o revisar la guía de uso.",
                "keyboard_builder": get_setup_complete_kb
            },
            "setup_vip_channel_prompt": {
                "text": "🔐 **Configurar Canal VIP**\n\n"
                        "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
                        "El bot detectará automáticamente el ID del canal.\n\n"
                        "**Importante**: Asegúrate de que el bot sea administrador del canal "
                        "con permisos para invitar usuarios.",
                "keyboard_builder": lambda: get_setup_confirmation_kb("cancel_channel_setup") # Uso de lambda para pasar args
            },
            "setup_free_channel_prompt": {
                "text": "🆓 **Configurar Canal Gratuito**\n\n"
                        "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
                        "El bot detectará automáticamente el ID del canal.\n\n"
                        "**Importante**: Asegúrate de que el bot sea administrador del canal "
                        "con permisos para aprobar solicitudes de unión.",
                "keyboard_builder": lambda: get_setup_confirmation_kb("cancel_channel_setup")
            },
            "setup_manual_channel_id_prompt": {
                "text": "📝 **Ingresa el ID del Canal Manualmente**\n\n"
                        "Por favor, ingresa el ID numérico de tu canal. Normalmente empieza con `-100`.",
                "keyboard_builder": lambda: get_setup_confirmation_kb("cancel_channel_setup")
            },
            "setup_missions_info": {
                "text": "ℹ️ **Información sobre Misiones**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "estos elementos estará disponible próximamente.",
                "keyboard_builder": get_setup_gamification_kb
            },
            "setup_badges_info": {
                "text": "ℹ️ **Información sobre Insignias**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "estos elementos estará disponible próximamente.",
                "keyboard_builder": get_setup_gamification_kb
            },
            "setup_rewards_info": {
                "text": "ℹ️ **Información sobre Recompensas**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "estos elementos estará disponible próximamente.",
                "keyboard_builder": get_setup_gamification_kb
            },
            "setup_levels_info": {
                "text": "ℹ️ **Información sobre Niveles**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "estos elementos estará disponible próximamente.",
                "keyboard_builder": get_setup_gamification_kb
            },
            "setup_premium_tariff_info": {
                "text": "ℹ️ **Información sobre Tarifas Premium**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "tarifas premium o personalizadas estará disponible próximamente.",
                "keyboard_builder": get_setup_tariffs_kb
            },
            "setup_custom_tariffs_info": {
                "text": "ℹ️ **Información sobre Tarifas Personalizadas**\n\n"
                        "Esta es una sección informativa. La implementación para crear/editar "
                        "tarifas premium o personalizadas estará disponible próximamente.",
                "keyboard_builder": get_setup_tariffs_kb
            },
            "setup_guide_info": {
                "text": "📖 **Guía de Uso del Bot**\n\n"
                        "Aquí encontrarás información detallada sobre cómo usar y configurar tu bot. "
                        "Temas:\n"
                        "• Gestión de usuarios\n"
                        "• Creación de contenido\n"
                        "• Marketing y monetización\n\n"
                        "*(Contenido de la guía próximamente)*",
                "keyboard_builder": get_setup_complete_kb
            },
            "setup_advanced_info": {
                "text": "🔧 **Configuración Avanzada (Próximamente)**\n\n"
                        "Esta sección contendrá opciones avanzadas para la personalización del bot, "
                        "integraciones y herramientas de depuración.\n\n"
                        "*(Opciones avanzadas próximamente)*",
                "keyboard_builder": get_setup_complete_kb
            },

            # --- Menús de Administrador ---
            "admin_main": {
                "text": "👑 **Panel de Administración**\n\n"
                        "Desde aquí puedes gestionar todos los aspectos de tu bot: "
                        "canales, usuarios, gamificación y tarifas.",
                "keyboard_builder": get_admin_main_kb
            },
            "admin_channels": {
                "text": "📢 **Gestión de Canales**\n\n"
                        "Configura o actualiza los canales VIP y gratuitos asociados a tu bot.",
                "keyboard_builder": get_admin_channels_kb
            },
            "admin_gamification": {
                "text": "🎮 **Gestión de Gamificación**\n\n"
                        "Administra misiones, insignias y recompensas para tus usuarios.",
                "keyboard_builder": get_admin_gamification_kb
            },
            "admin_tariffs": {
                "text": "💳 **Gestión de Tarifas VIP**\n\n"
                        "Crea, edita o desactiva las tarifas de suscripción de tu bot.",
                "keyboard_builder": get_admin_tariffs_kb
            },
            "admin_users": {
                "text": "👥 **Gestión de Usuarios**\n\n"
                        "Visualiza y gestiona a los usuarios de tu bot, sus suscripciones y roles.",
                "keyboard_builder": get_admin_users_kb
            },
            "admin_channel_id_input": {
                "text": "📝 **Ingresar ID de Canal Manualmente**\n\n"
                        "Por favor, envía el ID numérico del canal (ej. `-100123456789`) o reenvía un mensaje "
                        "de dicho canal para que pueda detectarlo.",
                "keyboard_builder": get_admin_channel_id_input_kb
            },
            # --- Menús de Usuario General ---
            # 'main' es un estado genérico que se resolverá en vip_main o free_main
            "vip_main": { 
                "text": "✨ **Bienvenido al Diván de Diana**\n\n"
                        "Tu suscripción VIP te da acceso completo a todas las funciones. "
                        "¡Disfruta de la experiencia premium!",
                "keyboard_builder": get_main_menu_kb # Usa el teclado de usuario general/VIP
            },
            "free_main": { 
                "text": "🌟 **Bienvenido a los Kinkys**\n\n"
                        "Explora nuestro contenido gratuito y descubre todo lo que tenemos para ti. "
                        "¿Listo para una experiencia única?",
                "keyboard_builder": get_free_user_menu_kb # Usa el teclado específico para usuarios gratuitos
            },
            # Agrega más menús aquí según sea necesario

            # Menús específicos que pueden ser para todos los roles o dependen del contexto
            "profile": {
                "text": "👤 **Mi Perfil**\n\nAquí puedes ver tu información, puntos y suscripciones.",
                "keyboard_builder": lambda: InlineKeyboardBuilder().button(text="🔙 Volver", callback_data="main").as_markup() # Ejemplo, crea tu propio teclado
            },
            "missions": {
                "text": "🎯 **Mis Misiones**\n\nAquí puedes ver las misiones disponibles y tu progreso.",
                "keyboard_builder": lambda: InlineKeyboardBuilder().button(text="🔙 Volver", callback_data="main").as_markup()
            },
            "rewards": {
                "text": "🎁 **Mis Recompensas**\n\nAquí puedes canjear tus recompensas.",
                "keyboard_builder": lambda: InlineKeyboardBuilder().button(text="🔙 Volver", callback_data="main").as_markup()
            },
            "auctions": {
                "text": "📈 **Subastas**\n\nParticipa en subastas por objetos únicos.",
                "keyboard_builder": lambda: InlineKeyboardBuilder().button(text="🔙 Volver", callback_data="main").as_markup()
            },
            "ranking": {
                "text": "🏆 **Ranking**\n\nConsulta tu posición en el ranking global.",
                "keyboard_builder": lambda: InlineKeyboardBuilder().button(text="🔙 Volver", callback_data="main").as_markup()
            },
        }

    async def create_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession,
        bot: Bot = None # Asegúrate de que el objeto bot siempre se pase desde los handlers
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a menu based on the current state and user role.
        
        Returns:
            Tuple[str, InlineKeyboardMarkup]: (text, keyboard)
        """
        try:
            role = await get_user_role(bot, user_id, session=session) # Obtenemos el rol una vez al inicio
            
            # Si el menu_state es 'main' (genérico para usuarios no-admin),
            # decidimos si es vip_main o free_main basado en el rol.
            if menu_state == "main":
                if role == "vip":
                    menu_state = "vip_main"
                elif role == "free":
                    menu_state = "free_main"
                # Si el rol es 'admin', el flujo de start.py ya lo maneja para 'admin_main'
                # por lo que no debería llegar aquí con 'main' si es admin.

            # Handle setup flow for new installations
            if menu_state.startswith("setup_") or menu_state == "admin_setup_choice":
                return await self._create_setup_menu(menu_state, user_id, session)
            
            # Handle role-based main menus (ahora 'menu_state' ya es específico si era 'main')
            if menu_state == "admin_main": # Ahora es un estado explícito
                return self._create_main_menu("admin")
            elif menu_state == "vip_main": # Ahora es un estado explícito
                return self._create_main_menu("vip")
            elif menu_state == "free_main": # Ahora es un estado explícito
                return self._create_main_menu("free")
            
            # Handle specific menu states
            return await self._create_specific_menu(menu_state, user_id, session, role)
            
        except Exception as e:
            logger.error(f"Error creating menu for state {menu_state}, user {user_id}: {e}")
            return self._create_fallback_menu(role)
    
    def _create_main_menu(self, role: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the main menu based on user role."""
        if role == "admin":
            return (
                "🛠️ **Panel de Administración**\n\n"
                "Bienvenido al centro de control del bot. Desde aquí puedes gestionar "
                "todos los aspectos del sistema.",
                get_admin_main_kb()
            )
        elif role == "vip":
            return (
                "✨ **Bienvenido al Diván de Diana**\n\n"
                "Tu suscripción VIP te da acceso completo a todas las funciones. "
                "¡Disfruta de la experiencia premium!",
                get_main_menu_kb() # Usar get_main_menu_kb para VIPs
            )
        else: # Covers "free" and any other unrecognized roles
            return (
                "🌟 **Bienvenido a los Kinkys**\n\n"
                "Explora nuestro contenido gratuito y descubre todo lo que tenemos para ti. "
                "¿Listo para una experiencia única?",
                get_free_user_menu_kb() # Usar get_free_user_menu_kb para usuarios gratuitos
            )
    
    async def _create_setup_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create setup menus for initial bot configuration."""
        if menu_state == "setup_main":
            return (
                "🚀 **Bienvenido a la Configuración Inicial**\n\n"
                "¡Hola! Vamos a configurar tu bot paso a paso para que esté listo "
                "para tus usuarios. Este proceso es rápido y fácil.\n\n"
                "**¿Qué vamos a configurar?**\n"
                "• 📢 Canales (VIP y/o Gratuito)\n"
                "• 💳 Tarifas de suscripción\n"
                "• 🎮 Sistema de gamificación\n\n"
                "¡Empecemos!",
                get_setup_main_kb()
            )
        elif menu_state == "setup_channels":
            return (
                "📢 **Configuración de Canales**\n\n"
                "Los canales son el corazón de tu bot. Puedes configurar:\n\n"
                "🔐 **Canal VIP**: Para suscriptores premium\n"
                "🆓 **Canal Gratuito**: Para usuarios sin suscripción\n\n"
                "**Recomendación**: Configura al menos un canal para empezar. "
                "Puedes agregar más canales después desde el panel de administración.",
                get_setup_channels_kb()
            )
        elif menu_state == "setup_complete":
            return (
                "✅ **Configuración Completada**\n\n"
                "¡Perfecto! Tu bot está listo para usar. Puedes acceder al panel de "
                "administración en cualquier momento.",
                get_setup_complete_kb()
            )
        # --- NUEVO BLOQUE: admin_setup_choice ---
        elif menu_state == "admin_setup_choice":
            return self.create_setup_choice_menu() # Reutiliza el método para el menú de elección
        # --- FIN NUEVO BLOQUE ---
        elif menu_state == "setup_vip_channel_prompt":
            return (
                "🔐 **Configurar Canal VIP**\n\n"
                "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para invitar usuarios.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_free_channel_prompt":
            return (
                "🆓 **Configurar Canal Gratuito**\n\n"
                "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para aprobar solicitudes de unión.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_manual_channel_id_prompt":
            return (
                "📝 **Ingresa el ID del Canal Manualmente**\n\n"
                "Por favor, ingresa el ID numérico de tu canal. Normalmente empieza con `-100`.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_gamification":
            return (
                "🎮 **Configuración de Gamificación**\n\n"
                "El sistema de gamificación mantiene a tus usuarios comprometidos con:\n\n"
                "🎯 **Misiones**: Tareas que los usuarios pueden completar\n"
                "🏅 **Insignias**: Reconocimientos por logros\n"
                "🎁 **Recompensas**: Premios por acumular puntos\n"
                "📊 **Niveles**: Sistema de progresión\n\n"
                "**Recomendación**: Usa la configuración por defecto para empezar rápido.",
                get_setup_gamification_kb()
            )
        elif menu_state == "setup_tariffs":
            return (
                "💳 **Configuración de Tarifas VIP**\n\n"
                "Las tarifas determinan los precios y duración de las suscripciones VIP.\n\n"
             

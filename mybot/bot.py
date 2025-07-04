import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ErrorEvent
from constants.keyboards import main_menu_keyboard

# --- CONFIGURACIÓN DE LOGGING MEJORADA ---
def setup_logging():
    """Configuración robusta de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reducir ruido de librerías externas
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)



# Imports
from database.setup import init_db, get_session
from utils.message_safety import patch_message_methods
from utils.config import BOT_TOKEN, VIP_CHANNEL_ID

# Handlers imports
from handlers import start, free_user, daily_gift, minigames, setup as setup_handlers
from handlers.channel_access import router as channel_access_router
from handlers.user import start_token
from handlers.vip import menu as vip, gamification
from handlers.vip.auction_user import router as auction_user_router
from handlers.reaction_callback import router as reaction_callback_router
from handlers.admin import admin_router
from handlers.admin.auction_admin import router as auction_admin_router
from handlers.lore_handlers import router as lore_router
from handlers.missions_handler import router as missions_router
from handlers.info_handler import router as info_router
from handlers.free_channel_admin import router as free_channel_admin_router
from handlers.publication_test import router as publication_test_router

import combinar_pistas
from backpack import router as backpack_router

# Services imports
from services import (
    channel_request_scheduler,
    vip_subscription_scheduler,
    vip_membership_scheduler,
)
from services.scheduler import auction_monitor_scheduler, free_channel_cleanup_scheduler

# Middlewares
from middlewares import PointsMiddleware, UserRegistrationMiddleware

# --- MANEJO DE ERRORES GLOBAL ---
async def global_error_handler(event: ErrorEvent) -> None:
    """Manejo centralizado de errores"""
    logger = logging.getLogger(__name__)
    
    # Log del error
    logger.error(
        f"Error en {event.update.update_id if event.update else 'Unknown'}: "
        f"{type(event.exception).__name__}: {event.exception}",
        exc_info=True
    )
    
    # Notificar errores críticos a admins (opcional)
    if isinstance(event.exception, (ConnectionError, TimeoutError)):
        logger.critical("Error de conexión crítico detectado")
        # Aquí podrías notificar a admins
    
    return True  # Marca el error como manejado

# --- MIDDLEWARE MEJORADO ---
class SessionMiddleware:
    """Middleware para inyección de sesión de BD y bot"""
    
    def __init__(self, session_factory, bot_instance):
        self.session_factory = session_factory
        self.bot_instance = bot_instance
    
    async def __call__(self, handler, event, data):
        try:
            async with self.session_factory() as session:
                data["session"] = session
                data["bot"] = self.bot_instance
                return await handler(event, data)
        except Exception as e:
            logging.error(f"Error en SessionMiddleware: {e}", exc_info=True)
            raise

# --- GESTOR DE TAREAS EN SEGUNDO PLANO ---
class BackgroundTaskManager:
    """Gestor para tareas en segundo plano con manejo de errores"""
    
    def __init__(self):
        self.tasks: list[asyncio.Task] = []
    
    def add_task(self, coro, name: str):
        """Añade una tarea con manejo de errores"""
        async def safe_task():
            try:
                await coro
            except asyncio.CancelledError:
                logging.info(f"Tarea {name} cancelada")
                raise
            except Exception as e:
                logging.error(f"Error en tarea {name}: {e}", exc_info=True)
        
        task = asyncio.create_task(safe_task(), name=name)
        self.tasks.append(task)
        return task
    
    async def shutdown(self):
        """Cierre ordenado de todas las tareas"""
        logging.info("Cerrando tareas en segundo plano...")
        
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logging.info("Todas las tareas cerradas")

# --- FUNCIÓN PRINCIPAL MEJORADA ---
async def main() -> None:
    """Función principal con manejo robusto de errores"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Inicialización
        logger.info("Inicializando base de datos...")
        await init_db()
        
        logger.info("Aplicando parches de seguridad...")
        patch_message_methods()
        
        Session = await get_session()
        
        logger.info(f"VIP channel ID: {VIP_CHANNEL_ID}")
        logger.info("Configurando bot...")

        # Configuración del bot
        bot = Bot(
            BOT_TOKEN, 
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=MemoryStorage())

        # Registrar manejo de errores PRIMERO
        dp.error.register(global_error_handler)

        # Configurar middlewares en orden correcto
        session_middleware = SessionMiddleware(Session, bot)
        user_reg_middleware = UserRegistrationMiddleware()
        points_middleware = PointsMiddleware()

        # Middlewares outer (se ejecutan primero)
        dp.message.outer_middleware(session_middleware)
        dp.callback_query.outer_middleware(session_middleware)
        dp.chat_join_request.outer_middleware(session_middleware)
        dp.chat_member.outer_middleware(session_middleware)
        dp.poll_answer.outer_middleware(session_middleware)
        dp.message_reaction.outer_middleware(session_middleware)

        # Middleware de registro de usuario
        dp.message.outer_middleware(user_reg_middleware)
        dp.callback_query.outer_middleware(user_reg_middleware)
        dp.chat_join_request.outer_middleware(user_reg_middleware)
        dp.chat_member.outer_middleware(user_reg_middleware)
        dp.poll_answer.outer_middleware(user_reg_middleware)
        dp.message_reaction.outer_middleware(user_reg_middleware)

        # Middleware de puntos (inner)
        dp.message.middleware(points_middleware)
        dp.poll_answer.middleware(points_middleware)
        dp.message_reaction.middleware(points_middleware)

        # Registrar routers en orden de prioridad
        logger.info("Registrando handlers...")
        routers = [
            ("setup", setup_handlers.router),
            ("admin", admin_router),
            ("auction_admin", auction_admin_router),
            ("start_token", start_token),
            ("start", start.router),
            ("backpack", backpack_router),
            ("missions", missions_router),
            ("info", info_router),
            ("free_channel_admin", free_channel_admin_router),
            ("publication_test", publication_test_router),
            ("vip_menu", vip.router),
            ("gamification", gamification.router),
            ("auction_user", auction_user_router),
            ("reaction_callback", reaction_callback_router),
            ("daily_gift", daily_gift.router),
            ("minigames", minigames.router),
            ("free_user", free_user.router),
            ("lore", lore_router),
            ("combinar_pistas", combinar_pistas.router),
            ("channel_access", channel_access_router),
        ]
        
        for name, router in routers:
            dp.include_router(router)
            logger.info(f"Router {name} registrado")

        # Configurar tareas en segundo plano
        task_manager = BackgroundTaskManager()
        
        logger.info("Iniciando tareas en segundo plano...")
        task_manager.add_task(
            channel_request_scheduler(bot, Session), 
            "channel_requests"
        )
        task_manager.add_task(
            vip_subscription_scheduler(bot, Session), 
            "vip_subscriptions"
        )
        task_manager.add_task(
            vip_membership_scheduler(bot, Session), 
            "vip_memberships"
        )
        task_manager.add_task(
            auction_monitor_scheduler(bot, Session), 
            "auction_monitor"
        )
        task_manager.add_task(
            free_channel_cleanup_scheduler(bot, Session), 
            "channel_cleanup"
        )

        # Iniciar polling
        logger.info("Bot iniciado correctamente. Comenzando polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.critical(f"Error crítico en main(): {e}", exc_info=True)
        raise
    finally:
        logger.info("Cerrando bot...")
        try:
            await task_manager.shutdown()
            if 'bot' in locals():
                await bot.session.close()
        except Exception as e:
            logger.error(f"Error durante el cierre: {e}", exc_info=True)

# --- PUNTO DE ENTRADA ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot detenido por el usuario")
    except Exception as e:
        logging.critical(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
            

from handlers.admin.admin_menu import router as admin_router
from handlers.admin.vip_menu import router as vip_router
from handlers.admin.free_menu import router as free_router
from handlers.admin.config_menu import router as config_router
from handlers.admin.channel_admin import router as channel_admin_router
from handlers.admin.subscription_plans import router as subscription_plans_router
from handlers.admin.game_admin import router as game_admin_router
from handlers.admin.event_admin import router as event_admin_router
from handlers.admin.admin_config import router as admin_config_router
from handlers.admin.trivia_admin import router as trivia_admin_router

# Asegúrate de incluir trivia_admin_router al registrar routers:
admin_router.include_router(trivia_admin_router)

__all__ = [
    "admin_router",
    "vip_router",
    "free_router",
    "config_router",
    "channel_admin_router",
    "subscription_plans_router",
    "game_admin_router",
    "event_admin_router",
    "admin_config_router",
]

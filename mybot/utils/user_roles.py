from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, VipSubscription
from functools import lru_cache
import os
import time
from typing import Dict, Tuple
from datetime import datetime

from .config import VIP_CHANNEL_ID

logger = logging.getLogger(__name__)

DEFAULT_VIP_MULTIPLIER = int(os.environ.get("VIP_POINTS_MULTIPLIER", "2"))



# Cache para roles (mejora rendimiento)
@lru_cache(maxsize=1000)
def _cached_is_admin(user_id: int) -> bool:
    """Función interna con cache"""
    return False  # El valor real se setea en check_admin_status

async def check_admin_status(user_id: int, session: AsyncSession) -> bool:
    """Verifica el estado de admin en la base de datos y actualiza la cache"""
    result = await session.execute(
        select(User.is_admin).where(User.id == user_id)
    )
    is_admin = result.scalar_one_or_none() or False
    _cached_is_admin.cache_clear()  # Limpia cache antes de actualizar
    _cached_is_admin.cache_set(user_id, is_admin)
    return is_admin

async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Verifica si el usuario es admin (usa cache)"""
    # Primero verifica en cache
    if _cached_is_admin(user_id):
        return True
    
    # Si no está en cache, consulta la base de datos
    return await check_admin_status(user_id, session)

def clear_role_cache(user_id: int = None):
    """Limpia la cache de roles"""
    if user_id:
        # lru_cache does not have cache_remove for specific keys
        # For specific key removal, a custom cache or a different caching library would be needed.
        # For simplicity, clearing the entire cache for now if a specific user_id is requested.
        _cached_is_admin.cache_clear()
    else:
        _cached_is_admin.cache_clear()

async def is_vip_member(bot: Bot, user_id: int, session: AsyncSession | None = None) -> bool:
    """Check if the user should be considered a VIP."""
    from services.config_service import ConfigService

    # First check database subscription status
    if session:
        try:
            # Check if user has active VIP subscription in database
            user = await session.get(User, user_id)
            if user and user.role == "vip":
                # Check if subscription is still valid
                if user.vip_expires_at is None or user.vip_expires_at > datetime.utcnow():
                    logger.debug(f"User {user_id} is VIP via database record")
                    return True
                else:
                    # Subscription expired, update role
                    user.role = "free"
                    await session.commit()
                    logger.info(f"User {user_id} VIP subscription expired, updated to free")
            
            # Also check VipSubscription table
            stmt = select(VipSubscription).where(VipSubscription.user_id == user_id)
            result = await session.execute(stmt)
            subscription = result.scalar_one_or_none()
            if subscription:
                if subscription.expires_at is None or subscription.expires_at > datetime.utcnow():
                    logger.debug(f"User {user_id} is VIP via subscription table")
                    return True
                else:
                    logger.debug(f"User {user_id} subscription expired")
        except Exception as e:
            logger.error(f"Error checking VIP status in database for user {user_id}: {e}")

    # Fallback to channel membership check
    vip_channel_id = VIP_CHANNEL_ID
    if session:
        try:
            config_service = ConfigService(session)
            stored_vip_id = await config_service.get_vip_channel_id()
            if stored_vip_id is not None:
                vip_channel_id = stored_vip_id
        except Exception as e:
            logger.error(f"Error getting VIP channel ID from config: {e}")

    if not vip_channel_id:
        logger.debug(f"No VIP channel configured, user {user_id} is not VIP")
        return False

    try:
        member = await bot.get_chat_member(vip_channel_id, user_id)
        is_member = member.status in {"member", "administrator", "creator"}
        logger.debug(f"User {user_id} channel membership check: {is_member} (status: {member.status})")
        return is_member
    except Exception as e:
        logger.warning(f"Error checking channel membership for user {user_id}: {e}")
        return False


async def get_points_multiplier(bot: Bot, user_id: int, session: AsyncSession | None = None) -> int:
    """Return VIP multiplier for the user."""
    if await is_vip_member(bot, user_id, session=session):
        return DEFAULT_VIP_MULTIPLIER
    return 1


# Backwards compatibility
is_vip = is_vip_member


async def get_user_role(user_id: int, session: AsyncSession) -> str:
    """Obtiene el rol del usuario (admin/vip/normal)"""
    if await is_admin(user_id, session):
        return "admin"
    # Aquí puedes agregar lógica para VIP
    return "normal"


    

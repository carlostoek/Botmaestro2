from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from functools import lru_cache

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

async def get_user_role(user_id: int, session: AsyncSession) -> str:
    """Obtiene el rol del usuario (admin/vip/normal)"""
    if await is_admin(user_id, session):
        return "admin"
    # Aquí puedes agregar lógica para VIP
    return "normal"

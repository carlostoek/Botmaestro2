from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User

async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Verifica si el usuario es admin"""
    result = await session.execute(
        select(User.is_admin).where(User.id == user_id)
    )
    return result.scalar_one_or_none() or False

async def get_user_role(user_id: int, session: AsyncSession) -> str:
    """Obtiene el rol del usuario (admin/vip/normal)"""
    if await is_admin(user_id, session):
        return "admin"
    
    # Aquí puedes agregar lógica para verificar usuarios VIP
    # Por ejemplo:
    # result = await session.execute(select(...))
    # if result.scalar_one_or_none():
    #     return "vip"
    
    return "normal"
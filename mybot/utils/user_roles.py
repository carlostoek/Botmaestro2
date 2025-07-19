from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Verifica si el usuario es admin usando la sesión proporcionada"""
    from database.models import User  # Import local para evitar circular imports
    
    result = await session.execute(
        select(User.is_admin).where(User.id == user_id)
    )
    is_admin_status = result.scalar_one_or_none()
    return is_admin_status or False

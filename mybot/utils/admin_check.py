from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import User

async def is_admin(user_id: int, session: AsyncSession) -> bool:
    """Verifica si un usuario es administrador"""
    result = await session.execute(
        select(User).filter_by(id=user_id)
    )
    user = result.scalars().first()
    return user and user.is_admin

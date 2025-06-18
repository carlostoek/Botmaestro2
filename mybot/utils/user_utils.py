import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from database.models import User
from .text_utils import sanitize_text

logger = logging.getLogger(__name__)

async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """Return existing user or create a new one safely."""
    user = await session.get(User, user_id)
    if user:
        return user

    user = User(
        id=user_id,
        username=sanitize_text(username),
        first_name=sanitize_text(first_name),
        last_name=sanitize_text(last_name),
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        logger.info("Created new user: %s", user_id)
    except IntegrityError:
        await session.rollback()
        user = await session.get(User, user_id)
    return user

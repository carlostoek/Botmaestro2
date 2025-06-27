from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from database.models import User
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, telegram_id: int) -> User | None:
        return await self.session.get(User, telegram_id)

    async def create_user(
        self,
        telegram_id: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User:
        stmt = (
            pg_insert(User)
            .values(
                id=telegram_id,
                first_name=sanitize_text(first_name),
                last_name=sanitize_text(last_name),
                username=sanitize_text(username),
            )
            .on_conflict_do_nothing(index_elements=[User.id])
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        if result.rowcount:
            logger.info("Created new user: %s", telegram_id)
        user = await self.session.get(User, telegram_id)
        return user

    async def update_user_info(
        self,
        user: User,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User:
        user.first_name = sanitize_text(first_name)
        user.last_name = sanitize_text(last_name)
        user.username = sanitize_text(username)
        await self.session.commit()
        await self.session.refresh(user)
        return user

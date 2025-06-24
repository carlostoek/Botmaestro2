from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import ButtonReaction, User

class ReactionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_reaction_count(self, user_id: int, *, since: datetime | None = None) -> int:
        """Return number of reactions by a user optionally since a datetime."""
        stmt = select(func.count(ButtonReaction.id)).where(ButtonReaction.user_id == user_id)
        if since:
            stmt = stmt.where(ButtonReaction.created_at >= since)
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count or 0

    async def get_weekly_top_users(self, limit: int = 3) -> list[tuple[User, int]]:
        week_start = datetime.utcnow() - timedelta(days=7)
        stmt = (
            select(ButtonReaction.user_id, func.count(ButtonReaction.id))
            .where(ButtonReaction.created_at >= week_start)
            .group_by(ButtonReaction.user_id)
            .order_by(func.count(ButtonReaction.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        user_counts = result.all()
        users = []
        for user_id, count in user_counts:
            user = await self.session.get(User, user_id)
            if user:
                users.append((user, count))
        return users

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import MiniGameUsage, Purchase, User
from services.point_service import PointService

class MiniGameService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def _get_usage(self, user_id: int, game: str) -> MiniGameUsage:
        usage = await self.session.get(MiniGameUsage, {"user_id": user_id, "game": game})
        if not usage:
            usage = MiniGameUsage(user_id=user_id, game=game, free_used_at=None, extra_uses=0)
            self.session.add(usage)
            await self.session.commit()
        return usage

    async def can_use_free(self, user_id: int, game: str) -> bool:
        usage = await self._get_usage(user_id, game)
        if not usage.free_used_at:
            return True
        return usage.free_used_at.date() != datetime.utcnow().date()

    async def use_free(self, user_id: int, game: str) -> None:
        usage = await self._get_usage(user_id, game)
        usage.free_used_at = datetime.utcnow()
        await self.session.commit()

    async def add_extra_uses(self, user_id: int, game: str, amount: int, cost: int) -> bool:
        user = await self.session.get(User, user_id)
        if not user or user.points < cost:
            return False
        await self.point_service.deduct_points(user_id, cost)
        usage = await self._get_usage(user_id, game)
        usage.extra_uses += amount
        purchase = Purchase(user_id=user_id, item=f"extra_{game}", amount=cost)
        self.session.add(purchase)
        await self.session.commit()
        return True

    async def use_extra(self, user_id: int, game: str) -> bool:
        usage = await self._get_usage(user_id, game)
        if usage.extra_uses > 0:
            usage.extra_uses -= 1
            await self.session.commit()
            return True
        return False

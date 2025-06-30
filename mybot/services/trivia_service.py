from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from aiogram import Bot

from database.models import (
    Trivia,
    TriviaResult,
    User,
    LorePiece,
    UserLorePiece,
)
from .point_service import PointService
from .level_service import LevelService


class TriviaService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
        self.level_service = LevelService(session)

    async def create_trivia(
        self,
        trigger_code: str,
        question: str,
        options: list[str],
        correct_index: int,
        reward_points: int = 0,
        unlocks_lore_piece_code: str | None = None,
        level_increment: int = 0,
    ) -> Trivia:
        trivia = Trivia(
            trigger_code=trigger_code,
            question=question,
            options=options,
            correct_index=correct_index,
            reward_points=reward_points,
            unlocks_lore_piece_code=unlocks_lore_piece_code,
            level_increment=level_increment,
        )
        self.session.add(trivia)
        await self.session.commit()
        await self.session.refresh(trivia)
        return trivia

    async def list_trivias(self, offset: int = 0, limit: int = 5) -> tuple[list[Trivia], int]:
        total = (await self.session.execute(select(func.count()).select_from(Trivia))).scalar_one()
        result = await self.session.execute(
            select(Trivia).order_by(Trivia.id).offset(offset).limit(limit)
        )
        return result.scalars().all(), total

    async def get_trivia_by_id(self, trivia_id: int) -> Trivia | None:
        return await self.session.get(Trivia, trivia_id)

    async def get_trivia_by_code(self, trigger_code: str) -> Trivia | None:
        stmt = select(Trivia).where(Trivia.trigger_code == trigger_code, Trivia.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_trivia(
        self,
        trivia_id: int,
        **kwargs,
    ) -> bool:
        trivia = await self.session.get(Trivia, trivia_id)
        if not trivia:
            return False
        for field, value in kwargs.items():
            if hasattr(trivia, field) and value is not None:
                setattr(trivia, field, value)
        await self.session.commit()
        return True

    async def delete_trivia(self, trivia_id: int) -> bool:
        trivia = await self.session.get(Trivia, trivia_id)
        if not trivia:
            return False
        await self.session.delete(trivia)
        await self.session.commit()
        return True

    async def answer_trivia(
        self, user_id: int, trivia: Trivia, option_index: int, bot: Bot | None = None
    ) -> bool:
        correct = option_index == trivia.correct_index
        exists_stmt = select(TriviaResult).where(
            TriviaResult.user_id == user_id, TriviaResult.trivia_id == trivia.id
        )
        existing = (await self.session.execute(exists_stmt)).scalar_one_or_none()
        if existing:
            return correct

        self.session.add(
            TriviaResult(user_id=user_id, trivia_id=trivia.id, is_correct=correct)
        )
        if correct and trivia.reward_points:
            await self.point_service.add_points(user_id, trivia.reward_points, bot=bot)
        if correct and trivia.level_increment:
            user = await self.session.get(User, user_id)
            if user:
                user.level += trivia.level_increment
                self.session.add(user)
                await self.session.commit()
                await self.level_service.check_for_level_up(user, bot=bot)
        await self.session.commit()

        if correct and trivia.unlocks_lore_piece_code:
            lore_stmt = select(LorePiece).where(
                LorePiece.code_name == trivia.unlocks_lore_piece_code
            )
            piece = (await self.session.execute(lore_stmt)).scalar_one_or_none()
            if piece:
                check_stmt = select(UserLorePiece).where(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == piece.id,
                )
                exists = (await self.session.execute(check_stmt)).scalar_one_or_none()
                if not exists:
                    self.session.add(
                        UserLorePiece(user_id=user_id, lore_piece_id=piece.id)
                    )
                    await self.session.commit()
        return correct

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from database.models import Trivia, UserTriviaResult
from .point_service import PointService


class TriviaService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def create_trivia(
        self,
        code_name: str,
        question: str,
        options: list[str],
        correct_index: int,
        reward_points: int = 0,
    ) -> Trivia:
        trivia = Trivia(
            code_name=code_name.strip(),
            question=question.strip(),
            options=options,
            correct_index=correct_index,
            reward_points=reward_points,
        )
        self.session.add(trivia)
        await self.session.commit()
        await self.session.refresh(trivia)
        return trivia

    async def list_trivias(self) -> list[Trivia]:
        result = await self.session.execute(select(Trivia).order_by(Trivia.id))
        return result.scalars().all()

    async def get_trivia_by_id(self, trivia_id: int) -> Trivia | None:
        return await self.session.get(Trivia, trivia_id)

    async def update_trivia(
        self,
        trivia_id: int,
        *,
        code_name: str | None = None,
        question: str | None = None,
        options: list[str] | None = None,
        correct_index: int | None = None,
        reward_points: int | None = None,
        is_active: bool | None = None,
    ) -> bool:
        trivia = await self.session.get(Trivia, trivia_id)
        if not trivia:
            return False
        if code_name is not None:
            trivia.code_name = code_name.strip()
        if question is not None:
            trivia.question = question.strip()
        if options is not None:
            trivia.options = options
        if correct_index is not None:
            trivia.correct_index = correct_index
        if reward_points is not None:
            trivia.reward_points = reward_points
        if is_active is not None:
            trivia.is_active = is_active
        await self.session.commit()
        return True

    async def delete_trivia(self, trivia_id: int) -> bool:
        trivia = await self.session.get(Trivia, trivia_id)
        if not trivia:
            return False
        await self.session.delete(trivia)
        await self.session.commit()
        return True

    async def record_answer(
        self,
        user_id: int,
        trivia_id: int,
        selected_index: int,
        bot: Bot | None = None,
    ) -> tuple[bool, bool, int]:
        trivia = await self.session.get(Trivia, trivia_id)
        if not trivia or not trivia.is_active:
            return False, False, 0
        stmt = select(UserTriviaResult).where(
            UserTriviaResult.user_id == user_id,
            UserTriviaResult.trivia_id == trivia_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return False, existing.is_correct, existing.points_awarded
        is_correct = selected_index == trivia.correct_index
        points = trivia.reward_points if is_correct else 0
        result = UserTriviaResult(
            user_id=user_id,
            trivia_id=trivia_id,
            selected_index=selected_index,
            is_correct=is_correct,
            points_awarded=points,
        )
        self.session.add(result)
        if points:
            await self.point_service.add_points(user_id, points, bot=bot)
        await self.session.commit()
        return True, is_correct, points

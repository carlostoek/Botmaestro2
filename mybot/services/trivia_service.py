import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import TriviaQuestion, TriviaResult
from services.point_service import PointService
from backpack import desbloquear_pista_narrativa


def parse_options_from_db(options_field) -> list[str]:
    if isinstance(options_field, list):
        return options_field
    if isinstance(options_field, str):
        try:
            import json
            return json.loads(options_field)
        except Exception:
            return [opt.strip() for opt in options_field.split("|") if opt.strip()]
    return []


class TriviaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_random_trivia_question(self, user_id: int) -> TriviaQuestion | None:
        stmt = select(TriviaQuestion)
        result = await self.session.execute(stmt)
        questions = result.scalars().all()
        if not questions:
            return None
        answered_stmt = select(TriviaResult.question_id).where(
            TriviaResult.user_id == user_id, TriviaResult.is_correct == True
        )
        answered = await self.session.execute(answered_stmt)
        answered_ids = {row[0] for row in answered.all()}
        available = [q for q in questions if q.id not in answered_ids]
        if not available:
            return None
        return random.choice(available)

    async def record_trivia_result(self, user_id: int, question_id: int, is_correct: bool) -> TriviaResult:
        result = TriviaResult(user_id=user_id, question_id=question_id, is_correct=is_correct)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def get_trivia_attempts(self, user_id: int, question_id: int) -> int:
        stmt = select(func.count(TriviaResult.id)).where(
            TriviaResult.user_id == user_id, TriviaResult.question_id == question_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def check_if_trivia_answered_correctly(self, user_id: int, question_id: int) -> bool:
        stmt = select(TriviaResult).where(
            TriviaResult.user_id == user_id,
            TriviaResult.question_id == question_id,
            TriviaResult.is_correct == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def handle_correct_answer(self, user_id: int, question: TriviaQuestion, bot=None):
        await PointService(self.session).add_points(user_id, question.points, bot=bot)
        if question.unlocks:
            await desbloquear_pista_narrativa(bot, user_id, question.unlocks, {"source": "trivia"})

    async def handle_incorrect_answer(self, user_id: int, question_id: int):
        await self.record_trivia_result(user_id, question_id, False)


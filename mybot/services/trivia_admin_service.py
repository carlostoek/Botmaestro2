from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TriviaQuestionModel, TriviaTemplate, UserTriviaHistory


class TriviaAdminService:
    """Utility helpers for trivia admin panels."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_trivia_stats(self) -> dict:
        """Return basic statistics for trivia admin dashboard."""
        total_questions = await self.session.scalar(
            select(func.count()).select_from(TriviaQuestionModel)
        )
        active_templates = await self.session.scalar(
            select(func.count()).select_from(TriviaTemplate).where(TriviaTemplate.is_active == True)
        )
        # Active sessions are kept in memory by TriviaManager; here we just report zero
        active_sessions = 0
        players_today = await self.session.scalar(
            select(func.count(func.distinct(UserTriviaHistory.user_id)))
            .where(func.date(UserTriviaHistory.completed_at) == func.date(func.now()))
        )
        return {
            "total_questions": total_questions or 0,
            "active_templates": active_templates or 0,
            "active_sessions": active_sessions,
            "players_today": players_today or 0,
        }

    async def get_questions_summary(self) -> list[dict]:
        result = await self.session.execute(
            select(TriviaQuestionModel).order_by(TriviaQuestionModel.created_at.desc())
        )
        questions = result.scalars().all()
        return [
            {"id": q.id, "question": q.question}
            for q in questions
        ]

    async def get_questions_paginated(self, page: int, per_page: int):
        stmt = (
            select(TriviaQuestionModel)
            .order_by(TriviaQuestionModel.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_total_question_pages(self, per_page: int) -> int:
        total = await self.session.scalar(
            select(func.count()).select_from(TriviaQuestionModel)
        ) or 0
        pages = (total + per_page - 1) // per_page
        return max(pages, 1)

    async def get_question_by_id(self, question_id: str):
        return await self.session.get(TriviaQuestionModel, question_id)

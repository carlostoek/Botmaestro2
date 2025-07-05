from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import UserTriviaHistory, UnlockedContent


class TriviaAnalytics:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_user_history(self, user_id: int) -> List[UserTriviaHistory]:
        stmt = select(UserTriviaHistory).where(UserTriviaHistory.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_performance(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento del usuario"""
        history = await self.get_user_history(user_id)
        average_score = 0.0
        if history:
            average_score = sum(h.score / h.total_questions for h in history) / len(history)
        return {
            "total_sessions": len(history),
            "average_score": average_score,
            "best_category": await self.get_best_category(user_id),
            "improvement_trend": await self.calculate_improvement_trend(user_id),
            "completion_rate": await self.get_completion_rate(user_id),
        }

    async def get_trivia_effectiveness(self, template_id: str) -> Dict[str, Any]:
        """Analiza la efectividad de un template de trivia"""
        sessions = await self.get_template_sessions(template_id)
        activation_rate = 0
        potential = await self.get_potential_activations(template_id)
        if potential:
            activation_rate = len(sessions) / potential
        completion_rate = (
            sum(1 for s in sessions if s.completed_at) / len(sessions)
            if sessions else 0
        )
        average_score = (
            sum(s.score / s.total_questions for s in sessions) / len(sessions)
            if sessions else 0
        )
        return {
            "activation_rate": activation_rate,
            "completion_rate": completion_rate,
            "average_score": average_score,
            "content_unlock_rate": await self.get_unlock_rate(template_id),
        }

    async def get_template_sessions(self, template_id: str) -> List[UserTriviaHistory]:
        stmt = select(UserTriviaHistory).where(UserTriviaHistory.template_id == template_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_potential_activations(self, template_id: str) -> int:
        # Placeholder: count potential activations from game events
        return 1

    async def get_unlock_rate(self, template_id: str) -> float:
        stmt = select(func.count()).select_from(UnlockedContent).where(
            UnlockedContent.unlocked_by == template_id
        )
        result = await self.db.execute(stmt)
        total_unlocks = result.scalar_one_or_none() or 0
        total_sessions = len(await self.get_template_sessions(template_id))
        return total_unlocks / total_sessions if total_sessions else 0

    async def get_best_category(self, user_id: int) -> str:
        # Placeholder: derive category from history triggers
        history = await self.get_user_history(user_id)
        categories: Dict[str, int] = {}
        for rec in history:
            categories[rec.triggered_by] = categories.get(rec.triggered_by, 0) + rec.score
        if not categories:
            return ""
        return max(categories, key=categories.get)

    async def calculate_improvement_trend(self, user_id: int) -> float:
        # Placeholder: compute trend as difference between first and last scores
        history = await self.get_user_history(user_id)
        if len(history) < 2:
            return 0.0
        first = history[0].score / history[0].total_questions
        last = history[-1].score / history[-1].total_questions
        return last - first

    async def get_completion_rate(self, user_id: int) -> float:
        history = await self.get_user_history(user_id)
        completed = sum(1 for rec in history if rec.completed_at)
        return completed / len(history) if history else 0.0

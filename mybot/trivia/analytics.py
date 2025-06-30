from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy import select

from database.models import UserTriviaHistory, TriviaTemplate


class TriviaAnalytics:
    """Utility class to calculate basic trivia statistics."""

    def __init__(self, db_session):
        self.db = db_session

    async def get_user_history(self, user_id: int) -> List[UserTriviaHistory]:
        stmt = select(UserTriviaHistory).where(UserTriviaHistory.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_best_category(self, user_id: int) -> str | None:
        """Return the category with the highest average score for the user."""
        history = await self.get_user_history(user_id)
        if not history:
            return None
        scores: Dict[str, List[float]] = {}
        for entry in history:
            tmpl_stmt = select(TriviaTemplate).where(TriviaTemplate.id == entry.template_id)
            tmpl = (await self.db.execute(tmpl_stmt)).scalar_one_or_none()
            category = getattr(tmpl, "name", "unknown") if tmpl else "unknown"
            scores.setdefault(category, []).append(entry.score / max(entry.total_questions, 1))
        best_cat = None
        best_score = -1.0
        for cat, vals in scores.items():
            avg = sum(vals) / len(vals)
            if avg > best_score:
                best_score = avg
                best_cat = cat
        return best_cat

    async def calculate_improvement_trend(self, user_id: int) -> float:
        """Very simple improvement trend calculation based on scores over time."""
        history = await self.get_user_history(user_id)
        history = sorted(history, key=lambda h: h.completed_at)
        if len(history) < 2:
            return 0.0
        scores = [h.score / max(h.total_questions, 1) for h in history]
        first, last = scores[0], scores[-1]
        return last - first

    async def get_completion_rate(self, user_id: int) -> float:
        history = await self.get_user_history(user_id)
        if not history:
            return 0.0
        completed = [h for h in history if h.total_questions]
        return len(completed) / len(history)

    async def get_user_performance(self, user_id: int) -> Dict[str, Any]:
        history = await self.get_user_history(user_id)
        avg_score = (
            sum(h.score / max(h.total_questions, 1) for h in history) / len(history)
            if history
            else 0.0
        )
        return {
            "total_sessions": len(history),
            "average_score": avg_score,
            "best_category": await self.get_best_category(user_id),
            "improvement_trend": await self.calculate_improvement_trend(user_id),
            "completion_rate": await self.get_completion_rate(user_id),
        }

    async def get_template_sessions(self, template_id: str) -> List[UserTriviaHistory]:
        stmt = select(UserTriviaHistory).where(UserTriviaHistory.template_id == template_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_potential_activations(self, template_id: str) -> int:
        # Placeholder: this would normally analyse triggers or user base
        sessions = await self.get_template_sessions(template_id)
        return max(len(sessions), 1)

    async def get_unlock_rate(self, template_id: str) -> float:
        # Placeholder implementation
        sessions = await self.get_template_sessions(template_id)
        unlocked = [s for s in sessions if s.rewards_earned]
        return len(unlocked) / len(sessions) if sessions else 0.0

    async def get_trivia_effectiveness(self, template_id: str) -> Dict[str, Any]:
        sessions = await self.get_template_sessions(template_id)
        activation_rate = len(sessions) / await self.get_potential_activations(template_id)
        completion_rate = sum(1 for s in sessions if s.completed_at) / len(sessions) if sessions else 0.0
        avg_score = (
            sum(s.score / max(s.total_questions, 1) for s in sessions) / len(sessions)
            if sessions
            else 0.0
        )
        return {
            "activation_rate": activation_rate,
            "completion_rate": completion_rate,
            "average_score": avg_score,
            "content_unlock_rate": await self.get_unlock_rate(template_id),
        }

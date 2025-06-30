from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

from services.mission_service import MissionService

logger = logging.getLogger(__name__)


class TriviaQuestIntegration:
    """Integrates trivia results with the mission system."""

    @staticmethod
    async def check_trivia_missions(
        user_id: int,
        result: dict,
        session: AsyncSession,
        bot=None,
    ) -> list[dict]:
        """Update trivia mission progress and return newly completed missions."""
        mission_service = MissionService(session)
        completed: list[dict] = []

        try:
            # Generic progress for answering a trivia question
            await mission_service.update_progress(user_id, "trivia", bot=bot)
            if result.get("is_correct"):
                await mission_service.update_progress(
                    user_id, "trivia_correct", bot=bot
                )
        except Exception as exc:
            logger.exception("Error updating trivia mission progress: %s", exc)
            return completed

        # Fetch active missions to see which ones are now completed
        missions = await mission_service.get_active_missions(user_id=user_id)
        user = await session.get(User, user_id)
        for mission in missions:
            is_completed, _ = await mission_service.check_mission_completion_status(
                user, mission
            )
            if is_completed:
                completed.append(
                    {
                        "description": mission.description or mission.name,
                        "reward_points": mission.reward_points,
                        "reward_lorepiece": mission.unlocks_lore_piece_code,
                    }
                )
        return completed

    @staticmethod
    async def trigger_special_missions(
        user_id: int,
        stats: dict,
        session: AsyncSession,
        bot=None,
    ) -> list[dict]:
        """Trigger special missions based on user trivia stats."""
        mission_service = MissionService(session)
        completed: list[dict] = []

        try:
            streak = stats.get("streak", 0)
            if streak >= 10:
                success, mission = await mission_service.complete_mission(
                    user_id, "trivia_streak_10", bot=bot
                )
                if success and mission:
                    completed.append(
                        {
                            "description": mission.description or mission.name,
                            "reward_points": mission.reward_points,
                            "reward_lorepiece": mission.unlocks_lore_piece_code,
                        }
                    )
        except Exception as exc:
            logger.exception("Error triggering special trivia missions: %s", exc)

        return completed

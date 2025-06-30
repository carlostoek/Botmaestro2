from __future__ import annotations

from typing import Dict


async def unlock_storyboard_from_trivia(user_id: int, storyboard_id: str, trivia_context: Dict[str, any], storyboard_manager):
    await storyboard_manager.activate_storyboard(
        user_id=user_id,
        storyboard_id=storyboard_id,
        trigger_context={
            "source": "trivia_completion",
            "trivia_score": trivia_context.get("score"),
            "trivia_template": trivia_context.get("template_id"),
        },
    )


class TriviaPointsIntegration:
    async def calculate_trivia_points(self, score: int, difficulty: int, time_bonus: bool) -> int:
        base_points = score * 10
        difficulty_multiplier = 1 + (difficulty - 1) * 0.2
        time_multiplier = 1.5 if time_bonus else 1.0
        return int(base_points * difficulty_multiplier * time_multiplier)

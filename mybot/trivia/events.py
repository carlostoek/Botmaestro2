from __future__ import annotations

from typing import Any, Dict

from .schema import TriggerEvent
from .manager import TriviaManager


class GameEventListener:
    def __init__(self, trivia_manager: TriviaManager, storyboard_manager, points_system):
        self.trivia_manager = trivia_manager
        self.storyboard_manager = storyboard_manager
        self.points_system = points_system

    async def on_level_up(self, user_id: int, old_level: int, new_level: int):
        await self.trivia_manager.check_triggers(
            user_id=user_id,
            event=TriggerEvent.LEVEL_UP,
            context={"old_level": old_level, "new_level": new_level},
        )

    async def on_points_milestone(self, user_id: int, points: int, milestone: int):
        await self.trivia_manager.check_triggers(
            user_id=user_id,
            event=TriggerEvent.POINTS_MILESTONE,
            context={"points": points, "milestone": milestone},
        )

    async def on_story_completion(self, user_id: int, story_id: str):
        await self.trivia_manager.check_triggers(
            user_id=user_id,
            event=TriggerEvent.STORY_COMPLETION,
            context={"story_id": story_id},
        )

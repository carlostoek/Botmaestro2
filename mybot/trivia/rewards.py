from __future__ import annotations

from typing import Any, Dict

from .schema import RewardType, TriviaReward


class RewardProcessor:
    def __init__(self, points_system, storyboard_manager, content_manager):
        self.points_system = points_system
        self.storyboard_manager = storyboard_manager
        self.content_manager = content_manager

    async def process_reward(self, user_id: int, reward: TriviaReward, context: Dict[str, Any]):
        if reward.type == RewardType.POINTS:
            await self.points_system.add_points(user_id, reward.value)
        elif reward.type == RewardType.LEVEL_BOOST:
            await self.points_system.boost_level(user_id, reward.value)
        elif reward.type == RewardType.SPECIAL_CONTENT:
            await self.content_manager.unlock_content(user_id, reward.value)
        elif reward.type == RewardType.STORYBOARD_UNLOCK:
            await self.storyboard_manager.unlock_storyboard(user_id, reward.value)
        elif reward.type == RewardType.ACHIEVEMENT:
            await self.content_manager.unlock_achievement(user_id, reward.value)
        if reward.immediate:
            await self.trigger_immediate_effects(user_id, reward, context)

    async def trigger_immediate_effects(self, user_id: int, reward: TriviaReward, context: Dict[str, Any]):
        # Placeholder for custom logic
        pass

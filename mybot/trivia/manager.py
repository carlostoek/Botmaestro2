from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiogram import Bot
from aiogram.fsm.context import FSMContext

from .schema import (
    TriviaSession,
    TriviaTemplate,
    TriviaQuestion,
    TriggerEvent,
)


class TriviaManager:
    def __init__(self, bot: Bot, db_session, points_system, storyboard_manager):
        self.bot = bot
        self.db = db_session
        self.points_system = points_system
        self.storyboard_manager = storyboard_manager
        self.active_sessions: Dict[int, TriviaSession] = {}

    async def check_triggers(self, user_id: int, event: TriggerEvent, context: Dict[str, Any]):
        templates = await self.get_triggered_templates(event, user_id, context)
        for template in templates:
            if await self.meets_requirements(user_id, template, context):
                await self.start_trivia_session(user_id, template, context)

    async def get_triggered_templates(
        self, event: TriggerEvent, user_id: int, context: Dict[str, Any]
    ) -> List[TriviaTemplate]:
        # Placeholder: fetch templates from DB matching event
        return []

    async def meets_requirements(
        self, user_id: int, template: TriviaTemplate, context: Dict[str, Any]
    ) -> bool:
        # TODO: implement requirement checks
        return True

    async def get_user_level(self, user_id: int) -> int:
        # Placeholder using points_system
        return await self.points_system.get_level(user_id)

    async def select_questions(
        self, template: TriviaTemplate, user_id: int
    ) -> List[TriviaQuestion]:
        # TODO: implement question selection logic
        return []

    async def start_trivia_session(
        self, user_id: int, template: TriviaTemplate, context: Dict[str, Any]
    ) -> None:
        questions = await self.select_questions(template, user_id)
        session = TriviaSession(
            id=f"trivia_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            channel_id=context.get("channel_id", user_id),
            questions=questions,
            triggered_by=template.id,
            context=context,
            rewards_on_correct=template.rewards.get("correct", []),
            rewards_on_wrong=template.rewards.get("wrong", []),
            rewards_on_completion=template.rewards.get("completion", []),
        )
        self.active_sessions[user_id] = session
        from .content import TriviaContentDelivery
        await TriviaContentDelivery.send_trivia_intro(self.bot, session)

    async def process_answer(self, user_id: int, answer: str, state: FSMContext) -> None:
        session = self.active_sessions.get(user_id)
        if not session:
            return
        # TODO: validate answer and update score
        session.current_question_index += 1
        if session.current_question_index >= len(session.questions):
            await self.complete_trivia_session(session, state)
        else:
            await self.send_next_question(session)

    async def complete_trivia_session(self, session: TriviaSession, state: FSMContext) -> None:
        # TODO: process completion rewards and clean up
        if session.user_id in self.active_sessions:
            del self.active_sessions[session.user_id]
        await state.set_state(None)

    async def send_answer_result(self, session: TriviaSession, is_correct: bool, explanation: str | None = None) -> None:
        from .content import TriviaContentDelivery
        await TriviaContentDelivery.send_answer_result(self.bot, session, is_correct, explanation or "")

    async def send_next_question(self, session: TriviaSession) -> None:
        from .content import TriviaContentDelivery
        await TriviaContentDelivery.send_question(self.bot, session)


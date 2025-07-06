import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Mission,
    User,
    UserMissionEntry,
    Challenge,
    UserChallengeProgress,
)
from database.narrative_models import LorePiece, UserLorePiece

from utils.text_utils import sanitize_text
from services.point_service import PointService

logger = logging.getLogger(__name__)

MISSION_PLACEHOLDER: list = []


class MissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.point_service = PointService(session)

    async def get_active_missions(
        self, user_id: int | None = None, mission_type: str | None = None
    ) -> list[Mission]:
        stmt = select(Mission).where(Mission.is_active == True)
        if mission_type:
            stmt = stmt.where(Mission.type == mission_type)

        result = await self.session.execute(stmt)
        missions = [
            m
            for m in result.scalars().all()
            if not m.duration_days
            or (m.created_at + datetime.timedelta(days=m.duration_days))
            > datetime.datetime.utcnow()
        ]

        if user_id:
            user = await self.session.get(User, user_id)
            if user:
                filtered: list[Mission] = []
                for mission in missions:
                    completed, _ = await self.check_mission_completion_status(user, mission)
                    if not completed:
                        filtered.append(mission)
                missions = filtered

        return missions

    async def get_daily_active_missions(self, user_id: int | None = None) -> list[Mission]:
        return await self.get_active_missions(user_id=user_id, mission_type="daily")

    async def get_mission_by_id(self, mission_id: str) -> Mission | None:
        return await self.session.get(Mission, mission_id)

    async def check_mission_completion_status(
        self, user: User, mission: Mission, target_message_id: int | None = None
    ) -> tuple[bool, str]:
        record = user.missions_completed.get(mission.id)

        if mission.type == "one_time":
            if record:
                return True, "already_completed"
        elif mission.type == "daily":
            if record:
                last = datetime.datetime.fromisoformat(record)
                if datetime.datetime.now() - last < datetime.timedelta(days=1):
                    return True, "daily_limit_reached"
        elif mission.type == "weekly":
            if record:
                last = datetime.datetime.fromisoformat(record)
                if datetime.datetime.now() - last < datetime.timedelta(weeks=1):
                    return True, "weekly_limit_reached"
        elif mission.type == "reaction":
            if record:
                return True, "already_completed"

        return False, ""

    async def complete_mission(
        self,
        user_id: int,
        mission_id: str,
        reaction_type: str | None = None,
        target_message_id: int | None = None,
        *,
        bot=None,
    ) -> tuple[bool, Mission | None]:
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission or not mission.is_active:
            logger.warning(
                "Failed to complete mission: User %s or mission %s not found or inactive.",
                user_id,
                mission_id,
            )
            return False, None

        is_completed, reason = await self.check_mission_completion_status(user, mission, target_message_id)
        if is_completed:
            logger.info(
                "User %s attempted to complete mission %s but it was already completed (%s).",
                user_id,
                mission_id,
                reason,
            )
            return False, None

        user.missions_completed[mission.id] = datetime.datetime.now().isoformat()

        await self.point_service.add_points(user_id, mission.reward_points, bot=bot)

        if mission.type == "daily":
            user.last_daily_mission_reset = datetime.datetime.now()
        elif mission.type == "weekly":
            user.last_weekly_mission_reset = datetime.datetime.now()

        unlock_code = getattr(mission, "unlocks_lore_piece_code", None)
        if not unlock_code and mission.action_data:
            unlock_code = mission.action_data.get("unlocks_lore_piece_code")

        if unlock_code:
            lore_stmt = select(LorePiece).where(LorePiece.code_name == unlock_code)
            lore_piece = (await self.session.execute(lore_stmt)).scalar_one_or_none()
            if lore_piece:
                check_stmt = select(UserLorePiece).where(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == lore_piece.id,
                )
                exists = (await self.session.execute(check_stmt)).scalar_one_or_none()
                if not exists:
                    self.session.add(UserLorePiece(user_id=user_id, lore_piece_id=lore_piece.id))
                    logger.info(
                        "User %s unlocked lore piece %s via mission %s",
                        user_id,
                        unlock_code,
                        mission_id,
                    )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        if bot:
            from utils.message_utils import get_mission_completed_message
            from utils.keyboard_utils import get_mission_completed_keyboard

            text = await get_mission_completed_message(mission)
            await bot.send_message(user_id, text, reply_markup=get_mission_completed_keyboard())

        logger.info(
            "User %s successfully completed mission %s (Type: %s, Message: %s).",
            user_id,
            mission_id,
            mission.type,
            target_message_id,
        )
        return True, mission

    async def create_mission(
        self,
        name: str,
        description: str,
        mission_type: str,
        target_value: int,
        reward_points: int,
        duration_days: int = 0,
        *,
        requires_action: bool = False,
        action_data: dict | None = None,
    ) -> Mission:
        mission_id = f"{mission_type}_{sanitize_text(name).lower().replace(' ', '_').replace('.', '').replace(',', '')}"
        new_mission = Mission(
            id=mission_id,
            name=sanitize_text(name),
            description=sanitize_text(description),
            reward_points=reward_points,
            type=mission_type,
            target_value=target_value,
            duration_days=duration_days,
            requires_action=requires_action,
            action_data=action_data,
            is_active=True,
        )
        self.session.add(new_mission)
        await self.session.commit()
        await self.session.refresh(new_mission)
        return new_mission

    async def toggle_mission_status(self, mission_id: str, status: bool) -> bool:
        mission = await self.session.get(Mission, mission_id)
        if mission:
            mission.is_active = status
            await self.session.commit()
            return True
        return False

    async def update_progress(
        self,
        user_id: int,
        mission_type: str,
        *,
        increment: int = 1,
        current_value: int | None = None,
        bot=None,
    ) -> None:
        missions = await self.get_active_missions(mission_type=mission_type)
        for mission in missions:
            stmt = select(UserMissionEntry).where(
                UserMissionEntry.user_id == user_id,
                UserMissionEntry.mission_id == mission.id,
            )
            result = await self.session.execute(stmt)
            record = result.scalar_one_or_none()
            if not record:
                record = UserMissionEntry(user_id=user_id, mission_id=mission.id)
                self.session.add(record)
            if record.completed:
                continue

            if mission_type == "login_streak" and current_value is not None:
                progress = current_value
                record.progress_value = progress
            else:
                if record.progress_value is None:
                    record.progress_value = 0
                record.progress_value += increment
                progress = record.progress_value

            if progress >= mission.target_value:
                record.completed = True
                record.completed_at = datetime.datetime.utcnow()
                await self.point_service.add_points(user_id, mission.reward_points, bot=bot)
                if bot:
                    from utils.message_utils import get_mission_completed_message
                    from utils.keyboard_utils import get_mission_completed_keyboard

                    text = await get_mission_completed_message(mission)
                    await bot.send_message(user_id, text, reply_markup=get_mission_completed_keyboard())
        await self.session.commit()

    async def delete_mission(self, mission_id: str) -> bool:
        mission = await self.session.get(Mission, mission_id)
        if mission:
            await self.session.delete(mission)
            await self.session.commit()
            return True
        return False

    async def get_active_challenges(self, challenge_type: str | None = None) -> list[Challenge]:
        now = datetime.datetime.utcnow()
        stmt = select(Challenge).where(Challenge.start_date <= now, Challenge.end_date >= now)
        if challenge_type:
            stmt = stmt.where(Challenge.type == challenge_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def increment_challenge_progress(
        self,
        user_id: int,
        goal_type: str,
        increment: int = 1,
        bot=None,
    ) -> list[Challenge]:
        completed: list[Challenge] = []
        challenges = await self.get_active_challenges()
        for challenge in challenges:
            if challenge.goal_type != goal_type:
                continue
            prog = await self.session.get(
                UserChallengeProgress,
                {"user_id": user_id, "challenge_id": challenge.id},
            )
            if not prog:
                prog = UserChallengeProgress(user_id=user_id, challenge_id=challenge.id)
                self.session.add(prog)
            if prog.completed:
                continue

            prog.current_value += increment
            if prog.current_value >= challenge.goal_value:
                prog.completed = True
                prog.completed_at = datetime.datetime.utcnow()
                completed.append(challenge)
                await self.point_service.add_points(user_id, 100, bot=bot)
        await self.session.commit()
        return completed

                           

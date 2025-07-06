import datetime import random import logging from sqlalchemy.ext.asyncio import AsyncSession from sqlalchemy import select, update

from database.models import ( Mission, User, UserMissionEntry, UserItem, Hint, UserHint, Combination, UserCombination, Level, UserLevel, UserDailyGift, UserReferral, Referral ) from database.narrative_models import LorePiece, UserLorePiece from utils.text_utils import sanitize_text from services.point_service import PointService

logger = logging.getLogger(name)

MISSION_PLACEHOLDER: list = []

class MissionService: def init(self, session: AsyncSession): self.session = session self.point_service = PointService(session)

async def get_active_missions(self, user_id: int = None, mission_type: str = None) -> list[Mission]:
    stmt = select(Mission).where(Mission.is_active == True)
    if mission_type:
        stmt = stmt.where(Mission.type == mission_type)
    result = await self.session.execute(stmt)
    missions = [m for m in result.scalars().all() if not m.duration_days or 
               (m.created_at + datetime.timedelta(days=m.duration_days)) > datetime.datetime.utcnow()]

    if user_id:
        user = await self.session.get(User, user_id)
        if user:
            filtered_missions = []
            now = datetime.datetime.now()

            for mission in missions:
                is_completed_for_period, _ = await self.check_mission_completion_status(user, mission)
                if not is_completed_for_period:
                    filtered_missions.append(mission)
            return filtered_missions
    return missions

async def get_daily_active_missions(self, user_id: int | None = None) -> list[Mission]:
    return await self.get_active_missions(user_id=user_id, mission_type="daily")

async def get_mission_by_id(self, mission_id: str) -> Mission | None:
    return await self.session.get(Mission, mission_id)

async def check_mission_completion_status(self, user: User, mission: Mission, target_message_id: int = None) -> tuple[bool, str]:
    mission_completion_record = user.missions_completed.get(mission.id)

    if mission.type == "one_time":
        if mission_completion_record:
            return True, "already_completed"
    elif mission.type == "daily":
        if mission_completion_record:
            last_completed = datetime.datetime.fromisoformat(mission_completion_record)
            if (datetime.datetime.now() - last_completed) < datetime.timedelta(days=1):
                return True, "daily_limit_reached"
    elif mission.type == "weekly":
        if mission_completion_record:
            last_completed = datetime.datetime.fromisoformat(mission_completion_record)
            if (datetime.datetime.now() - last_completed) < datetime.timedelta(weeks=1):
                return True, "weekly_limit_reached"
    elif mission.type == "reaction":
        if mission_completion_record:
            return True, "already_completed"

    return False, ""

async def complete_mission(self, user_id: int, mission_id: str, reaction_type: str = None, target_message_id: int = None, *, bot=None) -> tuple[bool, Mission | None]:
    user = await self.session.get(User, user_id)
    mission = await self.session.get(Mission, mission_id)

    if not user or not mission or not mission.is_active:
        logger.warning(f"Failed to complete mission: User {user_id} or mission {mission_id} not found or inactive.")
        return False, None

    is_completed, reason = await self.check_mission_completion_status(user, mission, target_message_id)
    if is_completed:
        logger.info(f"User {user_id} attempted to complete mission {mission_id} but it was already completed ({reason}).")
        return False, None

    now = datetime.datetime.now().isoformat()
    user.missions_completed[mission.id] = now

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
                logger.info(f"User {user_id} unlocked lore piece {unlock_code} via mission {mission_id}")

    self.session.add(user)
    await self.session.commit()
    await self.session.refresh(user)

    if bot:
        from utils.message_utils import get_mission_completed_message
        from utils.keyboard_utils import get_mission_completed_keyboard

        text = await get_mission_completed_message(mission)
        await bot.send_message(user_id, text, reply_markup=get_mission_completed_keyboard())

    logger.info(f"User {user_id} successfully completed mission {mission_id} (Type: {mission.type}, Message: {target_message_id}).")
    return True, mission

async def create_mission(self, name: str, description: str, mission_type: str, target_value: int, reward_points: int, duration_days: int = 0, *, requires_action: bool = False, action_data: dict | None = None) -> Mission:
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

async def update_progress(self, user_id: int, mission_type: str, *, increment: int = 1, current_value: int | None = None, bot=None) -> None:
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

async def get_active_challenges(self, challenge_type: str | None = None) -> list:
    now = datetime.datetime.utcnow()
    stmt = select(Challenge).where(Challenge.start_date <= now, Challenge.end_date >= now)
    if challenge_type:
        stmt = stmt.where(Challenge.type == challenge_type)
    result = await self.session.execute(stmt)
    return result.scalars().all()

async def increment_challenge_progress(self, user_id: int, goal_type: str, increment: int = 1, bot=None) -> list:
    completed = []
    challenges = await self.get_active_challenges()
    for challenge in challenges:
        if challenge.goal_type != goal_type:
            continue
        prog = await self.session.get(UserChallengeProgress, {"user_id": user_id, "challenge_id": challenge.id})
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

                           

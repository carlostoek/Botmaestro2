import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import (
    Mission,
    User,
    UserMissionEntry,
    Challenge,
    UserChallengeProgress,
    LorePiece,
    UserLorePiece,
)
from utils.text_utils import sanitize_text
import logging

logger = logging.getLogger(__name__)

# Placeholder structure for future missions
MISSION_PLACEHOLDER: list = []

class MissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        from services.point_service import PointService
        self.point_service = PointService(session)

    async def get_active_missions(self, user_id: int = None, mission_type: str = None) -> list[Mission]:
        """
        Retrieves active missions, optionally filtered by user completion status and type.
        """
        stmt = select(Mission).where(Mission.is_active == True)
        if mission_type:
            stmt = stmt.where(Mission.mission_type == mission_type)
        result = await self.session.execute(stmt)
        missions = [m for m in result.scalars().all() if not m.duration_days or (m.created_at + datetime.timedelta(days=m.duration_days)) > datetime.datetime.utcnow()]

        if user_id: # Filter out completed missions for a specific user based on reset rules
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
        """Return missions of type 'daily' that are active today."""
        return await self.get_active_missions(user_id=user_id, mission_type="daily")

    async def get_mission_by_id(self, mission_id: int) -> Mission | None: # Changed type hint to int
        return await self.session.get(Mission, mission_id)

    async def get_active_mission(
        self, user_id: int, channel_type: str, mission_type: str
    ) -> Mission | None:
        """Return the first active mission matching channel and type not yet completed."""
        missions = await self.get_active_missions(mission_type=mission_type)
        user = await self.session.get(User, user_id)
        if not user:
            return None
        for mission in missions:
            if mission.action_data:
                m_channel = mission.action_data.get("channel_type")
                if m_channel and m_channel != channel_type:
                    continue
            completed, _ = await self.check_mission_completion_status(user, mission)
            if not completed:
                return mission
        return None

    async def check_mission_completion_status(self, user: User, mission: Mission, target_message_id: int = None) -> tuple[bool, str]:
        """
        Checks if a user has completed a mission for the current reset period,
        or if it's a one-time mission already completed.
        Returns (is_completed_for_period, reason_if_completed)
        """
        mission_completion_record = user.missions_completed.get(str(mission.id)) # Use str(mission.id) for dict key
        
        if mission.mission_type == "one_time":
            if mission_completion_record:
                return True, "already_completed"
        elif mission.mission_type == "daily":
            if mission_completion_record:
                last_completed = datetime.datetime.fromisoformat(mission_completion_record)
                if (datetime.datetime.now() - last_completed) < datetime.timedelta(days=1):
                    return True, "daily_limit_reached"
        elif mission.mission_type == "weekly":
            if mission_completion_record:
                last_completed = datetime.datetime.fromisoformat(mission_completion_record)
                if (datetime.datetime.now() - last_completed) < datetime.timedelta(weeks=1):
                    return True, "weekly_limit_reached"
        elif mission.mission_type == "reaction":
            # For reaction missions, check if already completed once
            # If the mission is reaction, it should have action_data with target_message_id
            if mission.action_data and mission.action_data.get("target_message_id") == target_message_id:
                # Check if the specific reaction mission related to this message_id is completed
                # This ensures a user can react to multiple *different* interactive posts
                # but only complete the specific mission linked to *this* post once.
                user_mission_entry_stmt = select(UserMissionEntry).where(
                    UserMissionEntry.user_id == user.id,
                    UserMissionEntry.mission_id == mission.id,
                    UserMissionEntry.completed == True
                )
                existing_entry = (await self.session.execute(user_mission_entry_stmt)).scalar_one_or_none()
                if existing_entry:
                    return True, "already_completed_reaction_for_this_post"
            # If no specific target_message_id is provided, or it doesn't match the mission's action_data
            # then a general check for any completion record for this mission ID
            elif mission_completion_record: # Fallback if action_data not perfectly matched or missing
                return True, "already_completed"
        
        return False, "" # Not completed for current period or not a one-time mission

    async def complete_mission(
        self,
        user_id: int,
        mission_id: int, # Changed type hint to int
        reaction_type: str = None,
        target_message_id: int = None,
        *,
        bot=None,
    ) -> tuple[bool, Mission | None]:
        """
        Marks a mission as completed for a user, adds points, and handles reset logic.
        Returns (True, mission_object) on success, (False, None) on failure.
        """
        user = await self.session.get(User, user_id)
        mission = await self.session.get(Mission, mission_id)

        if not user or not mission or not mission.is_active:
            logger.warning(f"Failed to complete mission: User {user_id} or mission {mission_id} not found or inactive.")
            return False, None

        # Check if already completed for the current period
        is_completed, reason = await self.check_mission_completion_status(user, mission, target_message_id)
        if is_completed:
            logger.info(f"User {user_id} attempted to complete mission {mission_id} but it was already completed ({reason}).")
            return False, None

        # Ensure user has a UserMissionEntry for this mission
        user_mission_entry_stmt = select(UserMissionEntry).where(
            UserMissionEntry.user_id == user_id,
            UserMissionEntry.mission_id == mission.id
        )
        user_mission_entry = (await self.session.execute(user_mission_entry_stmt)).scalar_one_or_none()

        if not user_mission_entry:
            user_mission_entry = UserMissionEntry(user_id=user_id, mission_id=mission.id)
            self.session.add(user_mission_entry)
        
        # Mark as completed
        user_mission_entry.completed = True
        user_mission_entry.completed_at = datetime.datetime.utcnow() # Use UTC for consistency

        # Add mission to user's completed list with timestamp (for reset logic in User model)
        now = datetime.datetime.now().isoformat()
        user.missions_completed[str(mission.id)] = now # Ensure mission.id is stored as string key
        

        # Add points to user. Event multiplier should be handled by PointService or calling context.
        # For simplicity here, we just add the base points.
        # If event multiplier logic is outside this, ensure it's applied before calling add_points.
        # If it's inside PointService, this is fine.
        point_service = self.point_service # assuming point_service is still available in __init__
        if not hasattr(self, 'point_service'): # Fallback if not initialized in __init__
             from services.point_service import PointService
             point_service = PointService(self.session)

        await point_service.add_points(user_id, mission.reward_points, bot=bot)

        # Update last reset timestamps for daily/weekly missions
        if mission.mission_type == "daily":
            user.last_daily_mission_reset = datetime.datetime.now()
        elif mission.mission_type == "weekly":
            user.last_weekly_mission_reset = datetime.datetime.now()

        # Desbloqueo de pistas de lore vinculadas a la misión
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
                        f"User {user_id} unlocked lore piece {unlock_code} via mission {mission_id}"
                    )

        # Ensure JSON field updates are marked for SQLAlchemy
        self.session.add(user) # Mark user as modified

        await self.session.commit()
        await self.session.refresh(user)

        if bot:
            from utils.message_utils import get_mission_completed_message
            from utils.keyboard_utils import get_mission_completed_keyboard

            text = await get_mission_completed_message(mission)
            await bot.send_message(
                user_id,
                text,
                reply_markup=get_mission_completed_keyboard(),
            )

        logger.info(
            f"User {user_id} successfully completed mission {mission_id} (Type: {mission.mission_type}, Message: {target_message_id})."
        )
        return True, mission

    async def create_mission(
        self,
        name: str,
        description: str,
        mission_type: str,
        target_value: int,
        reward_points: int,
        reward_type: str = "points",
        reward_content: str | None = None,
        duration_days: int = 0,
        channel_type: str = "vip",
        *,
        requires_action: bool = False,
        action_data: dict | None = None,
        unlocks_lore_piece_code: str | None = None, # Added this to pass to model
    ) -> Mission:
        new_mission = Mission(
            name=sanitize_text(name),
            description=sanitize_text(description),
            channel_type=channel_type,
            reward_points=reward_points,
            reward_type=reward_type,
            reward_content=reward_content,
            mission_type=mission_type,
            target_value=target_value,
            duration_days=duration_days,
            requires_action=requires_action,
            action_data=action_data,
            is_active=True,
            unlocks_lore_piece_code=unlocks_lore_piece_code, # Pass unlocks_lore_piece_code
        )
        self.session.add(new_mission)
        await self.session.commit()
        await self.session.refresh(new_mission)
        return new_mission

    async def toggle_mission_status(self, mission_id: int, status: bool) -> bool: # Changed type hint to int
        mission = await self.session.get(Mission, mission_id)
        if mission:
            mission.is_active = status
            await self.session.commit()
            return True
        return False

    async def update_mission(self, mission_id: int, **fields) -> Mission | None: # Changed type hint to int
        """Update mission fields and return the updated mission."""
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return None
        for key, value in fields.items():
            if hasattr(mission, key) and value is not None:
                setattr(mission, key, value)
        await self.session.commit()
        await self.session.refresh(mission)
        return mission

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
                    await bot.send_message(
                        user_id,
                        text,
                        reply_markup=get_mission_completed_keyboard(),
                    )
        await self.session.commit()

    async def delete_mission(self, mission_id: int) -> bool: # Changed type hint to int
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

    async def increment_challenge_progress(self, user_id: int, goal_type: str, increment: int = 1, bot=None) -> list[Challenge]:
        """Increment progress for active challenges matching goal_type.
        Returns list of challenges completed in this call."""
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


# services/mission_service.py
import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from database.models import (
    Mission,
    User,
    UserMission,
    UserMissionProgress,
    Challenge,
    UserChallengeProgress,
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

    async def get_active_missions(self, user_id: int = None, mission_type: str = None, category: str = None) -> list[Mission]:
        """
        Retrieves active missions, optionally filtered by user completion status, type, and category.
        """
        stmt = select(Mission).where(Mission.is_active == True)
        
        if mission_type:
            stmt = stmt.where(Mission.type == mission_type)
            
        if category:
            stmt = stmt.where(Mission.category == category)
            
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

    async def get_onboarding_missions(self, user_type: str, user_id: int = None) -> list[Mission]:
        """Get onboarding missions for a specific user type."""
        category = f"{user_type}_onboarding"
        stmt = select(Mission).where(
            Mission.is_active == True,
            Mission.category == category
        ).order_by(Mission.order_priority, Mission.created_at)
        
        result = await self.session.execute(stmt)
        missions = result.scalars().all()
        
        if user_id:
            # Filter out already completed missions
            user = await self.session.get(User, user_id)
            if user:
                filtered_missions = []
                for mission in missions:
                    is_completed, _ = await self.check_mission_completion_status(user, mission)
                    if not is_completed:
                        filtered_missions.append(mission)
                return filtered_missions
        
        return missions

    async def assign_onboarding_missions(self, user_id: int, user_type: str) -> bool:
        """Assign onboarding missions to a user based on their type."""
        user = await self.session.get(User, user_id)
        if not user:
            return False
        
        # Check if onboarding is already complete
        if user_type == "vip" and user.vip_onboarding_complete:
            return False
        elif user_type == "free" and user.free_onboarding_complete:
            return False
        
        # Get onboarding missions for this user type
        onboarding_missions = await self.get_onboarding_missions(user_type)
        
        if not onboarding_missions:
            logger.warning(f"No onboarding missions found for user type: {user_type}")
            return False
        
        # Assign missions to user
        assigned_count = 0
        for mission in onboarding_missions:
            # Check if mission is already assigned
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission.id
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                user_mission = UserMission(
                    user_id=user_id,
                    mission_id=mission.id,
                    progress=0,
                    completed=False
                )
                self.session.add(user_mission)
                assigned_count += 1
        
        if assigned_count > 0:
            await self.session.commit()
            logger.info(f"Assigned {assigned_count} onboarding missions to user {user_id} (type: {user_type})")
        
        return assigned_count > 0

    async def check_onboarding_completion(self, user_id: int, user_type: str) -> bool:
        """Check if user has completed all onboarding missions for their type."""
        onboarding_missions = await self.get_onboarding_missions(user_type)
        
        if not onboarding_missions:
            return True  # No onboarding missions means onboarding is complete
        
        # Check if all onboarding missions are completed
        for mission in onboarding_missions:
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission.id,
                UserMission.completed == True
            )
            result = await self.session.execute(stmt)
            completed_mission = result.scalar_one_or_none()
            
            if not completed_mission:
                return False  # Found an incomplete mission
        
        return True  # All missions completed

    async def mark_onboarding_complete(self, user_id: int, user_type: str) -> bool:
        """Mark onboarding as complete for a user."""
        user = await self.session.get(User, user_id)
        if not user:
            return False
        
        if user_type == "vip":
            user.vip_onboarding_complete = True
        elif user_type == "free":
            user.free_onboarding_complete = True
        else:
            return False
        
        await self.session.commit()
        logger.info(f"Marked {user_type} onboarding complete for user {user_id}")
        return True

    async def get_mission_by_id(self, mission_id: str) -> Mission | None:
        return await self.session.get(Mission, mission_id)

    async def check_mission_completion_status(self, user: User, mission: Mission, target_message_id: int = None) -> tuple[bool, str]:
        """
        Checks if a user has completed a mission for the current reset period,
        or if it's a one-time mission already completed.
        Returns (is_completed_for_period, reason_if_completed)
        """
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
            # For reaction missions, check if the specific reaction for that message_id is recorded
            if mission.action_data and mission.action_data.get('target_message_id') == target_message_id:
                if user.channel_reactions and str(target_message_id) in user.channel_reactions:
                    return True, "already_reacted_to_this_message"
            elif mission_completion_record: # If it's a generic reaction mission, check one-time completion
                return True, "already_completed"
        
        return False, "" # Not completed for current period or not a one-time mission

    async def complete_mission(
        self,
        user_id: int,
        mission_id: str,
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

        # Add mission to user's completed list with timestamp
        now = datetime.datetime.now().isoformat()
        user.missions_completed[mission.id] = now
        
        # Specific handling for reaction missions: record the message_id for which the reaction was given
        if mission.type == "reaction" and mission.requires_action and target_message_id:
            if not user.channel_reactions:
                user.channel_reactions = {}
            user.channel_reactions[str(target_message_id)] = now  # Record the reaction for this specific message

        # Update UserMission record if it exists
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()
        
        if user_mission:
            user_mission.completed = True
            user_mission.completed_at = datetime.datetime.now()
            user_mission.progress = mission.target_value

        # Add points to user
        point_service = self.point_service
        if not hasattr(self, 'point_service'):
             from services.point_service import PointService
             point_service = PointService(self.session)

        await point_service.add_points(user_id, mission.reward_points, bot=bot)

        # Update last reset timestamps for daily/weekly missions
        if mission.type == "daily":
            user.last_daily_mission_reset = datetime.datetime.now()
        elif mission.type == "weekly":
            user.last_weekly_mission_reset = datetime.datetime.now()
        
        # Ensure JSON field updates are marked for SQLAlchemy
        self.session.add(user) # Mark user as modified

        await self.session.commit()
        await self.session.refresh(user)

        # Check if onboarding is complete after this mission
        if mission.category in ["vip_onboarding", "free_onboarding"]:
            user_type = mission.category.split("_")[0]  # Extract 'vip' or 'free'
            if await self.check_onboarding_completion(user_id, user_type):
                await self.mark_onboarding_complete(user_id, user_type)
                
                # Send completion message
                if bot:
                    completion_message = (
                        f"🎉 **¡Onboarding Completado!**\n\n"
                        f"Has completado todas las misiones de introducción para usuarios {user_type.upper()}.\n"
                        f"¡Ahora puedes explorar todas las funciones disponibles!"
                    )
                    try:
                        await bot.send_message(user_id, completion_message)
                    except Exception as e:
                        logger.warning(f"Could not send onboarding completion message to {user_id}: {e}")

        if bot:
            from utils.message_utils import get_mission_completed_message
            from utils.keyboard_utils import get_mission_completed_keyboard

            text = await get_mission_completed_message(mission)
            try:
                await bot.send_message(
                    user_id,
                    text,
                    reply_markup=get_mission_completed_keyboard(),
                )
            except Exception as e:
                logger.warning(f"Could not send mission completion message to {user_id}: {e}")

        logger.info(
            f"User {user_id} successfully completed mission {mission_id} (Type: {mission.type}, Message: {target_message_id})."
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
        category: str = "standard",
        user_type: str = "all",
        order_priority: int = 0,
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
            is_active=True,
            category=category,
            user_type=user_type,
            order_priority=order_priority,
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
            stmt = select(UserMissionProgress).where(
                UserMissionProgress.user_id == user_id,
                UserMissionProgress.mission_id == mission.id,
            )
            result = await self.session.execute(stmt)
            record = result.scalar_one_or_none()
            if not record:
                record = UserMissionProgress(user_id=user_id, mission_id=mission.id)
                self.session.add(record)
            if record.completed:
                continue
            if mission_type == "login_streak" and current_value is not None:
                progress = current_value
                record.progress_value = progress
            else:
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
                    try:
                        await bot.send_message(
                            user_id,
                            text,
                            reply_markup=get_mission_completed_keyboard(),
                        )
                    except Exception as e:
                        logger.warning(f"Could not send mission completion message to {user_id}: {e}")
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
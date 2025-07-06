# services/mission_service.py
import datetime
import random
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

# Importaciones corregidas
from database.models import (
    Mission, User, UserMissionEntry, Item, UserItem, Hint, UserHint, 
    Combination, UserCombination, Level, UserLevel, UserDailyGift, 
    UserReferral, Referral
)
from database.narrative_models import LorePiece, UserLorePiece
from utils.text_utils import sanitize_text
from services.point_service import PointService

logger = logging.getLogger(__name__)

# Placeholder structure for future missions
MISSION_PLACEHOLDER: list = []

class MissionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)

    async def get_active_missions(self, user_id: int = None, mission_type: str = None) -> list[Mission]:
        """
        Retrieves active missions, optionally filtered by user completion status and type.
        """
        stmt = select(Mission).where(Mission.is_active == True)
        if mission_type:
            stmt = stmt.where(Mission.type == mission_type)
        result = await self.session.execute(stmt)
        missions = [m for m in result.scalars().all() if not m.duration_days or 
                   (m.created_at + datetime.timedelta(days=m.duration_days)) > datetime.datetime.utcnow()]

        if user_id:  # Filter out completed missions for a specific user based on reset rules
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
            if mission_completion_record:
                return True, "already_completed"
        
        return False, ""  # Not completed for current period or not a one-time mission

    # Resto de las funciones...


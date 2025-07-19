# mybot/database/models/gamification.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    Boolean,
    JSON,
    Text,
    ForeignKey,
    Float,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from database.base import Base

class Reward(Base):
    """Rewards unlocked by reaching a number of points."""

    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    required_points = Column(Integer, nullable=False)
    reward_type = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class UserReward(Base):
    """Stores claimed rewards per user."""

    __tablename__ = "user_rewards"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    reward_id = Column(Integer, ForeignKey("rewards.id"), primary_key=True)
    claimed_at = Column(DateTime, default=func.now())


class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    condition_type = Column(String, nullable=False)
    condition_value = Column(Integer, nullable=False)
    reward_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    achievement_id = Column(String, ForeignKey("achievements.id"), primary_key=True)
    unlocked_at = Column(DateTime, default=func.now())
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uix_user_achievements"),)


class Mission(Base):
    __tablename__ = "missions"
    id = Column(String, primary_key=True, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    reward_points = Column(Integer, default=0)
    type = Column(String, default="one_time")
    target_value = Column(Integer, default=1)
    duration_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False)
    action_data = Column(JSON, nullable=True)
    unlocks_lore_piece_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())


class UserMissionEntry(Base):
    """Consolidated mission progress and completion per user."""

    __tablename__ = "user_mission_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    mission_id = Column(String, ForeignKey("missions.id"))
    progress_value = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "mission_id", name="uix_user_mission_entry"),)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    multiplier = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class Raffle(Base):
    __tablename__ = "raffles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    prize = Column(String, nullable=True)
    winner_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)


class RaffleEntry(Base):
    __tablename__ = "raffle_entries"
    raffle_id = Column(Integer, ForeignKey("raffles.id"), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    condition_type = Column(String, nullable=False)
    condition_value = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    awarded_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uix_user_badges"),)


class Level(Base):
    __tablename__ = "levels"

    level_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    min_points = Column(Integer, nullable=False)
    reward = Column(String, nullable=True)
    unlocks_lore_piece_code = Column(String, nullable=True)


class UserStats(Base):
    """Activity and progression stats per user (points stored in User)."""

    __tablename__ = "user_stats"
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    last_activity_at = Column(DateTime, default=func.now())
    last_checkin_at = Column(DateTime, nullable=True)
    last_daily_gift_at = Column(DateTime, nullable=True)
    last_notified_points = Column(Float, default=0)
    messages_sent = Column(Integer, default=0)
    checkin_streak = Column(Integer, default=0)
    last_roulette_at = Column(DateTime, nullable=True)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    goal_type = Column(String, nullable=False)
    goal_value = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)


class UserChallengeProgress(Base):
    __tablename__ = "user_challenge_progress"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), primary_key=True)
    current_value = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)


class MiniGamePlay(Base):
    """Record usage of minigames such as roulette or challenges."""

    __tablename__ = "minigame_play"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    game_type = Column(String, nullable=False)
    used_at = Column(DateTime, default=func.now())
    is_free = Column(Boolean, default=False)
    cost_points = Column(Float, default=0)

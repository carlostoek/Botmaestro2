"""Modelos para el sistema de gamificación."""

import enum
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Float,
    DateTime, Boolean, Index, UniqueConstraint, Enum, ARRAY
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base, TimestampMixin

class MissionTypeEnum(str, enum.Enum):
    """Tipos de misiones disponibles."""
    
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE_TIME"
    EVENT = "EVENT"
    STORY = "STORY"

class MissionStatusEnum(str, enum.Enum):
    """Estados posibles de las misiones."""
    
    AVAILABLE = "AVAILABLE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

class UserPoints(Base, TimestampMixin):
    """Puntos (besitos) de los usuarios."""
    
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    current_points = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    
    # Estadísticas de puntos
    points_from_messages = Column(Float, default=0.0)
    points_from_reactions = Column(Float, default=0.0)
    points_from_missions = Column(Float, default=0.0)
    points_from_dailygift = Column(Float, default=0.0)
    points_from_minigames = Column(Float, default=0.0)
    points_from_narrative = Column(Float, default=0.0)
    
    # Multiplicadores
    active_multipliers = Column(JSON, default={})
    
    # Historial
    last_points_update = Column(DateTime(timezone=True), server_default=func.now())
    points_history = Column(JSON, default=[])
    
    # Relaciones
    user = relationship("User", back_populates="points")
    
    def __repr__(self) -> str:
        """Representación de texto de los puntos del usuario."""
        return f"<UserPoints(user_id={self.user_id}, current={self.current_points}, total_earned={self.total_earned})>"

class Achievement(Base, TimestampMixin):
    """Logros disponibles en el sistema."""
    
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    
    # Criterios y recompensas
    criteria = Column(JSON, nullable=False)
    points_reward = Column(Float, default=0.0)
    item_rewards = Column(JSON, default={})
    
    # Metadata
    category = Column(String(50), nullable=False)
    difficulty = Column(Integer, default=1)
    is_hidden = Column(Boolean, default=False)
    is_milestone = Column(Boolean, default=False)
    
    # Relaciones
    user_achievements = relationship(
        "UserAchievement", 
        back_populates="achievement",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación de texto del logro."""
        return f"<Achievement(key='{self.key}', name='{self.name}')>"

class UserAchievement(Base, TimestampMixin):
    """Logros obtenidos por los usuarios."""
    
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    
    # Estado del logro
    is_completed = Column(Boolean, default=False)
    progress = Column(Float, default=0.0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Datos adicionales
    completion_data = Column(JSON, default={})
    
    # Relaciones
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uix_user_achievement"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto del logro del usuario."""
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id}, completed={self.is_completed})>"

class Mission(Base, TimestampMixin):
    """Misiones disponibles en el sistema."""
    
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    
    # Tipo y categoría
    mission_type = Column(Enum(MissionTypeEnum), nullable=False)
    category = Column(String(50), nullable=False)
    
    # Requisitos
    requirements = Column(JSON, default={})
    level_required = Column(Integer, default=1)
    is_vip_only = Column(Boolean, default=False)
    
    # Mecánica
    objectives = Column(JSON, nullable=False)
    time_limit_hours = Column(Integer, nullable=True)
    
    # Recompensas
    points_reward = Column(Float, default=0.0)
    item_rewards = Column(JSON, default={})
    achievement_key = Column(String(50), nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    user_missions = relationship(
        "UserMission", 
        back_populates="mission",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación de texto de la misión."""
        return f"<Mission(key='{self.key}', type={self.mission_type}, title='{self.title}')>"

class UserMission(Base, TimestampMixin):
    """Misiones asignadas a usuarios."""
    
    __tablename__ = "user_missions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    
    # Estado
    status = Column(Enum(MissionStatusEnum), default=MissionStatusEnum.AVAILABLE)
    progress = Column(JSON, default={})
    progress_percentage = Column(Float, default=0.0)
    
    # Fechas
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Recompensas
    reward_claimed = Column(Boolean, default=False)
    reward_claimed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    user = relationship("User", back_populates="missions")
    mission = relationship("Mission", back_populates="user_missions")
    
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", name="uix_user_mission"),
        Index("idx_user_mission_status", "user_id", "status"),
        Index("idx_user_mission_expires", "user_id", "expires_at"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto de la misión del usuario."""
        return f"<UserMission(user_id={self.user_id}, mission_id={self.mission_id}, status={self.status})>"
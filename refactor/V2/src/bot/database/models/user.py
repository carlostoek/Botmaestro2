"""Modelo de usuario."""

from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """Modelo para almacenar información de usuarios."""
    
    __tablename__ = "users"
    
    # Campos principales
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), nullable=True)
    
    # Configuración y estado
    is_admin = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    vip_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Progreso y personalización
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    user_settings = Column(JSON, default={})
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    emotional_system_version = Column(Integer, default=2)
    
    # Estadísticas
    messages_count = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)
    
    # Relaciones
    character_relationships = relationship(
        "UserCharacterRelationship", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    narrative_states = relationship(
        "UserNarrativeState",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    achievements = relationship(
        "UserAchievement",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    missions = relationship(
        "UserMission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    points = relationship(
        "UserPoints",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación de texto del usuario."""
        return f"<User(id={self.id}, username={self.username}, is_vip={self.is_vip})>"
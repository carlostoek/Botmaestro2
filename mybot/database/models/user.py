from sqlalchemy import Column, BigInteger, String, Float, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declared_attr
from database.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, unique=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    points = Column(Float, default=0)
    level = Column(Integer, default=1)
    achievements = Column(JSON, default={})
    missions_completed = Column(JSON, default={})
    last_daily_mission_reset = Column(DateTime, default=func.now())
    last_weekly_mission_reset = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    role = Column(String, default="free")
    vip_expires_at = Column(DateTime, nullable=True)
    last_reminder_sent_at = Column(DateTime, nullable=True)
    menu_state = Column(String, default="root")

    # SOLUCIÓN: Usar declared_attr para resolver dependencia circular
    @declared_attr
    def narrative_state(cls):
        # Importación local para evitar dependencia circular
        from database.models.user_narrative_state import UserNarrativeState
        return relationship(
            UserNarrativeState,
            back_populates="user",
            uselist=False,
            lazy="selectin",
            cascade="all, delete-orphan"
        )
from __future__ import annotations

from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
import datetime

from mybot.database.models import Base


class UserMissionEntry(AsyncAttrs, Base):
    """Track mission progress and completion per user."""

    __tablename__ = "user_mission_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", name="uix_user_mission_entry"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    mission_id: Mapped[int] = mapped_column(Integer, ForeignKey("missions.id"))
    progress_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

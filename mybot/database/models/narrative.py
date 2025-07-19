# mybot/database/models/narrative.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    BigInteger,
    JSON,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base

class StoryFragment(Base):
    """
    Represents a modular block of the story.
    Each fragment is a step in the narrative journey.
    """
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)
    character = Column(String, default='Lucien')
    auto_next_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=True)
    level = Column(Integer, default=1, comment="Narrative level, e.g., 1-3 for free, 4-6 for VIP")
    min_besitos = Column(Integer, default=0, comment="Minimum 'besitos' (points) required to view")
    required_role = Column(String, nullable=True, comment="e.g., 'vip' to restrict access")
    reward_besitos = Column(Integer, default=0, comment="Besitos awarded upon reaching this fragment")
    unlocks_achievement_id = Column(String, ForeignKey('achievements.id'), nullable=True)
    choices = relationship("NarrativeChoice", back_populates="source_fragment", foreign_keys='NarrativeChoice.source_fragment_id')


class NarrativeChoice(Base):
    """
    Represents a decision a user can make, linking one StoryFragment to another.
    """
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=False)
    text = Column(String, nullable=False)
    source_fragment = relationship("StoryFragment", back_populates="choices", foreign_keys=[source_fragment_id])


class Hint(Base):
    """
    Represents a hint that can be combined to reveal a clue.
    """
    __tablename__ = 'hints'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class UserHint(Base):
    """
    Represents a hint owned by a user.
    """
    __tablename__ = 'user_hints'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    hint_id = Column(Integer, ForeignKey('hints.id'), nullable=False)
    quantity = Column(Integer, default=1)

class Clue(Base):
    """
    Represents a clue that is revealed by combining hints.
    """
    __tablename__ = 'clues'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class HintCombination(Base):
    """
    Represents a combination of hints that reveals a clue.
    """
    __tablename__ = 'hint_combinations'
    id = Column(Integer, primary_key=True)
    clue_id = Column(Integer, ForeignKey('clues.id'), nullable=False)
    hint1_id = Column(Integer, ForeignKey('hints.id'), nullable=False)
    hint2_id = Column(Integer, ForeignKey('hints.id'), nullable=False)
    hint3_id = Column(Integer, ForeignKey('hints.id'), nullable=True)
    hint4_id = Column(Integer, ForeignKey('hints.id'), nullable=True)
    hint5_id = Column(Integer, ForeignKey('hints.id'), nullable=True)
    is_active = Column(Boolean, default=True)

class UserClue(Base):
    """
    Represents a clue owned by a user.
    """
    __tablename__ = 'user_clues'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    clue_id = Column(Integer, ForeignKey('clues.id'), nullable=False)
    quantity = Column(Integer, default=1)

class LorePiece(Base):
    """Discrete lore or clue piece that users can unlock."""

    __tablename__ = "lore_pieces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    is_main_story = Column(Boolean, default=False)
    unlock_condition_type = Column(String, nullable=True)
    unlock_condition_value = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class UserLorePiece(Base):
    """Mapping of unlocked lore pieces per user."""

    __tablename__ = "user_lore_pieces"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), primary_key=True)
    unlocked_at = Column(DateTime, default=func.now())
    context = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "lore_piece_id", name="uix_user_lore_pieces"),
    )

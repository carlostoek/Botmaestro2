# mybot/database/narrative_models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    JSON,
    DateTime,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class LorePiece(Base):
    __tablename__ = "narrative_lore_pieces"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)
    piece_type = Column(String) # diary_page, photo, object, letter, memory
    category = Column(String) # diana_past, world_building, diana_present
    found_in_level = Column(Integer)
    rarity = Column(String) # common, rare, legendary
    diana_comment_on_find = Column(Text, nullable=True)
    diana_comment_if_asked = Column(Text, nullable=True)
    emotional_weight = Column(Integer, default=0)
    combines_with = Column(JSON, nullable=True)
    combination_result = Column(String, nullable=True)
    changes_diana_behavior = Column(Boolean, default=False)
    behavior_change_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class UnsentLetter(Base):
    __tablename__ = "narrative_unsent_letters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_event = Column(String)
    letter_date = Column(String)
    emotional_state = Column(String)
    subject = Column(String)
    content = Column(Text)
    min_trust_required = Column(Float)
    min_level_required = Column(Integer)
    discovery_chance = Column(Float)
    gives_points = Column(Integer)
    trust_increase = Column(Float)
    unlocks_special_dialogue = Column(Boolean, default=False)
    required_relationship_stage = Column(String, nullable=True)
    specific_archetype_bonus = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

class NarrativeEvent(Base):
    __tablename__ = "narrative_events"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(String) # lunar_phase, seasonal, relationship_milestone
    trigger_conditions = Column(JSON)
    announcement_message = Column(Text)
    diana_special_mood = Column(String)
    special_dialogues = Column(JSON)
    exclusive_missions = Column(JSON)
    duration_hours = Column(Integer)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)
    min_trust_required = Column(Float, nullable=True)
    exclusive_lore_pieces = Column(JSON, nullable=True)
    min_level_required = Column(Integer, nullable=True)
    vip_exclusive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
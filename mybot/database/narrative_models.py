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
    ForeignKey,
    BigInteger,
    Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

# Enums para el sistema narrativo
class RelationshipStage(PyEnum):
    STRANGER = "stranger"
    CURIOUS = "curious"
    ACQUAINTANCE = "acquaintance"
    TRUSTED = "trusted"
    CONFIDANT = "confidant"
    INTIMATE = "intimate"

class EmotionalState(PyEnum):
    NEUTRAL = "neutral"
    INTRIGUED = "intrigued"
    PLAYFUL = "playful"
    VULNERABLE = "vulnerable"
    DEFENSIVE = "defensive"
    WARM = "warm"
    MYSTERIOUS = "mysterious"
    INTENSE = "intense"
    NOSTALGIC = "nostalgic"
    HOPEFUL = "hopeful"

class UserArchetype(PyEnum):
    UNKNOWN = "unknown"
    ROMANTIC = "romantic"
    DIRECT = "direct"
    ANALYTICAL = "analytical"
    EXPLORER = "explorer"
    PATIENT = "patient"
    PERSISTENT = "persistent"

Base = declarative_base()

class NarrativeState(Base):
    """Estado narrativo del usuario con Diana"""
    __tablename__ = "narrative_states"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Nivel narrativo actual (0-6)
    narrative_level = Column(Integer, default=0)
    current_chapter = Column(String, default="prologue")
    
    # Métricas de relación
    trust_level = Column(Float, default=0.0)  # 0.0 a 1.0
    vulnerability_shown = Column(Float, default=0.0)  # 0.0 a 1.0
    mystery_remaining = Column(Float, default=1.0)  # 1.0 a 0.0
    emotional_connection = Column(Float, default=0.0)  # 0.0 a 1.0
    
    # Contadores de interacción
    total_interactions = Column(Integer, default=0)
    meaningful_conversations = Column(Integer, default=0)
    secrets_revealed = Column(Integer, default=0)
    vulnerable_moments = Column(Integer, default=0)
    
    # Estados y flags
    relationship_stage = Column(Enum(RelationshipStage), default=RelationshipStage.STRANGER)
    current_emotional_state = Column(Enum(EmotionalState), default=EmotionalState.NEUTRAL)
    user_archetype = Column(Enum(UserArchetype), default=UserArchetype.UNKNOWN)
    archetype_confidence = Column(Float, default=0.0)
    
    # Progreso de misiones narrativas
    active_narrative_missions = Column(JSON, default=list)
    completed_narrative_missions = Column(JSON, default=list)
    
    # Eventos y triggers
    triggered_events = Column(JSON, default=list)
    pending_revelations = Column(JSON, default=list)
    
    # Timestamps importantes
    first_interaction = Column(DateTime, default=datetime.utcnow)
    last_meaningful_interaction = Column(DateTime)
    last_vulnerability_shown = Column(DateTime)
    relationship_milestones = Column(JSON, default=dict)  # {"milestone": timestamp}
    
    # Datos de comportamiento
    interaction_patterns = Column(JSON, default=dict)
    response_style_metrics = Column(JSON, default=dict)
    topic_preferences = Column(JSON, default=list)
    
    # Relaciones
    user = relationship("User", back_populates="narrative_state", uselist=False)
    dialogue_history = relationship("DialogueHistory", back_populates="narrative_state")
    
    def __repr__(self):
        return f"<NarrativeState(user_id={self.user_id}, level={self.narrative_level}, trust={self.trust_level})>"

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

class UserLorePiece(Base):
    """Relación entre usuarios y las piezas de lore que han encontrado"""
    __tablename__ = "user_lore_pieces"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey("narrative_lore_pieces.id"), nullable=False)
    
    # Cuándo y cómo la encontró
    found_at = Column(DateTime, default=datetime.utcnow)
    found_through = Column(String)  # "mission", "exploration", "gift", "combination"
    
    # Interacción con la pieza
    times_viewed = Column(Integer, default=1)
    last_viewed = Column(DateTime, default=datetime.utcnow)
    has_asked_diana = Column(Boolean, default=False)
    diana_revealed_extra = Column(Boolean, default=False)
    
    # Si la ha usado para combinar
    used_in_combination = Column(Boolean, default=False)
    combination_result_id = Column(Integer, ForeignKey("narrative_lore_pieces.id"))
    
    # Notas o reflexiones del usuario
    user_notes = Column(Text)
    
    # Relaciones
    user = relationship("User", backref="found_lore_pieces")
    lore_piece = relationship("LorePiece", foreign_keys=[lore_piece_id])
    combination_result = relationship("LorePiece", foreign_keys=[combination_result_id])
    
    def __repr__(self):
        return f"<UserLorePiece(user_id={self.user_id}, piece={self.lore_piece_id})>"

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

class DialogueHistory(Base):
    __tablename__ = "narrative_dialogue_history"
    id = Column(Integer, primary_key=True)
    narrative_state_id = Column(Integer, ForeignKey('narrative_states.id'))
    narrative_state = relationship("NarrativeState", back_populates="dialogue_history")
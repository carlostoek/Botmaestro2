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
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from database.setup import Base

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
    HOPEFUL = "hoepful"

class UserArchetype(PyEnum):
    UNKNOWN = "unknown"
    ROMANTIC = "romantic"
    DIRECT = "direct"
    ANALYTICAL = "analytical"
    EXPLORER = "explorer"
    PATIENT = "patient"
    PERSISTENT = "persistent"

class NarrativeState(Base):
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
    
    def __repr__(self):
        return f"<NarrativeState(user_id={self.user_id}, level={self.narrative_level}, trust={self.trust_level})>"

class LorePiece(Base):
    __tablename__ = "lore_pieces"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserLorePiece(Base):
    __tablename__ = "user_lore_pieces"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=False)
    found_at = Column(DateTime, default=datetime.utcnow)
    user_notes = Column(Text)
    user = relationship("User ", backref="found_lore_pieces")
    lore_piece = relationship("LorePiece", foreign_keys=[lore_piece_id])
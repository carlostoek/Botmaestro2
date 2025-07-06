# mybot/database/narrative_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, BigInteger, Enum
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
    HOPEFUL = "hopeful"

class UserArchetype(PyEnum):
    UNKNOWN = "unknown"
    ROMANTIC = "romantic"
    DIRECT = "direct"
    ANALYTICAL = "analytical"
    EXPLORER = "explorer"
    PATIENT = "patient"
    PERSISTENT = "persistent"

# Modelo principal de estado narrativo
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

    # Timestamps importantes
    first_interaction = Column(DateTime, default=datetime.utcnow)
    last_meaningful_interaction = Column(DateTime)
    last_vulnerability_shown = Column(DateTime)

    # Relaciones
    user = relationship("User", back_populates="narrative_state", uselist=False)

# Piezas de lore
class LorePiece(Base):
    """Piezas de historia/lore que los usuarios pueden descubrir"""
    __tablename__ = "lore_pieces"

    id = Column(Integer, primary_key=True)
    code_name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    piece_type = Column(String, nullable=False)  # "diary", "memory", "artifact", "letter"

    # Condiciones de desbloqueo
    required_level = Column(Integer, default=0)
    required_trust = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

class UserLorePiece(Base):
    """Relación entre usuarios y las piezas de lore que han encontrado"""
    __tablename__ = "user_lore_pieces"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=False)

    found_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", backref="found_lore_pieces")
    lore_piece = relationship("LorePiece")


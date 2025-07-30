"""Modelos para el sistema emocional de personajes."""

import enum
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Float,
    DateTime, Boolean, Index, UniqueConstraint, Enum, ARRAY
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base, TimestampMixin

class RelationshipStatusEnum(str, enum.Enum):
    """Estados posibles de relación entre usuario y personaje."""
    
    INITIAL = "initial"
    ACQUAINTANCE = "acquaintance" 
    FRIENDLY = "friendly"
    CLOSE = "close"
    INTIMATE = "intimate"
    STRAINED = "strained"
    REPAIRED = "repaired"
    DISTANT = "distant"
    COMPLEX = "complex"

class CharacterEmotionalProfile(Base, TimestampMixin):
    """Perfiles base para personajes en el sistema."""
    
    __tablename__ = "character_emotional_profiles"
    
    id = Column(Integer, primary_key=True)
    character_name = Column(String(50), nullable=False, unique=True)
    
    # Valores emocionales base (0-100)
    base_joy = Column(Float, default=50.0)
    base_trust = Column(Float, default=30.0)
    base_fear = Column(Float, default=20.0)
    base_sadness = Column(Float, default=15.0)
    base_anger = Column(Float, default=10.0)
    base_surprise = Column(Float, default=25.0)
    base_anticipation = Column(Float, default=40.0)
    base_disgust = Column(Float, default=5.0)
    
    # Rasgos de personalidad del personaje
    personality_traits = Column(JSON, default={})
    
    # Relaciones
    relationships = relationship(
        "UserCharacterRelationship", 
        back_populates="character",
        cascade="all, delete-orphan"
    )
    
    emotional_states = relationship(
        "UserCharacterEmotionalState", 
        back_populates="character",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación de texto del perfil emocional."""
        return f"<CharacterEmotionalProfile(id={self.id}, name={self.character_name})>"

class UserCharacterRelationship(Base, TimestampMixin):
    """Relaciones entre usuarios y personajes."""
    
    __tablename__ = "user_character_relationships"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_emotional_profiles.id", ondelete="CASCADE"), nullable=False)
    
    relationship_status = Column(Enum(RelationshipStatusEnum), default=RelationshipStatusEnum.INITIAL)
    relationship_level = Column(Integer, default=1)
    trust_level = Column(Float, default=0.0)
    familiarity = Column(Float, default=0.0)
    rapport = Column(Float, default=0.0)
    
    interaction_count = Column(Integer, default=0)
    first_interaction_at = Column(DateTime(timezone=True), server_default=func.now())
    last_interaction_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="character_relationships")
    character = relationship("CharacterEmotionalProfile", back_populates="relationships")
    
    emotional_state = relationship(
        "UserCharacterEmotionalState", 
        back_populates="relationship",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    emotional_memories = relationship(
        "EmotionalMemory",
        back_populates="relationship",
        cascade="all, delete-orphan"
    )
    
    personality_adaptation = relationship(
        "PersonalityAdaptation",
        back_populates="relationship",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "character_id", name="uix_user_character_relationship"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto de la relación."""
        return f"<UserCharacterRelationship(user_id={self.user_id}, character_id={self.character_id}, status={self.relationship_status})>"

class UserCharacterEmotionalState(Base, TimestampMixin):
    """Estado emocional actual de un personaje hacia un usuario."""
    
    __tablename__ = "user_character_emotional_states"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_emotional_profiles.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("user_character_relationships.id", ondelete="CASCADE"), nullable=False)
    
    # Valores emocionales (0-100)
    joy = Column(Float, default=50.0)
    trust = Column(Float, default=30.0)
    fear = Column(Float, default=20.0)
    sadness = Column(Float, default=15.0)
    anger = Column(Float, default=10.0)
    surprise = Column(Float, default=25.0)
    anticipation = Column(Float, default=40.0)
    disgust = Column(Float, default=5.0)
    
    dominant_emotion = Column(String(20), default="neutral")
    
    # Relaciones
    relationship = relationship(
        "UserCharacterRelationship", 
        back_populates="emotional_state",
        foreign_keys=[relationship_id]
    )
    
    character = relationship(
        "CharacterEmotionalProfile", 
        back_populates="emotional_states"
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "character_id", name="uix_user_character_emotional_state"),
        Index("idx_user_character_emotional_dominant", "user_id", "character_id", "dominant_emotion"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto del estado emocional."""
        return f"<UserCharacterEmotionalState(user_id={self.user_id}, character_id={self.character_id}, dominant={self.dominant_emotion})>"

class EmotionalMemory(Base, TimestampMixin):
    """Memorias emocionales de personajes sobre interacciones con usuarios."""
    
    __tablename__ = "emotional_memories"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_emotional_profiles.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("user_character_relationships.id", ondelete="CASCADE"), nullable=False)
    
    memory_type = Column(String(50), nullable=False)
    summary = Column(String(255), nullable=False)
    details = Column(Text)
    emotional_context = Column(JSON, default={})
    related_interaction_ids = Column(ARRAY(Integer), default=[])
    
    importance_score = Column(Float, default=1.0)
    last_recalled_at = Column(DateTime(timezone=True), nullable=True)
    recall_count = Column(Integer, default=0)
    is_forgotten = Column(Boolean, default=False)
    
    # Relaciones
    relationship = relationship(
        "UserCharacterRelationship", 
        back_populates="emotional_memories",
        foreign_keys=[relationship_id]
    )
    
    __table_args__ = (
        Index("idx_emotional_memories_user_char", "user_id", "character_id"),
        Index("idx_emotional_memories_importance", "user_id", "character_id", "importance_score", "is_forgotten"),
        Index("idx_emotional_memories_last_recalled", "user_id", "character_id", "last_recalled_at"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto de la memoria emocional."""
        return f"<EmotionalMemory(id={self.id}, user_id={self.user_id}, summary='{self.summary[:20]}...')>"

class PersonalityAdaptation(Base, TimestampMixin):
    """Adaptaciones de personalidad de personajes basadas en interacciones con usuarios."""
    
    __tablename__ = "personality_adaptations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_emotional_profiles.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("user_character_relationships.id", ondelete="CASCADE"), nullable=False)
    
    # Adaptaciones de personalidad (0-1)
    warmth = Column(Float, default=0.5)
    formality = Column(Float, default=0.5)
    humor = Column(Float, default=0.5)
    directness = Column(Float, default=0.5)
    assertiveness = Column(Float, default=0.5)
    curiosity = Column(Float, default=0.5)
    emotional_expressiveness = Column(Float, default=0.5)
    
    # Preferencias de comunicación
    communication_preferences = Column(JSON, default={})
    topic_preferences = Column(JSON, default={})
    taboo_topics = Column(ARRAY(String), default=[])
    
    # Confianza en las adaptaciones
    confidence_score = Column(Float, default=0.5)
    
    # Relaciones
    relationship = relationship(
        "UserCharacterRelationship", 
        back_populates="personality_adaptation",
        foreign_keys=[relationship_id]
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", "character_id", name="uix_personality_adaptation"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto de la adaptación de personalidad."""
        return f"<PersonalityAdaptation(user_id={self.user_id}, character_id={self.character_id}, confidence={self.confidence_score})>"
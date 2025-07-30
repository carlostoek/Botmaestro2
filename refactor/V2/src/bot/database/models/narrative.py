"""Modelos para el sistema narrativo."""

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, BigInteger, JSON, Float,
    Boolean, Index, UniqueConstraint, ARRAY
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin

class StoryFragment(Base, TimestampMixin):
    """Fragmentos de historia para el sistema narrativo."""
    
    __tablename__ = "story_fragments"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    character = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    
    # Metadatos del fragmento
    tags = Column(ARRAY(String), default=[])
    level_required = Column(Integer, default=1)
    is_vip_only = Column(Boolean, default=False)
    
    # Recompensas
    reward_besitos = Column(Float, default=0.0)
    reward_items = Column(JSON, default={})
    unlock_achievements = Column(ARRAY(String), default=[])
    
    # Relaciones
    choices = relationship(
        "NarrativeChoice", 
        back_populates="fragment",
        cascade="all, delete-orphan"
    )
    
    user_states = relationship(
        "UserNarrativeState",
        back_populates="current_fragment",
        foreign_keys="[UserNarrativeState.current_fragment_key]"
    )
    
    emotional_triggers = relationship(
        "EmotionalNarrativeTrigger",
        back_populates="fragment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación de texto del fragmento de historia."""
        return f"<StoryFragment(key='{self.key}', character='{self.character}')>"

class NarrativeChoice(Base, TimestampMixin):
    """Opciones de decisión en fragmentos narrativos."""
    
    __tablename__ = "narrative_choices"
    
    id = Column(Integer, primary_key=True)
    fragment_key = Column(String(50), ForeignKey("story_fragments.key", ondelete="CASCADE"), nullable=False)
    text = Column(String(255), nullable=False)
    target_fragment_key = Column(String(50), nullable=False)
    
    # Condiciones
    required_items = Column(JSON, default={})
    required_relationship_level = Column(Integer, default=0)
    required_points = Column(Float, default=0.0)
    
    # Efectos
    points_change = Column(Float, default=0.0)
    relationship_change = Column(Float, default=0.0)
    emotional_impacts = Column(JSON, default={})
    
    # Relaciones
    fragment = relationship("StoryFragment", back_populates="choices")
    
    def __repr__(self) -> str:
        """Representación de texto de la opción narrativa."""
        return f"<NarrativeChoice(id={self.id}, text='{self.text[:20]}...', target='{self.target_fragment_key}')>"

class UserNarrativeState(Base, TimestampMixin):
    """Estado del usuario en la narrativa."""
    
    __tablename__ = "user_narrative_states"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_fragment_key = Column(String(50), ForeignKey("story_fragments.key", ondelete="SET NULL"), nullable=True)
    
    # Progreso narrativo
    visited_fragments = Column(ARRAY(String), default=[])
    decisions_made = Column(JSON, default={})
    narrative_items = Column(JSON, default={})
    narrative_variables = Column(JSON, default={})
    
    # Relaciones
    user = relationship("User", back_populates="narrative_states")
    current_fragment = relationship(
        "StoryFragment", 
        back_populates="user_states",
        foreign_keys=[current_fragment_key]
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", name="uix_user_narrative_state"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto del estado narrativo del usuario."""
        return f"<UserNarrativeState(user_id={self.user_id}, current_fragment='{self.current_fragment_key}')>"

class EmotionalNarrativeTrigger(Base, TimestampMixin):
    """Disparadores emocionales para elementos narrativos."""
    
    __tablename__ = "emotional_narrative_triggers"
    
    id = Column(Integer, primary_key=True)
    fragment_key = Column(String(50), ForeignKey("story_fragments.key", ondelete="CASCADE"), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    character_name = Column(String(50), nullable=False)
    
    # Condiciones del disparador
    condition_type = Column(String(50), nullable=False)
    condition_value = Column(JSON, nullable=False)
    
    # Respuesta emocional
    emotional_response = Column(JSON, nullable=False)
    priority = Column(Integer, default=1)
    
    # Relaciones
    fragment = relationship("StoryFragment", back_populates="emotional_triggers")
    
    __table_args__ = (
        Index("idx_emotional_triggers_fragment", "fragment_key"),
        Index("idx_emotional_triggers_character", "character_name"),
    )
    
    def __repr__(self) -> str:
        """Representación de texto del disparador emocional narrativo."""
        return f"<EmotionalNarrativeTrigger(id={self.id}, character='{self.character_name}', trigger='{self.trigger_type}')>"
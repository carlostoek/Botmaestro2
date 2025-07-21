from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.types import DateTime
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from .base import Base

class StoryFragment(Base):
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    fragment_id = Column(String(50), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    fragment_type = Column(String(20), nullable=False)  # 'start', 'normal', 'decision'
    created_at = Column(DateTime, default=func.now())  # Corregido
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    auto_next_fragment_id = Column(
        Integer, 
        ForeignKey('story_fragments.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )

    # Access conditions
    level = Column(Integer, default=1)
    min_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True, index=True)
    
    # Rewards
    reward_besitos = Column(Integer, default=0)
    unlocks_achievement_id = Column(
        String, 
        ForeignKey('achievements.id', ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    choices = relationship(
        "NarrativeChoice", 
        back_populates="source_fragment", 
        foreign_keys="NarrativeChoice.source_fragment_id",  # Corregido: usar string
        cascade="all, delete-orphan"
    )
    
    next_fragment = relationship(
        "StoryFragment",
        remote_side=[id],
        foreign_keys=[auto_next_fragment_id],
        post_update=True,
        lazy="joined"
    )

    achievement_link = relationship(
        "Achievement",
        foreign_keys=[unlocks_achievement_id],
        back_populates="story_fragments",
        lazy="joined"
    )


class NarrativeChoice(Base):
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    text = Column(String, nullable=False)
    
    # Condiciones opcionales para la decisión
    required_besitos = Column(Integer, default=0)
    required_role = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())

    source_fragment = relationship(
        "StoryFragment", 
        back_populates="choices", 
        foreign_keys=[source_fragment_id]
    )
    
    destination_fragment = relationship(
        "StoryFragment",
        foreign_keys=[destination_fragment_id]
    )


class UserNarrativeState(Base):
    __tablename__ = 'user_narrative_states'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    choices_made = Column(JSON, default=[])
    
    # Estadísticas adicionales
    fragments_visited = Column(Integer, default=0)
    total_besitos_earned = Column(Integer, default=0)
    narrative_started_at = Column(DateTime, default=func.now())
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship(
        "User", 
        back_populates="narrative_state",
        lazy="joined",
        single_parent=True
    )
    
    current_fragment = relationship(
        "StoryFragment",
        foreign_keys=[current_fragment_id],
        lazy="joined"
    )
    

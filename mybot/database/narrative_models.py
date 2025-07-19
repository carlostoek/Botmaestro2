from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from .base import Base

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
    
    # Cambiado a referencia por ID en vez de KEY
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

    # Relationships
    choices = relationship(
        "NarrativeChoice", 
        back_populates="source_fragment", 
        foreign_keys='NarrativeChoice.source_fragment_id',
        cascade="all, delete-orphan"
    )
    
    next_fragment = relationship(
        "StoryFragment",
        remote_side=[id],
        foreign_keys=[auto_next_fragment_id],
        post_update=True,
        lazy="joined"
    )

    @declared_attr
    def achievement(cls):
        return relationship("Achievement", foreign_keys=[cls.unlocks_achievement_id])


class NarrativeChoice(Base):
    """
    Represents a decision a user can make, linking one StoryFragment to another.
    """
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    destination_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    text = Column(String, nullable=False)

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
    """
    Tracks the narrative progress for each individual user.
    """
    __tablename__ = 'user_narrative_states'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    choices_made = Column(JSON, default=[])

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
    

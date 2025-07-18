# mybot/database/narrative_models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    BigInteger,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from .models import Base, User  # Import Base from the main models file

class StoryFragment(Base):
    """
    Represents a modular block of the story.
    Each fragment is a step in the narrative journey.
    """
    __tablename__ = 'story_fragments'

    id = Column(Integer, primary_key=True)
    # A unique key for programmatic access, e.g., "INTRO_LUCIEN_1"
    key = Column(String, unique=True, nullable=False, index=True)
    
    # Narrative content
    text = Column(Text, nullable=False)
    character = Column(String, default='Lucien') # Character speaking (Lucien, Diana, etc.)
    
    # Branching logic
    # If this is not null, the story progresses automatically to the next fragment
    # without waiting for user input. Useful for sequential storytelling.
    auto_next_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=True)

    # Conditions for accessing this fragment
    level = Column(Integer, default=1, comment="Narrative level, e.g., 1-3 for free, 4-6 for VIP")
    min_besitos = Column(Integer, default=0, comment="Minimum 'besitos' (points) required to view")
    required_role = Column(String, nullable=True, comment="e.g., 'vip' to restrict access")
    
    # Rewards for reaching this fragment
    reward_besitos = Column(Integer, default=0, comment="Besitos awarded upon reaching this fragment")
    # Link to an achievement to be unlocked
    unlocks_achievement_id = Column(String, ForeignKey('achievements.id'), nullable=True)

    # Relationships
    choices = relationship("NarrativeChoice", back_populates="source_fragment", foreign_keys='NarrativeChoice.source_fragment_id')


class NarrativeChoice(Base):
    """
    Represents a decision a user can make, linking one StoryFragment to another.
    """
    __tablename__ = 'narrative_choices'

    id = Column(Integer, primary_key=True)
    # The fragment where this choice is presented
    source_fragment_id = Column(Integer, ForeignKey('story_fragments.id'), nullable=False)
    # The fragment the user is taken to if they select this choice
    destination_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=False)
    
    # The text displayed on the button for this choice
    text = Column(String, nullable=False)

    # Relationship back to the source fragment
    source_fragment = relationship("StoryFragment", back_populates="choices", foreign_keys=[source_fragment_id])


class UserNarrativeState(Base):
    """
    Tracks the narrative progress for each individual user.
    This ensures a personalized and persistent story experience.
    """
    __tablename__ = 'user_narrative_states'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    
    # The user's current position in the story
    current_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=False)
    
    # A log of all choices made by the user to allow for complex branching later
    # Format: [{"choice_id": X, "source_fragment": "Y", "destination_fragment": "Z", "timestamp": "..."}]
    choices_made = Column(JSON, default=[])

    # Relationship to the User model
    user = relationship("User")

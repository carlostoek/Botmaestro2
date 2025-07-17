from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    BigInteger,
    DateTime,
)
from sqlalchemy.orm import relationship
from .setup import Base
import datetime

class NarrativeFragment(Base):
    """Represents a block of story (a message from a character)."""
    __tablename__ = 'narrative_fragments'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)
    character = Column(String, default='Lucien')
    
    decisions = relationship("NarrativeDecision", back_populates="fragment")

class NarrativeDecision(Base):
    """Represents a decision a user can make."""
    __tablename__ = 'narrative_decisions'
    id = Column(Integer, primary_key=True)
    fragment_id = Column(Integer, ForeignKey('narrative_fragments.id'))
    text = Column(String, nullable=False)
    next_fragment_key = Column(String, ForeignKey('narrative_fragments.key'))
    
    fragment = relationship("NarrativeFragment", back_populates="decisions")
    conditions = relationship("NarrativeCondition", back_populates="decision")

class NarrativeCondition(Base):
    """Conditions for a decision to be available."""
    __tablename__ = 'narrative_conditions'
    id = Column(Integer, primary_key=True)
    decision_id = Column(Integer, ForeignKey('narrative_decisions.id'))
    type = Column(String, nullable=False)  # e.g., 'min_points', 'requires_item', 'is_vip'
    value = Column(String, nullable=False)
    
    decision = relationship("NarrativeDecision", back_populates="conditions")

class UserNarrativeState(Base):
    """Saves the progress of each user in the story."""
    __tablename__ = 'user_narrative_states'
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_key = Column(String, ForeignKey('narrative_fragments.key'))
    
    user = relationship("User")

class UserDecisionLog(Base):
    """Logs all decisions made by the user."""
    __tablename__ = 'user_decision_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    decision_id = Column(Integer, ForeignKey('narrative_decisions.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    decision = relationship("NarrativeDecision")
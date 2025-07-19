from sqlalchemy import Column, BigInteger, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base

class UserNarrativeState(Base):
    __tablename__ = 'user_narrative_states'
    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_fragment_key = Column(String, ForeignKey('story_fragments.key'), nullable=False)
    choices_made = Column(JSON, default=[])

    # SOLUCIÓN: Usar referencia de cadena para User
    user = relationship(
        "User", 
        back_populates="narrative_state",
        lazy="joined",
        single_parent=True
    )
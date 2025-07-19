from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..base import Base

class NarrativeFragment(Base):
    __tablename__ = 'narrative_fragments'
    
    id = Column(Integer, primary_key=True, index=True)
    fragment_id = Column(String(50), unique=True, index=True)
    content = Column(Text, nullable=False)
    level = Column(Integer, nullable=False)  # 1-3: free, 4-6: VIP
    required_besitos = Column(Integer, default=0)
    required_item_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    unlock_conditions = Column(JSON, nullable=True)  # e.g., {"mission_completed": "mission_id", "min_reactions": 5}
    decisions = Column(JSON, nullable=False)  # Lista de decisiones posibles
    
    # Relación opcional con ítems si es necesario
    required_item = relationship("Item", back_populates="narrative_requirements")

class UserStoryState(Base):
    __tablename__ = 'user_story_states'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    current_fragment_id = Column(String(50), ForeignKey('narrative_fragments.fragment_id'))
    decisions = Column(JSON, default=dict)  # Almacenar decisiones como {fragment_id: choice_index, ...}
    unlocked_fragments = Column(JSON, default=list)  # Lista de fragment_ids desbloqueados
    story_progress = Column(Integer, default=0)  # Porcentaje o nivel de progreso
    
    # Relaciones
    current_fragment = relationship("NarrativeFragment", foreign_keys=[current_fragment_id])
    user = relationship("User", back_populates="story_state")

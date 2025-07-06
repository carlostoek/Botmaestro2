# database/narrative_models.py

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
    dialogue_history = relationship("DialogueHistory", back_populates="narrative_state")
    
    def __repr__(self):
        return f"<NarrativeState(user_id={self.user_id}, level={self.narrative_level}, trust={self.trust_level})>"

# Piezas de lore y conocimiento
class LorePiece(Base):
    """Piezas de historia/lore que los usuarios pueden descubrir"""
    __tablename__ = "lore_pieces"
    
    id = Column(Integer, primary_key=True)
    code_name = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    piece_type = Column(String, nullable=False)  # "diary", "memory", "artifact", "letter"
    
    # Metadata
    chapter = Column(String)
    emotional_tone = Column(String)
    reveals_about = Column(String)  # "past", "personality", "fears", "desires"
    
    # Condiciones de desbloqueo
    required_level = Column(Integer, default=0)
    required_trust = Column(Float, default=0.0)
    prerequisite_pieces = Column(JSON, default=list)  # Lista de code_names requeridos
    special_condition = Column(String)  # "full_moon", "midnight", "after_rejection", etc.
    
    # Efectos al descubrir
    trust_impact = Column(Float, default=0.0)
    unlocks_dialogue = Column(String)  # Nuevo diálogo disponible
    triggers_event = Column(String)  # Evento que se activa
    
    # Hints para encontrarla
    discovery_hints = Column(JSON, default=list)
    is_hidden = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<LorePiece(code_name={self.code_name}, type={self.piece_type})>"

class UserLorePiece(Base):
    """Relación entre usuarios y las piezas de lore que han encontrado"""
    __tablename__ = "user_lore_pieces"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=False)
    
    # Cuándo y cómo la encontró
    found_at = Column(DateTime, default=datetime.utcnow)
    found_through = Column(String)  # "mission", "exploration", "gift", "combination"
    
    # Interacción con la pieza
    times_viewed = Column(Integer, default=1)
    last_viewed = Column(DateTime, default=datetime.utcnow)
    has_asked_diana = Column(Boolean, default=False)
    diana_revealed_extra = Column(Boolean, default=False)
    
    # Si la ha usado para combinar
    used_in_combination = Column(Boolean, default=False)
    combination_result_id = Column(Integer, ForeignKey("lore_pieces.id"))
    
    # Notas o reflexiones del usuario
    user_notes = Column(Text)
    
    # Relaciones
    user = relationship("User", backref="found_lore_pieces")
    lore_piece = relationship("LorePiece", foreign_keys=[lore_piece_id])
    combination_result = relationship("LorePiece", foreign_keys=[combination_result_id])
    
    def __repr__(self):
        return f"<UserLorePiece(user_id={self.user_id}, piece={self.lore_piece_id})>"

# Cartas no enviadas
class UnsentLetter(Base):
    """Cartas no enviadas de Diana - elementos narrativos especiales"""
    __tablename__ = "unsent_letters"
    
    id = Column(Integer, primary_key=True)
    code_name = Column(String, unique=True, nullable=False)
    
    # Contenido
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    postscript = Column(Text)  # P.D. opcional
    
    # Metadata narrativa
    written_date = Column(String)  # Fecha ficticia en la narrativa
    emotional_state = Column(String)  # Estado emocional cuando la escribió
    trigger_memory = Column(String)  # Qué recuerdo la motivó
    
    # Condiciones de desbloqueo
    required_narrative_level = Column(Integer, default=3)
    required_trust_level = Column(Float, default=0.5)
    required_event = Column(String)  # Evento específico que la desbloquea
    special_condition = Column(String)  # Condición especial (luna llena, etc.)
    
    # Estado
    is_discoverable = Column(Boolean, default=True)
    discovery_hint = Column(Text)  # Pista para encontrarla
    
    # Impacto al descubrirla
    trust_impact = Column(Float, default=0.1)
    vulnerability_reveal = Column(Float, default=0.2)
    unlocks_dialogue_option = Column(String)  # Nueva opción de diálogo
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UnsentLetter(code_name={self.code_name}, title={self.title})>"

class UserUnsentLetter(Base):
    """Registro de cartas descubiertas por usuarios"""
    __tablename__ = "user_unsent_letters"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    letter_id = Column(Integer, ForeignKey("unsent_letters.id"), nullable=False)
    
    # Descubrimiento
    found_at = Column(DateTime, default=datetime.utcnow)
    found_through = Column(String)  # "exploration", "trust_milestone", "special_event"
    
    # Interacción
    times_read = Column(Integer, default=1)
    last_read = Column(DateTime, default=datetime.utcnow)
    user_reaction = Column(String)  # Cómo reaccionó el usuario
    asked_diana_about_it = Column(Boolean, default=False)
    diana_response_given = Column(Text)  # Respuesta especial de Diana
    
    # Relaciones
    user = relationship("User", backref="found_letters")
    letter = relationship("UnsentLetter")
    
    def __repr__(self):
        return f"<UserUnsentLetter(user_id={self.user_id}, letter_id={self.letter_id})>"

# Eventos narrativos
class NarrativeEvent(Base):
    """Eventos narrativos que ocurren durante la interacción"""
    __tablename__ = "narrative_events"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # "revelation", "milestone", "choice", "discovery"
    event_code = Column(String, nullable=False)  # Código único del evento
    
    # Detalles del evento
    title = Column(String, nullable=False)
    description = Column(Text)
    impact_description = Column(Text)  # Cómo afectó la relación
    
    # Contexto
    narrative_level = Column(Integer)
    chapter = Column(String)
    trigger_condition = Column(String)  # Qué causó el evento
    
    # Impacto
    trust_impact = Column(Float, default=0.0)
    vulnerability_impact = Column(Float, default=0.0)
    mystery_impact = Column(Float, default=0.0)
    
    # Datos adicionales
    dialogue_shown = Column(Text)  # Lo que Diana dijo
    user_response = Column(Text)  # Lo que el usuario respondió
    choices_presented = Column(JSON)  # Si hubo opciones
    choice_made = Column(String)  # Qué eligió el usuario
    
    # Timestamps
    occurred_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", backref="narrative_events")
    
    def __repr__(self):
        return f"<NarrativeEvent(user_id={self.user_id}, type={self.event_type}, code={self.event_code})>"

# Historial de diálogos
class DialogueHistory(Base):
    """Historial de diálogos con Diana"""
    __tablename__ = "dialogue_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    narrative_state_id = Column(Integer, ForeignKey("narrative_states.id"))
    
    # Contenido del diálogo
    user_message = Column(Text, nullable=False)
    diana_response = Column(Text, nullable=False)
    
    # Contexto
    narrative_level = Column(Integer)
    emotional_state = Column(Enum(EmotionalState))
    detected_archetype = Column(Enum(UserArchetype))
    
    # Análisis del mensaje
    message_sentiment = Column(Float)  # -1 a 1
    detected_intent = Column(String)  # "flirt", "question", "share", "challenge"
    emotional_words_count = Column(Integer, default=0)
    vulnerability_score = Column(Float, default=0.0)
    
    # Impacto
    trust_change = Column(Float, default=0.0)
    connection_change = Column(Float, default=0.0)
    
    # Metadata
    response_time = Column(Float)  # Segundos que tardó en responder
    message_length = Column(Integer)
    contains_emoji = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", backref="dialogue_history")
    narrative_state = relationship("NarrativeState", back_populates="dialogue_history")
    
    def __repr__(self):
        return f"<DialogueHistory(user_id={self.user_id}, level={self.narrative_level})>"

# Fragmentos de memoria
class MemoryFragment(Base):
    """Fragmentos de memoria de Diana que se pueden descubrir"""
    __tablename__ = "memory_fragments"
    
    id = Column(Integer, primary_key=True)
    code_name = Column(String, unique=True, nullable=False)
    
    # Contenido
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(String)  # "childhood", "trauma", "love", "loss", "hope"
    emotional_weight = Column(Float, default=0.5)  # 0-1 intensidad emocional
    
    # Contexto temporal
    memory_age = Column(String)  # "recent", "distant", "ancient", "timeless"
    season = Column(String)  # "spring", "summer", "autumn", "winter"
    time_of_day = Column(String)  # "dawn", "morning", "afternoon", "evening", "night"
    
    # Triggers y condiciones
    trigger_words = Column(JSON, default=list)  # Palabras que pueden activarla
    required_trust = Column(Float, default=0.3)
    required_vulnerability = Column(Float, default=0.2)
    prerequisite_memory = Column(String)  # code_name de memoria previa requerida
    
    # Efectos
    unlocks_dialogue_branch = Column(String)
    reveals_personality

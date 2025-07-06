# mybot/database/narrative_models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    JSON,
    DateTime,
    ForeignKey,
    BigInteger,
    Enum
)
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
    HOPEFUL = "hoepful"

class UserArchetype(PyEnum):
    UNKNOWN = "unknown"
    ROMANTIC = "romantic"
    DIRECT = "direct"
    ANALYTICAL = "analytical"
    EXPLORER = "explorer"
    PATIENT = "patient"
    PERSISTENT = "persistent"

class NarrativeState(Base):
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
    dialogue_history = relationship(
        "DialogueHistory", back_populates="narrative_state"
    )
    
    def __repr__(self):
        return f"<NarrativeState(user_id={self.user_id}, level={self.narrative_level}, trust={self.trust_level})>"

class LorePiece(Base):
    __tablename__ = "lore_pieces"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserLorePiece(Base):
    __tablename__ = "user_lore_pieces"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    lore_piece_id = Column(Integer, ForeignKey("lore_pieces.id"), nullable=False)
    found_at = Column(DateTime, default=datetime.utcnow)
    user_notes = Column(Text)
    user = relationship("User ", backref="found_lore_pieces")
    lore_piece = relationship("LorePiece", foreign_keys=[lore_piece_id])


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
    response_time = Column(Float)
    message_length = Column(Integer)
    contains_emoji = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", backref="dialogue_history")
    narrative_state = relationship("NarrativeState", back_populates="dialogue_history")

    def __repr__(self):
        return f"<DialogueHistory(user_id={self.user_id}, level={self.narrative_level})>"


class NarrativeEvent(Base):
    """Eventos narrativos que ocurren durante la interacción"""
    __tablename__ = "narrative_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)
    event_code = Column(String, nullable=False)

    # Detalles del evento
    title = Column(String, nullable=False)
    description = Column(Text)
    impact_description = Column(Text)

    # Contexto
    narrative_level = Column(Integer)
    chapter = Column(String)
    trigger_condition = Column(String)

    # Impacto
    trust_impact = Column(Float, default=0.0)
    vulnerability_impact = Column(Float, default=0.0)
    mystery_impact = Column(Float, default=0.0)

    # Datos adicionales
    dialogue_shown = Column(Text)
    user_response = Column(Text)
    choices_presented = Column(JSON)
    choice_made = Column(String)

    # Timestamps
    occurred_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", backref="narrative_events")

    def __repr__(self):
        return f"<NarrativeEvent(user_id={self.user_id}, type={self.event_type}, code={self.event_code})>"


# MODELOS FALTANTES


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
    reveals_personality_aspect = Column(String)
    trust_impact = Column(Float, default=0.05)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserMemoryFragment(Base):
    """Registro de fragmentos de memoria descubiertos por usuarios"""

    __tablename__ = "user_memory_fragments"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    memory_id = Column(Integer, ForeignKey("memory_fragments.id"), nullable=False)

    # Descubrimiento
    discovered_at = Column(DateTime, default=datetime.utcnow)
    discovery_context = Column(String)  # "conversation", "exploration", "trust_milestone"
    trigger_phrase = Column(Text)  # Qué dijo el usuario que activó la memoria

    # Respuesta del usuario
    user_response = Column(Text)
    showed_empathy = Column(Boolean, default=False)
    emotional_resonance = Column(Float, default=0.0)  # 0-1 qué tan bien conectó

    # Relaciones
    user = relationship("User", backref="discovered_memories")
    memory = relationship("MemoryFragment")


class DianaResponse(Base):
    """Respuestas predefinidas de Diana para situaciones específicas"""

    __tablename__ = "diana_responses"

    id = Column(Integer, primary_key=True)
    response_code = Column(String, unique=True, nullable=False)

    # Contexto
    situation_type = Column(String)  # "greeting", "farewell", "confession", "rejection"
    emotional_state = Column(Enum(EmotionalState))
    relationship_stage = Column(Enum(RelationshipStage))

    # Contenido
    response_text = Column(Text, nullable=False)
    alternative_texts = Column(JSON, default=list)  # Variaciones

    # Condiciones
    min_trust_required = Column(Float, default=0.0)
    max_trust_allowed = Column(Float, default=1.0)
    time_of_day_preference = Column(String)  # "night", "day", "any"

    # Metadata
    tone = Column(String)  # "playful", "mysterious", "vulnerable", "defensive"
    contains_hint = Column(Boolean, default=False)
    hint_target = Column(String)  # A qué apunta la pista


class NarrativeTrigger(Base):
    """Triggers que activan eventos narrativos"""

    __tablename__ = "narrative_triggers"

    id = Column(Integer, primary_key=True)
    trigger_code = Column(String, unique=True, nullable=False)

    # Tipo y condiciones
    trigger_type = Column(String)  # "word", "action", "time", "milestone"
    trigger_data = Column(JSON)  # Datos específicos del trigger

    # Qué activa
    activates_event = Column(String)  # código del evento
    activates_memory = Column(String)  # código de memoria
    activates_dialogue = Column(String)  # rama de diálogo

    # Condiciones
    min_narrative_level = Column(Integer, default=0)
    required_emotional_state = Column(String)
    cooldown_hours = Column(Integer, default=0)  # Horas antes de poder reactivar

    # Estado
    is_active = Column(Boolean, default=True)
    single_use = Column(Boolean, default=False)


class EmotionalMemory(Base):
    """Sistema de memoria emocional de Diana"""

    __tablename__ = "emotional_memories"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Momento emocional
    emotion_type = Column(String)  # "joy", "sadness", "fear", "trust", "surprise"
    intensity = Column(Float)  # 0-1
    context = Column(Text)  # Qué causó esta emoción

    # Respuesta de Diana
    diana_reaction = Column(Text)
    vulnerability_shown = Column(Float, default=0.0)

    # Impacto a largo plazo
    shapes_future_responses = Column(Boolean, default=False)
    reference_count = Column(Integer, default=0)  # Veces que Diana lo menciona

    created_at = Column(DateTime, default=datetime.utcnow)
    last_referenced = Column(DateTime)

    # Relaciones
    user = relationship("User", backref="emotional_memories")


class UserChoice(Base):
    """Registro de decisiones importantes del usuario"""

    __tablename__ = "user_choices"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    # Decisión
    choice_point = Column(String, nullable=False)  # Momento de decisión
    options_presented = Column(JSON)  # Opciones disponibles
    choice_made = Column(String)  # Qué eligió

    # Contexto
    narrative_level = Column(Integer)
    current_trust = Column(Float)
    emotional_context = Column(String)

    # Consecuencias
    immediate_consequence = Column(Text)
    long_term_impact = Column(String)
    altered_narrative_path = Column(Boolean, default=False)

    # Diana's reaction
    diana_response = Column(Text)
    relationship_impact = Column(Float, default=0.0)

    made_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", backref="narrative_choices")


class NarrativePath(Base):
    """Caminos narrativos disponibles"""

    __tablename__ = "narrative_paths"

    id = Column(Integer, primary_key=True)
    path_code = Column(String, unique=True, nullable=False)

    # Información
    path_name = Column(String, nullable=False)
    description = Column(Text)
    path_type = Column(String)  # "main", "branch", "secret", "ending"

    # Requisitos
    min_narrative_level = Column(Integer, default=0)
    required_choices = Column(JSON, default=list)  # Decisiones previas necesarias
    required_trust = Column(Float, default=0.0)
    required_items = Column(JSON, default=list)  # Items o lore pieces necesarios

    # Contenido
    key_events = Column(JSON, default=list)
    unique_dialogues = Column(JSON, default=list)
    exclusive_rewards = Column(JSON, default=list)

    # Estado
    is_active = Column(Boolean, default=True)
    is_ending_path = Column(Boolean, default=False)


class SecretRoom(Base):
    """Lugares secretos en el mundo de Diana"""

    __tablename__ = "secret_rooms"

    id = Column(Integer, primary_key=True)
    room_code = Column(String, unique=True, nullable=False)

    # Información
    name = Column(String, nullable=False)
    description = Column(Text)
    atmosphere = Column(Text)  # Descripción atmosférica

    # Acceso
    access_method = Column(String)  # "password", "item", "trust", "special_event"
    access_requirement = Column(JSON)  # Datos específicos del requisito
    hint_text = Column(Text)  # Pista para encontrarlo

    # Contenido
    contains_items = Column(JSON, default=list)
    contains_lore = Column(JSON, default=list)
    special_dialogue = Column(Text)  # Lo que Diana dice al encontrarlo

    # Propiedades especiales
    changes_diana_mood = Column(Boolean, default=False)
    mood_change = Column(String)
    permanent_effect = Column(String)  # Efecto permanente al descubrirlo


class UserSecretRoom(Base):
    """Registro de lugares secretos descubiertos"""

    __tablename__ = "user_secret_rooms"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("secret_rooms.id"), nullable=False)

    # Descubrimiento
    discovered_at = Column(DateTime, default=datetime.utcnow)
    discovery_method = Column(String)
    attempts_before_success = Column(Integer, default=1)

    # Interacción
    times_visited = Column(Integer, default=1)
    last_visited = Column(DateTime, default=datetime.utcnow)
    items_found = Column(JSON, default=list)

    # Relaciones
    user = relationship("User", backref="discovered_rooms")
    room = relationship("SecretRoom")


class DianaSecret(Base):
    """Secretos profundos de Diana"""

    __tablename__ = "diana_secrets"

    id = Column(Integer, primary_key=True)
    secret_code = Column(String, unique=True, nullable=False)

    # Contenido
    secret_type = Column(String)  # "past", "fear", "desire", "truth"
    content = Column(Text, nullable=False)
    gravity = Column(Integer)  # 1-5, qué tan importante es

    # Revelación
    revelation_conditions = Column(JSON)
    min_trust_required = Column(Float, default=0.8)
    special_requirement = Column(String)

    # Impacto
    changes_everything = Column(Boolean, default=False)
    trust_impact = Column(Float)
    unlocks_ending = Column(String)


class UserDianaSecret(Base):
    """Registro de secretos descubiertos"""

    __tablename__ = "user_diana_secrets"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    secret_id = Column(Integer, ForeignKey("diana_secrets.id"), nullable=False)

    # Descubrimiento
    revealed_at = Column(DateTime, default=datetime.utcnow)
    revelation_context = Column(Text)
    user_reaction = Column(Text)

    # Consecuencias
    relationship_changed = Column(Boolean, default=True)
    new_dynamic = Column(String)

    # Relaciones
    user = relationship("User", backref="known_secrets")
    secret = relationship("DianaSecret")


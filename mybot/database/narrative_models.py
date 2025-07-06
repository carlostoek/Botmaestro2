# database/narrative_models.py
"""
Modelos de base de datos para el sistema narrativo del bot.
Estos modelos manejan todo el estado narrativo, memorias y progresión con Diana.
"""

from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, Boolean, 
    JSON, Text, ForeignKey, Float, Index, Enum as SQLEnum
)
from uuid import uuid4
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
import enum

# Importar la base existente
from database.models import Base

class UserArchetype(enum.Enum):
    """Arquetipos de usuario identificados por el sistema"""
    ROMANTIC = "romantic"
    DIRECT = "direct" 
    ANALYTICAL = "analytical"
    EXPLORER = "explorer"
    PATIENT = "patient"
    PERSISTENT = "persistent"
    UNKNOWN = "unknown"

class RelationshipStage(enum.Enum):
    """Etapas de la relación con Diana"""
    STRANGER = "stranger"
    CURIOUS = "curious"
    ACQUAINTANCE = "acquaintance" 
    TRUSTED = "trusted"
    CONFIDANT = "confidant"
    INTIMATE = "intimate"

class NarrativeState(AsyncAttrs, Base):
    """Estado narrativo y emocional del usuario con Diana"""
    __tablename__ = "narrative_states"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    
    # Métricas de relación (0.0 a 1.0)
    trust_level = Column(Float, default=0.0)
    vulnerability_shown = Column(Float, default=0.0) 
    emotional_depth = Column(Float, default=0.0)
    mystery_preservation = Column(Float, default=1.0)  # Qué tanto respeta el misterio
    
    # Arquetipos y personalidad
    user_archetype = Column(SQLEnum(UserArchetype), default=UserArchetype.UNKNOWN)
    archetype_confidence = Column(Float, default=0.0)
    secondary_archetype = Column(SQLEnum(UserArchetype), nullable=True)
    
    # Estado narrativo
    current_chapter = Column(String, default="introduction")
    relationship_stage = Column(SQLEnum(RelationshipStage), default=RelationshipStage.STRANGER)
    last_meaningful_interaction = Column(DateTime, nullable=True)
    
    # Decisiones y elecciones importantes
    key_decisions = Column(JSON, default={})  
    # Formato: {"first_vulnerability": "shared_fear", "diana_wall_response": "respected"}
    
    # Referencias a memorias compartidas
    shared_memories = Column(JSON, default=[])
    emotional_callbacks_available = Column(JSON, default=[])
    
    # Estadísticas de interacción
    total_interactions = Column(Integer, default=0)
    meaningful_conversations = Column(Integer, default=0)
    vulnerabilities_shared = Column(Integer, default=0)
    times_respected_boundaries = Column(Integer, default=0)
    times_pushed_boundaries = Column(Integer, default=0)
    
    # Para el sistema de respuestas contextuales
    response_style_metrics = Column(JSON, default={
        "poetic": 0, "direct": 0, "analytical": 0, 
        "emotional": 0, "protective": 0, "respectful": 0
    })
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class DialogueMemory(AsyncAttrs, Base):
    """Memorias de diálogos significativos entre Diana y el usuario"""
    __tablename__ = "dialogue_memories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    
    # Tipo y contexto
    memory_type = Column(String, nullable=False)  
    # Tipos: "vulnerability", "understanding", "conflict", "breakthrough", "boundary_respect"
    
    chapter = Column(String, nullable=False)  # En qué capítulo ocurrió
    emotional_context = Column(String)  # "tense", "warm", "vulnerable", "playful"
    
    # Contenido del diálogo
    trigger_context = Column(Text)  # Qué provocó este momento
    user_message = Column(Text)  # Mensaje exacto del usuario
    diana_response = Column(Text)  # Respuesta de Diana
    
    # Impacto emocional (-1 a 1)
    trust_impact = Column(Float, default=0.0)
    vulnerability_impact = Column(Float, default=0.0)
    relationship_impact = Column(Float, default=0.0)
    
    # Para referencias futuras
    can_be_referenced = Column(Boolean, default=True)
    times_referenced = Column(Integer, default=0)
    last_referenced = Column(DateTime, nullable=True)
    
    # Metadatos especiales
    is_breakthrough_moment = Column(Boolean, default=False)
    unlocked_new_responses = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=func.now())

class LorePiece(AsyncAttrs, Base):
    """Fragmentos de historia, pistas y objetos narrativos"""
    __tablename__ = "lore_pieces"
    
    code = Column(String, primary_key=True)  # "L1_DIARY_1", "L3_LETTER_2"
    name = Column(String, nullable=False)
    description = Column(Text)  # Descripción al encontrarla
    content = Column(Text)  # Contenido completo
    
    # Categorización
    piece_type = Column(String, nullable=False)
    # Tipos: "diary_page", "letter", "photo", "memory", "object", "secret"
    
    category = Column(String, nullable=False)
    # Categorías: "diana_past", "diana_present", "world_building", "relationship"
    
    found_in_level = Column(Integer, nullable=False)
    rarity = Column(String, default="common")  # common, rare, legendary
    
    # Sistema de combinación
    combines_with = Column(JSON, default=[])  # ["L3_KEY_1", "L5_PHOTO_2"]
    combination_result = Column(String, nullable=True)  # Código de resultado
    combination_narrative = Column(Text, nullable=True)  # Historia al combinar
    
    # Reacciones de Diana
    diana_comment_on_find = Column(Text, nullable=True)
    diana_comment_if_asked = Column(Text, nullable=True)
    changes_diana_behavior = Column(Boolean, default=False)
    behavior_change_description = Column(Text, nullable=True)
    
    # Metadatos narrativos
    emotional_weight = Column(Integer, default=1)  # 1-10 importancia emocional
    reveals_about_diana = Column(JSON, default=[])  # ["vulnerability", "past_trauma"]
    
    # Requisitos para encontrar
    min_trust_required = Column(Float, default=0.0)
    min_relationship_stage = Column(String, nullable=True)
    requires_specific_memory = Column(String, nullable=True)  # memory_type requerido
    
    created_at = Column(DateTime, default=func.now())

class UserLorePiece(AsyncAttrs, Base):
    """Registro de pistas encontradas por cada usuario (su mochila)"""
    __tablename__ = "user_lore_pieces"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    lore_piece_code = Column(String, ForeignKey("lore_pieces.code"), primary_key=True)
    
    # Contexto del descubrimiento
    found_at = Column(DateTime, default=func.now())
    found_context = Column(String)  # "mission_reward", "exploration", "diana_gift"
    discovery_method = Column(Text, nullable=True)  # Cómo exactamente la encontró
    
    # Interacción con la pieza
    has_read = Column(Boolean, default=False)
    first_read_at = Column(DateTime, nullable=True)
    times_viewed = Column(Integer, default=0)
    asked_diana_about_it = Column(Boolean, default=False)
    diana_reaction_logged = Column(Text, nullable=True)
    
    # Sistema de combinación
    used_in_combination = Column(Boolean, default=False)
    successful_combinations = Column(JSON, default=[])
    failed_combination_attempts = Column(JSON, default=[])
    
    # Impacto narrativo
    changed_dialogue_options = Column(Boolean, default=False)
    unlocked_memories = Column(JSON, default=[])

class UnsentLetter(AsyncAttrs, Base):
    """Cartas que Diana escribió pero nunca envió"""
    __tablename__ = "unsent_letters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    
    # Contexto de la carta
    trigger_event = Column(String, nullable=False)
    # Eventos: "after_first_vulnerability", "after_trust_breakthrough", "before_intimate_level"
    
    letter_date = Column(String)  # Fecha ficticia en la carta
    emotional_state = Column(String)  # Estado de Diana al escribirla
    
    # Contenido
    subject = Column(String)  # "Sobre lo que dijiste ayer..."
    content = Column(Text, nullable=False)
    signature = Column(String, default="D")  # Cómo firma
    
    # Condiciones de descubrimiento
    min_trust_required = Column(Float, default=0.5)
    min_level_required = Column(Integer, default=3)
    required_relationship_stage = Column(String, nullable=True)
    specific_archetype_bonus = Column(String, nullable=True)  # Más fácil para cierto arquetipo
    
    # Probabilidad y límites
    discovery_chance = Column(Float, default=0.1)  # 0-1 probabilidad base
    can_be_found_multiple_times = Column(Boolean, default=False)
    max_discoveries = Column(Integer, default=1)
    
    # Recompensas
    gives_points = Column(Integer, default=0)
    trust_increase = Column(Float, default=0.0)
    unlocks_special_dialogue = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

class UserUnsentLetter(AsyncAttrs, Base):
    """Registro de cartas no enviadas encontradas por usuarios"""
    __tablename__ = "user_unsent_letters"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    letter_id = Column(String, ForeignKey("unsent_letters.id"), primary_key=True)
    
    # Descubrimiento
    found_at = Column(DateTime, default=func.now())
    found_where = Column(String)  # "random_event", "mission_reward", "exploration"
    
    # Reacción del usuario
    user_reaction = Column(String, nullable=True)  # "touched", "curious", "protective"
    user_response = Column(Text, nullable=True)  # Si respondieron algo
    
    # Impacto narrativo
    diana_noticed = Column(Boolean, default=False)
    diana_mentioned_it = Column(Boolean, default=False)
    changed_dynamics = Column(Boolean, default=False)
    special_dialogue_unlocked = Column(Boolean, default=False)

class NarrativeEvent(AsyncAttrs, Base):
    """Eventos narrativos especiales temporales o recurrentes"""
    __tablename__ = "narrative_events"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Tipo y triggers
    event_type = Column(String, nullable=False)
    # Tipos: "lunar_phase", "seasonal", "special_date", "relationship_milestone"
    
    trigger_conditions = Column(JSON, nullable=False)
    # Ejemplos: {"type": "lunar", "phase": "new_moon"}
    #          {"type": "date", "dates": ["14-02", "25-12"]}
    #          {"type": "relationship", "stage": "intimate", "trust": 0.8}
    
    # Contenido narrativo
    announcement_message = Column(Text)
    diana_special_mood = Column(String)  # "nostalgic", "vulnerable", "mysterious"
    special_dialogues = Column(JSON, default=[])
    
    # Misiones y recompensas especiales
    exclusive_missions = Column(JSON, default=[])
    exclusive_lore_pieces = Column(JSON, default=[])
    temporary_shop_items = Column(JSON, default=[])
    
    # Configuración temporal
    duration_hours = Column(Integer, default=24)
    is_recurring = Column(Boolean, default=True)
    recurrence_pattern = Column(String, nullable=True)  # "monthly", "lunar", "seasonal"
    
    # Requisitos de participación
    min_level_required = Column(Integer, default=1)
    min_trust_required = Column(Float, default=0.0)
    vip_exclusive = Column(Boolean, default=False)
    
    # Estadísticas
    times_occurred = Column(Integer, default=0)
    last_occurred = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

class UserNarrativeEvent(AsyncAttrs, Base):
    """Participación de usuarios en eventos narrativos"""
    __tablename__ = "user_narrative_events"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    event_id = Column(String, ForeignKey("narrative_events.id"), primary_key=True)
    
    # Participación
    first_participated = Column(DateTime, default=func.now())
    times_participated = Column(Integer, default=1)
    last_participated = Column(DateTime, default=func.now())
    
    # Progreso en el evento
    missions_completed = Column(JSON, default=[])
    special_items_obtained = Column(JSON, default=[])
    exclusive_dialogues_seen = Column(JSON, default=[])
    
    # Logros del evento
    event_points_earned = Column(Integer, default=0)
    special_achievement_unlocked = Column(Boolean, default=False)
    perfect_completion = Column(Boolean, default=False)

# Índices para optimización
Index('idx_narrative_state_user_archetype', NarrativeState.user_id, NarrativeState.user_archetype)
Index('idx_dialogue_memory_user_type', DialogueMemory.user_id, DialogueMemory.memory_type)
Index('idx_dialogue_memory_breakthrough', DialogueMemory.is_breakthrough_moment)
Index('idx_lore_piece_level_type', LorePiece.found_in_level, LorePiece.piece_type)
Index('idx_user_lore_piece_user', UserLorePiece.user_id)
Index('idx_unsent_letter_trigger', UnsentLetter.trigger_event)
Index('idx_narrative_event_type_active', NarrativeEvent.event_type, NarrativeEvent.is_active)
  

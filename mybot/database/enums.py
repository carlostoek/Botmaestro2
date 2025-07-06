from enum import Enum as PyEnum

class RelationshipStage(PyEnum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CONFIDANT = "confidant"
    INTIMATE = "intimate"

class EmotionalState(PyEnum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    VULNERABLE = "vulnerable"

class UserArchetype(PyEnum):
    UNKNOWN = "unknown"
    GUARDIAN = "guardian"
    CONFIDANT = "confidant"
    MYSTERY_LOVER = "mystery_lover"
    ROMANTIC = "romantic"
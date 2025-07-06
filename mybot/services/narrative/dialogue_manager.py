# services/narrative/dialogue_manager.py
"""
Gestor principal de diálogos de Diana.
Maneja la generación contextual de respuestas basadas en el estado narrativo.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
import random
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.narrative_models import (
    NarrativeState, DialogueMemory, UserArchetype, 
    RelationshipStage
)
from database.models import User

class DianaDialogueManager:
    """Gestiona todos los diálogos de Diana de manera contextual"""
    
    def __init__(self):
        self.dialogue_templates = self._load_dialogue_templates()
        self.emotional_modifiers = self._load_emotional_modifiers()
    
    def _load_dialogue_templates(self) -> Dict:
        """Carga las plantillas base de diálogos"""
        return {
            "greeting": {
                RelationshipStage.STRANGER: [
                    "Oh... no esperaba visitas a esta hora. ¿En qué puedo ayudarte?",
                    "Bienvenido. Soy Diana. Lucien me dijo que podrías venir...",
                ],
                RelationshipStage.CURIOUS: [
                    "Volviste... Hay algo en ti que despierta mi curiosidad.",
                    "Cada vez que vienes, me pregunto qué buscas realmente aquí.",
                ],
                RelationshipStage.ACQUAINTANCE: [
                    "Me alegra verte de nuevo. ¿Cómo has estado?",
                    "Pensé en nuestra última conversación... Fue... inusual.",
                ],
                RelationshipStage.TRUSTED: [
                    "Tu presencia se ha vuelto... reconfortante. No esperaba eso.",
                    "[sonríe suavemente] Llegas justo cuando necesitaba alguien con quien hablar.",
                ],
                RelationshipStage.CONFIDANT: [
                    "Hay pocas personas con las que puedo ser yo misma. Tú eres una de ellas.",
                    "¿Sabes? Ya no siento la necesidad de mantener todos mis muros contigo.",
                ],
                RelationshipStage.INTIMATE: [
                    "Cada vez que te veo, confirmo que tomé la decisión correcta al confiar en ti.",
                    "Tu presencia ha transformado este lugar... y a mí.",
                ],
            },
            
            "vulnerability_response": {
                "positive": [
                    "Tu honestidad... desarma. No muchos se atreven a ser tan genuinos.",
                    "Hay algo hermoso en tu vulnerabilidad. Me hace querer... [pausa] ser igual de honesta.",
                    "Gracias por confiar en mí con esto. Sé lo difícil que puede ser.",
                ],
                "negative": [
                    "Entiendo que quieras ayudar, pero algunos muros existen por una razón.",
                    "No necesito que me rescates. Solo... que me entiendas.",
                    "Aprecio la intención, pero hay cosas que debo resolver sola.",
                ],
            },
            
            "boundary_respect": {
                "acknowledged": [
                    "No muchos entienden que respetar la distancia es otra forma de acercarse. Tú sí.",
                    "Tu capacidad de estar presente sin invadir... es excepcional.",
                    "Gracias por entender que puedo ser vulnerable sin ser conquistable.",
                ],
            },
            
            "mission_introduction": {
                "playful": [
                    "Tengo algo especial preparado para ti... si te atreves.",
                    "¿Listo para otro desafío? Prometo que valdrá la pena.",
                ],
                "mysterious": [
                    "Hay secretos en esta mansión que pocos conocen. ¿Quieres descubrir uno?",
                    "Lo que voy a mostrarte... cambiará cómo ves este lugar. ¿Estás preparado?",
                ],
                "intimate": [
                    "He estado pensando en compartir algo contigo... algo personal.",
                    "Hay una parte de mí que quiero mostrarte. Pero necesito saber que estás listo.",
                ],
            },
        }
    
    def _load_emotional_modifiers(self) -> Dict:
        """Modificadores según el estado emocional"""
        return {
            "time_based": {
                "late_night": {  # 23:00 - 4:00
                    "vulnerability_increase": 0.2,
                    "form

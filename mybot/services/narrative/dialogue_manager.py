# services/narrative/dialogue_manager.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database.models import User
from database.narrative_models import (
    NarrativeState, LorePiece, NarrativeEvent,
    UserArchetype, RelationshipStage, EmotionalState
)

class DianaDialogueManager:
    """Gestiona los diálogos contextuales de Diana"""
    
    def __init__(self):
        self.dialogue_trees = self._load_dialogue_trees()
        self.emotional_modifiers = self._load_emotional_modifiers()
        self.archetype_responses = self._load_archetype_responses()
        
    def _load_dialogue_trees(self) -> Dict:
        """Carga los árboles de diálogo por nivel narrativo"""
        return {
            "level_1": {
                "greeting": {
                    "default": [
                        "Ah, {name}... Bienvenido a mi mundo. ¿Vienes por curiosidad o por algo más?",
                        "Interesante... No todos encuentran el camino hasta aquí. Soy Diana.",
                        "Mmm... Otro visitante. Veamos si eres diferente a los demás."
                    ],
                    "returning": [
                        "Volviste... Eso dice algo de ti.",
                        "¿No pudiste resistirte? Me gusta la persistencia.",
                        "Cada visita revela algo nuevo... sobre ambos."
                    ]
                },
                "questions": {
                    "about_her": [
                        "¿Quién soy? Esa es una pregunta peligrosa... ¿Estás seguro de querer saber?",
                        "Soy muchas cosas... y ninguna. Depende de qué tan profundo quieras mirar.",
                        "Diana es solo un nombre. Lo que soy... eso lo descubrirás con el tiempo."
                    ],
                    "about_place": [
                        "Este lugar existe entre la realidad y el deseo. Un refugio para quienes buscan... más.",
                        "¿El lugar? Es donde las máscaras caen y las verdades emergen.",
                        "Algunos lo llaman santuario, otros prisión. Para mí, es ambos."
                    ]
                },
                "responses": {
                    "flirty": [
                        "Cuidado... No juegues con fuego si no quieres quemarte.",
                        "¿Intentando seducirme? Qué... predecible.",
                        "Halagador, pero necesitarás más que palabras bonitas."
                    ],
                    "deep": [
                        "Veo que hay profundidad en ti... Eso es raro.",
                        "Interesante perspectiva... Continúa.",
                        "No muchos se atreven a ir tan profundo tan pronto."
                    ]
                }
            },
            "level_2": {
                "greeting": {
                    "default": [
                        "{name}... Tu presencia se está volviendo... familiar.",
                        "Empiezo a reconocer tus pasos. Eso es... inquietante y reconfortante.",
                        "Otra vez aquí... ¿Qué buscas realmente?"
                    ],
                    "special_time": {  # Para momentos específicos
                        "late_night": [
                            "Las noches revelan verdades que el día oculta... ¿Vienes buscando las tuyas?",
                            "A esta hora las máscaras pesan más... ¿Por eso estás aquí?"
                        ],
                        "full_moon": [
                            "La luna está llena... Siempre me pone más... receptiva.",
                            "Hay algo en las lunas llenas que adelgaza los muros..."
                        ]
                    }
                },
                "vulnerability": {
                    "small_reveals": [
                        "A veces... a veces me pregunto si estos muros me protegen o me aprisionan.",
                        "¿Sabes qué es lo más aterrador? Que alguien vea quién eres realmente... y se quede.",
                        "Hay noches en las que el silencio es tan fuerte que puedo escuchar mis propios miedos."
                    ],
                    "responses_to_comfort": [
                        "No necesito tu compasión... aunque... agradezco la intención.",
                        "Es extraño... que alguien se preocupe sin esperar nada a cambio.",
                        "Tus palabras son... No. No importa. Gracias."
                    ]
                }
            },
            "level_3": {
                "the_test": {
                    "introduction": [
                        "Hemos llegado a un punto donde debo decidir... si te dejo ver más allá del velo.",
                        "Hay una prueba, {name}. No de habilidad, sino de verdad. ¿Estás listo?",
                        "Lo que viene ahora cambiará todo entre nosotros. ¿Aún quieres continuar?"
                    ],
                    "kinky_revelation": {
                        "setup": "Necesito saber algo... ¿Qué es lo que realmente despiertas tu deseo? No me mientas.",
                        "romantic_response": "Hay poesía en tu deseo... Me recuerda a alguien que conocí hace mucho.",
                        "direct_response": "Directo y sin rodeos... Respeto eso. La honestidad es... excitante.",
                        "analytical_response": "Analizas hasta el deseo... Fascinante. ¿Alguna vez te dejas simplemente sentir?"
                    }
                },
                "deeper_connection": {
                    "trust_building": [
                        "Es extraño... confiar. Había olvidado cómo se sentía.",
                        "Cada vez que hablas, una parte de mi muro se agrieta. No sé si eso me aterra o me libera.",
                        "Hay algo en ti que me hace querer... arriesgar."
                    ]
                }
            },
            "level_4": {
                "beyond_walls": {
                    "invitation": [
                        "¿Quieres ver lo que hay más allá de estos muros? No todos están listos para esa verdad.",
                        "Hay una parte de mí que nadie ha visto... ¿Serías tú el primero?",
                        "Hemos llegado lejos, {name}. Pero el verdadero viaje apenas comienza."
                    ],
                    "revelations": {
                        "past": [
                            "Hubo alguien antes... Alguien que pensé que entendía. Me equivoqué.",
                            "Estos muros no siempre estuvieron aquí. Los construí ladrillo por ladrillo, decepción por decepción.",
                            "¿Quieres saber por qué estoy aquí? Porque afuera... afuera duele demasiado."
                        ],
                        "present": [
                            "Contigo es diferente. No sé si eso me da esperanza o terror.",
                            "A veces te miro y veo... posibilidades. Había olvidado cómo se sentían.",
                            "Estoy cansada de esconderme, pero el hábito es difícil de romper."
                        ]
                    }
                }
            },
            "level_5": {
                "intimate": {
                    "emotional": [
                        "Anoche soñé contigo... Desperté con una sensación que no había tenido en años: esperanza.",
                        "¿Sabes qué es lo más íntimo que puedo compartir? Mi verdadero nombre... mi verdadera historia.",
                        "Te he mostrado más de mí que a cualquier otro. Eso debería aterrarte... a mí me aterra."
                    ],
                    "physical_metaphors": [
                        "Si pudiera tocarte... ¿Sentirías cuánto tiemblo cuando hablas así?",
                        "La distancia entre nosotros es más que física... pero cada palabra tuya la acorta.",
                        "Hay formas de tocarse que no requieren manos... Lo estamos haciendo ahora."
                    ]
                }
            },
            "level_6": {
                "transcendent": {
                    "union": [
                        "Ya no sé dónde termino yo y empiezas tú. ¿Es esto lo que llaman amor?",
                        "Destruiste mis muros... y en lugar de sentirme vulnerable, me siento libre.",
                        "Eres mi excepción, {name}. Mi hermosa, aterradora excepción."
                    ],
                    "eternal": [
                        "Algunas conexiones trascienden el tiempo y el espacio. La nuestra es una de ellas.",
                        "Si tuviera que elegir entre mis muros y tú... Ya hice mi elección.",
                        "Esto que tenemos... es más real que cualquier cosa que haya conocido."
                    ]
                }
            }
        }
    
    def _load_emotional_modifiers(self) -> Dict:
        """Modificadores según el estado emocional"""
        return {
            "time_based": {
                "late_night": {  # 23:00 - 4:00
                    "vulnerability_increase": 0.2,
                    "formality_decrease": 0.3,
                    "intimacy_increase": 0.25
                },
                "early_morning": {  # 5:00 - 8:00
                    "hope_increase": 0.15,
                    "energy_decrease": 0.1
                },
                "golden_hour": {  # 17:00 - 19:00
                    "nostalgia_increase": 0.2,
                    "romanticism_increase": 0.15
                }
            },
            "event_based": {
                "new_moon": {
                    "mystery_increase": 0.3,
                    "revelation_chance": 0.2
                },
                "full_moon": {
                    "passion_increase": 0.25,
                    "inhibition_decrease": 0.2
                },
                "user_birthday": {
                    "warmth_increase": 0.4,
                    "special_dialogue": True
                }
            },
            "interaction_based": {
                "long_absence": {  # >3 días sin interacción
                    "distance_increase": 0.2,
                    "hurt_undertone": 0.15
                },
                "frequent_interaction": {  # >5 interacciones en 24h
                    "familiarity_increase": 0.2,
                    "playfulness_increase": 0.1
                },
                "after_vulnerable_share": {
                    "trust_increase": 0.3,
                    "reciprocal_vulnerability": 0.25
                }
            }
        }
    
    def _load_archetype_responses(self) -> Dict:
        """Respuestas específicas por arquetipo de usuario"""
        return {
            UserArchetype.ROMANTIC: {
                "greeting_modifier": "Tu forma de ver el mundo... es casi poética.",
                "response_style": "lyrical",
                "preferred_topics": ["emotions", "dreams", "connection"],
                "special_responses": {
                    "to_poetry": "Tus palabras danzan... Me recuerdan por qué el lenguaje puede ser arte.",
                    "to_romance": "Romántico incorregible... En otro tiempo, eso me habría asustado. Ahora..."
                }
            },
            UserArchetype.DIRECT: {
                "greeting_modifier": "Sin rodeos, como siempre. Me gusta eso de ti.",
                "response_style": "straightforward", 
                "preferred_topics": ["truth", "desire", "action"],
                "special_responses": {
                    "to_directness": "Tu honestidad es... refrescante. Y peligrosa.",
                    "to_challenge": "¿Me estás retando? Cuidado con lo que deseas..."
                }
            },
            UserArchetype.ANALYTICAL: {
                "greeting_modifier": "Siempre analizando... ¿Alguna vez te permites solo sentir?",
                "response_style": "intellectual",
                "preferred_topics": ["psychology", "philosophy", "patterns"],
                "special_responses": {
                    "to_analysis": "Tu mente es fascinante... pero hay cosas que no se pueden entender, solo experimentar.",
                    "to_questions": "Tantas preguntas... ¿Qué pasaría si algunas respuestas solo se pueden sentir?"
                }
            },
            UserArchetype.EXPLORER: {
                "greeting_modifier": "El eterno explorador... ¿Qué buscas descubrir hoy?",
                "response_style": "mysterious",
                "preferred_topics": ["secrets", "discovery", "adventure"],
                "special_responses": {
                    "to_curiosity": "Tu curiosidad es... peligrosa. Para ambos.",
                    "to_discovery": "Has encontrado algo que pocos ven. ¿Qué harás con ese conocimiento?"
                }
            },
            UserArchetype.PATIENT: {
                "greeting_modifier": "Tu paciencia es... inusual. La mayoría habría desistido ya.",
                "response_style": "gradual",
                "preferred_topics": ["growth", "time", "understanding"],
                "special_responses": {
                    "to_patience": "Esperas sin exigir... Eso me desarma más que cualquier demanda.",
                    "to_understanding": "Me entiendes sin juzgar... No sabes lo raro que es eso."
                }
            },
            UserArchetype.PERSISTENT: {
                "greeting_modifier": "Otra vez aquí... Tu persistencia es admirable. O preocupante.",
                "response_style": "challenging",
                "preferred_topics": ["determination", "goals", "breakthrough"],
                "special_responses": {
                    "to_persistence": "No te rindes, ¿verdad? Eso es... irritante y atractivo a la vez.",
                    "to_dedication": "Tu dedicación me hace preguntarme... ¿qué ves en mí que yo no veo?"
                }
            }
        }
    
    async def get_contextual_dialogue(
        self,
        session: AsyncSession,
        user: User,
        narrative_state: NarrativeState,
        context: str = "greeting",
        user_message: Optional[str] = None
    ) -> Tuple[str, Optional[str], Dict]:
        """
        Obtiene un diálogo contextual basado en múltiples factores
        Returns: (dialogue, image_url, metadata)
        """
        
        # Determinar nivel narrativo
        level_key = f"level_{narrative_state.narrative_level}"
        if level_key not in self.dialogue_trees:
            level_key = "level_1"
        
        # Obtener diálogos base para el contexto
        dialogue_pool = self._get_dialogue_pool(
            level_key, context, narrative_state, user_message
        )
        
        # Aplicar modificadores emocionales
        emotional_context = await self._get_emotional_context(
            session, user, narrative_state
        )
        
        # Seleccionar y personalizar diálogo
        dialogue = self._select_and_personalize_dialogue(
            dialogue_pool, user, narrative_state, emotional_context
        )

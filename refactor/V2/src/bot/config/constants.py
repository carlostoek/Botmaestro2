"""Constantes para el bot."""

# Puntos (Besitos)
DEFAULT_POINTS_PER_MESSAGE = 1.0
DEFAULT_POINTS_PER_REACTION = 0.5
DEFAULT_POINTS_PER_POLL = 2.0
DEFAULT_POINTS_PER_DAILY_GIFT = 5.0
VIP_POINTS_MULTIPLIER = 1.5

# Relaciones
RELATIONSHIP_LEVELS = {
    1: {"name": "Desconocidos", "points": 0},
    2: {"name": "Conocidos", "points": 500},
    3: {"name": "Amigos", "points": 1500},
    4: {"name": "Buenos Amigos", "points": 3000},
    5: {"name": "Cercanos", "points": 5000},
    6: {"name": "Íntimos", "points": 8000},
    7: {"name": "Almas Gemelas", "points": 12000},
}

# Emociones
EMOTION_TYPES = [
    "joy", "trust", "fear", "sadness",
    "anger", "surprise", "anticipation", "disgust"
]

EMOTION_NAMES = {
    "joy": "Alegría",
    "trust": "Confianza",
    "fear": "Miedo",
    "sadness": "Tristeza",
    "anger": "Enojo",
    "surprise": "Sorpresa",
    "anticipation": "Anticipación",
    "disgust": "Disgusto",
}

# Tiempos
DAILY_GIFT_COOLDOWN_HOURS = 24
SESSION_TIMEOUT_MINUTES = 30
AUCTION_DURATION_HOURS = 48

# Mensajes
MAX_MESSAGE_LENGTH = 4096

# Niveles de usuario
USER_LEVELS = {
    1: {"name": "Novato", "points": 0},
    2: {"name": "Aprendiz", "points": 500},
    3: {"name": "Explorador", "points": 1000},
    4: {"name": "Aventurero", "points": 2000},
    5: {"name": "Héroe", "points": 3500},
    6: {"name": "Campeón", "points": 5500},
    7: {"name": "Leyenda", "points": 8000},
    8: {"name": "Mito", "points": 11000},
    9: {"name": "Semidiós", "points": 14500},
    10: {"name": "Cosmos", "points": 18500},
}

# Paths de comandos
COMMANDS = {
    "start": "Iniciar el bot",
    "help": "Mostrar ayuda",
    "menu": "Mostrar menú principal",
    "perfil": "Ver tu perfil",
    "mochila": "Ver tu inventario",
    "historia": "Continuar tu historia",
    "dailygift": "Reclamar tu regalo diario",
    "ruleta": "Girar la ruleta de la fortuna",
    "tienda": "Visitar la tienda",
    "misiones": "Ver misiones disponibles",
}

# Tipos de misiones
MISSION_TYPES = {
    "DAILY": "Diaria",
    "WEEKLY": "Semanal",
    "ONE_TIME": "Única",
    "EVENT": "Evento",
    "STORY": "Historia",
}

# Configuración de teclados
KEYBOARD_WIDTH = 2
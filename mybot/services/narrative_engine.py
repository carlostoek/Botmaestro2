from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

class TriggerType(Enum):
    POINTS_GAINED = "points_gained"         # Puntos ganados (acumulados por el usuario)
    LEVEL_UP = "level_up"                   # Subida de nivel del usuario
    MISSION_COMPLETED = "mission_completed" # Misión completada por el usuario
    REACTION = "reaction"                   # Reacción en canal dada por el usuario
    # Podemos agregar más tipos de disparador en el futuro, por ejemplo:
    POLL_ANSWERED = "poll_answered"         # Encuesta contestada (ejemplo para encuestas)
    # ... otros tipos de evento

@dataclass
class NarrativeEvent:
    """Evento de gamificación que podría disparar contenido narrativo."""
    user_id: int
    trigger_type: TriggerType
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class NarrativeEngine:
    def __init__(self, storyboard_service, point_service, mission_service,
                 lore_service, level_service, bot):
        """
        Inicializa el motor narrativo con referencias a servicios y al bot de Telegram.
        """
        self.storyboard_service = storyboard_service
        self.point_service = point_service
        self.mission_service = mission_service
        self.lore_service = lore_service
        self.level_service = level_service
        self.bot = bot  # Referencia al bot de Aiogram para enviar mensajes al usuario

        # Mapeo de tipos de disparador a métodos manejadores
        self.narrative_triggers = {
            TriggerType.POINTS_GAINED: self._handle_points_trigger,
            TriggerType.LEVEL_UP: self._handle_level_up_trigger,
            TriggerType.MISSION_COMPLETED: self._handle_mission_completed_trigger,
            TriggerType.REACTION: self._handle_reaction_trigger,
            TriggerType.POLL_ANSWERED: self._handle_poll_trigger  # opcional, para encuestas
        }

    async def process_event(self, event: NarrativeEvent):
        """Procesa un evento de gamificación y evalúa si debe disparar alguna escena narrativa."""
        # 1. Llamar al manejador específico del tipo de evento (si existe)
        handler = self.narrative_triggers.get(event.trigger_type)
        if handler:
            await handler(event)
        # 2. Verificar progreso narrativo general (escenas de la historia principal)
        await self._check_narrative_progression(event.user_id)

    # --- Métodos manejadores de cada tipo de evento ---

    async def _handle_points_trigger(self, event: NarrativeEvent):
        """Maneja eventos de puntos ganados por el usuario."""
        points_earned = event.data.get('points', 0)  # puntos ganados en esta acción
        if points_earned <= 0:
            return
        # Calcular puntos totales antes y después de este evento
        total_points = await self.point_service.get_user_points(event.user_id)
        previous_points = total_points - points_earned
        # Consultar condiciones de tipo 'points_gained' definidas en la base de datos
        conditions = await self.storyboard_service.get_conditions_by_type(TriggerType.POINTS_GAINED.value)
        for condition in conditions:
            # Suponemos que trigger_value es numérico (umbral de puntos alcanzado)
            try:
                threshold = int(condition.trigger_value)
            except ValueError:
                continue
            # Si el usuario acaba de cruzar el umbral (antes tenía menos, ahora tiene al menos el umbral)
            if previous_points < threshold <= total_points:
                await self._trigger_scene(event.user_id, condition.scene_id)
                # Asumimos una escena por umbral; salir después de mostrarla
                break

    async def _handle_level_up_trigger(self, event: NarrativeEvent):
        """Maneja eventos de subida de nivel."""
        old_level = event.data.get('old_level')
        new_level = event.data.get('new_level')
        if new_level is None or old_level is None:
            # Si no se proporcionan, obtener niveles directamente del servicio
            old_level = old_level or (new_level - 1 if new_level else await self.level_service.get_user_level(event.user_id) - 1)
            new_level = new_level or await self.level_service.get_user_level(event.user_id)
        # Consultar todas las condiciones de tipo 'level_up'
        conditions = await self.storyboard_service.get_conditions_by_type(TriggerType.LEVEL_UP.value)
        for condition in conditions:
            try:
                level_threshold = int(condition.trigger_value)
            except ValueError:
                continue
            # Verificar si el usuario acaba de alcanzar o superar el nivel indicado
            if old_level < level_threshold <= new_level:
                await self._trigger_scene(event.user_id, condition.scene_id)
                break

    async def _handle_mission_completed_trigger(self, event: NarrativeEvent):
        """Maneja eventos de misión completada."""
        mission_id = event.data.get('mission_id')
        if not mission_id:
            return
        # Buscar condición exacta de misión completada (trigger_value coincide con ID de misión)
        condition = await self.storyboard_service.get_condition(TriggerType.MISSION_COMPLETED.value, mission_id)
        if condition:
            await self._trigger_scene(event.user_id, condition.scene_id)

    async def _handle_reaction_trigger(self, event: NarrativeEvent):
        """Maneja eventos de reacción en un canal."""
        emoji = event.data.get('emoji')
        if not emoji:
            return
        # Buscar condición exacta de reacción (emoji específico)
        condition = await self.storyboard_service.get_condition(TriggerType.REACTION.value, emoji)
        if condition:
            await self._trigger_scene(event.user_id, condition.scene_id)

    async def _handle_poll_trigger(self, event: NarrativeEvent):
        """Maneja eventos de encuesta contestada (opcional, para futuros eventos)."""
        poll_id = event.data.get('poll_id')        # identificador de la encuesta (o pregunta)
        selected_option = event.data.get('option') # opción elegida, si aplica
        # **Ejemplo**: disparar escena si cierta encuesta fue contestada de forma particular
        if poll_id:
            condition_key = f"{poll_id}:{selected_option}" if selected_option else str(poll_id)
            condition = await self.storyboard_service.get_condition(TriggerType.POLL_ANSWERED.value, condition_key)
            if condition:
                await self._trigger_scene(event.user_id, condition.scene_id)

    # --- Métodos auxiliares internos ---

    async def _trigger_scene(self, user_id: int, scene_id: str):
        """
        Busca la escena por ID y la presenta al usuario si no la ha visto aún.
        """
        # Obtener datos completos de la escena
        scene = await self.storyboard_service.get_scene_by_id(scene_id)
        if scene is None:
            return  # Escena no encontrada
        # Verificar que el usuario no haya visto ya esta escena
        if await self._user_has_seen_scene(user_id, scene_id):
            return
        # Mostrar la escena al usuario
        await self._present_scene_to_user(user_id, scene)

    async def _check_narrative_progression(self, user_id: int):
        """
        Verifica si el usuario debe avanzar en la historia principal (siguiente escena del storyboard).
        Busca la siguiente escena disponible que el usuario no haya visto y cuya condición (si tiene) esté cumplida.
        """
        current_progress = await self._get_user_story_progress(user_id)
        # Obtener próximas escenas no vistas (ordenadas por orden/storyboard)
        next_scenes: List = await self.storyboard_service.get_available_scenes(user_id, current_progress)
        for scene in next_scenes:
            # Verificar condiciones específicas de la escena (si la escena tiene condiciones adicionales en storyboard_conditions)
            # En caso de usar condiciones integradas en la escena, implementar lógica similar a _evaluate_scene_conditions.
            # Aquí asumimos que si aparece en la lista es porque ya cumple condiciones o no tiene.
            if not await self._user_has_seen_scene(user_id, scene.scene_id):
                await self._present_scene_to_user(user_id, scene)
                break  # Mostrar solo una escena por evento (evita inundar al usuario)

    async def _present_scene_to_user(self, user_id: int, scene):
        """
        Marca la escena como vista por el usuario y envía el contenido narrativo al chat privado del usuario.
        """
        # Registrar en la base de datos que el usuario vio esta escena
        await self._update_user_story_progress(user_id, scene.scene_id)
        # Enviar el contenido de la escena al usuario via bot de Telegram
        # Formateamos el mensaje combinando personaje y diálogo, por ejemplo:
        message_text = f"**{scene.character}:** {scene.dialogue}"
        try:
            await self.bot.send_message(chat_id=user_id, text=message_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Error enviando escena {scene.scene_id} al usuario {user_id}: {e}")

    # --- Métodos de progreso/registro de usuario (interfaz con user_story_progress) ---

    async def _user_has_seen_scene(self, user_id: int, scene_id: str) -> bool:
        """Comprueba en la base de datos si el usuario ya vio la escena dada."""
        return await self.storyboard_service.user_has_seen_scene(user_id, scene_id)

    async def _update_user_story_progress(self, user_id: int, scene_id: str):
        """Inserta un registro indicando que el usuario ha visto la escena dada."""
        await self.storyboard_service.mark_scene_seen(user_id, scene_id)

    async def _get_user_story_progress(self, user_id: int) -> int:
        """
        Obtiene un indicador numérico del progreso narrativo del usuario (por ejemplo, el mayor `order_position` de escena vista).
        Si el usuario no ha visto escenas, devuelve 0.
        """
        return await self.storyboard_service.get_user_max_order(user_id)

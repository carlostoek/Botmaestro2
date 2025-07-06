# services/narrative/narrative_events.py
"""
Sistema de eventos narrativos especiales.
Gestiona eventos temporales como Luna Nueva, estaciones, etc.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import ephem
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from aiogram import Bot

from database.narrative_models import (
    NarrativeEvent, UserNarrativeEvent,
    NarrativeState
)
from database.models import User
from utils.config import CHANNEL_ID, VIP_CHANNEL_ID

class NarrativeEventManager:
    """Gestiona eventos narrativos especiales y temporales"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_events: Dict[str, NarrativeEvent] = {}
    
    async def check_and_activate_events(self, session: AsyncSession):
        """Verifica y activa eventos según sus condiciones"""
        
        # Obtener todos los eventos activos
        result = await session.execute(
            select(NarrativeEvent).filter(NarrativeEvent.is_active == True)
        )
        events = result.scalars().all()
        
        for event in events:
            should_activate = await self._check_event_conditions(event)
            
            if should_activate and event.id not in self.active_events:
                await self._activate_event(session, event)
            elif not should_activate and event.id in self.active_events:
                await self._deactivate_event(session, event)
    
    async def _check_event_conditions(self, event: NarrativeEvent) -> bool:
        """Verifica si se cumplen las condiciones para activar un evento"""
        
        conditions = event.trigger_conditions
        event_type = conditions.get("type")
        
        if event_type == "lunar":
            return self._check_lunar_condition(conditions)
        elif event_type == "date":
            return self._check_date_condition(conditions)
        elif event_type == "seasonal":
            return self._check_seasonal_condition(conditions)
        elif event_type == "relationship":
            # Este se verifica por usuario, no globalmente
            return False
        
        return False
    
    def _check_lunar_condition(self, conditions: Dict) -> bool:
        """Verifica condiciones lunares"""
        
        required_phase = conditions.get("phase", "new_moon")
        
        # Calcular fase lunar actual
        moon = ephem.Moon()
        moon.compute()
        
        # Convertir a días desde luna nueva
        phase_days = moon.phase / 100 * 29.53  # Ciclo lunar en días
        
        # Mapeo de fases
        phases = {
            "new_moon": (0, 2),
            "waxing_crescent": (2, 7),
            "first_quarter": (7, 9),
            "waxing_gibbous": (9, 14),
            "full_moon": (14, 16),
            "waning_gibbous": (16, 21),
            "last_quarter": (21, 23),
            "waning_crescent": (23, 29.53)
        }
        
        if required_phase in phases:
            min_day, max_day = phases[required_phase]
            return min_day <= phase_days <= max_day
        
        return False
    
    def _check_date_condition(self, conditions: Dict) -> bool:
        """Verifica condiciones de fecha específica"""
        
        dates = conditions.get("dates", [])
        today = datetime.now().strftime("%d-%m")
        
        return today in dates
    
    def _check_seasonal_condition(self, conditions: Dict) -> bool:
        """Verifica condiciones estacionales"""
        
        season = conditions.get("season")
        month = datetime.now().month
        
        seasons = {
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "autumn": [9, 10, 11],
            "winter": [12, 1, 2]
        }
        
        if season in seasons:
            return month in seasons[season]
        
        return False
    
    async def _activate_event(
        self,
        session: AsyncSession,
        event: NarrativeEvent
    ):
        """Activa un evento narrativo"""
        
        self.active_events[event.id] = event
        
        # Actualizar estadísticas del evento
        event.times_occurred += 1
        event.last_occurred = datetime.utcnow()
        await session.commit()
        
        # Anunciar en canales apropiados
        announcement = f"""
🌙 <b>Evento Especial: {event.name}</b>

<i>{event.description}</i>

{event.announcement_message}

⏰ <b>Duración:</b> {event.duration_hours} horas
✨ <b>Recompensas especiales disponibles</b>
"""
        
        channels = [CHANNEL_ID]
        if not event.vip_exclusive:
            channels.append(VIP_CHANNEL_ID)
        
        for channel_id in channels:
            try:
                await self.bot.send_message(
                    channel_id,
                    announcement,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Error anunciando evento en {channel_id}: {e}")
    
    async def _deactivate_event(
        self,
        session: AsyncSession,
        event: NarrativeEvent
    ):
        """Desactiva un evento narrativo"""
        
        if event.id in self.active_events:
            del self.active_events[event.id]
        
        # Anunciar fin del evento
        announcement = f"""
🌙 <b>Evento Finalizado: {event.name}</b>

El evento especial ha terminado. 
¡Gracias a todos los que participaron!

Nos vemos en el próximo evento... 🌟
"""
        
        channels = [CHANNEL_ID]
        if not event.vip_exclusive:
            channels.append(VIP_CHANNEL_ID)
        
        for channel_id in channels:
            try:
                await self.bot.send_message(
                    channel_id,
                    announcement,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Error anunciando fin de evento en {channel_id}: {e}")
    
    async def check_user_special_events(
        self,
        session: AsyncSession,
        user: User,
        narrative_state: NarrativeState
    ) -> List[NarrativeEvent]:
        """Verifica eventos especiales disponibles para un usuario específico"""
        
        available_events = []
        
        for event_id, event in self.active_events.items():
            # Verificar requisitos mínimos
            if user.level < event.min_level_required:
                continue
            
            if narrative_state.trust_level < event.min_trust_required:
                continue
            
            # Verificar si es exclusivo VIP
            if event.vip_exclusive and user.role != "vip":
                continue
            
            # Verificar condiciones específicas de relación
            if event.trigger_conditions.get("type") == "relationship":
                rel_conditions = event.trigger_conditions
                required_stage = rel_conditions.get("stage")
                required_trust = rel_conditions.get("trust", 0)
                
                if required_stage and narrative_state.relationship_stage.value != required_stage:
                    continue
                
                if narrative_state.trust_level < required_trust:
                    continue
            
            available_events.append(event)
        
        return available_events
    
    async def participate_in_event(
        self,
        session: AsyncSession,
        user: User,
        event: NarrativeEvent
    ) -> UserNarrativeEvent:
        """Registra la participación de un usuario en un evento"""
        
        # Buscar participación existente
        result = await session.execute(
            select(UserNarrativeEvent).filter(
                and_(
                    UserNarrativeEvent.user_id == user.id,
                    UserNarrativeEvent.event_id == event.id
                )
            )
        )
        participation = result.scalar_one_or_none()
        
        if not participation:
            participation = UserNarrativeEvent(
                user_id=user.id,
                event_id=event.id
            )
            session.add(participation)
        else:
            participation.times_participated += 1
            participation.last_participated = datetime.utcnow()
        
        await session.commit()
        return participation
    
    async def unlock_event_letter(
        self,
        session: AsyncSession,
        user: User,
        event: NarrativeEvent
    ) -> Optional[UnsentLetter]:
        """Desbloquea una carta especial durante un evento"""
        
        # Buscar cartas asociadas al evento
        result = await session.execute(
            select(UnsentLetter).filter(
                UnsentLetter.trigger_event == f"event_{event.id}"
            )
        )
        letters = result.scalars().all()
        
        if not letters:
            return None
        
        # Seleccionar carta apropiada según el perfil del usuario
        narrative_state = await session.get(NarrativeState, user.id)
        
        best_letter = None
        for letter in letters:
            # Verificar requisitos
            if narrative_state.trust_level < letter.min_trust_required:
                continue
            
            if user.level < letter.min_level_required:
                continue
            
            # Bonus por arquetipo
            if (letter.specific_archetype_bonus and 
                narrative_state.user_archetype.value == letter.specific_archetype_bonus):
                return letter  # Prioridad máxima
            
            if not best_letter:
                best_letter = letter
        
        return best_letter

# Scheduler para eventos narrativos
async def narrative_event_scheduler(bot: Bot, Session):
    """Scheduler que verifica y gestiona eventos narrativos"""
    
    event_manager = NarrativeEventManager(bot)
    
    while True:
        try:
            async with Session() as session:
                await event_manager.check_and_activate_events(session)
            
            # Verificar cada hora
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"Error en narrative event scheduler: {e}")
            await asyncio.sleep(60)  # Esperar 1 minuto en caso de error
          

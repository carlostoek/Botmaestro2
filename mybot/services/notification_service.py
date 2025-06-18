"""
Servicio de notificaciones para el sistema.
Maneja notificaciones push, recordatorios y alertas del sistema.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database.models import User, Auction, AuctionParticipant
from services.config_service import ConfigService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio centralizado para el manejo de notificaciones.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.config_service = ConfigService(session)
    
    async def send_notification(
        self,
        user_id: int,
        message: str,
        parse_mode: str = "Markdown",
        disable_notification: bool = False
    ) -> bool:
        """
        Enviar notificación a un usuario específico.
        
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )
            logger.info(f"Notification sent to user {user_id}")
            return True
        except TelegramForbiddenError:
            logger.warning(f"User {user_id} has blocked the bot")
            return False
        except TelegramBadRequest as e:
            logger.error(f"Bad request sending notification to {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending notification to {user_id}: {e}")
            return False
    
    async def send_bulk_notification(
        self,
        user_ids: List[int],
        message: str,
        parse_mode: str = "Markdown",
        batch_size: int = 30,
        delay_between_batches: float = 1.0
    ) -> Dict[str, int]:
        """
        Enviar notificaciones masivas con control de rate limiting.
        
        Returns:
            Dict con estadísticas de envío
        """
        stats = {"sent": 0, "failed": 0, "blocked": 0}
        
        # Procesar en lotes para evitar rate limiting
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            
            # Enviar notificaciones del lote actual
            tasks = []
            for user_id in batch:
                task = self.send_notification(user_id, message, parse_mode, disable_notification=True)
                tasks.append(task)
            
            # Esperar resultados del lote
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in results:
                if isinstance(result, bool):
                    if result:
                        stats["sent"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
            
            # Pausa entre lotes
            if i + batch_size < len(user_ids):
                await asyncio.sleep(delay_between_batches)
        
        logger.info(f"Bulk notification completed: {stats}")
        return stats
    
    async def send_vip_expiry_reminders(self) -> int:
        """
        Enviar recordatorios de expiración VIP.
        
        Returns:
            int: Número de recordatorios enviados
        """
        now = datetime.utcnow()
        remind_threshold = now + timedelta(hours=24)
        
        # Obtener mensaje personalizado
        reminder_msg = await self.config_service.get_value("vip_reminder_message")
        if not reminder_msg:
            reminder_msg = (
                "⚠️ **Recordatorio VIP**\n\n"
                "Tu suscripción VIP expira en menos de 24 horas.\n"
                "¡Renueva ahora para no perder el acceso a las funciones premium!"
            )
        
        # Buscar usuarios que necesitan recordatorio
        stmt = select(User).where(
            User.role == "vip",
            User.vip_expires_at <= remind_threshold,
            User.vip_expires_at > now,
            (User.last_reminder_sent_at.is_(None)) |
            (User.last_reminder_sent_at <= now - timedelta(hours=24))
        )
        
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        sent_count = 0
        for user in users:
            if await self.send_notification(user.id, reminder_msg):
                user.last_reminder_sent_at = now
                sent_count += 1
        
        if sent_count > 0:
            await self.session.commit()
            logger.info(f"Sent {sent_count} VIP expiry reminders")
        
        return sent_count
    
    async def send_auction_notifications(
        self,
        auction: Auction,
        notification_type: str,
        exclude_user_id: Optional[int] = None,
        **kwargs
    ) -> int:
        """
        Enviar notificaciones relacionadas con subastas.
        
        Args:
            auction: La subasta relacionada
            notification_type: Tipo de notificación ('new_bid', 'ending_soon', 'ended')
            exclude_user_id: ID de usuario a excluir (ej: el que hizo la puja)
            **kwargs: Parámetros adicionales para el mensaje
        
        Returns:
            int: Número de notificaciones enviadas
        """
        # Obtener participantes con notificaciones habilitadas
        stmt = select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction.id,
            AuctionParticipant.notifications_enabled == True
        )
        
        if exclude_user_id:
            stmt = stmt.where(AuctionParticipant.user_id != exclude_user_id)
        
        result = await self.session.execute(stmt)
        participants = result.scalars().all()
        
        if not participants:
            return 0
        
        # Generar mensaje según el tipo
        message = await self._generate_auction_message(auction, notification_type, **kwargs)
        
        # Enviar notificaciones
        user_ids = [p.user_id for p in participants]
        stats = await self.send_bulk_notification(user_ids, message)
        
        # Actualizar timestamp de última notificación
        now = datetime.utcnow()
        for participant in participants:
            participant.last_notified_at = now
        
        await self.session.commit()
        
        return stats["sent"]
    
    async def _generate_auction_message(
        self,
        auction: Auction,
        notification_type: str,
        **kwargs
    ) -> str:
        """Generar mensaje de notificación para subastas."""
        if notification_type == "new_bid":
            bidder_name = kwargs.get("bidder_name", "Alguien")
            amount = kwargs.get("amount", 0)
            time_remaining = kwargs.get("time_remaining", "")
            
            return (
                f"🔔 **Nueva puja en '{auction.name}'**\n\n"
                f"💰 Puja actual: {amount} puntos\n"
                f"👤 Pujador: {bidder_name}\n"
                f"⏰ Tiempo restante: {time_remaining}\n\n"
                f"¡Haz tu puja para no perder la oportunidad!"
            )
        
        elif notification_type == "ending_soon":
            time_remaining = kwargs.get("time_remaining", "")
            current_bid = auction.current_highest_bid or auction.initial_price
            
            return (
                f"⏰ **¡Subasta terminando pronto!**\n\n"
                f"🏛️ **Subasta:** {auction.name}\n"
                f"💰 **Puja actual:** {current_bid} puntos\n"
                f"⏰ **Tiempo restante:** {time_remaining}\n\n"
                f"¡Última oportunidad para pujar!"
            )
        
        elif notification_type == "ended":
            winner_name = kwargs.get("winner_name", "Nadie")
            winning_bid = auction.current_highest_bid or 0
            
            return (
                f"🏁 **Subasta finalizada: '{auction.name}'**\n\n"
                f"🏆 **Ganador:** {winner_name}\n"
                f"💰 **Puja ganadora:** {winning_bid} puntos\n"
                f"🎁 **Premio:** {auction.prize_description}"
            )
        
        elif notification_type == "cancelled":
            return (
                f"❌ **Subasta cancelada: '{auction.name}'**\n\n"
                f"La subasta ha sido cancelada por el administrador.\n"
                f"Disculpa las molestias."
            )
        
        else:
            return f"📢 Notificación sobre la subasta '{auction.name}'"
    
    async def send_system_announcement(
        self,
        message: str,
        target_role: str = "all",
        exclude_blocked: bool = True
    ) -> Dict[str, int]:
        """
        Enviar anuncio del sistema a usuarios.
        
        Args:
            message: Mensaje a enviar
            target_role: Rol objetivo ('all', 'vip', 'free', 'admin')
            exclude_blocked: Si excluir usuarios que han bloqueado el bot
        
        Returns:
            Dict con estadísticas de envío
        """
        # Construir query según el rol objetivo
        stmt = select(User.id)
        
        if target_role == "vip":
            stmt = stmt.where(User.role == "vip")
        elif target_role == "free":
            stmt = stmt.where(User.role == "free")
        elif target_role == "admin":
            stmt = stmt.where(User.role == "admin")
        # 'all' no necesita filtro adicional
        
        result = await self.session.execute(stmt)
        user_ids = [row[0] for row in result.all()]
        
        if not user_ids:
            return {"sent": 0, "failed": 0, "blocked": 0}
        
        # Enviar anuncio
        announcement_text = f"📢 **Anuncio del Sistema**\n\n{message}"
        stats = await self.send_bulk_notification(user_ids, announcement_text)
        
        logger.info(f"System announcement sent to {target_role}: {stats}")
        return stats
    
    async def send_achievement_notification(
        self,
        user_id: int,
        achievement_name: str,
        achievement_description: str = ""
    ) -> bool:
        """Enviar notificación de logro desbloqueado."""
        message = (
            f"🏆 **¡Logro Desbloqueado!**\n\n"
            f"🎉 **{achievement_name}**\n"
        )
        
        if achievement_description:
            message += f"\n📝 {achievement_description}"
        
        message += "\n\n¡Sigue así para desbloquear más logros!"
        
        return await self.send_notification(user_id, message)
    
    async def send_level_up_notification(
        self,
        user_id: int,
        new_level: int,
        level_name: str,
        reward: str = ""
    ) -> bool:
        """Enviar notificación de subida de nivel."""
        message = (
            f"🎉 **¡Subiste de Nivel!**\n\n"
            f"🆙 **Nuevo Nivel:** {new_level} - {level_name}\n"
        )
        
        if reward:
            message += f"🎁 **Recompensa:** {reward}\n"
        
        message += "\n¡Continúa participando para seguir subiendo!"
        
        return await self.send_notification(user_id, message)
    
    async def send_mission_completion_notification(
        self,
        user_id: int,
        mission_name: str,
        points_earned: int
    ) -> bool:
        """Enviar notificación de misión completada."""
        message = (
            f"✅ **¡Misión Completada!**\n\n"
            f"🎯 **Misión:** {mission_name}\n"
            f"💎 **Puntos ganados:** {points_earned}\n\n"
            f"¡Excelente trabajo! Sigue completando misiones para ganar más puntos."
        )
        
        return await self.send_notification(user_id, message)
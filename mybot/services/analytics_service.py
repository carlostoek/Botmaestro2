"""
Servicio de analíticas y métricas del sistema.
Proporciona insights sobre el uso del bot y engagement de usuarios.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from database.models import (
    User, UserProgress, Mission, UserMission, Auction, Bid,
    VipSubscription, ButtonReaction, UserReward, UserBadge
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Servicio para generar analíticas y métricas del sistema.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_engagement_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtener métricas de engagement de usuarios.
        
        Args:
            days: Número de días hacia atrás para analizar
        
        Returns:
            Dict con métricas de engagement
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Usuarios activos (con actividad reciente)
        active_users_stmt = select(func.count(User.id)).where(
            User.id.in_(
                select(UserProgress.user_id).where(
                    UserProgress.last_activity_at >= cutoff_date
                )
            )
        )
        active_users_result = await self.session.execute(active_users_stmt)
        active_users = active_users_result.scalar() or 0
        
        # Total de usuarios
        total_users_stmt = select(func.count(User.id))
        total_users_result = await self.session.execute(total_users_stmt)
        total_users = total_users_result.scalar() or 0
        
        # Usuarios VIP activos
        vip_users_stmt = select(func.count(User.id)).where(
            User.role == "vip",
            or_(
                User.vip_expires_at.is_(None),
                User.vip_expires_at > datetime.utcnow()
            )
        )
        vip_users_result = await self.session.execute(vip_users_stmt)
        vip_users = vip_users_result.scalar() or 0
        
        # Misiones completadas en el período
        missions_completed_stmt = select(func.count(UserMission.id)).where(
            UserMission.completed == True,
            UserMission.completed_at >= cutoff_date
        )
        missions_result = await self.session.execute(missions_completed_stmt)
        missions_completed = missions_result.scalar() or 0
        
        # Reacciones en el período
        reactions_stmt = select(func.count(ButtonReaction.id)).where(
            ButtonReaction.created_at >= cutoff_date
        )
        reactions_result = await self.session.execute(reactions_stmt)
        reactions_count = reactions_result.scalar() or 0
        
        # Calcular tasas
        engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
        vip_conversion_rate = (vip_users / total_users * 100) if total_users > 0 else 0
        
        return {
            "period_days": days,
            "total_users": total_users,
            "active_users": active_users,
            "vip_users": vip_users,
            "engagement_rate": round(engagement_rate, 2),
            "vip_conversion_rate": round(vip_conversion_rate, 2),
            "missions_completed": missions_completed,
            "reactions_count": reactions_count,
            "avg_missions_per_active_user": round(missions_completed / active_users, 2) if active_users > 0 else 0
        }
    
    async def get_gamification_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema de gamificación."""
        
        # Distribución de puntos
        points_stats_stmt = select(
            func.avg(User.points).label('avg_points'),
            func.max(User.points).label('max_points'),
            func.min(User.points).label('min_points'),
            func.count(User.id).label('total_users')
        ).where(User.points > 0)
        
        points_result = await self.session.execute(points_stats_stmt)
        points_stats = points_result.first()
        
        # Distribución de niveles
        level_distribution_stmt = select(
            User.level,
            func.count(User.id).label('user_count')
        ).group_by(User.level).order_by(User.level)
        
        level_result = await self.session.execute(level_distribution_stmt)
        level_distribution = {row.level: row.user_count for row in level_result.all()}
        
        # Misiones más populares
        popular_missions_stmt = select(
            Mission.name,
            func.count(UserMission.id).label('completion_count')
        ).join(
            UserMission, Mission.id == UserMission.mission_id
        ).where(
            UserMission.completed == True
        ).group_by(Mission.id, Mission.name).order_by(
            desc('completion_count')
        ).limit(10)
        
        popular_missions_result = await self.session.execute(popular_missions_stmt)
        popular_missions = [
            {"name": row.name, "completions": row.completion_count}
            for row in popular_missions_result.all()
        ]
        
        # Recompensas más reclamadas
        popular_rewards_stmt = select(
            func.count(UserReward.reward_id).label('claim_count')
        ).group_by(UserReward.reward_id).order_by(desc('claim_count')).limit(5)
        
        popular_rewards_result = await self.session.execute(popular_rewards_stmt)
        total_reward_claims = sum(row.claim_count for row in popular_rewards_result.all())
        
        # Insignias otorgadas
        badges_awarded_stmt = select(func.count(UserBadge.id))
        badges_result = await self.session.execute(badges_awarded_stmt)
        badges_awarded = badges_result.scalar() or 0
        
        return {
            "points_stats": {
                "average": round(points_stats.avg_points or 0, 2),
                "maximum": points_stats.max_points or 0,
                "minimum": points_stats.min_points or 0,
                "active_users": points_stats.total_users or 0
            },
            "level_distribution": level_distribution,
            "popular_missions": popular_missions,
            "total_reward_claims": total_reward_claims,
            "badges_awarded": badges_awarded
        }
    
    async def get_auction_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Obtener métricas del sistema de subastas."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Subastas en el período
        auctions_stmt = select(func.count(Auction.id)).where(
            Auction.created_at >= cutoff_date
        )
        auctions_result = await self.session.execute(auctions_stmt)
        total_auctions = auctions_result.scalar() or 0
        
        # Subastas completadas
        completed_auctions_stmt = select(func.count(Auction.id)).where(
            Auction.created_at >= cutoff_date,
            Auction.status == 'ended'
        )
        completed_result = await self.session.execute(completed_auctions_stmt)
        completed_auctions = completed_result.scalar() or 0
        
        # Total de pujas
        bids_stmt = select(func.count(Bid.id)).where(
            Bid.timestamp >= cutoff_date
        )
        bids_result = await self.session.execute(bids_stmt)
        total_bids = bids_result.scalar() or 0
        
        # Puntos en circulación (pujas totales)
        points_circulation_stmt = select(func.sum(Bid.amount)).where(
            Bid.timestamp >= cutoff_date
        )
        points_result = await self.session.execute(points_circulation_stmt)
        points_in_circulation = points_result.scalar() or 0
        
        # Participantes únicos
        unique_participants_stmt = select(func.count(func.distinct(Bid.user_id))).where(
            Bid.timestamp >= cutoff_date
        )
        participants_result = await self.session.execute(unique_participants_stmt)
        unique_participants = participants_result.scalar() or 0
        
        # Promedio de pujas por subasta
        avg_bids_per_auction = (total_bids / total_auctions) if total_auctions > 0 else 0
        
        # Tasa de finalización
        completion_rate = (completed_auctions / total_auctions * 100) if total_auctions > 0 else 0
        
        return {
            "period_days": days,
            "total_auctions": total_auctions,
            "completed_auctions": completed_auctions,
            "completion_rate": round(completion_rate, 2),
            "total_bids": total_bids,
            "unique_participants": unique_participants,
            "points_in_circulation": points_in_circulation,
            "avg_bids_per_auction": round(avg_bids_per_auction, 2),
            "avg_points_per_bid": round(points_in_circulation / total_bids, 2) if total_bids > 0 else 0
        }
    
    async def get_revenue_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de ingresos y suscripciones."""
        
        # Suscripciones totales
        total_subs_stmt = select(func.count(VipSubscription.user_id))
        total_subs_result = await self.session.execute(total_subs_stmt)
        total_subscriptions = total_subs_result.scalar() or 0
        
        # Suscripciones activas
        now = datetime.utcnow()
        active_subs_stmt = select(func.count(VipSubscription.user_id)).where(
            or_(
                VipSubscription.expires_at.is_(None),
                VipSubscription.expires_at > now
            )
        )
        active_subs_result = await self.session.execute(active_subs_stmt)
        active_subscriptions = active_subs_result.scalar() or 0
        
        # Suscripciones que expiran pronto (próximos 7 días)
        expiring_soon_stmt = select(func.count(VipSubscription.user_id)).where(
            VipSubscription.expires_at.between(now, now + timedelta(days=7))
        )
        expiring_result = await self.session.execute(expiring_soon_stmt)
        expiring_soon = expiring_result.scalar() or 0
        
        # Tasa de retención (aproximada)
        retention_rate = (active_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
        
        # Crecimiento mensual (últimos 30 días)
        monthly_cutoff = now - timedelta(days=30)
        monthly_growth_stmt = select(func.count(VipSubscription.user_id)).where(
            VipSubscription.created_at >= monthly_cutoff
        )
        monthly_result = await self.session.execute(monthly_growth_stmt)
        monthly_new_subs = monthly_result.scalar() or 0
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "expiring_soon": expiring_soon,
            "retention_rate": round(retention_rate, 2),
            "monthly_new_subscriptions": monthly_new_subs,
            "churn_risk": expiring_soon  # Usuarios en riesgo de cancelar
        }
    
    async def get_top_users(self, metric: str = "points", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener top usuarios según diferentes métricas.
        
        Args:
            metric: Métrica para ordenar ('points', 'level', 'missions_completed')
            limit: Número de usuarios a retornar
        """
        if metric == "points":
            stmt = select(User.id, User.username, User.first_name, User.points, User.level).order_by(
                desc(User.points)
            ).limit(limit)
        elif metric == "level":
            stmt = select(User.id, User.username, User.first_name, User.points, User.level).order_by(
                desc(User.level), desc(User.points)
            ).limit(limit)
        elif metric == "missions_completed":
            stmt = select(
                User.id, User.username, User.first_name, User.points, User.level,
                func.count(UserMission.id).label('missions_count')
            ).join(
                UserMission, User.id == UserMission.user_id
            ).where(
                UserMission.completed == True
            ).group_by(
                User.id, User.username, User.first_name, User.points, User.level
            ).order_by(
                desc('missions_count')
            ).limit(limit)
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        result = await self.session.execute(stmt)
        users = []
        
        for row in result.all():
            user_data = {
                "user_id": row.id,
                "username": row.username,
                "display_name": row.first_name or row.username or f"User {row.id}",
                "points": row.points,
                "level": row.level
            }
            
            if metric == "missions_completed":
                user_data["missions_completed"] = row.missions_count
            
            users.append(user_data)
        
        return users
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """Generar reporte diario completo."""
        
        # Obtener todas las métricas
        engagement = await self.get_user_engagement_metrics(days=1)
        gamification = await self.get_gamification_metrics()
        auctions = await self.get_auction_metrics(days=1)
        revenue = await self.get_revenue_metrics()
        
        # Top usuarios
        top_by_points = await self.get_top_users("points", 5)
        top_by_missions = await self.get_top_users("missions_completed", 5)
        
        return {
            "report_date": datetime.utcnow().isoformat(),
            "engagement_metrics": engagement,
            "gamification_metrics": gamification,
            "auction_metrics": auctions,
            "revenue_metrics": revenue,
            "top_users": {
                "by_points": top_by_points,
                "by_missions": top_by_missions
            }
        }
    
    async def get_user_activity_timeline(
        self, 
        user_id: int, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtener timeline de actividad de un usuario específico.
        
        Args:
            user_id: ID del usuario
            days: Días hacia atrás para analizar
        
        Returns:
            Lista de eventos de actividad
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        timeline = []
        
        # Misiones completadas
        missions_stmt = select(
            UserMission.completed_at,
            Mission.name,
            Mission.reward_points
        ).join(
            Mission, UserMission.mission_id == Mission.id
        ).where(
            UserMission.user_id == user_id,
            UserMission.completed == True,
            UserMission.completed_at >= cutoff_date
        ).order_by(desc(UserMission.completed_at))
        
        missions_result = await self.session.execute(missions_stmt)
        for row in missions_result.all():
            timeline.append({
                "timestamp": row.completed_at,
                "type": "mission_completed",
                "description": f"Completó misión: {row.name}",
                "points": row.reward_points
            })
        
        # Pujas en subastas
        bids_stmt = select(
            Bid.timestamp,
            Bid.amount,
            Auction.name
        ).join(
            Auction, Bid.auction_id == Auction.id
        ).where(
            Bid.user_id == user_id,
            Bid.timestamp >= cutoff_date
        ).order_by(desc(Bid.timestamp))
        
        bids_result = await self.session.execute(bids_stmt)
        for row in bids_result.all():
            timeline.append({
                "timestamp": row.timestamp,
                "type": "auction_bid",
                "description": f"Pujó {row.amount} puntos en '{row.name}'",
                "points": -row.amount  # Puntos gastados
            })
        
        # Ordenar timeline por timestamp
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return timeline
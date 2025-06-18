"""
Handlers para el sistema de analíticas del administrador.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.admin_analytics_kb import (
    get_admin_analytics_main_kb,
    get_analytics_period_kb,
    get_top_users_metric_kb,
    get_analytics_back_kb
)
from services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_analytics")
async def admin_analytics_main(callback: CallbackQuery, session: AsyncSession):
    """Menú principal de analíticas."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await update_menu(
        callback,
        "📊 **Centro de Analíticas**\n\n"
        "Obtén insights detallados sobre el rendimiento de tu bot y el engagement de usuarios.",
        get_admin_analytics_main_kb(),
        session,
        "admin_analytics"
    )
    await callback.answer()


@router.callback_query(F.data == "analytics_engagement")
async def show_engagement_metrics(callback: CallbackQuery, session: AsyncSession):
    """Mostrar métricas de engagement."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        analytics_service = AnalyticsService(session)
        metrics = await analytics_service.get_user_engagement_metrics(days=30)
        
        text = (
            f"📈 **Métricas de Engagement (30 días)**\n\n"
            f"👥 **Usuarios totales:** {metrics['total_users']}\n"
            f"🔥 **Usuarios activos:** {metrics['active_users']}\n"
            f"💎 **Usuarios VIP:** {metrics['vip_users']}\n"
            f"📊 **Tasa de engagement:** {metrics['engagement_rate']}%\n"
            f"💰 **Tasa de conversión VIP:** {metrics['vip_conversion_rate']}%\n\n"
            f"🎯 **Actividad:**\n"
            f"• Misiones completadas: {metrics['missions_completed']}\n"
            f"• Reacciones: {metrics['reactions_count']}\n"
            f"• Promedio misiones/usuario: {metrics['avg_missions_per_active_user']}\n"
        )
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            "analytics_engagement"
        )
    except Exception as e:
        logger.error(f"Error showing engagement metrics: {e}")
        await callback.answer("Error al cargar métricas", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "analytics_gamification")
async def show_gamification_metrics(callback: CallbackQuery, session: AsyncSession):
    """Mostrar métricas de gamificación."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        analytics_service = AnalyticsService(session)
        metrics = await analytics_service.get_gamification_metrics()
        
        points_stats = metrics['points_stats']
        level_dist = metrics['level_distribution']
        popular_missions = metrics['popular_missions']
        
        text = (
            f"🎮 **Métricas de Gamificación**\n\n"
            f"💎 **Estadísticas de Puntos:**\n"
            f"• Promedio: {points_stats['average']} pts\n"
            f"• Máximo: {points_stats['maximum']} pts\n"
            f"• Usuarios activos: {points_stats['active_users']}\n\n"
            f"📊 **Distribución de Niveles:**\n"
        )
        
        # Mostrar top 5 niveles más populares
        sorted_levels = sorted(level_dist.items(), key=lambda x: x[1], reverse=True)[:5]
        for level, count in sorted_levels:
            text += f"• Nivel {level}: {count} usuarios\n"
        
        text += f"\n🎯 **Misiones Populares:**\n"
        for mission in popular_missions[:5]:
            text += f"• {mission['name']}: {mission['completions']} completadas\n"
        
        text += f"\n🏅 **Insignias otorgadas:** {metrics['badges_awarded']}\n"
        text += f"🎁 **Recompensas reclamadas:** {metrics['total_reward_claims']}"
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            "analytics_gamification"
        )
    except Exception as e:
        logger.error(f"Error showing gamification metrics: {e}")
        await callback.answer("Error al cargar métricas", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "analytics_auctions")
async def show_auction_metrics(callback: CallbackQuery, session: AsyncSession):
    """Mostrar métricas de subastas."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        analytics_service = AnalyticsService(session)
        metrics = await analytics_service.get_auction_metrics(days=30)
        
        text = (
            f"🏛️ **Métricas de Subastas (30 días)**\n\n"
            f"📊 **Estadísticas generales:**\n"
            f"• Total de subastas: {metrics['total_auctions']}\n"
            f"• Subastas completadas: {metrics['completed_auctions']}\n"
            f"• Tasa de finalización: {metrics['completion_rate']}%\n\n"
            f"💰 **Actividad de pujas:**\n"
            f"• Total de pujas: {metrics['total_bids']}\n"
            f"• Participantes únicos: {metrics['unique_participants']}\n"
            f"• Puntos en circulación: {metrics['points_in_circulation']}\n\n"
            f"📈 **Promedios:**\n"
            f"• Pujas por subasta: {metrics['avg_bids_per_auction']}\n"
            f"• Puntos por puja: {metrics['avg_points_per_bid']}"
        )
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            "analytics_auctions"
        )
    except Exception as e:
        logger.error(f"Error showing auction metrics: {e}")
        await callback.answer("Error al cargar métricas", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "analytics_revenue")
async def show_revenue_metrics(callback: CallbackQuery, session: AsyncSession):
    """Mostrar métricas de ingresos."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        analytics_service = AnalyticsService(session)
        metrics = await analytics_service.get_revenue_metrics()
        
        text = (
            f"💰 **Métricas de Ingresos**\n\n"
            f"📊 **Suscripciones:**\n"
            f"• Total históricas: {metrics['total_subscriptions']}\n"
            f"• Activas actuales: {metrics['active_subscriptions']}\n"
            f"• Nuevas este mes: {metrics['monthly_new_subscriptions']}\n\n"
            f"📈 **Retención:**\n"
            f"• Tasa de retención: {metrics['retention_rate']}%\n"
            f"• Expiran pronto (7 días): {metrics['expiring_soon']}\n"
            f"• Riesgo de cancelación: {metrics['churn_risk']} usuarios\n\n"
        )
        
        if metrics['expiring_soon'] > 0:
            text += (
                f"⚠️ **Alerta:** {metrics['expiring_soon']} suscripciones expiran pronto. "
                f"Considera enviar recordatorios de renovación."
            )
        else:
            text += "✅ **Estado saludable:** No hay suscripciones expirando pronto."
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            "analytics_revenue"
        )
    except Exception as e:
        logger.error(f"Error showing revenue metrics: {e}")
        await callback.answer("Error al cargar métricas", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "analytics_top_users")
async def show_top_users_menu(callback: CallbackQuery, session: AsyncSession):
    """Mostrar menú de top usuarios."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await update_menu(
        callback,
        "🏆 **Top Usuarios**\n\nSelecciona la métrica para ver el ranking:",
        get_top_users_metric_kb(),
        session,
        "analytics_top_users_menu"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("top_users_"))
async def show_top_users_by_metric(callback: CallbackQuery, session: AsyncSession):
    """Mostrar top usuarios por métrica específica."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    metric = callback.data.split("_")[-1]
    
    try:
        analytics_service = AnalyticsService(session)
        top_users = await analytics_service.get_top_users(metric, limit=10)
        
        metric_names = {
            "points": "💎 Puntos",
            "level": "📊 Nivel", 
            "missions": "🎯 Misiones Completadas"
        }
        
        text = f"🏆 **Top 10 - {metric_names.get(metric, metric.title())}**\n\n"
        
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            if metric == "points":
                value = f"{user['points']} pts"
            elif metric == "level":
                value = f"Nivel {user['level']} ({user['points']} pts)"
            elif metric == "missions":
                value = f"{user.get('missions_completed', 0)} misiones"
            else:
                value = ""
            
            text += f"{medal} {user['display_name']} - {value}\n"
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            f"top_users_{metric}"
        )
    except Exception as e:
        logger.error(f"Error showing top users by {metric}: {e}")
        await callback.answer("Error al cargar ranking", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "analytics_daily_report")
async def show_daily_report(callback: CallbackQuery, session: AsyncSession):
    """Mostrar reporte diario completo."""
    if not is_admin(callback.from_user.id):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        analytics_service = AnalyticsService(session)
        report = await analytics_service.generate_daily_report()
        
        engagement = report['engagement_metrics']
        revenue = report['revenue_metrics']
        auctions = report['auction_metrics']
        
        text = (
            f"📈 **Reporte Diario**\n"
            f"📅 {report['report_date'][:10]}\n\n"
            f"👥 **Usuarios:**\n"
            f"• Activos hoy: {engagement['active_users']}\n"
            f"• VIP activos: {engagement['vip_users']}\n"
            f"• Engagement: {engagement['engagement_rate']}%\n\n"
            f"🎮 **Actividad:**\n"
            f"• Misiones completadas: {engagement['missions_completed']}\n"
            f"• Reacciones: {engagement['reactions_count']}\n\n"
            f"🏛️ **Subastas:**\n"
            f"• Nuevas subastas: {auctions['total_auctions']}\n"
            f"• Pujas realizadas: {auctions['total_bids']}\n\n"
            f"💰 **Suscripciones:**\n"
            f"• Nuevas este mes: {revenue['monthly_new_subscriptions']}\n"
            f"• Expiran pronto: {revenue['expiring_soon']}\n"
        )
        
        # Agregar top usuario del día
        top_users = report['top_users']['by_points']
        if top_users:
            top_user = top_users[0]
            text += f"\n🏆 **Top usuario:** {top_user['display_name']} ({top_user['points']} pts)"
        
        await update_menu(
            callback,
            text,
            get_analytics_back_kb(),
            session,
            "analytics_daily_report"
        )
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        await callback.answer("Error al generar reporte", show_alert=True)
    
    await callback.answer()
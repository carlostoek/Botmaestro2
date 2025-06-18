"""
Teclados para el sistema de analíticas del administrador.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_admin_analytics_main_kb() -> InlineKeyboardMarkup:
    """Teclado principal de analíticas."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Métricas de Engagement", callback_data="analytics_engagement")
    builder.button(text="🎮 Métricas de Gamificación", callback_data="analytics_gamification")
    builder.button(text="🏛️ Métricas de Subastas", callback_data="analytics_auctions")
    builder.button(text="💰 Métricas de Ingresos", callback_data="analytics_revenue")
    builder.button(text="🏆 Top Usuarios", callback_data="analytics_top_users")
    builder.button(text="📈 Reporte Diario", callback_data="analytics_daily_report")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_analytics_period_kb() -> InlineKeyboardMarkup:
    """Teclado para seleccionar período de análisis."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📅 Último día", callback_data="period_1")
    builder.button(text="📅 Última semana", callback_data="period_7")
    builder.button(text="📅 Último mes", callback_data="period_30")
    builder.button(text="📅 Últimos 3 meses", callback_data="period_90")
    builder.button(text="🔙 Volver", callback_data="admin_analytics")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_top_users_metric_kb() -> InlineKeyboardMarkup:
    """Teclado para seleccionar métrica de top usuarios."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💎 Por Puntos", callback_data="top_users_points")
    builder.button(text="📊 Por Nivel", callback_data="top_users_level")
    builder.button(text="🎯 Por Misiones", callback_data="top_users_missions")
    builder.button(text="🔙 Volver", callback_data="admin_analytics")
    
    builder.adjust(1)
    return builder.as_markup()


def get_analytics_back_kb() -> InlineKeyboardMarkup:
    """Teclado simple de regreso a analíticas."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver a Analíticas", callback_data="admin_analytics")
    builder.adjust(1)
    return builder.as_markup()


def get_export_options_kb() -> InlineKeyboardMarkup:
    """Teclado para opciones de exportación."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📄 Exportar como Texto", callback_data="export_text")
    builder.button(text="📊 Generar Gráfico", callback_data="export_chart")
    builder.button(text="📧 Enviar por Email", callback_data="export_email")
    builder.button(text="🔙 Volver", callback_data="admin_analytics")
    
    builder.adjust(1)
    return builder.as_markup()
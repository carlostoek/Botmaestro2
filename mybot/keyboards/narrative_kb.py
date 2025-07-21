"""
Teclados para el sistema de narrativa inmersiva.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_models import NarrativeChoice

async def get_narrative_keyboard(fragment, session: AsyncSession) -> InlineKeyboardMarkup:
    """Crea el teclado de decisiones para un fragmento narrativo."""
    builder = InlineKeyboardBuilder()
    
    # Obtener las opciones de decisión para este fragmento
    stmt = select(NarrativeChoice).where(
        NarrativeChoice.source_fragment_id == fragment.id
    ).order_by(NarrativeChoice.id)
    result = await session.execute(stmt)
    choices = result.scalars().all()
    
    # Agregar botones para cada decisión
    for index, choice in enumerate(choices):
        builder.button(
            text=choice.text,
            callback_data=f"narrative_choice:{index}"
        )
    
    # Si no hay decisiones, es un fragmento final o de transición automática
    if not choices:
        if fragment.auto_next_fragment_id:
            builder.button(
                text="➡️ Continuar",
                callback_data="narrative_auto_continue"
            )
        else:
            builder.button(
                text="📖 Ver Mi Historia",
                callback_data="narrative_stats"
            )
    
    # Botones de navegación adicionales
    builder.button(
        text="📊 Mi Progreso",
        callback_data="narrative_stats"
    )
    
    builder.button(
        text="❓ Ayuda",
        callback_data="narrative_help"
    )
    
    builder.adjust(1)  # Un botón por fila para mejor legibilidad
    return builder.as_markup()

def get_narrative_stats_keyboard() -> InlineKeyboardMarkup:
    """Teclado para las estadísticas narrativas."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📖 Continuar Historia", callback_data="continue_narrative")
    builder.button(text="❓ Ayuda", callback_data="narrative_help")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1)
    return builder.as_markup()

def get_narrative_choice_keyboard(choices: list) -> InlineKeyboardMarkup:
    """Crea teclado específico para decisiones narrativas."""
    builder = InlineKeyboardBuilder()
    
    for index, choice_text in enumerate(choices):
        builder.button(
            text=choice_text,
            callback_data=f"narrative_choice:{index}"
        )
    
    builder.adjust(1)
    return builder.as_markup()
# handlers/narrative/enhanced_backpack.py
"""
Sistema de mochila mejorado con funcionalidades narrativas.
Integra el sistema de combinación de pistas y gestión de objetos narrativos.
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Tuple

from database.narrative_models import (
    LorePiece, UserLorePiece, UnsentLetter,
    UserUnsentLetter, DialogueHistory
)
from database.models import User

router = Router(name="enhanced_backpack")

@router.message(Command("mochila"))
async def cmd_backpack(
    message: types.Message,
    session: AsyncSession,
    user: User
):
    """Muestra el contenido de la mochila del viajero"""
    
    # Obtener items del usuario
    lore_pieces = await _get_user_lore_pieces(session, user.id)
    unsent_letters = await _get_user_unsent_letters(session, user.id)
    special_items = await _get_special_items(session, user.id)
    
    if not any([lore_pieces, unsent_letters, special_items]):
        await message.answer(
            "🎒 <b>Tu Mochila</b>\n\n"
            "Tu mochila está vacía. Continúa explorando y completando misiones "
            "para encontrar pistas y objetos especiales."
        )
        return
    
    # Construir mensaje
    backpack_text = "🎒 <b>Tu Mochila de Viajero</b>\n\n"
    
    # Sección de pistas
    if lore_pieces:
        backpack_text += "📜 <b>Pistas y Fragmentos:</b>\n"
        for lp in lore_pieces:
            icon = _get_lore_icon(lp.piece_type)
            status = "✨" if not lp.has_read else ""
            backpack_text += f"{icon} {lp.lore.name} {status}\n"
        backpack_text += "\n"
    
    # Sección de cartas
    if unsent_letters:
        backpack_text += "💌 <b>Cartas No Enviadas:</b>\n"
        for letter in unsent_letters:
            status = "✨" if not letter.diana_noticed else "👁"
            backpack_text += f"📮 Carta de Diana {status}\n"
        backpack_text += "\n"
    
    # Sección de items especiales
    if special_items:
        backpack_text += "🎁 <b>Objetos Especiales:</b>\n"
        for item in special_items:
            backpack_text += f"⭐ {item['name']}\n"
        backpack_text += "\n"
    
    # Estadísticas
    total_items = len(lore_pieces) + len(unsent_letters) + len(special_items)
    unread_items = sum(1 for lp in lore_pieces if not lp.has_read)
    
    backpack_text += f"📊 <b>Total de objetos:</b> {total_items}\n"
    if unread_items > 0:
        backpack_text += f"✨ <b>Sin leer:</b> {unread_items}\n"
    
    # Teclado de navegación
    keyboard_buttons = []
    
    if lore_pieces:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="📜 Ver Pistas",
                callback_data="backpack_lore"
            )
        ])
    
    if unsent_letters:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="💌 Leer Cartas",
                callback_data="backpack_letters"
            )
        ])
    
    if len([lp for lp in lore_pieces if lp.lore.combines_with]) > 1:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="🔗 Combinar Pistas",
                callback_data="backpack_combine"
            )
        ])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(backpack_text, reply_markup=keyboard)

@router.callback_query(F.data == "backpack_lore")
async def show_lore_pieces(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Muestra lista de pistas del usuario"""
    
    lore_pieces = await _get_user_lore_pieces(session, user.id)
    
    if not lore_pieces:
        await callback.answer("No tienes pistas aún", show_alert=True)
        return
    
    # Crear botones para cada pista
    keyboard_buttons = []
    for user_lore in lore_pieces:
        icon = _get_lore_icon(user_lore.lore.piece_type)
        status = " ✨" if not user_lore.has_read else ""
        
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text=f"{icon} {user_lore.lore.name}{status}",
                callback_data=f"view_lore:{user_lore.lore_piece_code}"
            )
        ])
    
    keyboard_buttons.append([
        types.InlineKeyboardButton(
            text="↩️ Volver",
            callback_data="backpack_main"
        )
    ])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "📜 <b>Tus Pistas y Fragmentos</b>\n\n"
        "Selecciona una pista para examinarla:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("view_lore:"))
async def view_lore_piece(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Muestra el contenido de una pista específica"""
    
    lore_code = callback.data.split(":")[1]
    
    # Obtener la pista
    user_lore = await session.execute(
        select(UserLorePiece).filter(
            and_(
                UserLorePiece.user_id == user.id,
                UserLorePiece.lore_piece_code == lore_code
            )
        ).options(selectinload(UserLorePiece.lore))
    )
    user_lore = user_lore.scalar_one_or_none()
    
    if not user_lore:
        await callback.answer("Pista no encontrada", show_alert=True)
        return
    
    lore = user_lore.lore
    
    # Marcar como leída
    if not user_lore.has_read:
        user_lore.has_read = True
        user_lore.first_read_at = datetime.utcnow()
    
    user_lore.times_viewed += 1
    await session.commit()
    
    # Construir mensaje
    icon = _get_lore_icon(lore.piece_type)
    message_text = f"""
{icon} <b>{lore.name}</b>

<i>{lore.description}</i>

━━━━━━━━━━━━━━━

{lore.content}

━━━━━━━━━━━━━━━

📍 <b>Encontrado:</b> {user_lore.found_at.strftime('%d/%m/%Y')}
👁 <b>Visto:</b> {user_lore.times_viewed} veces
"""
    
    # Si Diana tiene un comentario
    if lore.diana_comment_on_find and user_lore.times_viewed == 1:
        message_text += f"\n🌸 <i>Diana: {lore.diana_comment_on_find}</i>"
    
    # Botones de acción
    keyboard_buttons = []
    
    # Si se puede preguntar a Diana
    if lore.diana_comment_if_asked and not user_lore.asked_diana_about_it:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="🌸 Preguntar a Diana",
                callback_data=f"ask_diana_lore:{lore_code}"
            )
        ])
    
    # Si se puede combinar
    if lore.combines_with:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="🔗 Ver Combinaciones",
                callback_data=f"lore_combinations:{lore_code}"
            )
        ])
    
    keyboard_buttons.append([
        types.InlineKeyboardButton(
            text="↩️ Volver a Pistas",
            callback_data="backpack_lore"
        )
    ])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(message_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("ask_diana_lore:"))
async def ask_diana_about_lore(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Pregunta a Diana sobre una pista específica"""
    
    lore_code = callback.data.split(":")[1]
    
    # Obtener la pista y marcar que se preguntó
    user_lore = await session.execute(
        select(UserLorePiece).filter(
            and_(
                UserLorePiece.user_id == user.id,
                UserLorePiece.lore_piece_code == lore_code
            )
        ).options(selectinload(UserLorePiece.lore))
    )
    user_lore = user_lore.scalar_one_or_none()
    
    if not user_lore or not user_lore.lore.diana_comment_if_asked:
        await callback.answer("No puedo preguntar sobre esto", show_alert=True)
        return
    
    # Marcar como preguntado
    user_lore.asked_diana_about_it = True
    user_lore.diana_reaction_logged = user_lore.lore.diana_comment_if_asked
    
    # Posible impacto en la relación
    narrative_state = await session.get(NarrativeState, user.id)
    if narrative_state and user_lore.lore.changes_diana_behavior:
        narrative_state.trust_level += 0.02
        narrative_state.shared_memories.append({
            "type": "lore_discussion",
            "lore_code": lore_code,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    await session.commit()
    
    # Mostrar respuesta de Diana
    response_text = f"""
🌸 <b>Diana observa la pista con una expresión compleja</b>

<i>{user_lore.lore.diana_comment_if_asked}</i>
"""
    
    if user_lore.lore.changes_diana_behavior:
        response_text += "\n\n<i>[Notas que algo cambió en la expresión de Diana]</i>"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="↩️ Volver",
            callback_data=f"view_lore:{lore_code}"
        )]
    ])
    
    await callback.message.edit_text(response_text, reply_markup=keyboard)
    await callback.answer("Diana parece afectada por tu pregunta...", show_alert=True)

@router.callback_query(F.data == "backpack_combine")
async def show_combination_menu(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Muestra el menú de combinación de pistas"""
    
    # Obtener pistas combinables
    combinable_lore = await _get_combinable_lore_pieces(session, user.id)
    
    if len(combinable_lore) < 2:
        await callback.answer(
            "Necesitas al menos 2 pistas que puedan combinarse",
            show_alert=True
        )
        return
    
    message_text = """
🔗 <b>Combinar Pistas</b>

Algunas pistas pueden combinarse para revelar nuevos secretos.
Selecciona las pistas que quieres intentar combinar:
"""
    
    # Estado para rastrear selección
    await callback.message.edit_text(
        message_text,
        reply_markup=_create_combination_keyboard(combinable_lore, [])
    )
    await callback.answer()

def _create_combination_keyboard(
    combinable_lore: List[UserLorePiece],
    selected: List[str]
) -> types.InlineKeyboardMarkup:
    """Crea teclado para selección de combinaciones"""
    
    keyboard_buttons = []
    
    for user_lore in combinable_lore:
        is_selected = user_lore.lore_piece_code in selected
        icon = "✅" if is_selected else _get_lore_icon(user_lore.lore.piece_type)
        
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text=f"{icon} {user_lore.lore.name}",
                callback_data=f"toggle_lore:{user_lore.lore_piece_code}"
            )
        ])
    
    # Botón de combinar si hay 2 seleccionados
    if len(selected) == 2:
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="✨ Intentar Combinar",
                callback_data=f"combine_lore:{selected[0]}:{selected[1]}"
            )
        ])
    
    keyboard_buttons.append([
        types.InlineKeyboardButton(
            text="↩️ Volver",
            callback_data="backpack_main"
        )
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

@router.callback_query(F.data.startswith("combine_lore:"))
async def attempt_combination(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User
):
    """Intenta combinar dos pistas"""
    
    parts = callback.data.split(":")
    lore1_code = parts[1]
    lore2_code = parts[2]
    
    # Verificar que el usuario tiene ambas pistas
    user_lore1 = await _get_user_lore_piece(session, user.id, lore1_code)
    user_lore2 = await _get_user_lore_piece(session, user.id, lore2_code)
    
    if not user_lore1 or not user_lore2:
        await callback.answer("No tienes esas pistas", show_alert=True)
        return
    
    # Verificar si se pueden combinar
    lore1 = user_lore1.lore
    lore2 = user_lore2.lore
    
    can_combine = (
        lore2_code in lore1.combines_with or
        lore1_code in lore2.combines_with
    )
    
    if not can_combine:
        # Combinación fallida
        await callback.message.edit_text(
            "❌ <b>Combinación Fallida</b>\n\n"
            "Estas pistas no parecen estar conectadas. "
            "Tal vez necesites encontrar otra pieza del rompecabezas...",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text="↩️ Intentar otra combinación",
                    callback_data="backpack_combine"
                )
            ]])
        )
        
        # Registrar intento fallido
        user_lore1.failed_combination_attempts.append({
            "with": lore2_code,
            "timestamp": datetime.utcnow().isoformat()
        })
        await session.commit()
        
        await callback.answer("No parece funcionar...", show_alert=True)
        return
    
    # Combinación exitosa
    result_code = lore1.combination_result or lore2.combination_result
    
    if result_code:
        # Desbloquear nueva pista
        result_lore = await session.get(LorePiece, result_code)
        
        if result_lore:
            # Agregar a la mochila
            user_result_lore = UserLorePiece(
                user_id=user.id,
                lore_piece_code=result_code,
                found_context="combination",
                discovery_method=f"Combinar {lore1.name} + {lore2.name}"
            )
            session.add(user_result_lore)
            
            # Marcar como usadas
            user_lore1.used_in_combination = True
            user_lore1.successful_combinations.append(lore2_code)
            user_lore2.used_in_combination = True
            user_lore2.successful_combinations.append(lore1_code)
            
            await session.commit()
            
            combination_text = f"""
✨ <b>¡Combinación Exitosa!</b>

Al juntar <i>{lore1.name}</i> con <i>{lore2.name}</i>, 
has descubierto algo nuevo:

🎁 <b>{result_lore.name}</b>
<i>{result_lore.description}</i>

{lore1.combination_narrative or "Las piezas encajan perfectamente, revelando un nuevo secreto."}
"""
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="📜 Ver Nueva Pista",
                    callback_data=f"view_lore:{result_code}"
                )],
                [types.InlineKeyboardButton(
                    text="↩️ Volver a Mochila",
                    callback_data="backpack_main"
                )]
            ])
            
            await callback.message.edit_text(combination_text, reply_markup=keyboard)
            await callback.answer("¡Descubriste algo importante!", show_alert=True)

def _get_lore_icon(piece_type: str) -> str:
    """Retorna el ícono apropiado para cada tipo de pista"""
    icons = {
        "diary_page": "📄",
        "letter": "✉️",
        "photo": "🖼",
        "memory": "💭",
        "object": "🔑",
        "secret": "🤫",
    }
    return icons.get(piece_type, "📜")

async def _get_user_lore_pieces(
    session: AsyncSession,
    user_id: int
) -> List[UserLorePiece]:
    """Obtiene todas las pistas del usuario"""
    result = await session.execute(
        select(UserLorePiece)
        .filter(UserLorePiece.user_id == user_id)
        .options(selectinload(UserLorePiece.lore))
        .order_by(UserLorePiece.found_at.desc())
    )
    return result.scalars().all()

async def _get_user_unsent_letters(
    session: AsyncSession,
    user_id: int
) -> List[UserUnsentLetter]:
    """Obtiene las cartas no enviadas del usuario"""
    result = await session.execute(
        select(UserUnsentLetter)
        .filter(UserUnsentLetter.user_id == user_id)
        .options(selectinload(UserUnsentLetter.letter))
        .order_by(UserUnsentLetter.found_at.desc())
    )
    return result.scalars().all()

async def _get_combinable_lore_pieces(
    session: AsyncSession,
    user_id: int
) -> List[UserLorePiece]:
    """Obtiene pistas que pueden combinarse"""
    result = await session.execute(
        select(UserLorePiece)
        .join(LorePiece)
        .filter(
            and_(
                UserLorePiece.user_id == user_id,
                UserLorePiece.used_in_combination == False,
                LorePiece.combines_with != []
            )
        )
        .options(selectinload(UserLorePiece.lore))
    )
    return result.scalars().all()

async def _get_special_items(
    session: AsyncSession,
    user_id: int
) -> List[Dict]:
    """Obtiene items especiales (placeholder para futura expansión)"""
    # Por ahora retorna lista vacía
    # En el futuro puede incluir recompensas especiales, regalos de Diana, etc.
    return []

async def _get_user_lore_piece(
    session: AsyncSession,
    user_id: int,
    lore_code: str
) -> Optional[UserLorePiece]:
    """Obtiene una pista específica del usuario"""
    result = await session.execute(
        select(UserLorePiece)
        .filter(
            and_(
                UserLorePiece.user_id == user_id,
                UserLorePiece.lore_piece_code == lore_code
            )
        )
        .options(selectinload(UserLorePiece.lore))
    )
    return result.scalar_one_or_none()

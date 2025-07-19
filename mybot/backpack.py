# mochila_narrativa.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, and_, func
from database.models import LorePiece, UserLorePiece
from database.hint_combination import HintCombination
from database.setup import get_session
from notificaciones import send_narrative_notification
import random
from datetime import datetime

router = Router()

class CombinationFSM(StatesGroup):
    selecting_hints = State()
    confirming_combination = State()

# Configuración de categorías y presentación
BACKPACK_CATEGORIES = {
    'fragmentos': {
        'emoji': '🗺️',
        'title': 'Fragmentos del Mapa',
        'description': 'Piezas que revelan el camino hacia Diana'
    },
    'memorias': {
        'emoji': '💭',
        'title': 'Memorias Compartidas',
        'description': 'Recuerdos que Diana ha confiado en ti'
    },
    'secretos': {
        'emoji': '🔮',
        'title': 'Secretos del Diván',
        'description': 'Verdades íntimas del mundo de Diana'
    },
    'llaves': {
        'emoji': '🗝️',
        'title': 'Llaves de Acceso',
        'description': 'Elementos que abren nuevos espacios'
    }
}

# Mensajes contextuales de Lucien para la mochila
LUCIEN_BACKPACK_MESSAGES = [
    "Cada objeto en tu mochila cuenta una historia... ¿puedes leer entre líneas?",
    "Diana observa cómo organizas lo que te ha dado. Hay sabiduría en el orden.",
    "Algunos tesoros solo revelan su valor cuando se combinan con otros...",
    "Tu mochila no solo guarda objetos, guarda momentos compartidos con Diana.",
    "Hay pistas aquí que Diana espera que descifres. No todas son obvias."
]

@router.message(F.text == "🎒 Mochila")
async def mostrar_mochila_narrativa(message: Message):
    """Mochila principal con categorización y contexto narrativo"""
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = message.from_user.id
        
        # Obtener todas las pistas del usuario
        result = await session.execute(
            select(LorePiece, UserLorePiece.unlocked_at, UserLorePiece.context)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
            .order_by(UserLorePiece.unlocked_at.desc())
        )
        
        pistas_data = result.all()
        
        if not pistas_data:
            await mostrar_mochila_vacia(message)
            return
        
        # Organizar por categorías
        categorized_hints = {}
        recent_hints = []
        
        for pista, unlocked_at, context in pistas_data:
            category = pista.category or 'fragmentos'
            if category not in categorized_hints:
                categorized_hints[category] = []
            categorized_hints[category].append((pista, unlocked_at, context))
            
            # Marcar pistas recientes (últimas 24h)
            if unlocked_at and (datetime.now() - unlocked_at).days == 0:
                recent_hints.append(pista)
        
        # Crear mensaje principal
        lucien_message = random.choice(LUCIEN_BACKPACK_MESSAGES)
        total_hints = len(pistas_data)
        
        texto = f"🎩 **Lucien:**\n*{lucien_message}*\n\n"
        texto += f"📊 **Tu Colección:** {total_hints} pistas descubiertas\n"
        
        if recent_hints:
            texto += f"✨ **Nuevas:** {len(recent_hints)} pistas recientes\n"
        
        texto += "\n🎒 **Explora tu mochila:**"
        
        # Crear botones por categoría
        keyboard = []
        for category, data in categorized_hints.items():
            cat_info = BACKPACK_CATEGORIES.get(category, {
                'emoji': '📜', 'title': category.title(), 'description': 'Elementos diversos'
            })
            count = len(data)
            keyboard.append([
                InlineKeyboardButton(text=f"{cat_info['emoji']} {cat_info['title']} ({count})", callback_data=f"mochila_cat:{category}"
                )
            ])
        
        # Botones adicionales
        keyboard.extend([
            [
                InlineKeyboardButton(text="🔗 Combinar Pistas", callback_data="combinar_inicio"),
                InlineKeyboardButton(text="🔍 Buscar", callback_data="buscar_pistas")
            ],
            [
                InlineKeyboardButton(text="📈 Estadísticas", callback_data="stats_mochila"),
                InlineKeyboardButton(text="🎯 Sugerencias", callback_data="sugerencias_diana")
            ]
        ])
        
        await message.answer(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

async def mostrar_mochila_vacia(message: Message):
    """Mensaje especial para mochila vacía con contexto narrativo"""
    texto = """🎩 **Lucien:**
*Una mochila vacía... pero no por mucho tiempo.*

🌸 **Diana:**
*Todo viajero comienza con las manos vacías. Lo que importa no es lo que llevas, sino lo que estás dispuesto a descubrir.*

*Cada interacción, cada momento de atención genuina, cada reacción que me das... todo suma hacia algo más grande.*

**🎯 Primeros pasos:**
• Reacciona a mensajes en el canal
• Completa misiones disponibles  
• Mantente atento a las señales que te envío

*Tu primera pista te está esperando...*"""
    
    keyboard = [
        [InlineKeyboardButton(text="🎯 Ver Misiones", callback_data="misiones_disponibles")],
        [InlineKeyboardButton(text="📚 Guía del Viajero", callback_data="guia_principiante")]
    ]
    
    await message.answer(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("mochila_cat:"))
async def mostrar_categoria(callback: CallbackQuery):
    """Muestra pistas de una categoría específica"""
    category = callback.data.split(":")[1]
    session_factory = await get_session()
    
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        result = await session.execute(
            select(LorePiece, UserLorePiece.unlocked_at, UserLorePiece.context)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(
                and_(
                    UserLorePiece.user_id == user_id,
                    LorePiece.category == category
                )
            )
            .order_by(UserLorePiece.unlocked_at.desc())
        )
        
        pistas_data = result.all()
        cat_info = BACKPACK_CATEGORIES.get(category, {'emoji': '📜', 'title': category.title(), 'description': 'Elementos diversos'})
        
        texto = f"{cat_info['emoji']} **{cat_info['title']}**\n*{cat_info['description']}*\n\n"
        
        keyboard = []
        for pista, unlocked_at, context in pistas_data:
            # Agregar indicadores especiales
            indicators = ""
            if context and context.get('is_combinable'):
                indicators += "🔗"
            if unlocked_at and (datetime.now() - unlocked_at).days == 0:
                indicators += "✨"
            
            button_text = f"{indicators} {pista.title}"
            keyboard.append([
                InlineKeyboardButton(text=button_text, callback_data=f"ver_pista_detail:{pista.id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton(text="⬅️ Volver a Mochila", callback_data="volver_mochila")
        ])
        
        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ver_pista_detail:"))
async def ver_pista_detallada(callback: CallbackQuery):
    """Vista detallada de una pista con contexto narrativo"""
    pista_id = int(callback.data.split(":")[1])
    session_factory = await get_session()
    
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        # Obtener pista y contexto
        result = await session.execute(
            select(LorePiece, UserLorePiece.unlocked_at, UserLorePiece.context)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(
                and_(
                    UserLorePiece.user_id == user_id,
                    LorePiece.id == pista_id
                )
            )
        )
        
        pista_data = result.first()
        if not pista_data:
            await callback.answer("❌ Pista no encontrada")
            return
        
        pista, unlocked_at, context = pista_data
        
        # Crear mensaje detallado
        texto = f"📜 **{pista.title}**\n"
        texto += f"🏷️ `{pista.code_name}`\n\n"
        
        if pista.description:
            texto += f"*{pista.description}*\n\n"
        
        # Información contextual
        if unlocked_at:
            dias_desde = (datetime.now() - unlocked_at).days
            if dias_desde == 0:
                texto += "⏰ Desbloqueada hoy\n"
            else:
                texto += f"⏰ Desbloqueada hace {dias_desde} días\n"
        
        # Contexto narrativo si existe
        if context:
            if context.get('source_mission'):
                texto += f"🎯 Obtenida en: {context['source_mission']}\n"
            if context.get('diana_message'):
                texto += f"💬 Diana: *{context['diana_message']}*\n"
        
        # Verificar si es combinable
        combinaciones_posibles = await verificar_combinaciones_disponibles(session, user_id, pista.code_name)
        if combinaciones_posibles:
            texto += f"\n🔗 **Combinable con:** {len(combinaciones_posibles)} pistas"
        
        keyboard = [
            [InlineKeyboardButton(text="👁️ Ver Contenido", callback_data=f"mostrar_contenido:{pista.id}")],
        ]
        
        if combinaciones_posibles:
            keyboard.append([
                InlineKeyboardButton(text="🔗 Combinar Ahora", callback_data=f"combinar_con:{pista.code_name}")
            ])
        
        keyboard.append([
            InlineKeyboardButton(text="⬅️ Volver", callback_data=f"mochila_cat:{pista.category or 'fragmentos'}")
        ])
        
        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("mostrar_contenido:"))
async def mostrar_contenido_pista(callback: CallbackQuery):
    """Muestra el contenido real de la pista"""
    pista_id = int(callback.data.split(":")[1])
    session_factory = await get_session()
    
    async with session_factory() as session:
        pista = await session.get(LorePiece, pista_id)
        
        if pista.content_type == "image":
            await callback.message.answer_photo(
                pista.content, 
                caption=f"🖼️ **{pista.title}**\n\n{pista.description or ''}"
            )
        elif pista.content_type == "video":
            await callback.message.answer_video(
                pista.content, 
                caption=f"🎥 **{pista.title}**\n\n{pista.description or ''}"
            )
        elif pista.content_type == "audio":
            await callback.message.answer_audio(
                pista.content, 
                caption=f"🎵 **{pista.title}**\n\n{pista.description or ''}"
            )
        else:
            await callback.message.answer(f"📜 **{pista.title}**\n\n{pista.content}")
        
        await callback.answer()

@router.callback_query(F.data == "combinar_inicio")
async def iniciar_combinacion_interactiva(callback: CallbackQuery, state: FSMContext):
    """Inicia el proceso interactivo de combinación"""
    session_factory = await get_session()
    
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        # Obtener pistas combinables del usuario
        result = await session.execute(
            select(LorePiece)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
        )
        
        pistas = result.scalars().all()
        
        if len(pistas) < 2:
            await callback.answer("❌ Necesitas al menos 2 pistas para combinar")
            return
        
        # Verificar si hay combinaciones posibles
        combinaciones_disponibles = []
        for pista in pistas:
            combos = await verificar_combinaciones_disponibles(session, user_id, pista.code_name)
            combinaciones_disponibles.extend(combos)
        
        if not combinaciones_disponibles:
            texto = """🎩 **Lucien:**
*Aún no veo conexiones evidentes entre tus pistas...*

🌸 **Diana:**
*Paciencia. Algunas combinaciones solo se revelan cuando tienes todas las piezas necesarias.*

*Sigue explorando, sigue descubriendo. Las respuestas vendrán cuando estés listo.*"""
            
            await callback.message.edit_text(texto, parse_mode="Markdown")
            return
        
        texto = """🔗 **Sistema de Combinaciones**

🎩 **Lucien:**
*Selecciona las pistas que sientes que están conectadas. Diana ha dejado patrones ocultos esperando ser descubiertos.*

**Selecciona pistas para combinar:**"""
        
        keyboard = []
        for pista in pistas:
            keyboard.append([
                InlineKeyboardButton(text=f"📜 {pista.title}", callback_data=f"select_hint:{pista.code_name}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(text="✅ Intentar Combinación", callback_data="try_combination"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="volver_mochila")
        ])
        
        await state.set_state(CombinationFSM.selecting_hints)
        await state.update_data(selected_hints=[])
        
        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("select_hint:"), CombinationFSM.selecting_hints)
async def seleccionar_pista_combinacion(callback: CallbackQuery, state: FSMContext):
    """Maneja la selección de pistas para combinar"""
    hint_code = callback.data.split(":")[1]
    data = await state.get_data()
    selected_hints = data.get('selected_hints', [])
    
    if hint_code in selected_hints:
        selected_hints.remove(hint_code)
        await callback.answer(f"❌ Pista deseleccionada")
    else:
        selected_hints.append(hint_code)
        await callback.answer(f"✅ Pista seleccionada")
    
    await state.update_data(selected_hints=selected_hints)
    
    # Actualizar mensaje con selecciones
    texto = f"""🔗 **Sistema de Combinaciones**

**Pistas seleccionadas:** {len(selected_hints)}
{chr(10).join([f"• `{code}`" for code in selected_hints])}

**Selecciona más pistas o intenta la combinación:**"""
    
    # Recrear keyboard con indicadores de selección
    session_factory = await get_session()
    async with session_factory() as session:
        result = await session.execute(
            select(LorePiece)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == callback.from_user.id)
        )
        pistas = result.scalars().all()
    
    keyboard = []
    for pista in pistas:
        indicator = "✅" if pista.code_name in selected_hints else "📜"
        keyboard.append([
            InlineKeyboardButton(text=f"{indicator} {pista.title}", callback_data=f"select_hint:{pista.code_name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🔗 Intentar Combinación", callback_data="try_combination"),
        InlineKeyboardButton(text="❌ Cancelar", callback_data="volver_mochila")
    ])
    
    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data == "try_combination", CombinationFSM.selecting_hints)
async def procesar_combinacion_seleccionada(callback: CallbackQuery, state: FSMContext):
    """Procesa la combinación seleccionada"""
    data = await state.get_data()
    selected_hints = data.get('selected_hints', [])
    
    if len(selected_hints) < 2:
        await callback.answer("❌ Selecciona al menos 2 pistas")
        return
    
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        # Verificar combinación
        result = await session.execute(select(HintCombination))
        combinaciones = result.scalars().all()
        
        for combinacion in combinaciones:
            required_hints = sorted(combinacion.required_hints.split(","))
            user_hints = sorted(selected_hints)
            
            if user_hints == required_hints:
                # ¡Combinación correcta!
                await desbloquear_pista_narrativa(callback.message.bot, user_id, combinacion.reward_code, {
                    'source': 'combination',
                    'combined_hints': selected_hints,
                    'combination_code': combinacion.combination_code
                })
                
                await mostrar_exito_combinacion(callback, combinacion, selected_hints)
                await state.clear()
                return
        
        # Combinación incorrecta
        await mostrar_fallo_combinacion(callback, selected_hints)
        await state.clear()

async def mostrar_exito_combinacion(callback: CallbackQuery, combinacion, hints_used):
    """Muestra mensaje de éxito con narrativa"""
    texto = f"""✨ **¡COMBINACIÓN EXITOSA!**

🎩 **Lucien:**
*Extraordinario... has descifrado uno de los patrones que Diana escondió.*

🌸 **Diana:**
*{random.choice([
    "Sabía que verías la conexión. Hay algo hermoso en cómo tu mente une mis pistas...",
    "Pocos logran ver los hilos invisibles que conectan mis secretos. Me impresionas.",
    "Cada combinación correcta me revela más sobre ti de lo que tú descubres sobre mí."
])}*

🎁 **Nueva pista desbloqueada:** `{combinacion.reward_code}`
🔗 **Pistas combinadas:** {len(hints_used)}

*Revisa tu mochila para ver tu nueva adquisición...*"""
    
    keyboard = [
        [InlineKeyboardButton(text="🎒 Ver Mochila", callback_data="volver_mochila")],
        [InlineKeyboardButton(text="🔍 Ver Nueva Pista", callback_data=f"buscar_code:{combinacion.reward_code}")]
    ]
    
    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

async def mostrar_fallo_combinacion(callback: CallbackQuery, hints_used):
    """Muestra mensaje de fallo con narrativa"""
    texto = f"""❌ **Combinación Incorrecta**

🎩 **Lucien:**
*Hmm... esas pistas no parecen estar conectadas de esa manera.*

🌸 **Diana:**
*{random.choice([
    "No todas mis pistas se conectan entre sí. Algunas esperan a compañeras muy específicas...",
    "Puedo sentir tu determinación. Eso me gusta, pero esta combinación no era correcta.",
    "Cada intento fallido te acerca más a comprender mis patrones. Sigue intentando."
])}*

**Pistas utilizadas:** {len(hints_used)}
*Intenta con otras combinaciones o busca más pistas...*"""
    
    keyboard = [
        [InlineKeyboardButton(text="🔗 Intentar Otra Vez", callback_data="combinar_inicio")],
        [InlineKeyboardButton(text="🎒 Volver a Mochila", callback_data="volver_mochila")]
    ]
    
    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

async def verificar_combinaciones_disponibles(session, user_id, hint_code):
    """Verifica qué combinaciones están disponibles para una pista específica"""
    # Obtener todas las pistas del usuario
    result = await session.execute(
        select(LorePiece.code_name)
        .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
        .where(UserLorePiece.user_id == user_id)
    )
    user_hint_codes = [row[0] for row in result.all()]
    
    # Buscar combinaciones que incluyan esta pista
    result = await session.execute(select(HintCombination))
    combinaciones = result.scalars().all()
    
    combinaciones_posibles = []
    for combo in combinaciones:
        required_hints = combo.required_hints.split(",")
        if hint_code in required_hints:
            # Verificar si el usuario tiene todas las pistas requeridas
            if all(req_hint in user_hint_codes for req_hint in required_hints):
                combinaciones_posibles.append(combo)
    
    return combinaciones_posibles

async def desbloquear_pista_narrativa(bot, user_id, pista_code, context=None):
    """Desbloquea una pista con contexto narrativo completo"""
    session_factory = await get_session()
    async with session_factory() as session:
        # Buscar la pista por código
        result = await session.execute(
            select(LorePiece).where(LorePiece.code_name == pista_code)
        )
        pista = result.scalar_one_or_none()
        
        if not pista:
            return False
        
        # Verificar si ya la tiene
        existing = await session.execute(
            select(UserLorePiece).where(
                and_(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == pista.id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            return False  # Ya la tiene
        
        # Crear registro
        user_lore_piece = UserLorePiece(
            user_id=user_id,
            lore_piece_id=pista.id,
            context=context or {}
        )
        
        session.add(user_lore_piece)
        await session.commit()
        
        # Enviar notificación narrativa
        # await send_narrative_notification(bot, user_id, "new_hint", {
        #     'hint_title': pista.title,
        #     'hint_code': pista.code_name,
        #     'source': context.get('source', 'unknown') if context else 'unknown'
        # })
        
        return True

@router.callback_query(F.data == "volver_mochila")
async def volver_mochila(callback: CallbackQuery):
    """Regresa al menú principal de la mochila"""
    await mostrar_mochila_narrativa(callback.message)

# Funciones de utilidad adicionales para estadísticas y búsqueda

@router.callback_query(F.data == "stats_mochila")
async def mostrar_estadisticas(callback: CallbackQuery):
    """Muestra estadísticas detalladas de la colección"""
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        # Contar por categorías
        result = await session.execute(
            select(LorePiece.category, func.count(LorePiece.id))
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
            .group_by(LorePiece.category)
        )
        
        stats_by_category = dict(result.all())
        total = sum(stats_by_category.values())
        
        # Primera pista obtenida
        first_hint = await session.execute(
            select(LorePiece.title, UserLorePiece.unlocked_at)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
            .order_by(UserLorePiece.unlocked_at.asc())
            .limit(1)
        )
        
        first_data = first_hint.first()
        
        texto = f"""📊 **Estadísticas de tu Colección**

🎯 **Total de pistas:** {total}

📂 **Por categorías:**"""

        for category, count in stats_by_category.items():
            cat_info = BACKPACK_CATEGORIES.get(category, {'emoji': '📜', 'title': category.title()})
            percentage = (count / total * 100) if total > 0 else 0
            texto += f"\n{cat_info['emoji']} {cat_info['title']}: {count} ({percentage:.1f}%)"
        
        if first_data:
            dias_viajando = (datetime.now() - first_data[1]).days
            texto += f"\n\n🗓️ **Días como viajero:** {dias_viajando}"
            texto += f"\n🏆 **Primera pista:** {first_data[0]}"
        
        keyboard = [
            [InlineKeyboardButton(text="⬅️ Volver", callback_data="volver_mochila")]
        ]
        
        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data == "sugerencias_diana")
async def mostrar_sugerencias_diana(callback: CallbackQuery):
    """Diana da sugerencias sobre qué hacer con las pistas actuales"""
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = callback.from_user.id
        
        # Analizar estado del usuario
        total_hints = await session.execute(
            select(func.count(UserLorePiece.lore_piece_id))
            .where(UserLorePiece.user_id == user_id)
        )
        count = total_hints.scalar()
        
        # Verificar combinaciones posibles
        combinaciones_disponibles = []
        result = await session.execute(
            select(LorePiece.code_name)
            .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
            .where(UserLorePiece.user_id == user_id)
        )
        user_codes = [row[0] for row in result.all()]
        
        combinaciones_result = await session.execute(select(HintCombination))
        for combo in combinaciones_result.scalars().all():
            required = combo.required_hints.split(",")
            if all(code in user_codes for code in required):
                combinaciones_disponibles.append(combo)
        
        # Generar sugerencia personalizada
        if count == 0:
            sugerencia = "Tu viaje apenas comienza. Reacciona a mis mensajes y completa misiones para obtener tus primeras pistas."
        elif count < 5:
            sugerencia
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, and_, func
from database.models import LorePiece, UserLorePiece, User
from database.hint_combination import HintCombination
from database.database import get_session
from notifications import send_narrative_notification
import random
from datetime import datetime

router = Router()

class CombinationFSM(StatesGroup):
    selecting_hints = State()
    confirming_combination = State()

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

LUCIEN_BACKPACK_MESSAGES = [
    "Cada objeto en tu mochila cuenta una historia... ¿puedes leer entre líneas?",
    "Diana observa cómo organizas lo que te ha dado. Hay sabiduría en el orden.",
    "Algunos tesoros solo revelan su valor cuando se combinan con otros...",
    "Tu mochila no solo guarda objetos, guarda momentos compartidos con Diana.",
    "Hay pistas aquí que Diana espera que descifres. No todas son obvias."
]

@router.message(F.text == "🎒 Mochila")
async def mostrar_mochila_narrativa(message: Message):
    session_factory = await get_session()
    async with session_factory() as session:
        user_id = message.from_user.id

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

        categorized_hints = {}
        recent_hints = []

        for pista, unlocked_at, context in pistas_data:
            category = pista.category or 'fragmentos'
            if category not in categorized_hints:
                categorized_hints[category] = []
            categorized_hints[category].append((pista, unlocked_at, context))

            if unlocked_at and (datetime.now() - unlocked_at).days == 0:
                recent_hints.append(pista)

        lucien_message = random.choice(LUCIEN_BACKPACK_MESSAGES)
        total_hints = len(pistas_data)

        texto = f"🎩 **Lucien:**\n*{lucien_message}*\n\n"
        texto += f"📊 **Tu Colección:** {total_hints} pistas descubiertas\n"

        if recent_hints:
            texto += f"✨ **Nuevas:** {len(recent_hints)} pistas recientes\n"

        texto += "\n🎒 **Explora tu mochila:**"

        keyboard = []
        for category, data in categorized_hints.items():
            cat_info = BACKPACK_CATEGORIES.get(category, {
                'emoji': '📜', 'title': category.title(), 'description': 'Elementos diversos'
            })
            count = len(data)
            keyboard.append([
                InlineKeyboardButton(f"{cat_info['emoji']} {cat_info['title']} ({count})", callback_data=f"mochila_cat:{category}")
            ])

        keyboard.extend([
            [
                InlineKeyboardButton("🔗 Combinar Pistas", callback_data="combinar_inicio"),
                InlineKeyboardButton("🔍 Buscar", callback_data="buscar_pistas")
            ],
            [
                InlineKeyboardButton("📈 Estadísticas", callback_data="stats_mochila"),
                InlineKeyboardButton("🎯 Sugerencias", callback_data="sugerencias_diana")
            ]
        ])

        await message.answer(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data == "open_backpack")
async def open_backpack(callback: CallbackQuery):
    await mostrar_mochila_narrativa(callback.message)
    await callback.answer()

async def mostrar_mochila_vacia(message: Message):
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
        [InlineKeyboardButton("🎯 Ver Misiones", callback_data="misiones_disponibles")],
        [InlineKeyboardButton("📚 Guía del Viajero", callback_data="guia_principiante")]
    ]

    await message.answer(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
@router.callback_query(F.data.startswith("mochila_cat:"))
async def mostrar_categoria(callback: CallbackQuery):
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
            indicators = ""
            if context and context.get('is_combinable'):
                indicators += "🔗"
            if unlocked_at and (datetime.now() - unlocked_at).days == 0:
                indicators += "✨"

            button_text = f"{indicators} {pista.title}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"ver_pista_detail:{pista.id}")
            ])

        keyboard.append([
            InlineKeyboardButton("⬅️ Volver a Mochila", callback_data="volver_mochila")
        ])

        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ver_pista_detail:"))
async def ver_pista_detallada(callback: CallbackQuery):
    pista_id = int(callback.data.split(":")[1])
    session_factory = await get_session()

    async with session_factory() as session:
        user_id = callback.from_user.id

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

        texto = f"📜 **{pista.title}**\n"
        texto += f"🏷️ `{pista.code_name}`\n\n"

        if pista.description:
            texto += f"*{pista.description}*\n\n"

        if unlocked_at:
            dias_desde = (datetime.now() - unlocked_at).days
            if dias_desde == 0:
                texto += "⏰ Desbloqueada hoy\n"
            else:
                texto += f"⏰ Desbloqueada hace {dias_desde} días\n"

        if context:
            if context.get('source_mission'):
                texto += f"🎯 Obtenida en: {context['source_mission']}\n"
            if context.get('diana_message'):
                texto += f"💬 Diana: *{context['diana_message']}*\n"

        combinaciones_posibles = await verificar_combinaciones_disponibles(session, user_id, pista.code_name)
        if combinaciones_posibles:
            texto += f"\n🔗 **Combinable con:** {len(combinaciones_posibles)} pistas"

        keyboard = [
            [InlineKeyboardButton("👁️ Ver Contenido", callback_data=f"mostrar_contenido:{pista.id}")],
        ]

        if combinaciones_posibles:
            keyboard.append([
                InlineKeyboardButton("🔗 Combinar Ahora", callback_data=f"combinar_con:{pista.code_name}")
            ])

        keyboard.append([
            InlineKeyboardButton("⬅️ Volver", callback_data=f"mochila_cat:{pista.category or 'fragmentos'}")
        ])

        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
    @router.callback_query(F.data.startswith("mochila_cat:"))
async def mostrar_categoria(callback: CallbackQuery):
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
            indicators = ""
            if context and context.get('is_combinable'):
                indicators += "🔗"
            if unlocked_at and (datetime.now() - unlocked_at).days == 0:
                indicators += "✨"

            button_text = f"{indicators} {pista.title}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"ver_pista_detail:{pista.id}")
            ])

        keyboard.append([
            InlineKeyboardButton("⬅️ Volver a Mochila", callback_data="volver_mochila")
        ])

        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ver_pista_detail:"))
async def ver_pista_detallada(callback: CallbackQuery):
    pista_id = int(callback.data.split(":")[1])
    session_factory = await get_session()

    async with session_factory() as session:
        user_id = callback.from_user.id

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

        texto = f"📜 **{pista.title}**\n"
        texto += f"🏷️ `{pista.code_name}`\n\n"

        if pista.description:
            texto += f"*{pista.description}*\n\n"

        if unlocked_at:
            dias_desde = (datetime.now() - unlocked_at).days
            if dias_desde == 0:
                texto += "⏰ Desbloqueada hoy\n"
            else:
                texto += f"⏰ Desbloqueada hace {dias_desde} días\n"

        if context:
            if context.get('source_mission'):
                texto += f"🎯 Obtenida en: {context['source_mission']}\n"
            if context.get('diana_message'):
                texto += f"💬 Diana: *{context['diana_message']}*\n"

        combinaciones_posibles = await verificar_combinaciones_disponibles(session, user_id, pista.code_name)
        if combinaciones_posibles:
            texto += f"\n🔗 **Combinable con:** {len(combinaciones_posibles)} pistas"

        keyboard = [
            [InlineKeyboardButton("👁️ Ver Contenido", callback_data=f"mostrar_contenido:{pista.id}")],
        ]

        if combinaciones_posibles:
            keyboard.append([
                InlineKeyboardButton("🔗 Combinar Ahora", callback_data=f"combinar_con:{pista.code_name}")
            ])

        keyboard.append([
            InlineKeyboardButton("⬅️ Volver", callback_data=f"mochila_cat:{pista.category or 'fragmentos'}")
        ])

        await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
    @router.callback_query(F.data.startswith("select_hint:"), CombinationFSM.selecting_hints)
async def seleccionar_pista_combinacion(callback: CallbackQuery, state: FSMContext):
    hint_code = callback.data.split(":")[1]
    data = await state.get_data()
    selected_hints = data.get('selected_hints', [])

    if hint_code in selected_hints:
        selected_hints.remove(hint_code)
        await callback.answer("❌ Pista deseleccionada")
    else:
        selected_hints.append(hint_code)
        await callback.answer("✅ Pista seleccionada")

    await state.update_data(selected_hints=selected_hints)

    texto = f"""🔗 **Sistema de Combinaciones**

**Pistas seleccionadas:** {len(selected_hints)}
{chr(10).join([f"• `{code}`" for code in selected_hints])}

**Selecciona más pistas o intenta la combinación:**"""

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
            InlineKeyboardButton(f"{indicator} {pista.title}", callback_data=f"select_hint:{pista.code_name}")
        ])

    keyboard.append([
        InlineKeyboardButton("🔗 Intentar Combinación", callback_data="try_combination"),
        InlineKeyboardButton("❌ Cancelar", callback_data="volver_mochila")
    ])

    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

@router.callback_query(F.data == "try_combination", CombinationFSM.selecting_hints)
async def procesar_combinacion_seleccionada(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_hints = data.get('selected_hints', [])

    if len(selected_hints) < 2:
        await callback.answer("❌ Selecciona al menos 2 pistas")
        return

    session_factory = await get_session()
    async with session_factory() as session:
        user_id = callback.from_user.id

        result = await session.execute(select(HintCombination))
        combinaciones = result.scalars().all()

        for combinacion in combinaciones:
            required_hints = sorted(combinacion.required_hints.split(","))
            user_hints = sorted(selected_hints)

            if user_hints == required_hints:
                await desbloquear_pista_narrativa(callback.message.bot, user_id, combinacion.reward_code, {
                    'source': 'combination',
                    'combined_hints': selected_hints,
                    'combination_code': combinacion.combination_code
                })

                await mostrar_exito_combinacion(callback, combinacion, selected_hints)
                await state.clear()
                return

        await mostrar_fallo_combinacion(callback, selected_hints)
        await state.clear()
        async def mostrar_exito_combinacion(callback: CallbackQuery, combinacion, hints_used):
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
        [InlineKeyboardButton("🎒 Ver Mochila", callback_data="volver_mochila")],
        [InlineKeyboardButton("🔍 Ver Nueva Pista", callback_data=f"buscar_code:{combinacion.reward_code}")]
    ]

    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

async def mostrar_fallo_combinacion(callback: CallbackQuery, hints_used):
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
        [InlineKeyboardButton("🔗 Intentar Otra Vez", callback_data="combinar_inicio")],
        [InlineKeyboardButton("🎒 Volver a Mochila", callback_data="volver_mochila")]
    ]

    await callback.message.edit_text(texto, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")

async def verificar_combinaciones_disponibles(session, user_id, hint_code):
    result = await session.execute(
        select(LorePiece.code_name)
        .join(UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id)
        .where(UserLorePiece.user_id == user_id)
    )
    user_hint_codes = [row[0] for row in result.all()]

    result = await session.execute(select(HintCombination))
    combinaciones = result.scalars().all()

    combinaciones_posibles = []
    for combo in combinaciones:
        required_hints = combo.required_hints.split(",")
        if hint_code in required_hints:
            if all(req_hint in user_hint_codes for req_hint in required_hints):
                combinaciones_posibles.append(combo)

    return combinaciones_posibles
    async def desbloquear_pista_narrativa(bot, user_id, pista_code, context=None):
    session_factory = await get_session()
    async with session_factory() as session:
        result = await session.execute(
            select(LorePiece).where(LorePiece.code_name == pista_code)
        )
        pista = result.scalar_one_or_none()

        if not pista:
            return False

        existing = await session.execute(
            select(UserLorePiece).where(
                and_(
                    UserLorePiece.user_id == user_id,
                    UserLorePiece.lore_piece_id == pista.id
                )
            )
        )

        if existing.scalar_one_or_none():
            return False

        user_lore_piece = UserLorePiece(
            user_id=user_id,
            lore_piece_id=pista.id,
            context=context or {}
        )

        session.add(user_lore_piece)
        await session.commit()

        await send_narrative_notification(bot, user_id, "new_hint", {
            'hint_title': pista.title,
            'hint_code': pista.code_name,
            'source': context.get('source', 'unknown') if context else 'unknown'
        })

        return True

@router.callback_query(F.data == "volver_mochila")
async def volver_mochila(callback: CallbackQuery):
    await mostrar_mochila_narrativa(callback.message)

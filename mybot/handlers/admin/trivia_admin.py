from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from states.trivia_admin_states import TriviaAdminStates
from services.trivia_admin_service import TriviaAdminService

router = Router()


async def show_trivia_main_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    service = TriviaAdminService(session)
    stats = await service.get_trivia_stats()
    text = "🎯 **ADMINISTRACIÓN DE TRIVIAS**\n\n"
    text += f"📝 Total preguntas: {stats['total_questions']}\n"
    text += f"📋 Templates activos: {stats['active_templates']}\n"
    text += f"🎮 Sesiones activas: {stats['active_sessions']}\n"
    text += f"👥 Jugadores hoy: {stats['players_today']}\n\n"
    text += "Selecciona una opción:"

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Gestionar Preguntas", callback_data="admin_trivia_questions")
    builder.button(text="📋 Gestionar Templates", callback_data="admin_trivia_templates")
    builder.button(text="🎮 Sesiones Activas", callback_data="admin_trivia_sessions")
    builder.button(text="📊 Analytics", callback_data="admin_trivia_analytics")
    builder.button(text="⚙️ Configuración", callback_data="admin_trivia_config")
    builder.button(text="🔙 Volver al Panel", callback_data="admin_main_menu")
    builder.adjust(2, 2, 1, 1)

    await update_menu(callback, text, builder.as_markup(), session, "admin_trivia_main")


@router.callback_query(F.data == "admin_trivia_main")
async def trivia_admin_main(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer("❌ No tienes permisos para gestionar trivias", show_alert=True)

    await show_trivia_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "admin_trivia_questions")
async def trivia_questions_menu(callback: CallbackQuery, session: AsyncSession):
    service = TriviaAdminService(session)
    questions = await service.get_questions_summary()

    text = "📝 **GESTIÓN DE PREGUNTAS**\n\n"
    text += f"Total: {len(questions)} preguntas\n\n"
    text += "📋 **Últimas preguntas:**\n"
    for q in questions[:5]:
        text += f"• {q['id'][:8]}... - {q['question'][:50]}...\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Nueva Pregunta", callback_data="admin_question_new")
    builder.button(text="📋 Listar Todas", callback_data="admin_questions_list")
    builder.button(text="🔍 Buscar", callback_data="admin_questions_search")
    builder.button(text="📊 Estadísticas", callback_data="admin_questions_stats")
    builder.button(text="📤 Importar", callback_data="admin_questions_import")
    builder.button(text="📥 Exportar", callback_data="admin_questions_export")
    builder.button(text="🔙 Volver", callback_data="admin_trivia_main")
    builder.adjust(2, 2, 2, 1)

    await update_menu(callback, text, builder.as_markup(), session, "admin_trivia_questions")


class QuestionCRUD:
    @staticmethod
    async def create_question_flow(callback: CallbackQuery, state: FSMContext):
        await state.set_state(TriviaAdminStates.waiting_question_text)
        text = "📝 **NUEVA PREGUNTA**\n\n"
        text += "Paso 1/7: Escribe el texto de la pregunta\n\n"
        text += "💡 Consejos:\n"
        text += "• Sé claro y específico\n"
        text += "• Evita ambigüedades\n"
        text += "• Máximo 500 caracteres\n\n"
        text += "Escribe tu pregunta:"
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancelar", callback_data="admin_questions_cancel")
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="Markdown")

    @staticmethod
    async def list_questions_paginated(callback: CallbackQuery, session: AsyncSession, page: int = 1):
        service = TriviaAdminService(session)
        per_page = 10
        questions = await service.get_questions_paginated(page, per_page)
        total_pages = await service.get_total_question_pages(per_page)

        text = f"📋 **LISTA DE PREGUNTAS** (Página {page}/{total_pages})\n\n"
        for i, q in enumerate(questions, start=(page - 1) * per_page + 1):
            difficulty = q.difficulty or 1
            difficulty_stars = "⭐" * difficulty
            text += f"{i}. `{q.id[:8]}` - {q.question[:40]}...\n   {q.question_type.replace('_', ' ').title()} {difficulty_stars}\n\n"

        builder = InlineKeyboardBuilder()
        if page > 1:
            builder.button(text="⬅️", callback_data=f"questions_page_{page-1}")
        builder.button(text=f"{page}/{total_pages}", callback_data="questions_current_page")
        if page < total_pages:
            builder.button(text="➡️", callback_data=f"questions_page_{page+1}")
        builder.row(
            InlineKeyboardButton(text="➕ Nueva", callback_data="admin_question_new"),
            InlineKeyboardButton(text="🔍 Buscar", callback_data="admin_questions_search"),
        )
        builder.button(text="🔙 Volver", callback_data="admin_trivia_questions")
        await update_menu(callback, text, builder.as_markup(), session, "admin_questions_list")

@router.callback_query(F.data == "admin_question_new")
async def start_new_question(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await QuestionCRUD.create_question_flow(callback, state)
    await callback.answer()


@router.callback_query(F.data == "admin_questions_list")
async def list_questions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await QuestionCRUD.list_questions_paginated(callback, session, 1)
    await callback.answer()


@router.callback_query(F.data.startswith("questions_page_"))
async def paginate_questions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    try:
        page = int(callback.data.split("_")[-1])
    except ValueError:
        page = 1
    await QuestionCRUD.list_questions_paginated(callback, session, page)
    await callback.answer()

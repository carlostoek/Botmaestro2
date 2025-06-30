from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from services.trivia_service import TriviaService
from keyboards.admin_trivia_kb import trivia_admin_main_kb
from utils.messages import TRIVIA_ADMIN_MENU
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb
from utils.user_roles import is_admin
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "🛠️ Administrar Trivias")
async def admin_trivia_menu(message: Message):
    await message.answer(TRIVIA_ADMIN_MENU, reply_markup=trivia_admin_main_kb())

@router.callback_query(F.data == "list_trivias")
async def list_trivias(call: CallbackQuery, session: AsyncSession):
    trivias = await TriviaService.get_active_trivias(session)
    text = "\n".join(f"{t.id}. {t.title}" for t in trivias) or "Sin trivias activas."
    await call.message.edit_text(f"📚 *Trivias activas:*\n{text}", parse_mode="Markdown", reply_markup=trivia_admin_main_kb())


@router.callback_query(F.data == "create_trivia")
async def create_trivia_callback(callback: CallbackQuery, session: AsyncSession):
    """Handle new trivia creation button."""
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    await callback.answer("Abriendo menú de creación...")

    try:
        await update_menu(
            callback,
            "🚧 Función de creación de trivias en construcción.",
            get_back_kb("admin_main_menu"),
            session,
            "admin_create_trivia",
        )
    except Exception as e:
        logger.error(f"Error showing trivia creation menu: {e}")
        await callback.message.answer(
            "❌ Error al abrir el menú de creación de trivia."
        )

# Aquí agregas más funciones para crear, editar y eliminar trivias y preguntas.

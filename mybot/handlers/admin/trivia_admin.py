from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from services.trivia_service import TriviaService
from keyboards.admin_trivia_kb import trivia_admin_main_kb
from utils.messages import TRIVIA_ADMIN_MENU

router = Router()

@router.message(F.text == "🛠️ Administrar Trivias")
async def admin_trivia_menu(message: Message):
    await message.answer(TRIVIA_ADMIN_MENU, reply_markup=trivia_admin_main_kb())

@router.callback_query(F.data == "list_trivias")
async def list_trivias(call: CallbackQuery, session: AsyncSession):
    trivias = await TriviaService.get_active_trivias(session)
    text = "\n".join(f"{t.id}. {t.title}" for t in trivias) or "Sin trivias activas."
    await call.message.edit_text(f"📚 *Trivias activas:*\n{text}", parse_mode="Markdown", reply_markup=trivia_admin_main_kb())

# Aquí agregas más funciones para crear, editar y eliminar trivias y preguntas.

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from keyboards.admin_trivia_kb import get_admin_trivia_main_kb

router = Router()

async def show_trivia_main_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await menu_manager.update_menu(
        callback,
        "🎲 **Administración de Trivias**",
        get_admin_trivia_main_kb(),
        session,
        "admin_trivia_main",
    )

@router.callback_query(F.data == "admin_trivia_main")
async def trivia_admin_main(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer("❌ No tienes permisos para gestionar trivias", show_alert=True)

    await show_trivia_main_menu(callback, session)
    await callback.answer()

@router.callback_query(F.data == "admin_trivia_questions")
async def trivia_questions_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Gestión de preguntas próximamente", show_alert=True)

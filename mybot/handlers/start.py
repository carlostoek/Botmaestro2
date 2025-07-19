"""
Enhanced start handler with improved user experience and multi-tenant support.
"""
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin, clear_role_cache
from utils.menu_factory import menu_factory

router = Router()

@router.message(Command("start"))
async def start_handler(
    message: types.Message, 
    session: AsyncSession
):
    # Limpiar cache si es necesario (ejemplo: después de cambios de rol)
    # clear_role_cache(message.from_user.id)
    
    welcome_text = "¡Bienvenido al bot!"
    keyboard = await menu_factory(
        user_id=message.from_user.id,
        session=session
    )
    await message.answer(welcome_text, reply_markup=keyboard)

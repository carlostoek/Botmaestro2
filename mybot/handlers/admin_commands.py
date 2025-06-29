from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, Document
from utils.admin_state import DatabaseUpdateStates
from utils.menu_manager import menu_manager
from sqlalchemy.ext.asyncio import create_async_engine
from utils.config import Config
import os

router = Router()

@router.message(Command("update_database"))
async def start_database_update(message: Message, state: FSMContext):
    if not await menu_manager.is_admin(message.from_user.id):
        await message.answer("\u26D4 No tienes permiso para usar este comando.")
        return

    await message.answer("\U0001F4C2 Por favor, envía el archivo SQL que deseas ejecutar.")
    await state.set_state(DatabaseUpdateStates.waiting_for_sql)

@router.message(F.document, state=DatabaseUpdateStates.waiting_for_sql)
async def process_sql_file(message: Message, state: FSMContext):
    document: Document = message.document
    if not document.file_name.endswith('.sql'):
        await message.answer("\u274C El archivo debe tener extensión .sql.")
        return

    file = await message.bot.get_file(document.file_id)
    file_path = f"temp/{document.file_name}"
    await message.bot.download_file(file.file_path, destination=file_path)

    try:
        await execute_sql_file(file_path)
        await message.answer("\u2705 Base de datos actualizada correctamente.")
    except Exception as e:
        await message.answer(f"\u274C Error al ejecutar el archivo SQL: {str(e)}")
    finally:
        os.remove(file_path)
        await state.clear()

async def execute_sql_file(file_path):
    engine = create_async_engine(Config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_commands = file.read()
        await conn.execute(sql_commands)

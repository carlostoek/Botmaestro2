from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from utils.user_roles import is_admin
from database.setup import get_session
from database.hint_model import Hint

router = Router()

class HintCreation(StatesGroup):
    waiting_for_code_name = State()
    waiting_for_type = State()
    waiting_for_content = State()

@router.message(Command("crear_pista"))
async def start_hint_creation(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Ingrese el nombre clave de la pista:")
    await state.set_state(HintCreation.waiting_for_code_name)

@router.message(StateFilter(HintCreation.waiting_for_code_name))
async def process_code_name(message: Message, state: FSMContext):
    await state.update_data(code_name=message.text.strip())
    await message.answer("Ingrese el tipo de la pista: 'text', 'image', o 'video'")
    await state.set_state(HintCreation.waiting_for_type)

@router.message(StateFilter(HintCreation.waiting_for_type))
async def process_hint_type(message: Message, state: FSMContext):
    hint_type = message.text.strip().lower()
    if hint_type not in ['text', 'image', 'video']:
        await message.answer("Tipo no válido. Ingrese: 'text', 'image', o 'video'")
        return
    await state.update_data(hint_type=hint_type)
    await message.answer("Ingrese el contenido de la pista (texto o URL del archivo):")
    await state.set_state(HintCreation.waiting_for_content)

@router.message(StateFilter(HintCreation.waiting_for_content))
async def process_hint_content(message: Message, state: FSMContext):
    session_factory = await get_session()
    async with session_factory() as session:
        data = await state.get_data()

        new_hint = Hint(
            code_name=data['code_name'],
            hint_type=data['hint_type'],
            content=message.text.strip()
        )
        session.add(new_hint)
        await session.commit()

    await message.answer(f"Pista '{data['code_name']}' creada exitosamente.")
    await state.clear()

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from utils.keyboard_utils import (
    get_admin_content_trivia_keyboard,
)
from keyboards.common import get_back_keyboard
from utils.admin_state import AdminTriviaStates
from services.trivia_service import TriviaService

router = Router()


@router.callback_query(F.data == "admin_content_trivia")
async def admin_content_trivia(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "❓ Gestionar Trivias - Selecciona una opción:",
        get_admin_content_trivia_keyboard(),
        session,
        "admin_content_trivia",
    )
    await callback.answer()


async def show_trivia_page(message: Message, session: AsyncSession, page: int = 0) -> None:
    limit = 5
    if page < 0:
        page = 0

    service = TriviaService(session)
    trivias, total = await service.list_trivias(offset=page * limit, limit=limit)

    lines = []
    for t in trivias:
        lines.append(
            f"ID {t.id}: {t.question[:40]}... ({t.reward_points} pts)"
        )

    text = "\n".join(lines) if lines else "No hay trivias registradas."

    keyboard: list[list[InlineKeyboardButton]] = []
    from utils.pagination import get_pagination_buttons

    for t in trivias:
        keyboard.append(
            [
                InlineKeyboardButton(text="✏️", callback_data=f"trivia_edit:{t.id}"),
                InlineKeyboardButton(text="🗑", callback_data=f"trivia_delete:{t.id}"),
            ]
        )

    total_pages = (total + limit - 1) // limit
    nav = get_pagination_buttons(page, total_pages, "trivia_page")
    if nav:
        keyboard.append(nav)

    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_trivia")])
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(F.data == "admin_trivia_list")
async def admin_trivia_list(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_trivia_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("trivia_page:"))
async def trivia_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    try:
        page = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        page = 0
    await show_trivia_page(callback.message, session, page)
    await callback.answer()


@router.callback_query(F.data == "admin_trivia_create")
async def trivia_create_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Código de activación de la trivia:",
        reply_markup=get_back_keyboard("admin_content_trivia"),
    )
    await state.set_state(AdminTriviaStates.creating_trigger)
    await callback.answer()


from keyboards.common import get_back_keyboard

@router.message(AdminTriviaStates.creating_trigger)
async def trivia_create_trigger(message: Message, state: FSMContext):
    await state.update_data(trigger_code=message.text.strip())
    await message.answer("Pregunta de la trivia:")
    await state.set_state(AdminTriviaStates.creating_question)


@router.message(AdminTriviaStates.creating_question)
async def trivia_create_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Opciones separadas por '|':")
    await state.set_state(AdminTriviaStates.creating_options)


@router.message(AdminTriviaStates.creating_options)
async def trivia_create_options(message: Message, state: FSMContext):
    opts = [o.strip() for o in message.text.split("|") if o.strip()]
    await state.update_data(options=opts)
    await message.answer("Índice de la respuesta correcta (empezando en 1):")
    await state.set_state(AdminTriviaStates.creating_correct)


@router.message(AdminTriviaStates.creating_correct)
async def trivia_create_correct(message: Message, state: FSMContext):
    try:
        idx = int(message.text) - 1
    except ValueError:
        await send_temporary_reply(message, "Número inválido")
        return
    await state.update_data(correct_index=idx)
    await message.answer("Puntos por respuesta correcta (0 para ninguno):")
    await state.set_state(AdminTriviaStates.creating_reward)


@router.message(AdminTriviaStates.creating_reward)
async def trivia_create_reward(message: Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await send_temporary_reply(message, "Número inválido")
        return
    await state.update_data(reward_points=points)
    await message.answer("Código de pista a desbloquear ('-' para omitir):")
    await state.set_state(AdminTriviaStates.creating_unlock)


@router.message(AdminTriviaStates.creating_unlock)
async def trivia_create_unlock(message: Message, state: FSMContext, session: AsyncSession):
    code = message.text.strip()
    if code == "-":
        code = None
    data = await state.get_data()
    service = TriviaService(session)
    await service.create_trivia(
        data["trigger_code"],
        data["question"],
        data["options"],
        data["correct_index"],
        data["reward_points"],
        unlocks_lore_piece_code=code,
    )
    await message.answer(
        "Trivia creada.", reply_markup=get_back_keyboard("admin_content_trivia")
    )
    await state.clear()


@router.callback_query(F.data.startswith("trivia_delete:"))
async def trivia_delete(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    tid = int(callback.data.split(":", 1)[1])
    service = TriviaService(session)
    await service.delete_trivia(tid)
    await callback.answer("Eliminada", show_alert=True)
    await show_trivia_page(callback.message, session, 0)


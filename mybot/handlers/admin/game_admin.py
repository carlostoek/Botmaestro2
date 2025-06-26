from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime

from utils.user_roles import is_admin
from utils.menu_utils import update_menu, send_temporary_reply
from utils.keyboard_utils import (
    get_admin_manage_users_keyboard,
    get_admin_users_list_keyboard,
    get_back_keyboard,
    get_admin_manage_content_keyboard,
    get_admin_content_missions_keyboard,
    get_admin_content_badges_keyboard,
    get_admin_content_levels_keyboard,
    get_admin_content_rewards_keyboard,
    get_admin_content_auctions_keyboard,
    get_admin_content_daily_gifts_keyboard,
    get_admin_content_minigames_keyboard,
    get_badge_selection_keyboard,
    get_reward_type_keyboard,
    get_mission_reward_type_keyboard,
)
from .missions_admin import show_missions_page
from .levels_admin import show_levels_page
from utils.admin_state import (
    AdminUserStates,
    AdminMissionStates,
    AdminBadgeStates,
    AdminDailyGiftStates,
    AdminRewardStates,
    AdminLevelStates,
)
from services.mission_service import MissionService
from services.reward_service import RewardService
from services.level_service import LevelService
from database.models import User, Mission, Level, Badge # Import Badge model
from services.point_service import PointService
from services.config_service import ConfigService
from services.badge_service import BadgeService
from utils.messages import BOT_MESSAGES

router = Router()


async def show_users_page(message: Message, session: AsyncSession, offset: int) -> None:
    """Display a paginated list of users with action buttons."""
    limit = 5
    if offset < 0:
        offset = 0

    total_stmt = select(func.count()).select_from(User)
    total_result = await session.execute(total_stmt)
    total_users = total_result.scalar_one()

    stmt = (
        select(User)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    text_lines = [
        "👥 Gestión de Usuarios",
        f"Mostrando {offset + 1}-{min(offset + limit, total_users)} de {total_users}",
        "",
    ]

    for user in users:
        display = user.username or (user.first_name or "Sin nombre")
        text_lines.append(f"- {display} (ID: {user.id}) - {user.points} pts")

    keyboard = get_admin_users_list_keyboard(users, offset, total_users, limit)

    await message.edit_text("\n".join(text_lines), reply_markup=keyboard)


@router.callback_query(F.data == "admin_manage_users")
async def admin_manage_users(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_users_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users_page_"))
async def admin_users_page(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    try:
        offset = int(callback.data.split("_")[-1])
    except ValueError:
        offset = 0
    await show_users_page(callback.message, session, offset)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_add_"))
async def admin_user_add(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="add", target_user=user_id)
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a sumar a {user_id}:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.assigning_points_amount)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_deduct_"))
async def admin_user_deduct(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(points_operation="deduct", target_user=user_id)
    await callback.message.answer(
        f"Ingresa la cantidad de puntos a restar a {user_id}:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.assigning_points_amount)
    await callback.answer()


@router.message(AdminUserStates.assigning_points_amount)
async def process_points_amount(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    try:
        amount = int(message.text)
    except ValueError:
        await send_temporary_reply(message, "Cantidad inválida. Ingresa un número.")
        return
    user_id = data.get("target_user")
    op = data.get("points_operation")
    service = PointService(session)
    if op == "add":
        await service.add_points(user_id, amount)
        await message.answer(f"Se han sumado {amount} puntos a {user_id}.")
    else:
        await service.deduct_points(user_id, amount)
        await message.answer(f"Se han restado {amount} puntos a {user_id}.")
    await state.clear()


@router.callback_query(F.data.startswith("admin_user_view_"))
async def admin_view_user(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    user_id = int(callback.data.split("_")[-1])
    user = await session.get(User, user_id)
    if not user:
        await callback.answer("Usuario no encontrado", show_alert=True)
        return
    display = user.username or (user.first_name or "Sin nombre")
    await callback.message.answer(f"Perfil de {display}\nPuntos: {user.points}")
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa un ID o nombre de usuario:",
        reply_markup=get_back_keyboard("admin_manage_users"),
    )
    await state.set_state(AdminUserStates.search_user_query)
    await callback.answer()


@router.message(AdminUserStates.search_user_query)
async def process_search_user(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()
    users = []
    if query.isdigit():
        user = await session.get(User, int(query))
        if user:
            users = [user]
    else:
        stmt = select(User).where(
            (User.username.ilike(f"%{query}%")) |
            (User.first_name.ilike(f"%{query}%")) |
            (User.last_name.ilike(f"%{query}%"))
        ).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()

    if not users:
        await send_temporary_reply(message, "No se encontraron usuarios.")
    else:
        response = "Resultados:\n" + "\n".join(
            f"- {(u.username or u.first_name or 'Sin nombre')} (ID: {u.id})" for u in users
        )
        await message.answer(response)
    await state.clear()


@router.callback_query(F.data == "admin_content_missions")
async def admin_content_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await show_missions_page(callback.message, session, 0)
    await callback.answer()


@router.callback_query(F.data == "toggle_daily_gift")
async def toggle_daily_gift(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    service = ConfigService(session)
    current = await service.get_value("daily_gift_enabled")
    new_value = "false" if current == "true" else "true"
    await service.set_value("daily_gift_enabled", new_value)
    await callback.answer("Configuración actualizada", show_alert=True)
    # The original error log indicated a syntax error in game_admin.py.
    # If admin_content_daily_gifts is in game_admin.py, this line would have caused the crash.
    # Assuming this function is now correctly defined elsewhere or has been fixed:
    from .game_admin import admin_content_daily_gifts # Ensure this import is handled correctly
    await admin_content_daily_gifts(callback, session)


@router.callback_query(F.data == "admin_create_mission")
async def admin_start_create_mission(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "Ingresa el nombre de la misión:",
        reply_markup=get_back_keyboard("admin_content_missions"),
    )
    await state.set_state(AdminMissionStates.creating_mission_name)
    await callback.answer()


@router.message(AdminMissionStates.creating_mission_name)
async def admin_process_mission_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Ingresa la descripción de la misión:")
    await state.set_state(AdminMissionStates.creating_mission_description)


@router.message(AdminMissionStates.creating_mission_description)
async def admin_process_mission_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 Reaccionar a publicaciones", callback_data="mission_type_reaction")],
            [InlineKeyboardButton(text="📝 Enviar mensajes", callback_data="mission_type_messages")],
            [InlineKeyboardButton(text="📅 Conectarse X días seguidos", callback_data="mission_type_login")],
            [InlineKeyboardButton(text="🎯 Personalizada", callback_data="mission_type_custom")],
        ]
    )
    await message.answer("🎯 Tipo de misión", reply_markup=kb)
    await state.set_state(AdminMissionStates.creating_mission_type)


@router.callback_query(F.data.startswith("mission_type_"))
async def admin_select_mission_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    m_type = callback.data.split("mission_type_")[-1]
    mapping = {
        "reaction": "reaction",
        "messages": "messages",
        "login": "login_streak",
        "custom": "custom",
    }
    await state.update_data(mission_type=mapping.get(m_type, m_type))
    await callback.message.edit_text("📊 Cantidad requerida")
    await state.set_state(AdminMissionStates.creating_mission_target)
    await callback.answer()


@router.message(AdminMissionStates.creating_mission_target)
async def admin_process_target(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        value = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido:")
        return
    await state.update_data(target=value)
    await message.answer("🏆 Recompensa en puntos")
    await state.set_state(AdminMissionStates.creating_mission_reward_points)


@router.message(AdminMissionStates.creating_mission_reward_points)
async def admin_process_reward_points(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido de puntos:")
        return
    await state.update_data(reward_points=points)
    # Preguntar por el tipo de recompensa adicional
    await message.answer(
        "Selecciona el tipo de recompensa adicional:",
        reply_markup=get_mission_reward_type_keyboard(),
    )
    await state.set_state(AdminMissionStates.creating_mission_reward_type)


@router.callback_query(F.data.startswith("mission_reward_type_"))
async def admin_select_mission_reward_type(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()

    selected_type = callback.data.split("mission_reward_type_")[-1]
    await state.update_data(reward_type=selected_type)

    if selected_type == "points":
        await callback.message.edit_text("⏳ Duración (en días, 0 para permanente)")
        await state.set_state(AdminMissionStates.creating_mission_duration)
    elif selected_type == "text":
        await callback.message.edit_text("Ingresa el texto de la recompensa:")
        await state.set_state(AdminMissionStates.creating_mission_reward_content)
    elif selected_type == "photo":
        await callback.message.edit_text("Envía la imagen para la recompensa:")
        await state.set_state(AdminMissionStates.creating_mission_reward_content)
    elif selected_type == "video":
        await callback.message.edit_text("Envía el video para la recompensa:")
        await state.set_state(AdminMissionStates.creating_mission_reward_content)

    await callback.answer()


@router.message(AdminMissionStates.creating_mission_reward_content)
async def admin_process_reward_content(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    reward_type = data.get("reward_type")
    reward_content = None

    if reward_type == "text":
        reward_content = message.text
    elif reward_type == "photo" and message.photo:
        reward_content = message.photo[-1].file_id
    elif reward_type == "video" and message.video:
        reward_content = message.video.file_id
    else:
        await send_temporary_reply(message, f"Por favor, envía un {reward_type} válido.")
        return

    await state.update_data(reward_content=reward_content)
    await message.answer("⏳ Duración (en días, 0 para permanente)")
    await state.set_state(AdminMissionStates.creating_mission_duration)


@router.message(AdminMissionStates.creating_mission_duration)
async def admin_process_duration(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    try:
        days = int(message.text)
    except ValueError:
        await message.answer("Ingresa un número válido de días:")
        return
    data = await state.get_data()
    mission_service = MissionService(session)
    await mission_service.create_mission(
        data["name"],
        data["description"],
        data["mission_type"],
        data["target"],
        data["reward_points"],
        reward_type=data.get("reward_type", "points"),
        reward_content=data.get("reward_content"),
        duration_days=days,
        channel_type="vip",
    )
    await message.answer(
        "✅ Misión creada correctamente", reply_markup=get_admin_content_missions_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "admin_toggle_mission")
async def admin_toggle_mission_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = []
    for m in missions:
        status = "✅" if m.is_active else "❌"
        keyboard.append(
            [InlineKeyboardButton(text=f"{status} {m.name}", callback_data=f"toggle_mission_{m.id}")]
        )
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Activar o desactivar misiones:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_mission_"))
async def toggle_mission_status(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = int(callback.data.split("toggle_mission_")[-1]) # Convert to int
    mission_service = MissionService(session)
    mission = await mission_service.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    await mission_service.toggle_mission_status(mission_id, not mission.is_active)
    status = "activada" if not mission.is_active else "desactivada"
    await callback.answer(f"Misión {status}", show_alert=True)
    # Refresh list
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = []
    for m in missions:
        status_icon = "✅" if m.is_active else "❌"
        keyboard.append(
            [InlineKeyboardButton(text=f"{status_icon} {m.name}", callback_data=f"toggle_mission_{m.id}")]
        )
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Activar o desactivar misiones:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data == "admin_view_missions")
async def admin_view_active_missions(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    stmt = select(Mission).where(Mission.is_active == True)
    result = await session.execute(stmt)
    missions = result.scalars().all()
    now = datetime.datetime.utcnow()
    lines = []
    for m in missions:
        remaining = "∞"
        if m.duration_days:
            end = m.created_at + datetime.timedelta(days=m.duration_days)
            remaining = str((end - now).days)
        lines.append(f"🗒️ {m.name} | 📊 {m.target_value} | 🎁 {m.reward_points} | ⏳ {remaining}d")
    text = "Misiones activas:" if lines else "No hay misiones activas."
    if lines:
        text += "\n" + "\n".join(lines)
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard("admin_content_missions"),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_delete_mission")
async def admin_delete_mission_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    result = await session.execute(select(Mission))
    missions = result.scalars().all()
    keyboard = [[InlineKeyboardButton(text=m.name, callback_data=f"delete_mission_{m.id}")] for m in missions]
    keyboard.append([InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_missions")])
    await callback.message.edit_text(
        "Selecciona la misión a eliminar:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_mission_"))
async def admin_confirm_delete_mission(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = int(callback.data.split("delete_mission_")[-1]) # Convert to int
    mission = await session.get(Mission, mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Confirmar", callback_data=f"confirm_delete_{mission_id}")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="admin_delete_mission")],
        ]
    )
    await callback.message.edit_text(
        f"¿Eliminar misión {mission.name}?",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_"))
async def admin_delete_mission(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    mission_id = int(callback.data.split("confirm_delete_")[-1]) # Convert to int
    service = MissionService(session)
    await service.delete_mission(mission_id)
    await callback.message.edit_text(
        "❌ Misión eliminada",
        reply_markup=get_admin_content_missions_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_content_badges")
async def admin_content_badges(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await update_menu(
        callback,
        "🏅 Insignias - Selecciona una opción:",
        get_admin_content_badges_keyboard(),
        session,
        "admin_content_badges",
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_badge")
async def admin_create_badge(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.edit_text(
        "📛 Nombre de la insignia:",
        reply_markup=get_back_keyboard("admin_content_badges"),
    )
    await state.set_state(AdminBadgeStates.creating_badge_name)
    await callback.answer()


@router.message(AdminBadgeStates.creating_badge_name)
async def badge_name_step(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await message.answer("📝 Descripción (corta):")
    await state.set_state(AdminBadgeStates.creating_badge_description)


@router.message(AdminBadgeStates.creating_badge_requirement)
async def badge_requirement_step(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(requirement=message.text.strip())
    await message.answer("🖼️ Emoji o símbolo (opcional, escribe 'no' para omitir):")
    await state.set_state(AdminBadgeStates.creating_badge_emoji)

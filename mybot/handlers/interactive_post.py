from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from keyboards.common import get_interactive_post_kb

router = Router()


@router.callback_query(F.data.startswith("ip_"))
async def handle_interactive_post_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    parts = callback.data.split("_")
    if len(parts) < 3:
        return await callback.answer()
    reaction_type = parts[1]  # e.g. 'r0'
    try:
        message_id = int(parts[2])
    except ValueError:
        return await callback.answer()

    service = MessageService(session, bot)
    reaction = await service.register_reaction(
        callback.from_user.id, message_id, reaction_type
    )
    if reaction is None:
        from utils.messages import BOT_MESSAGES

        await callback.answer(BOT_MESSAGES["reaction_already"])
        return
    from services.point_service import PointService
    from services.config_service import ConfigService
    from utils.messages import BOT_MESSAGES

    config = ConfigService(session)
    points_list = await config.get_reaction_points()
    idx = 0
    try:
        idx = int(reaction_type[1:])
    except (ValueError, IndexError):
        pass
    points = points_list[idx] if idx < len(points_list) else 0.0
    await PointService(session).add_points(callback.from_user.id, points, bot=bot)
    await callback.answer(
        BOT_MESSAGES["reaction_registered_points"].format(points=points)
    )

    # Update reaction counts on the message
    buttons = await config.get_reaction_buttons()
    counts = await service.get_reaction_counts(message_id, buttons)
    try:
        await bot.edit_message_reply_markup(
            callback.message.chat.id,
            message_id,
            reply_markup=get_interactive_post_kb(message_id, buttons, counts),
        )
    except TelegramAPIError:
        pass


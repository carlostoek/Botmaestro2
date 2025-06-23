from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from services.channel_service import ChannelService
from services.config_service import ConfigService

router = Router()


@router.callback_query(F.data.startswith("ip_"))
async def handle_interactive_post_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    parts = callback.data.split("_")
    channel_id = None
    if len(parts) == 4:
        # New format: ip_<channel_id>_r<idx>_<message_id>
        try:
            channel_id = int(parts[1])
            reaction_type = parts[2]
            message_id = int(parts[3])
        except ValueError:
            return await callback.answer()
    elif len(parts) >= 3:
        # Legacy format without channel id
        reaction_type = parts[1]
        try:
            message_id = int(parts[2])
        except ValueError:
            return await callback.answer()
        config = ConfigService(session)
        channel_id = await config.get_vip_channel_id()
    
    service = MessageService(session, bot)

    reaction = await service.register_reaction(
        callback.from_user.id, message_id, reaction_type
    )
    if reaction is None:
        from utils.messages import BOT_MESSAGES

        await callback.answer(BOT_MESSAGES["reaction_already"])

        return
    from services.point_service import PointService
    from utils.messages import BOT_MESSAGES

    channel_service = ChannelService(session)
    points_list = await channel_service.get_reaction_points(channel_id)
    idx = 0
    try:
        idx = int(reaction_type[1:])
    except (ValueError, IndexError):
        pass
    points = points_list[idx] if idx < len(points_list) else 0.0

    await PointService(session).add_points(
        callback.from_user.id,
        points,
        bot=bot,
    )
    await service.update_reaction_markup(
        callback.message.chat.id,
        message_id,
    )
    await callback.answer(
        BOT_MESSAGES["reaction_registered_points"].format(points=points)
    )


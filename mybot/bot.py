import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from database.setup import init_db, get_session

from handlers import start, free_user
from handlers import daily_gift, minigames
from handlers.channel_access import router as channel_access_router
from handlers.user import start_token
from handlers.vip import menu as vip
from handlers.vip import gamification
from handlers.vip.auction_user import router as auction_user_router
from handlers.interactive_post import router as interactive_post_router
from handlers.admin import admin_router
from handlers.admin.auction_admin import router as auction_admin_router
from handlers.free_channel_admin import router as free_channel_admin_router
from utils.config import BOT_TOKEN, VIP_CHANNEL_ID
import logging
from services import channel_request_scheduler, vip_subscription_scheduler
from services.scheduler import auction_monitor_scheduler, free_channel_cleanup_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main() -> None:
    await init_db()
    Session = await get_session()

    logger.info(f"VIP channel ID: {VIP_CHANNEL_ID}")
    logger.info(f"Bot starting...")

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    def session_middleware_factory(session_factory, bot_instance):
        async def middleware(handler, event, data):
            async with session_factory() as session:
                data["session"] = session
                data["bot"] = bot_instance
                try:
                    return await handler(event, data)
                except Exception as e:
                    logger.error(f"Error in handler: {e}", exc_info=True)
                    # Don't re-raise to prevent update from being marked as unhandled
                    return None
        return middleware

    # Apply middleware to available update types only
    dp.message.outer_middleware(session_middleware_factory(Session, bot))
    dp.callback_query.outer_middleware(session_middleware_factory(Session, bot))
    dp.chat_join_request.outer_middleware(session_middleware_factory(Session, bot))
    dp.chat_member.outer_middleware(session_middleware_factory(Session, bot))
    dp.poll_answer.outer_middleware(session_middleware_factory(Session, bot))
    dp.message_reaction.outer_middleware(session_middleware_factory(Session, bot))
    dp.inline_query.outer_middleware(session_middleware_factory(Session, bot))
    dp.chosen_inline_result.outer_middleware(session_middleware_factory(Session, bot))
    # Removed: dp.pre_checkout_query and dp.successful_payment (not available in aiogram 3.x)

    from middlewares import PointsMiddleware
    dp.message.middleware(PointsMiddleware())
    dp.poll_answer.middleware(PointsMiddleware())
    dp.message_reaction.middleware(PointsMiddleware())

    # Include routers in order of priority
    dp.include_router(start_token)
    dp.include_router(start.router)
    dp.include_router(admin_router)
    dp.include_router(auction_admin_router)
    dp.include_router(free_channel_admin_router)
    dp.include_router(vip.router)
    dp.include_router(gamification.router)
    dp.include_router(auction_user_router)
    dp.include_router(interactive_post_router)
    dp.include_router(daily_gift.router)
    dp.include_router(minigames.router)
    dp.include_router(free_user.router)
    dp.include_router(channel_access_router)

    # Add error handler for unhandled updates
    @dp.error()
    async def error_handler(event, exception):
        logger.error(f"Unhandled error: {exception}", exc_info=True)
        return True  # Mark as handled

    # Add fallback handlers for common update types
    @dp.message()
    async def fallback_message_handler(message):
        logger.debug(f"Fallback handler for message from user {message.from_user.id}")
        return True

    @dp.callback_query()
    async def fallback_callback_handler(callback):
        logger.debug(f"Fallback handler for callback from user {callback.from_user.id}")
        await callback.answer()
        return True

    @dp.inline_query()
    async def fallback_inline_handler(inline_query):
        logger.debug(f"Fallback handler for inline query from user {inline_query.from_user.id}")
        return True

    @dp.chosen_inline_result()
    async def fallback_chosen_inline_handler(chosen_inline_result):
        logger.debug(f"Fallback handler for chosen inline result from user {chosen_inline_result.from_user.id}")
        return True

    # Tareas programadas
    pending_task = asyncio.create_task(channel_request_scheduler(bot, Session))
    vip_task = asyncio.create_task(vip_subscription_scheduler(bot, Session))
    auction_task = asyncio.create_task(auction_monitor_scheduler(bot, Session))
    cleanup_task = asyncio.create_task(free_channel_cleanup_scheduler(bot, Session))

    try:
        logger.info("Bot is starting polling...")
        await dp.start_polling(bot, handle_signals=False)
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot...")
        pending_task.cancel()
        vip_task.cancel()
        auction_task.cancel()
        cleanup_task.cancel()
        
        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    pending_task, vip_task, auction_task, cleanup_task, 
                    return_exceptions=True
                ),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("Some tasks did not complete within timeout")
        
        await bot.session.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
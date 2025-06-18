import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramConflictError

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
from handlers.setup import router as setup_router
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
    try:
        await init_db()
        Session = await get_session()

        logger.info(f"VIP channel ID: {VIP_CHANNEL_ID}")
        logger.info(f"Bot starting...")

        bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher(storage=MemoryStorage())

        # Test bot connection and clear any existing webhooks
        try:
            me = await bot.get_me()
            logger.info(f"Bot connected: @{me.username} - {me.first_name}")
            
            # Force delete webhook and clear pending updates
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook deleted and pending updates cleared")
            
            # Wait a moment to ensure webhook is fully cleared
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to connect to bot: {e}")
            return

        def session_middleware_factory(session_factory, bot_instance):
            async def middleware(handler, event, data):
                async with session_factory() as session:
                    data["session"] = session
                    data["bot"] = bot_instance
                    try:
                        return await handler(event, data)
                    except Exception as e:
                        logger.error(f"Error in handler: {e}", exc_info=True)
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

        from middlewares import PointsMiddleware
        dp.message.middleware(PointsMiddleware())
        dp.poll_answer.middleware(PointsMiddleware())
        dp.message_reaction.middleware(PointsMiddleware())

        # Include routers in order of priority - START HANDLER FIRST!
        logger.info("Registering handlers...")
        dp.include_router(start.router)  # FIRST - handles /start
        dp.include_router(start_token)   # SECOND - handles /start with tokens
        dp.include_router(setup_router)
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
        logger.info("All handlers registered successfully")

        # Add error handler for unhandled updates
        @dp.error()
        async def error_handler(event, exception):
            if isinstance(exception, TelegramConflictError):
                logger.error("Conflict error - another bot instance is running!")
                return True
            logger.error(f"Unhandled error: {exception}", exc_info=True)
            return True

        # Add fallback handlers for common update types
        @dp.message()
        async def fallback_message_handler(message):
            logger.warning(f"Fallback handler triggered for message from user {message.from_user.id}: {message.text}")
            try:
                await message.answer("🤖 Comando no reconocido. Usa /start para comenzar.")
            except Exception as e:
                logger.error(f"Error in fallback message handler: {e}")
            return True

        @dp.callback_query()
        async def fallback_callback_handler(callback):
            logger.warning(f"Fallback handler triggered for callback from user {callback.from_user.id}: {callback.data}")
            try:
                await callback.answer("Acción no reconocida")
            except Exception as e:
                logger.error(f"Error in fallback callback handler: {e}")
            return True

        # Tareas programadas
        pending_task = asyncio.create_task(channel_request_scheduler(bot, Session))
        vip_task = asyncio.create_task(vip_subscription_scheduler(bot, Session))
        auction_task = asyncio.create_task(auction_monitor_scheduler(bot, Session))
        cleanup_task = asyncio.create_task(free_channel_cleanup_scheduler(bot, Session))

        logger.info("Bot is starting polling...")
        
        # Start polling with conflict handling
        try:
            await dp.start_polling(
                bot, 
                handle_signals=False,
                allowed_updates=dp.resolve_used_update_types()
            )
        except TelegramConflictError as e:
            logger.error(f"Conflict error during polling: {e}")
            logger.error("Another bot instance is already running. Please stop other instances first.")
            return
        
    except Exception as e:
        logger.error(f"Error during bot startup: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot...")
        try:
            if 'pending_task' in locals():
                pending_task.cancel()
            if 'vip_task' in locals():
                vip_task.cancel()
            if 'auction_task' in locals():
                auction_task.cancel()
            if 'cleanup_task' in locals():
                cleanup_task.cancel()
            
            # Wait for tasks to complete with timeout
            tasks_to_wait = []
            if 'pending_task' in locals():
                tasks_to_wait.append(pending_task)
            if 'vip_task' in locals():
                tasks_to_wait.append(vip_task)
            if 'auction_task' in locals():
                tasks_to_wait.append(auction_task)
            if 'cleanup_task' in locals():
                tasks_to_wait.append(cleanup_task)
            
            if tasks_to_wait:
                await asyncio.wait_for(
                    asyncio.gather(*tasks_to_wait, return_exceptions=True),
                    timeout=10.0
                )
        except asyncio.TimeoutError:
            logger.warning("Some tasks did not complete within timeout")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        try:
            if 'bot' in locals():
                await bot.session.close()
        except:
            pass
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
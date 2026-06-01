"""
آپلودر تریاک - فایل اصلی اجرای ربات
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, BOT_NAME, OWNER_ID

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """تنظیم دستورات پیش‌فرض ربات"""
    commands = [
        BotCommand(command="start", description="🚀 شروع ربات"),
        BotCommand(command="panel", description="🎛 پنل مدیریت"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot):
    """رویداد شروع ربات"""
    logger.info(f"✅ {BOT_NAME} در حال راه‌اندازی...")

    # ثبت Owner به عنوان ادمین اصلی
    from database.db import db
    try:
        owner_info = await bot.get_chat(OWNER_ID)
        db.add_admin(
            user_id=OWNER_ID,
            username=owner_info.username,
            first_name=owner_info.first_name,
            role='owner',
            added_by=OWNER_ID
        )
        logger.info(f"👑 Owner با موفقیت ثبت شد: {OWNER_ID}")
    except Exception as e:
        logger.warning(f"⚠️ خطا در ثبت Owner: {e}")

    # تنظیم BOT_USERNAME در سایر ماژول‌ها
    me = await bot.get_me()
    bot_username = me.username
    logger.info(f"🤖 ربات @{bot_username} آماده به کار است!")

    # تنظیم username در هندلرها
    import handlers.files as files_handler
    import handlers.upload as upload_handler
    files_handler.set_bot_username(bot_username)
    upload_handler.set_bot_username(bot_username)

    await set_bot_commands(bot)


async def main():
    """تابع اصلی اجرای ربات"""
    # بررسی توکن
    if BOT_TOKEN == "توکن_جدید_بات_خودت":
        logger.error("❌ لطفاً توکن ربات را در فایل config.py تنظیم کنید!")
        return

    # ایجاد نمونه بات و دیسپچر
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ثبت رویداد شروع
    dp.startup.register(on_startup)

    # ایمپورت و ثبت روترها
    from handlers.start import router as start_router
    from handlers.admin_panel import router as admin_router
    from handlers.files import router as files_router
    from handlers.upload import router as upload_router
    from handlers.broadcast import router as broadcast_router
    from handlers.backup import router as backup_router
    from handlers.support import router as support_router

    dp.include_router(admin_router)
    dp.include_router(files_router)
    dp.include_router(upload_router)
    dp.include_router(broadcast_router)
    dp.include_router(backup_router)
    dp.include_router(support_router)
    dp.include_router(start_router)  # start router باید آخر باشد

    logger.info("🚀 ربات در حال اجرا...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())

"""
هندلر شروع ربات - دریافت فایل از طریق لینک
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.utils.payload import decode_payload

from database.db import db
from config import BOT_NAME, STORAGE_CHANNEL_ID, MAIN_CHANNEL_USERNAME
from keyboards.user_kb import user_main_menu, support_button
from keyboards.force_join_kb import force_join_channels, force_join_remaining

router = Router()


async def check_user_joined_all_channels(bot, user_id: int) -> tuple:
    """
    بررسی عضویت کاربر در تمام کانال‌های اجباری
    Returns: (all_joined: bool, not_joined_channels: list)
    """
    if not db.is_force_join_enabled():
        return True, []

    channels = db.get_all_channels()
    if not channels:
        return True, []

    not_joined = []
    for ch in channels:
        ch_id = ch['channel_id'] if isinstance(ch, dict) else ch[1]
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ['left', 'kicked', 'banned']:
                not_joined.append(ch)
        except Exception:
            # اگر نتوانستیم بررسی کنیم، از آن صرف‌نظر می‌کنیم
            pass

    return len(not_joined) == 0, not_joined


@router.message(CommandStart())
async def cmd_start(message: Message):
    """شروع ربات"""
    user = message.from_user
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # بررسی بن بودن
    if db.is_banned(user.id):
        await message.answer(
            "⛔️ شما از استفاده از این ربات محروم شده‌اید.\n\n"
            "در صورت نیاز به پیگیری با پشتیبانی تماس بگیرید.",
            reply_markup=support_button()
        )
        return

    args = message.text.split()
    if len(args) > 1:
        # دریافت فایل از طریق لینک
        file_unique_id = args[1]
        await handle_file_download(message, file_unique_id)
        return

    # منوی اصلی
    await message.answer(
        f"🎯 به ربات <b>{BOT_NAME}</b> خوش آمدید!\n\n"
        "📥 با استفاده از این ربات می‌توانید فایل‌های خود را آپلود کرده و از طریق لینک اختصاصی به اشتراک بگذارید.\n\n"
        "📌 برای دریافت فایل، لینک اختصاصی را باز کنید.\n\n"
        "🔰 <b>راهنما:</b>\n"
        "• روی دکمه «دریافت فایل» کلیک کنید\n"
        "• یا لینک اختصاصی فایل را باز کنید",
        reply_markup=user_main_menu()
    )


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep_link(message: Message):
    """هندلر لینک‌های عمیق (deep link)"""
    # توسط cmd_start هندل می‌شود
    await cmd_start(message)


async def handle_file_download(message: Message, file_unique_id: str):
    """دریافت و ارسال فایل به کاربر"""
    bot = message.bot
    user_id = message.from_user.id

    file_record = db.get_file_by_unique_id(file_unique_id)
    if not file_record:
        await message.answer(
            "❌ فایل مورد نظر یافت نشد.\n"
            "ممکن است فایل حذف شده یا لینک نامعتبر باشد.",
            reply_markup=user_main_menu()
        )
        return

    # بررسی عضویت اجباری
    all_joined, not_joined = await check_user_joined_all_channels(bot, user_id)

    if not all_joined:
        channels_text = "\n".join([
            f"🔹 {ch['channel_title'] or 'کانال'}"
            if isinstance(ch, dict) else
            f"🔹 {ch[3] or 'کانال'}"
            for ch in not_joined
        ])

        from keyboards.force_join_kb import force_join_channels
        channels_list = []
        for ch in not_joined:
            if isinstance(ch, dict):
                channels_list.append({
                    'channel_username': ch['channel_username'],
                    'channel_title': ch['channel_title']
                })
            else:
                channels_list.append({
                    'channel_username': ch[2],
                    'channel_title': ch[3]
                })

        await message.answer(
            "⚠️ <b>عضویت در کانال‌های زیر الزامی است:</b>\n\n"
            "برای استفاده از ربات ابتدا در کانال‌های زیر عضو شوید:\n\n"
            f"{channels_text}\n\n"
            "سپس روی «عضو شدم» کلیک کنید.",
            reply_markup=force_join_channels(channels_list)
        )
        return

    # ارسال فایل
    storage_ch_id = db.get_storage_channel_id() or STORAGE_CHANNEL_ID
    file_id = file_record['file_id'] if isinstance(file_record, dict) else file_record[1]
    file_name = (file_record['file_name'] or 'فایل') if isinstance(file_record, dict) else (file_record[3] or 'فایل')
    file_type = (file_record['file_type'] or 'document') if isinstance(file_record, dict) else (file_record[5] or 'document')

    try:
        # تلاش برای کپی از کانال ذخیره
        storage_msg_id = file_record['storage_message_id'] if isinstance(file_record, dict) else file_record[8]
        if storage_msg_id and storage_ch_id:
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=storage_ch_id,
                    message_id=storage_msg_id,
                    caption=f"📄 {file_name}\n\n@{MAIN_CHANNEL_USERNAME.replace('@', '')}",
                )
            except Exception:
                # روش دوم: ارسال با file_id
                await send_file_by_type(bot, user_id, file_id, file_name, file_type)
        else:
            await send_file_by_type(bot, user_id, file_id, file_name, file_type)

        # افزایش شمارنده دانلود
        db.increment_download_count(file_unique_id)

        await message.answer(
            f"✅ فایل با موفقیت دریافت شد!\n\n"
            f"📄 نام فایل: {file_name}\n\n"
            f"🔰 {BOT_NAME}",
            reply_markup=user_main_menu()
        )
    except Exception as e:
        await message.answer(
            f"❌ خطا در ارسال فایل:\n{str(e)[:200]}\n\n"
            "لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=support_button()
        )


async def send_file_by_type(bot, chat_id: int, file_id: str, file_name: str, file_type: str):
    """ارسال فایل بر اساس نوع آن"""
    caption = f"📄 {file_name}\n\n@{MAIN_CHANNEL_USERNAME.replace('@', '')}"

    if file_type == 'photo':
        await bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
    elif file_type == 'video':
        await bot.send_video(chat_id=chat_id, video=file_id, caption=caption)
    elif file_type == 'audio':
        await bot.send_audio(chat_id=chat_id, audio=file_id, caption=caption)
    elif file_type == 'voice':
        await bot.send_voice(chat_id=chat_id, voice=file_id, caption=caption)
    elif file_type == 'animation':
        await bot.send_animation(chat_id=chat_id, animation=file_id, caption=caption)
    elif file_type == 'video_note':
        await bot.send_video_note(chat_id=chat_id, video_note=file_id)
    elif file_type == 'sticker':
        await bot.send_sticker(chat_id=chat_id, sticker=file_id)
    else:
        await bot.send_document(chat_id=chat_id, document=file_id, caption=caption)


@router.callback_query(F.data == "user_get_file")
async def user_get_file_callback(callback: CallbackQuery):
    """دکمه دریافت فایل در منوی کاربر"""
    await callback.answer("برای دریافت فایل، لینک اختصاصی را باز کنید یا /start FILE_ID را بزنید.", show_alert=True)


@router.callback_query(F.data == "user_support")
async def user_support_callback(callback: CallbackQuery):
    """دکمه تماس با پشتیبانی"""
    await callback.answer()
    await callback.message.edit_text(
        "📞 <b>تماس با پشتیبانی</b>\n\n"
        "برای ارتباط با پشتیبانی روی دکمه زیر کلیک کنید:",
        reply_markup=support_button()
    )


@router.callback_query(F.data == "user_main_menu")
async def user_main_menu_callback(callback: CallbackQuery):
    """بازگشت به منوی اصلی کاربر"""
    await callback.answer()
    await callback.message.edit_text(
        f"🎯 به ربات <b>{BOT_NAME}</b> خوش آمدید!\n\n"
        "📥 با استفاده از این ربات می‌توانید فایل‌های خود را آپلود کرده و از طریق لینک اختصاصی به اشتراک بگذارید.\n\n"
        "📌 برای دریافت فایل، لینک اختصاصی را باز کنید.",
        reply_markup=user_main_menu()
    )


@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery):
    """بررسی عضویت در کانال‌های اجباری"""
    bot = callback.bot
    user_id = callback.from_user.id

    all_joined, not_joined = await check_user_joined_all_channels(bot, user_id)

    if not all_joined:
        channels_text = "\n".join([
            f"🔹 {ch['channel_title'] or 'کانال'}"
            if isinstance(ch, dict) else
            f"🔹 {ch[3] or 'کانال'}"
            for ch in not_joined
        ])

        channels_list = []
        for ch in not_joined:
            if isinstance(ch, dict):
                channels_list.append({
                    'channel_username': ch['channel_username'],
                    'channel_title': ch['channel_title']
                })
            else:
                channels_list.append({
                    'channel_username': ch[2],
                    'channel_title': ch[3]
                })

        await callback.answer("❌ ابتدا در تمامی کانال‌های الزامی عضو شوید.", show_alert=True)
        await callback.message.edit_text(
            "⚠️ <b>هنوز در همه کانال‌ها عضو نشده‌اید!</b>\n\n"
            "لطفاً در کانال‌های زیر عضو شوید:\n\n"
            f"{channels_text}\n\n"
            "سپس روی «بررسی مجدد» کلیک کنید.",
            reply_markup=force_join_remaining(channels_list)
        )
        return

    await callback.answer("✅ عضویت شما تأیید شد!", show_alert=True)
    await callback.message.edit_text(
        f"✅ عضویت شما در تمام کانال‌ها تأیید شد!\n\n"
        f"حالا می‌توانید از ربات {BOT_NAME} استفاده کنید.",
        reply_markup=user_main_menu()
    )

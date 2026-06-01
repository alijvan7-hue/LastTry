"""
هندلر آپلود فایل توسط ادمین
فایل در کانال ذخیره‌سازی Storage Channel ذخیره می‌شود
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import db
from config import BOT_NAME, STORAGE_CHANNEL_ID
from states.admin_states import AdminStates
from keyboards.admin_kb import back_to_admin_panel, admin_main_menu

router = Router()

BOT_USERNAME = ""


def set_bot_username(username: str):
    global BOT_USERNAME
    BOT_USERNAME = username


@router.callback_query(F.data == "admin_upload")
async def admin_upload_callback(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند آپلود فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.UPLOAD_FILE)
    await callback.answer()
    await callback.message.edit_text(
        "📤 <b>آپلود فایل</b>\n\n"
        "لطفاً فایل مورد نظر خود را ارسال کنید.\n\n"
        "✅ پشتیبانی از انواع فایل:\n"
        "📄 اسناد (Document)\n"
        "🖼 عکس (Photo)\n"
        "🎥 ویدیو (Video)\n"
        "🎵 صوت (Audio)\n"
        "🎙 ویس (Voice)\n"
        "✨ گیف (Animation)\n\n"
        "⚠️ حداکثر حجم: 2 گیگابایت",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.UPLOAD_FILE, F.content_type.in_([
    'document', 'photo', 'video', 'audio', 'voice', 'animation',
    'video_note', 'sticker'
]))
async def process_upload_file(message: Message, state: FSMContext):
    """پردازش فایل آپلود شده"""
    if not db.is_admin(message.from_user.id):
        return

    # استخراج اطلاعات فایل بر اساس نوع
    file_id = None
    file_unique_id = None
    file_name = None
    file_size = 0
    file_type = message.content_type
    mime_type = None

    if message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file_name = message.document.file_name
        file_size = message.document.file_size or 0
        mime_type = message.document.mime_type
    elif message.photo:
        # بزرگترین سایز عکس
        photo = message.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        file_name = f"photo_{photo.file_unique_id}.jpg"
        file_size = photo.file_size or 0
    elif message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        file_name = message.video.file_name or f"video_{message.video.file_unique_id}.mp4"
        file_size = message.video.file_size or 0
        mime_type = message.video.mime_type
    elif message.audio:
        file_id = message.audio.file_id
        file_unique_id = message.audio.file_unique_id
        file_name = message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3"
        file_size = message.audio.file_size or 0
        mime_type = message.audio.mime_type
    elif message.voice:
        file_id = message.voice.file_id
        file_unique_id = message.voice.file_unique_id
        file_name = f"voice_{message.voice.file_unique_id}.ogg"
        file_size = message.voice.file_size or 0
        mime_type = message.voice.mime_type
    elif message.animation:
        file_id = message.animation.file_id
        file_unique_id = message.animation.file_unique_id
        file_name = message.animation.file_name or f"animation_{message.animation.file_unique_id}.gif"
        file_size = message.animation.file_size or 0
        mime_type = message.animation.mime_type
    elif message.video_note:
        file_id = message.video_note.file_id
        file_unique_id = message.video_note.file_unique_id
        file_name = f"video_note_{message.video_note.file_unique_id}.mp4"
        file_size = message.video_note.file_size or 0
    elif message.sticker:
        file_id = message.sticker.file_id
        file_unique_id = message.sticker.file_unique_id
        file_name = f"sticker_{message.sticker.file_unique_id}.webp"
        file_size = message.sticker.file_size or 0

    if not file_id:
        await message.answer("❌ خطا در دریافت فایل. لطفاً دوباره تلاش کنید.")
        return

    # ذخیره در کانال استوریج
    storage_ch_id = db.get_storage_channel_id() or STORAGE_CHANNEL_ID
    storage_message_id = 0

    try:
        sent_msg = await message.copy_to(chat_id=storage_ch_id)
        storage_message_id = sent_msg.message_id
    except Exception as e:
        await message.answer(
            f"❌ خطا در ذخیره‌سازی فایل در کانال:\n{str(e)[:200]}\n\n"
            "لطفاً اطمینان حاصل کنید که ربات در کانال ذخیره‌سازی ادمین است.",
            reply_markup=admin_main_menu()
        )
        await state.clear()
        return

    # ذخیره در دیتابیس
    file_db_id = db.add_file(
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_name=file_name,
        file_size=file_size,
        file_type=file_type,
        mime_type=mime_type,
        uploaded_by=message.from_user.id,
        storage_message_id=storage_message_id
    )

    # ساخت لینک
    global BOT_USERNAME
    bot_username = BOT_USERNAME or "BOT_USERNAME"
    link = f"https://t.me/{bot_username}?start={file_unique_id}"

    from keyboards.admin_kb import format_size
    size_str = format_size(file_size)

    await message.answer(
        f"✅ <b>فایل با موفقیت آپلود شد!</b>\n\n"
        f"🆔 شناسه فایل: <code>{file_db_id}</code>\n"
        f"📝 نام: {file_name or '—'}\n"
        f"📏 حجم: {size_str}\n"
        f"📂 نوع: {file_type}\n\n"
        f"📎 <b>لینک اختصاصی:</b>\n"
        f"<code>{link}</code>\n\n"
        "کاربران با کلیک روی این لینک و استارت ربات، فایل را دریافت می‌کنند.",
        reply_markup=admin_main_menu()
    )

    await state.clear()


@router.message(AdminStates.UPLOAD_FILE)
async def process_upload_invalid(message: Message):
    """اگر کاربر چیزی غیر از فایل ارسال کند"""
    if not db.is_admin(message.from_user.id):
        return

    await message.answer(
        "⚠️ لطفاً یک فایل معتبر ارسال کنید.\n"
        "انواع پشتیبانی شده: سند، عکس، ویدیو، صوت، ویس، گیف",
        reply_markup=back_to_admin_panel()
    )

"""
هندلر مدیریت فایل‌ها
لیست، جستجو، حذف، مشاهده لینک و اطلاعات فایل
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.payload import decode_payload

from database.db import db
from config import BOT_NAME, STORAGE_CHANNEL_ID, MAIN_CHANNEL_USERNAME
from states.admin_states import AdminStates
from keyboards.admin_kb import (
    files_list_keyboard, file_detail_keyboard,
    file_delete_confirm_keyboard, back_to_admin_panel, admin_main_menu
)

router = Router()

BOT_USERNAME = ""  # در main.py تنظیم می‌شود


def set_bot_username(username: str):
    global BOT_USERNAME
    BOT_USERNAME = username


@router.callback_query(F.data == "admin_files_list")
async def admin_files_list_callback(callback: CallbackQuery, state: FSMContext):
    """لیست فایل‌ها - صفحه اول"""
    await show_files_page(callback, state, page=0)


@router.callback_query(F.data.startswith("files_page_"))
async def files_page_callback(callback: CallbackQuery, state: FSMContext):
    """صفحه‌بندی فایل‌ها"""
    page = int(callback.data.split("_")[-1])
    await show_files_page(callback, state, page=page)


async def show_files_page(callback: CallbackQuery, state: FSMContext, page: int = 0):
    """نمایش یک صفحه از لیست فایل‌ها"""
    from database.db import db as database
    if not database.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.FILES_LIST)
    limit = 10
    offset = page * limit
    files = database.get_all_files(offset=offset, limit=limit)
    total = database.count_files()

    if not files:
        await callback.answer()
        await callback.message.edit_text(
            "📂 هیچ فایلی آپلود نشده است.",
            reply_markup=back_to_admin_panel()
        )
        return

    text = f"📂 <b>لیست فایل‌ها</b> (صفحه {page + 1})\n"
    text += f"📁 تعداد کل: {total}\n\n"
    text += "برای مشاهده جزئیات روی فایل کلیک کنید:"

    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=files_list_keyboard(files, page, total)
    )


@router.callback_query(F.data.startswith("file_detail_"))
async def file_detail_callback(callback: CallbackQuery, state: FSMContext):
    """نمایش جزئیات یک فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    file_db_id = int(callback.data.split("_")[-1])
    file_record = db.get_file_by_id(file_db_id)

    if not file_record:
        await callback.answer("فایل یافت نشد.", show_alert=True)
        return

    await state.set_state(AdminStates.FILE_DETAIL)
    await state.update_data(current_file_id=file_db_id)

    f = file_record
    file_name = f['file_name'] or 'بدون نام'
    file_size = f['file_size'] or 0
    file_type = f['file_type'] or 'نامشخص'
    uploaded_at = f['uploaded_at'] or '—'
    download_count = f['download_count'] or 0

    from keyboards.admin_kb import format_size
    size_str = format_size(file_size)

    text = (
        f"📄 <b>جزئیات فایل</b>\n\n"
        f"🆔 شناسه: <code>{f['id']}</code>\n"
        f"📝 نام: {file_name}\n"
        f"📏 حجم: {size_str}\n"
        f"📂 نوع: {file_type}\n"
        f"📅 تاریخ: {uploaded_at}\n"
        f"⬇️ تعداد دانلود: {download_count}\n"
    )

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=file_detail_keyboard(file_db_id))


@router.callback_query(F.data.startswith("file_link_"))
async def file_link_callback(callback: CallbackQuery):
    """نمایش لینک اختصاصی فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    file_db_id = int(callback.data.split("_")[-1])
    file_record = db.get_file_by_id(file_db_id)

    if not file_record:
        await callback.answer("فایل یافت نشد.", show_alert=True)
        return

    file_unique_id = file_record['file_unique_id']
    global BOT_USERNAME
    bot_username = BOT_USERNAME or "BOT_USERNAME"
    link = f"https://t.me/{bot_username}?start={file_unique_id}"

    await callback.answer()
    await callback.message.edit_text(
        f"📎 <b>لینک اختصاصی فایل:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"📝 نام فایل: {file_record['file_name'] or 'بدون نام'}\n\n"
        "کاربران با کلیک روی این لینک و استارت ربات، فایل را دریافت می‌کنند.",
        reply_markup=file_detail_keyboard(file_db_id)
    )


@router.callback_query(F.data.startswith("file_info_"))
async def file_info_callback(callback: CallbackQuery):
    """اطلاعات کامل فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    file_db_id = int(callback.data.split("_")[-1])
    file_record = db.get_file_by_id(file_db_id)

    if not file_record:
        await callback.answer("فایل یافت نشد.", show_alert=True)
        return

    from keyboards.admin_kb import format_size

    f = file_record
    await callback.answer()
    await callback.message.edit_text(
        f"ℹ️ <b>اطلاعات کامل فایل</b>\n\n"
        f"🆔 شناسه دیتابیس: <code>{f['id']}</code>\n"
        f"🆔 File ID: <code>{f['file_id'][:50]}...</code>\n"
        f"🆔 File Unique ID: <code>{f['file_unique_id']}</code>\n"
        f"📝 نام: {f['file_name'] or '—'}\n"
        f"📏 حجم: {format_size(f['file_size'] or 0)}\n"
        f"📂 نوع: {f['file_type'] or '—'}\n"
        f"📎 MIME: {f['mime_type'] or '—'}\n"
        f"👤 آپلودکننده: <code>{f['uploaded_by']}</code>\n"
        f"📅 تاریخ: {f['uploaded_at'] or '—'}\n"
        f"⬇️ دانلود: {f['download_count'] or 0}\n"
        f"💾 آیدی پیام ذخیره: {f['storage_message_id'] or 0}",
        reply_markup=file_detail_keyboard(file_db_id)
    )


@router.callback_query(F.data.startswith("file_delete_"))
async def file_delete_callback(callback: CallbackQuery, state: FSMContext):
    """تأیید حذف فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    file_db_id = int(callback.data.split("_")[-1])
    file_record = db.get_file_by_id(file_db_id)

    if not file_record:
        await callback.answer("فایل یافت نشد.", show_alert=True)
        return

    await state.set_state(AdminStates.FILE_DELETE_CONFIRM)
    await state.update_data(delete_file_id=file_db_id)

    await callback.answer()
    await callback.message.edit_text(
        f"⚠️ <b>آیا از حذف این فایل اطمینان دارید؟</b>\n\n"
        f"📝 نام: {file_record['file_name'] or 'بدون نام'}\n"
        f"🆔 شناسه: <code>{file_record['id']}</code>\n\n"
        "این عملیات غیرقابل بازگشت است!",
        reply_markup=file_delete_confirm_keyboard(file_db_id)
    )


@router.callback_query(F.data.startswith("file_delete_confirm_"))
async def file_delete_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """تأیید نهایی حذف فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    file_db_id = int(callback.data.split("_")[-1])
    file_record = db.get_file_by_id(file_db_id)

    if file_record:
        # تلاش برای حذف از کانال ذخیره
        storage_ch_id = db.get_storage_channel_id() or STORAGE_CHANNEL_ID
        storage_msg_id = file_record['storage_message_id']
        if storage_msg_id:
            try:
                await callback.bot.delete_message(storage_ch_id, storage_msg_id)
            except Exception:
                pass

        db.delete_file(file_db_id)

    await callback.answer("✅ فایل با موفقیت حذف شد.", show_alert=True)
    await state.clear()
    # بازگشت به لیست
    await show_files_page(callback, state, page=0)


# ==================== جستجوی فایل ====================

@router.callback_query(F.data == "admin_search_file")
async def admin_search_file_callback(callback: CallbackQuery, state: FSMContext):
    """جستجوی فایل"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.SEARCH_FILE)
    await callback.answer()
    await callback.message.edit_text(
        "🔍 <b>جستجوی فایل</b>\n\n"
        "نام فایل یا شناسه آن را وارد کنید:",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.SEARCH_FILE)
async def process_search_file(message: Message, state: FSMContext):
    """پردازش جستجوی فایل"""
    if not db.is_admin(message.from_user.id):
        return

    query = message.text.strip()
    results = db.search_files(query)

    if not results:
        await message.answer(
            "❌ هیچ فایلی با این مشخصات یافت نشد.",
            reply_markup=back_to_admin_panel()
        )
        return

    await state.set_state(AdminStates.SEARCH_RESULTS)
    text = f"🔍 <b>نتایج جستجو برای «{query}»:</b>\n\n"
    for f in results[:20]:
        text += f"📄 <code>{f['id']}</code> | {f['file_name'] or '—'} | {f['uploaded_at'] or '—'}\n"

    await message.answer(
        text,
        reply_markup=files_list_keyboard(results[:10])
    )

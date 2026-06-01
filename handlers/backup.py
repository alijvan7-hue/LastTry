"""
هندلر بکاپ دیتابیس
ارسال فایل SQLite به ادمین
"""

import os
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database.db import db
from config import DB_PATH
from states.admin_states import AdminStates
from keyboards.admin_kb import back_to_admin_panel, admin_main_menu

router = Router()


@router.callback_query(F.data == "admin_backup")
async def admin_backup_callback(callback: CallbackQuery, state: FSMContext):
    """دریافت بکاپ دیتابیس"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    db_path = db.get_backup_path()

    if not os.path.exists(db_path):
        await callback.answer("❌ فایل دیتابیس یافت نشد.", show_alert=True)
        return

    await callback.answer("در حال آماده‌سازی بکاپ...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"teriak_backup_{timestamp}.db"

    try:
        file_input = FSInputFile(db_path, filename=backup_filename)
        await callback.message.answer_document(
            document=file_input,
            caption=(
                f"💾 <b>بکاپ دیتابیس</b>\n\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}\n"
                f"📏 حجم: {os.path.getsize(db_path) / 1024:.1f} KB\n"
                f"👥 کاربران: {db.count_users():,}\n"
                f"📁 فایل‌ها: {db.count_files():,}"
            )
        )
        await callback.answer("✅ بکاپ با موفقیت ارسال شد.", show_alert=True)

    except Exception as e:
        await callback.answer(f"❌ خطا: {str(e)[:100]}", show_alert=True)

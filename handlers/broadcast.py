"""
هندلر پیام همگانی (Broadcast)
ارسال پیام به تمام کاربران ربات
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from database.db import db
from states.admin_states import AdminStates
from keyboards.admin_kb import back_to_admin_panel, broadcast_confirm_keyboard, admin_main_menu

router = Router()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند پیام همگانی"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.BROADCAST_MESSAGE)
    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>پیام همگانی</b>\n\n"
        "لطفاً پیام مورد نظر خود را ارسال کنید.\n"
        "این پیام به تمام کاربران ربات ارسال خواهد شد.\n\n"
        "✅ می‌توانید متن، عکس، ویدیو، صوت و ... ارسال کنید.\n\n"
        "⚠️ پس از ارسال پیام، امکان ویرایش یا حذف وجود ندارد.",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.BROADCAST_MESSAGE, F.content_type.in_([
    'text', 'photo', 'video', 'document', 'audio', 'voice', 'animation',
    'video_note', 'sticker'
]))
async def process_broadcast_message(message: Message, state: FSMContext):
    """پیش‌نمایش پیام همگانی قبل از ارسال"""
    if not db.is_admin(message.from_user.id):
        return

    # ذخیره اطلاعات پیام
    await state.update_data(
        broadcast_msg_id=message.message_id,
        broadcast_chat_id=message.chat.id,
        broadcast_content_type=message.content_type,
        broadcast_caption=message.caption,
        broadcast_text=message.text,
    )

    await state.set_state(AdminStates.BROADCAST_CONFIRM)

    await message.answer(
        "📢 <b>پیش‌نمایش پیام همگانی</b>\n\n"
        "آیا از ارسال این پیام به <b>همه کاربران</b> اطمینان دارید؟\n\n"
        f"👥 تعداد کاربران: <b>{db.count_users():,}</b>",
        reply_markup=broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """ارسال پیام همگانی به تمام کاربران"""
    if not db.is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    data = await state.get_data()
    msg_id = data.get('broadcast_msg_id')
    chat_id = data.get('broadcast_chat_id')

    if not msg_id or not chat_id:
        await callback.answer("خطا: اطلاعات پیام یافت نشد.", show_alert=True)
        return

    users = db.get_all_users()
    total = len(users)
    success = 0
    failed = 0

    await callback.answer("در حال ارسال...")
    status_msg = await callback.message.edit_text(
        f"📢 <b>در حال ارسال پیام همگانی...</b>\n\n"
        f"👥 کل کاربران: {total:,}\n"
        f"✅ موفق: {success:,}\n"
        f"❌ ناموفق: {failed:,}\n\n"
        "لطفاً صبر کنید..."
    )

    for i, user in enumerate(users):
        try:
            await callback.bot.copy_message(
                chat_id=user['user_id'],
                from_chat_id=chat_id,
                message_id=msg_id
            )
            success += 1
        except TelegramAPIError:
            failed += 1
        except Exception:
            failed += 1

        # آپدیت وضعیت هر 20 کاربر
        if (i + 1) % 20 == 0 or (i + 1) == total:
            try:
                await status_msg.edit_text(
                    f"📢 <b>در حال ارسال پیام همگانی...</b>\n\n"
                    f"👥 کل کاربران: {total:,}\n"
                    f"✅ موفق: {success:,}\n"
                    f"❌ ناموفق: {failed:,}\n"
                    f"📊 پیشرفت: {i + 1}/{total}"
                )
            except Exception:
                pass

            await asyncio.sleep(0.5)

    await status_msg.edit_text(
        "📢 <b>پیام همگانی با موفقیت ارسال شد!</b>\n\n"
        f"👥 کل کاربران: {total:,}\n"
        f"✅ موفق: {success:,}\n"
        f"❌ ناموفق: {failed:,}",
        reply_markup=admin_main_menu()
    )

    await state.clear()

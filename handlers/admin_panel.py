"""
هندلر پنل مدیریت
شامل: وضعیت، ادمین‌ها، کاربران، تنظیمات
"""

import os
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from database.db import db
from config import BOT_NAME, OWNER_ID, STORAGE_CHANNEL_ID
from states.admin_states import AdminStates
from keyboards.admin_kb import (
    admin_main_menu, back_to_admin_panel, cancel_operation,
    admins_list_keyboard, users_management_menu,
    user_info_keyboard, users_list_keyboard,
    settings_keyboard, force_join_menu_keyboard,
    channels_list_for_removal
)
from keyboards.user_kb import user_main_menu

router = Router()


def is_admin(user_id: int) -> bool:
    return db.is_admin(user_id) or user_id == OWNER_ID


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID or db.is_owner(user_id)


# ==================== ورود به پنل ====================

@router.message(F.text == "/panel")
async def cmd_panel(message: Message, state: FSMContext):
    """ورود به پنل مدیریت"""
    await state.clear()
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("⛔️ شما دسترسی به پنل مدیریت ندارید.")
        return

    await state.set_state(AdminStates.MAIN_MENU)
    await message.answer(
        f"🎛 <b>پنل مدیریت {BOT_NAME}</b>\n\n"
        f"👤 ادمین: {message.from_user.full_name}\n"
        f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d')}\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_main_menu()
    )


@router.callback_query(F.data == "admin_main_menu")
async def admin_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی اصلی پنل"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.MAIN_MENU)
    await callback.answer()
    await callback.message.edit_text(
        f"🎛 <b>پنل مدیریت {BOT_NAME}</b>\n\n"
        f"👤 ادمین: {callback.from_user.full_name}\n"
        f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d')}\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_main_menu()
    )


@router.callback_query(F.data == "admin_close")
async def admin_close_callback(callback: CallbackQuery, state: FSMContext):
    """بستن پنل مدیریت"""
    await state.clear()
    await callback.answer("پنل بسته شد.")
    await callback.message.edit_text(
        f"🎯 {BOT_NAME}\n\n📥 برای دریافت فایل، لینک اختصاصی را باز کنید.",
        reply_markup=user_main_menu()
    )


# ==================== بررسی وضعیت ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """نمایش وضعیت ربات"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    stats = db.get_stats()
    force_join_status = "✅ فعال" if stats['force_join'] else "❌ غیرفعال"

    await callback.answer()
    await callback.message.edit_text(
        "📊 <b>وضعیت ربات</b>\n\n"
        f"👥 تعداد کاربران: <b>{stats['users']:,}</b>\n"
        f"📁 تعداد فایل‌ها: <b>{stats['files']:,}</b>\n"
        f"👤 تعداد ادمین‌ها: <b>{stats['admins']}</b>\n"
        f"🚫 کاربران بن شده: <b>{stats['banned']:,}</b>\n"
        f"📢 کانال‌های اجباری: <b>{stats['channels']}</b>\n"
        f"⚙️ عضویت اجباری: {force_join_status}",
        reply_markup=back_to_admin_panel()
    )


# ==================== مدیریت ادمین‌ها ====================

@router.callback_query(F.data == "admin_admins_list")
async def admin_admins_list_callback(callback: CallbackQuery, state: FSMContext):
    """نمایش لیست ادمین‌ها"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.ADMINS_LIST)
    admins = db.get_all_admins()

    text = "👥 <b>لیست ادمین‌ها:</b>\n\n"
    for a in admins:
        role = "👑 Owner" if a['role'] == 'owner' else "👤 Admin"
        name = a['first_name'] or a['username'] or f"ID: {a['user_id']}"
        text += f"{role} - {name} | <code>{a['user_id']}</code>\n"

    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=admins_list_keyboard(admins)
    )


@router.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_callback(callback: CallbackQuery, state: FSMContext):
    """افزودن ادمین جدید"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند ادمین اضافه کند.", show_alert=True)
        return

    await state.set_state(AdminStates.ADD_ADMIN)
    await callback.answer()
    await callback.message.edit_text(
        "➕ <b>افزودن ادمین جدید</b>\n\n"
        "لطفاً شناسه عددی کاربر را ارسال کنید:\n"
        "مثال: <code>123456789</code>\n\n"
        "می‌توانید از فوروارد پیام کاربر هم استفاده کنید.",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.ADD_ADMIN)
async def process_add_admin(message: Message, state: FSMContext):
    """پردازش افزودن ادمین"""
    if not is_owner(message.from_user.id):
        return

    target_id = None
    target_username = None
    target_first_name = None

    # فوروارد پیام
    if message.forward_from:
        target_id = message.forward_from.id
        target_username = message.forward_from.username
        target_first_name = message.forward_from.first_name
    elif message.forward_from_chat and message.forward_from_chat.type == 'private':
        target_id = message.forward_from_chat.id
        target_username = message.forward_from_chat.username
        target_first_name = message.forward_from_chat.first_name
    elif message.text:
        text = message.text.strip()
        if text.isdigit():
            target_id = int(text)
        elif text.startswith('@'):
            await message.answer("⚠️ لطفاً شناسه عددی کاربر را ارسال کنید (نه یوزرنیم).")
            return
        else:
            await message.answer("⚠️ لطفاً یک شناسه عددی معتبر ارسال کنید.")
            return

    if not target_id:
        await message.answer("⚠️ نمی‌توان کاربر را شناسایی کرد. لطفاً شناسه عددی را وارد کنید.")
        return

    if db.is_admin(target_id):
        await message.answer(
            f"⚠️ این کاربر در حال حاضر ادمین است.",
            reply_markup=admin_main_menu()
        )
        await state.clear()
        return

    db.add_admin(
        user_id=target_id,
        username=target_username,
        first_name=target_first_name,
        role='admin',
        added_by=message.from_user.id
    )

    await message.answer(
        f"✅ ادمین جدید با موفقیت افزوده شد!\n\n"
        f"🆔 شناسه: <code>{target_id}</code>",
        reply_markup=admin_main_menu()
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_remove_"))
async def admin_remove_callback(callback: CallbackQuery, state: FSMContext):
    """حذف ادمین"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند ادمین حذف کند.", show_alert=True)
        return

    target_id = int(callback.data.split("_")[-1])

    if target_id == OWNER_ID:
        await callback.answer("⛔️ نمی‌توان Owner را حذف کرد.", show_alert=True)
        return

    await state.set_state(AdminStates.REMOVE_ADMIN_CONFIRM)
    await state.update_data(remove_admin_id=target_id)

    # ساخت کیبورد تأیید
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ بله، حذف کن", callback_data=f"admin_remove_confirm_{target_id}"),
        InlineKeyboardButton(text="❌ خیر", callback_data="admin_admins_list")
    )

    await callback.answer()
    await callback.message.edit_text(
        f"⚠️ آیا از حذف ادمین با شناسه <code>{target_id}</code> اطمینان دارید؟",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin_remove_confirm_"))
async def admin_remove_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """تأیید نهایی حذف ادمین"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند ادمین حذف کند.", show_alert=True)
        return

    target_id = int(callback.data.split("_")[-1])
    db.remove_admin(target_id)

    await callback.answer("✅ ادمین با موفقیت حذف شد.", show_alert=True)
    await state.clear()

    # نمایش لیست به‌روز شده
    admins = db.get_all_admins()
    text = "👥 <b>لیست ادمین‌ها:</b>\n\n"
    for a in admins:
        role = "👑 Owner" if a['role'] == 'owner' else "👤 Admin"
        name = a['first_name'] or a['username'] or f"ID: {a['user_id']}"
        text += f"{role} - {name} | <code>{a['user_id']}</code>\n"

    await callback.message.edit_text(text, reply_markup=admins_list_keyboard(admins))


# ==================== مدیریت کاربران ====================

@router.callback_query(F.data == "admin_users_menu")
async def admin_users_menu_callback(callback: CallbackQuery, state: FSMContext):
    """منوی مدیریت کاربران"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.USERS_LIST)
    await callback.answer()
    await callback.message.edit_text(
        "🚫 <b>مدیریت کاربران</b>\n\n"
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=users_management_menu()
    )


@router.callback_query(F.data == "admin_users_list")
async def admin_users_list_callback(callback: CallbackQuery, state: FSMContext):
    """لیست کاربران"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return
    await show_users_page(callback, state, page=0)


@router.callback_query(F.data.startswith("users_page_"))
async def users_page_callback(callback: CallbackQuery, state: FSMContext):
    """صفحه‌بندی کاربران"""
    page = int(callback.data.split("_")[-1])
    await show_users_page(callback, state, page=page)


async def show_users_page(callback: CallbackQuery, state: FSMContext, page: int = 0):
    """نمایش صفحه‌ای از کاربران"""
    limit = 10
    offset = page * limit
    all_users = db.get_all_users()
    users = all_users[offset:offset + limit]

    if not users:
        await callback.answer()
        await callback.message.edit_text(
            "👥 هیچ کاربری ثبت نشده.",
            reply_markup=back_to_admin_panel()
        )
        return

    await state.set_state(AdminStates.USERS_LIST)
    text = f"👥 <b>لیست کاربران</b> (صفحه {page + 1})\n\n"
    for u in users:
        uid = u['user_id']
        uname = u['username'] or '—'
        fname = u['first_name'] or '—'
        banned = "🚫" if u['is_banned'] else "✅"
        text += f"{banned} <code>{uid}</code> | {fname} | @{uname}\n"

    await callback.answer()
    await callback.message.edit_text(
        text,
        reply_markup=users_list_keyboard(users, page)
    )


@router.callback_query(F.data == "admin_user_search")
async def admin_user_search_callback(callback: CallbackQuery, state: FSMContext):
    """جستجوی کاربر"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.USER_SEARCH)
    await callback.answer()
    await callback.message.edit_text(
        "🔍 <b>جستجوی کاربر</b>\n\n"
        "شناسه عددی، یوزرنیم یا نام کاربر را وارد کنید:",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.USER_SEARCH)
async def process_user_search(message: Message, state: FSMContext):
    """پردازش جستجوی کاربر"""
    if not is_admin(message.from_user.id):
        return

    query = message.text.strip()
    users = db.search_users(query)

    if not users:
        await message.answer("❌ هیچ کاربری یافت نشد.", reply_markup=back_to_admin_panel())
        return

    await state.set_state(AdminStates.USERS_LIST)
    text = f"🔍 نتیجه جستجو برای «{query}»:\n\n"
    for u in users[:20]:
        uid = u['user_id']
        uname = u['username'] or "—"
        name = u['first_name'] or "—"
        banned = "🚫" if u['is_banned'] else "✅"
        text += f"{banned} <code>{uid}</code> | {name} | @{uname}\n"

    await message.answer(text, reply_markup=users_list_keyboard(users[:10]))


@router.callback_query(F.data.startswith("user_info_"))
async def user_info_callback(callback: CallbackQuery, state: FSMContext):
    """نمایش اطلاعات کاربر"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    user = db.get_user(user_id)

    if not user:
        await callback.answer("کاربر یافت نشد.", show_alert=True)
        return

    await state.set_state(AdminStates.USER_INFO)
    await state.update_data(viewed_user_id=user_id)

    banned_status = "🚫 بن شده" if user['is_banned'] else "✅ فعال"
    ban_reason = f"\n📝 دلیل: {user['ban_reason']}" if user['ban_reason'] else ""

    await callback.answer()
    await callback.message.edit_text(
        f"👤 <b>اطلاعات کاربر</b>\n\n"
        f"🆔 شناسه: <code>{user['user_id']}</code>\n"
        f"👤 نام: {user['first_name'] or '—'}\n"
        f"👤 نام خانوادگی: {user['last_name'] or '—'}\n"
        f"📎 یوزرنیم: {'@' + user['username'] if user['username'] else '—'}\n"
        f"📅 تاریخ عضویت: {user['joined_at'] or '—'}\n"
        f"🚫 وضعیت: {banned_status}{ban_reason}",
        reply_markup=user_info_keyboard(user_id, bool(user['is_banned']))
    )


@router.callback_query(F.data.startswith("user_ban_"))
async def user_ban_callback(callback: CallbackQuery, state: FSMContext):
    """بن کاربر"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند کاربر بن کند.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminStates.BAN_USER)
    await state.update_data(ban_user_id=user_id)

    await callback.answer()
    await callback.message.edit_text(
        f"🚫 <b>بن کاربر</b>\n\n"
        f"کاربر: <code>{user_id}</code>\n\n"
        "لطفاً دلیل بن را وارد کنید (یا «-» برای بدون دلیل):",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.BAN_USER)
async def process_ban_user(message: Message, state: FSMContext):
    """پردازش بن کاربر"""
    if not is_owner(message.from_user.id):
        return

    data = await state.get_data()
    user_id = data.get('ban_user_id')
    reason = message.text.strip()
    if reason == '-':
        reason = None

    db.ban_user(user_id, reason)
    await message.answer(
        f"✅ کاربر <code>{user_id}</code> با موفقیت بن شد.",
        reply_markup=admin_main_menu()
    )
    await state.clear()


@router.callback_query(F.data.startswith("user_unban_"))
async def user_unban_callback(callback: CallbackQuery):
    """آن‌بن کاربر"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند کاربر را آن‌بن کند.", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    db.unban_user(user_id)

    await callback.answer("✅ کاربر با موفقیت آن‌بن شد.", show_alert=True)
    # بازگشت به اطلاعات کاربر
    user = db.get_user(user_id)
    if user:
        await callback.message.edit_text(
            f"👤 <b>اطلاعات کاربر</b>\n\n"
            f"🆔 شناسه: <code>{user['user_id']}</code>\n"
            f"👤 نام: {user['first_name'] or '—'}\n"
            f"📎 یوزرنیم: {'@' + user['username'] if user['username'] else '—'}\n"
            f"🚫 وضعیت: ✅ فعال",
            reply_markup=user_info_keyboard(user_id, False)
        )


# ==================== عضویت اجباری ====================

@router.callback_query(F.data == "admin_force_join")
async def force_join_menu_callback(callback: CallbackQuery, state: FSMContext):
    """منوی عضویت اجباری"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.FORCE_JOIN_SETTINGS)
    is_enabled = db.is_force_join_enabled()

    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>مدیریت عضویت اجباری</b>\n\n"
        "کاربران قبل از دریافت فایل باید در کانال‌های تعیین شده عضو شوند.",
        reply_markup=force_join_menu_keyboard(is_enabled)
    )


@router.callback_query(F.data == "fj_toggle")
async def fj_toggle_callback(callback: CallbackQuery):
    """تغییر وضعیت عضویت اجباری"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    current = db.is_force_join_enabled()
    db.set_setting('force_join_enabled', '0' if current else '1')
    new_status = not current

    await callback.answer(
        f"عضویت اجباری {'فعال' if new_status else 'غیرفعال'} شد.",
        show_alert=True
    )

    await callback.message.edit_text(
        "📢 <b>مدیریت عضویت اجباری</b>\n\n"
        "کاربران قبل از دریافت فایل باید در کانال‌های تعیین شده عضو شوند.",
        reply_markup=force_join_menu_keyboard(new_status)
    )


@router.callback_query(F.data == "fj_add_channel")
async def fj_add_channel_callback(callback: CallbackQuery, state: FSMContext):
    """افزودن کانال به عضویت اجباری"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.ADD_CHANNEL)
    await callback.answer()
    await callback.message.edit_text(
        "➕ <b>افزودن کانال جدید</b>\n\n"
        "لطفاً آیدی عددی کانال یا یوزرنیم آن را ارسال کنید:\n\n"
        "مثال:\n"
        "<code>-1001234567890</code>\n"
        "<code>@channel_username</code>\n\n"
        "⚠️ ربات باید در کانال عضو و ادمین باشد.",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.ADD_CHANNEL)
async def process_add_channel(message: Message, state: FSMContext):
    """پردازش افزودن کانال"""
    if not is_admin(message.from_user.id):
        return

    from utils.helpers import extract_channel_info
    channel_input, is_id = extract_channel_info(message.text.strip())

    if not channel_input:
        await message.answer("⚠️ لطفاً یک آیدی یا یوزرنیم معتبر وارد کنید.")
        return

    try:
        if is_id:
            chat = await message.bot.get_chat(channel_input)
        else:
            chat = await message.bot.get_chat(f"@{channel_input}")

        channel_id = chat.id
        channel_username = chat.username
        channel_title = chat.title

        success = db.add_channel(channel_id, channel_username, channel_title)

        if success:
            await message.answer(
                f"✅ کانال با موفقیت افزوده شد!\n\n"
                f"📢 عنوان: {channel_title}\n"
                f"🆔 شناسه: <code>{channel_id}</code>\n"
                f"📎 یوزرنیم: {'@' + channel_username if channel_username else '—'}",
                reply_markup=admin_main_menu()
            )
        else:
            await message.answer(
                "⚠️ این کانال قبلاً ثبت شده است.",
                reply_markup=admin_main_menu()
            )
    except Exception as e:
        await message.answer(
            f"❌ خطا در افزودن کانال:\n{str(e)[:200]}\n\n"
            "اطمینان حاصل کنید که ربات در کانال عضو و ادمین است.",
            reply_markup=back_to_admin_panel()
        )
        return

    await state.clear()


@router.callback_query(F.data == "fj_remove_channel")
async def fj_remove_channel_callback(callback: CallbackQuery, state: FSMContext):
    """حذف کانال - نمایش لیست"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    channels = db.get_all_channels()
    if not channels:
        await callback.answer("هیچ کانالی ثبت نشده است.", show_alert=True)
        return

    await state.set_state(AdminStates.REMOVE_CHANNEL)
    await callback.answer()
    await callback.message.edit_text(
        "🗑 <b>حذف کانال</b>\n\n"
        "کانال مورد نظر برای حذف را انتخاب کنید:",
        reply_markup=channels_list_for_removal(channels)
    )


@router.callback_query(F.data.startswith("fj_remove_confirm_"))
async def fj_remove_confirm_callback(callback: CallbackQuery):
    """تأیید حذف کانال"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    channel_id = int(callback.data.split("_")[-1])
    db.remove_channel(channel_id)

    await callback.answer("✅ کانال با موفقیت حذف شد.", show_alert=True)
    # به‌روزرسانی لیست
    channels = db.get_all_channels()
    if channels:
        await callback.message.edit_text(
            "🗑 <b>حذف کانال</b>\n\nکانال مورد نظر را انتخاب کنید:",
            reply_markup=channels_list_for_removal(channels)
        )
    else:
        await callback.message.edit_text(
            "📢 <b>مدیریت عضویت اجباری</b>\n\nهیچ کانالی ثبت نشده.",
            reply_markup=force_join_menu_keyboard(db.is_force_join_enabled())
        )


@router.callback_query(F.data == "fj_list_channels")
async def fj_list_channels_callback(callback: CallbackQuery):
    """لیست کانال‌های اجباری"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    channels = db.get_all_channels()
    if not channels:
        await callback.answer("هیچ کانالی ثبت نشده.", show_alert=True)
        return

    text = "📋 <b>لیست کانال‌های اجباری:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        title = ch['channel_title'] or 'بدون نام'
        username = f"@{ch['channel_username']}" if ch['channel_username'] else '—'
        text += f"{i}. {title} | {username} | <code>{ch['channel_id']}</code>\n"

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=back_to_admin_panel())


# ==================== تنظیمات ====================

@router.callback_query(F.data == "admin_settings")
async def admin_settings_callback(callback: CallbackQuery, state: FSMContext):
    """منوی تنظیمات"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ دسترسی غیرمجاز", show_alert=True)
        return

    await state.set_state(AdminStates.SETTINGS)
    storage = db.get_storage_channel_id() or STORAGE_CHANNEL_ID

    await callback.answer()
    await callback.message.edit_text(
        f"⚙️ <b>تنظیمات ربات</b>\n\n"
        f"📦 کانال ذخیره‌سازی: <code>{storage}</code>\n\n"
        "یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=settings_keyboard()
    )


@router.callback_query(F.data == "settings_storage")
async def settings_storage_callback(callback: CallbackQuery, state: FSMContext):
    """تنظیم کانال ذخیره‌سازی"""
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔️ فقط Owner می‌تواند تنظیمات را تغییر دهد.", show_alert=True)
        return

    await state.set_state(AdminStates.SET_STORAGE_CHANNEL)
    await callback.answer()
    await callback.message.edit_text(
        "📦 <b>تنظیم کانال ذخیره‌سازی</b>\n\n"
        "لطفاً آیدی عددی کانال ذخیره‌سازی را وارد کنید:\n\n"
        "مثال: <code>-1001234567890</code>\n\n"
        "⚠️ ربات باید در این کانال ادمین باشد و اجازه ارسال پیام داشته باشد.",
        reply_markup=back_to_admin_panel()
    )


@router.message(AdminStates.SET_STORAGE_CHANNEL)
async def process_set_storage_channel(message: Message, state: FSMContext):
    """پردازش تنظیم کانال ذخیره‌سازی"""
    if not is_owner(message.from_user.id):
        return

    text = message.text.strip()
    if not (text.startswith('-100') and text[1:].isdigit()):
        await message.answer("⚠️ لطفاً یک آیدی عددی معتبر (مثل -100...) وارد کنید.")
        return

    channel_id = int(text)
    try:
        chat = await message.bot.get_chat(channel_id)
        db.set_setting('storage_channel_id', str(channel_id))
        await message.answer(
            f"✅ کانال ذخیره‌سازی با موفقیت تنظیم شد!\n\n"
            f"📦 کانال: {chat.title}\n"
            f"🆔 شناسه: <code>{channel_id}</code>",
            reply_markup=admin_main_menu()
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            f"❌ خطا: {str(e)[:200]}\n\n"
            "اطمینان حاصل کنید که ربات در کانال عضو است.",
            reply_markup=back_to_admin_panel()
        )

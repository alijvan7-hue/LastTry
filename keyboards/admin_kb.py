"""
کیبوردهای پنل مدیریت
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_main_menu() -> InlineKeyboardMarkup:
    """منوی اصلی پنل مدیریت"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("📊 بررسی وضعیت", "admin_stats"),
        ("📢 پیام همگانی", "admin_broadcast"),
        ("📂 مدیریت فایل‌ها", "admin_files_list"),
        ("📤 آپلود فایل", "admin_upload"),
        ("🔍 جستجوی فایل", "admin_search_file"),
        ("👥 مدیریت ادمین‌ها", "admin_admins_list"),
        ("🚫 مدیریت کاربران", "admin_users_menu"),
        ("📢 عضویت اجباری", "admin_force_join"),
        ("💾 دریافت بکاپ", "admin_backup"),
        ("⚙️ تنظیمات", "admin_settings"),
    ]
    for text, callback in buttons:
        builder.row(InlineKeyboardButton(text=text, callback_data=callback))
    builder.row(InlineKeyboardButton(text="❌ بستن پنل", callback_data="admin_close"))
    return builder.as_markup()


def back_to_admin_panel() -> InlineKeyboardMarkup:
    """دکمه بازگشت به پنل مدیریت"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به پنل",
        callback_data="admin_main_menu"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ لغو عملیات",
        callback_data="admin_close"
    ))
    return builder.as_markup()


def cancel_operation() -> InlineKeyboardMarkup:
    """دکمه لغو عملیات"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="❌ لغو عملیات",
        callback_data="admin_main_menu"
    ))
    return builder.as_markup()


# ==================== مدیریت فایل‌ها ====================

def files_list_keyboard(files: list, page: int = 0, total: int = 0) -> InlineKeyboardMarkup:
    """کیبورد لیست فایل‌ها"""
    builder = InlineKeyboardBuilder()
    for f in files:
        f_id = f['id'] if isinstance(f, dict) else f[0]
        f_name = (f['file_name'] or 'بدون نام') if isinstance(f, dict) else (f[3] or 'بدون نام')
        f_size = (f['file_size'] or 0) if isinstance(f, dict) else (f[4] or 0)
        size_str = format_size(f_size)
        builder.row(InlineKeyboardButton(
            text=f"📄 {f_name[:30]} | {size_str}",
            callback_data=f"file_detail_{f_id}"
        ))

    # دکمه‌های صفحه‌بندی
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ قبلی", callback_data=f"files_page_{page - 1}"
        ))
    if len(files) == 10:
        nav_buttons.append(InlineKeyboardButton(
            text="بعدی ➡️", callback_data=f"files_page_{page + 1}"
        ))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_main_menu"))
    return builder.as_markup()


def file_detail_keyboard(file_db_id: int) -> InlineKeyboardMarkup:
    """کیبورد جزئیات فایل"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📎 مشاهده لینک",
        callback_data=f"file_link_{file_db_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🗑 حذف فایل",
        callback_data=f"file_delete_{file_db_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="ℹ️ اطلاعات فایل",
        callback_data=f"file_info_{file_db_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="admin_files_list"
    ))
    return builder.as_markup()


def file_delete_confirm_keyboard(file_db_id: int) -> InlineKeyboardMarkup:
    """کیبورد تأیید حذف فایل"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ بله، حذف کن", callback_data=f"file_delete_confirm_{file_db_id}"),
        InlineKeyboardButton(text="❌ خیر", callback_data=f"file_detail_{file_db_id}")
    )
    return builder.as_markup()


# ==================== مدیریت ادمین‌ها ====================

def admins_list_keyboard(admins: list) -> InlineKeyboardMarkup:
    """کیبورد لیست ادمین‌ها"""
    builder = InlineKeyboardBuilder()
    for admin in admins:
        uid = admin['user_id'] if isinstance(admin, dict) else admin[0]
        uname = (admin['username'] or f"ID: {uid}") if isinstance(admin, dict) else (admin[1] or f"ID: {uid}")
        role = (admin['role'] or 'admin') if isinstance(admin, dict) else (admin[3] or 'admin')
        role_emoji = "👑" if role == 'owner' else "👤"
        builder.row(InlineKeyboardButton(
            text=f"{role_emoji} {uname} ({role})",
            callback_data=f"admin_remove_{uid}"
        ))

    builder.row(InlineKeyboardButton(
        text="➕ افزودن ادمین",
        callback_data="admin_add_admin"
    ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_main_menu"))
    return builder.as_markup()


# ==================== مدیریت کاربران ====================

def users_management_menu() -> InlineKeyboardMarkup:
    """منوی مدیریت کاربران"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔍 جستجوی کاربر",
        callback_data="admin_user_search"
    ))
    builder.row(InlineKeyboardButton(
        text="📋 لیست کاربران",
        callback_data="admin_users_list"
    ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_main_menu"))
    return builder.as_markup()


def user_info_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    """کیبورد اطلاعات کاربر"""
    builder = InlineKeyboardBuilder()
    if is_banned:
        builder.row(InlineKeyboardButton(
            text="✅ آن‌بن کاربر",
            callback_data=f"user_unban_{user_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🚫 بن کاربر",
            callback_data=f"user_ban_{user_id}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_users_menu"))
    return builder.as_markup()


def users_list_keyboard(users: list, page: int = 0) -> InlineKeyboardMarkup:
    """کیبورد لیست کاربران"""
    builder = InlineKeyboardBuilder()
    for u in users:
        uid = u['user_id'] if isinstance(u, dict) else u[0]
        uname = (u['username'] or f"ID: {uid}") if isinstance(u, dict) else (u[1] or f"ID: {uid}")
        banned = (u['is_banned']) if isinstance(u, dict) else u[5]
        status = "🚫" if banned else "✅"
        builder.row(InlineKeyboardButton(
            text=f"{status} {uname}",
            callback_data=f"user_info_{uid}"
        ))

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"users_page_{page - 1}"))
    if len(users) == 10:
        nav_buttons.append(InlineKeyboardButton(text="بعدی ➡️", callback_data=f"users_page_{page + 1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_users_menu"))
    return builder.as_markup()


# ==================== عضویت اجباری ====================

def force_join_menu_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    """منوی مدیریت عضویت اجباری"""
    builder = InlineKeyboardBuilder()
    status = "✅ فعال" if is_enabled else "❌ غیرفعال"
    toggle_text = "❌ غیرفعال کردن" if is_enabled else "✅ فعال کردن"

    builder.row(InlineKeyboardButton(
        text=f"وضعیت: {status}",
        callback_data="fj_status"
    ))
    builder.row(InlineKeyboardButton(
        text=toggle_text,
        callback_data="fj_toggle"
    ))
    builder.row(InlineKeyboardButton(
        text="➕ افزودن کانال",
        callback_data="fj_add_channel"
    ))
    builder.row(InlineKeyboardButton(
        text="➖ حذف کانال",
        callback_data="fj_remove_channel"
    ))
    builder.row(InlineKeyboardButton(
        text="📋 لیست کانال‌ها",
        callback_data="fj_list_channels"
    ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_main_menu"))
    return builder.as_markup()


def channels_list_for_removal(channels: list) -> InlineKeyboardMarkup:
    """کیبورد لیست کانال‌ها برای حذف"""
    builder = InlineKeyboardBuilder()
    for ch in channels:
        ch_id = ch['channel_id'] if isinstance(ch, dict) else ch[1]
        title = (ch['channel_title'] or 'بدون نام') if isinstance(ch, dict) else (ch[3] or 'بدون نام')
        builder.row(InlineKeyboardButton(
            text=f"🗑 {title}",
            callback_data=f"fj_remove_confirm_{ch_id}"
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_force_join"))
    return builder.as_markup()


# ==================== تنظیمات ====================

def settings_keyboard() -> InlineKeyboardMarkup:
    """کیبورد تنظیمات"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📦 تنظیم کانال ذخیره‌سازی",
        callback_data="settings_storage"
    ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_main_menu"))
    return builder.as_markup()


# ==================== Broadcast ====================

def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """کیبورد تأیید ارسال پیام همگانی"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ ارسال", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ لغو", callback_data="admin_main_menu")
    )
    return builder.as_markup()


# ==================== HELPERS ====================

def format_size(size_bytes: int) -> str:
    """تبدیل بایت به فرمت خوانا"""
    if not size_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

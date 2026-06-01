"""
کیبوردهای مربوط به عضویت اجباری
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def force_join_channels(channels: list) -> InlineKeyboardMarkup:
    """
    ساخت کیبورد عضویت اجباری با لیست کانال‌ها
    هر دکمه کاربر را به کانال مربوطه هدایت می‌کند
    """
    builder = InlineKeyboardBuilder()

    for i, ch in enumerate(channels, 1):
        username = ch.get('channel_username', '') if isinstance(ch, dict) else (ch[2] if len(ch) > 2 else '')
        title = ch.get('channel_title', f'کانال {i}') if isinstance(ch, dict) else (ch[3] if len(ch) > 3 else f'کانال {i}')

        if username:
            builder.row(InlineKeyboardButton(
                text=f"🔹 {title}",
                url=f"https://t.me/{username.replace('@', '')}"
            ))

    builder.row(InlineKeyboardButton(
        text="✅ عضو شدم",
        callback_data="check_join"
    ))

    return builder.as_markup()


def force_join_remaining(channels: list) -> InlineKeyboardMarkup:
    """
    کیبورد کانال‌هایی که کاربر هنوز عضو نشده
    """
    builder = InlineKeyboardBuilder()

    for i, ch in enumerate(channels, 1):
        username = ch.get('channel_username', '') if isinstance(ch, dict) else (ch[2] if len(ch) > 2 else '')
        title = ch.get('channel_title', f'کانال {i}') if isinstance(ch, dict) else (ch[3] if len(ch) > 3 else f'کانال {i}')

        if username:
            builder.row(InlineKeyboardButton(
                text=f"🔹 {title}",
                url=f"https://t.me/{username.replace('@', '')}"
            ))

    builder.row(InlineKeyboardButton(
        text="🔄 بررسی مجدد",
        callback_data="check_join"
    ))

    return builder.as_markup()

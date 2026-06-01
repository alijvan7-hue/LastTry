"""
کیبوردهای کاربران عادی
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def user_main_menu() -> InlineKeyboardMarkup:
    """منوی اصلی کاربر"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📥 دریافت فایل",
        callback_data="user_get_file"
    ))
    builder.row(InlineKeyboardButton(
        text="📞 تماس با پشتیبانی",
        callback_data="user_support"
    ))
    return builder.as_markup()


def support_button() -> InlineKeyboardMarkup:
    """دکمه تماس با پشتیبانی"""
    from config import OWNER_USERNAME
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📞 ارسال پیام به پشتیبانی",
        url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"
    ))
    return builder.as_markup()


def back_to_main() -> InlineKeyboardMarkup:
    """دکمه بازگشت به منوی اصلی"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔙 بازگشت به منوی اصلی",
        callback_data="user_main_menu"
    ))
    return builder.as_markup()

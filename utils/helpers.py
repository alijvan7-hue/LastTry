"""
توابع کمکی
"""

import re
from typing import Optional


def format_size(size_bytes: int) -> str:
    """تبدیل بایت به فرمت خوانا"""
    if not size_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def extract_user_id_from_text(text: str) -> Optional[int]:
    """
    استخراج شناسه کاربر از متن
    پشتیبانی از:
    - عدد مستقیم: 123456789
    - یوزرنیم: @username
    - لینک: t.me/username
    """
    text = text.strip()

    # عدد مستقیم
    if text.isdigit() or (text.startswith('-') and text[1:].isdigit()):
        return int(text)

    # یوزرنیم
    username_match = re.match(r'@(\w+)', text)
    if username_match:
        return None  # نیاز به API برای دریافت ID

    # لینک
    link_match = re.match(r'(?:https?://)?t\.me/(\w+)', text)
    if link_match:
        return None

    return None


def extract_channel_info(text: str) -> tuple:
    """
    استخراج اطلاعات کانال از متن ورودی
    Returns: (channel_id_or_username, is_id)
    """
    text = text.strip()

    # آیدی عددی منفی
    if text.startswith('-100') and text[1:].isdigit():
        return int(text), True

    if text.startswith('-') and text[1:].isdigit():
        return int(text), True

    # یوزرنیم
    username_match = re.match(r'(?:@)?(\w+)', text)
    if username_match:
        return username_match.group(1), False

    # لینک
    link_match = re.match(r'(?:https?://)?t\.me/(\w+)', text)
    if link_match:
        return link_match.group(1), False

    return None, False


def escape_markdown(text: str) -> str:
    """فرار دادن کاراکترهای مارک‌دون"""
    if not text:
        return ""
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text

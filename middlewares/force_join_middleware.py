"""
میدلور عضویت اجباری
قبل از دریافت فایل، عضویت کاربر در کانال‌های اجباری بررسی می‌شود
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database.db import db


class ForceJoinMiddleware(BaseMiddleware):
    """
    میدلور بررسی عضویت کاربر در کانال‌های اجباری
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # فقط پیام‌های متنی و callback های مربوط به دریافت فایل بررسی شوند
        if isinstance(event, Message):
            text = event.text or event.caption or ""
            # اگر کاربر در حال دریافت فایل است (start با پارامتر)
            if text.startswith("/start ") and len(text.split()) > 1:
                # اولویت با هندلر start است - در آنجا بررسی می‌کنیم
                pass

        return await handler(event, data)

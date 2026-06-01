"""
هندلر پشتیبانی - ارتباط کاربر با ادمین
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import db
from config import OWNER_ID, OWNER_USERNAME, BOT_NAME
from keyboards.user_kb import user_main_menu, support_button

router = Router()


@router.message(F.text == "📞 تماس با پشتیبانی")
async def support_text_handler(message: Message):
    """هندلر دکمه متنی تماس با پشتیبانی"""
    await message.answer(
        "📞 <b>تماس با پشتیبانی</b>\n\n"
        f"برای ارتباط با پشتیبانی {BOT_NAME}، روی دکمه زیر کلیک کنید:\n\n"
        "پیام‌ها و مشکلات خود را مستقیماً با پشتیبانی در میان بگذارید.",
        reply_markup=support_button()
    )

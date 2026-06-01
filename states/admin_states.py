"""
حالت‌های FSM برای پنل مدیریت
"""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    # منوی اصلی پنل
    MAIN_MENU = State()

    # مدیریت فایل‌ها
    FILES_LIST = State()
    FILE_DETAIL = State()
    FILE_DELETE_CONFIRM = State()

    # آپلود فایل
    UPLOAD_FILE = State()

    # جستجوی فایل
    SEARCH_FILE = State()
    SEARCH_RESULTS = State()

    # مدیریت ادمین‌ها
    ADMINS_LIST = State()
    ADD_ADMIN = State()
    REMOVE_ADMIN = State()
    REMOVE_ADMIN_CONFIRM = State()

    # مدیریت کاربران
    USERS_LIST = State()
    USER_INFO = State()
    BAN_USER = State()
    UNBAN_USER = State()
    USER_SEARCH = State()

    # پیام همگانی
    BROADCAST_MESSAGE = State()
    BROADCAST_CONFIRM = State()

    # عضویت اجباری
    FORCE_JOIN_SETTINGS = State()
    ADD_CHANNEL = State()
    REMOVE_CHANNEL = State()
    CHANNELS_LIST = State()

    # تنظیمات
    SETTINGS = State()
    SET_STORAGE_CHANNEL = State()

    # بکاپ
    BACKUP = State()

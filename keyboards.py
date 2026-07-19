from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db


# --- AUTH MENU ---
def auth_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Tizimga kirish"), KeyboardButton(text="®️ Ro'yxatdan o'tish")]
        ],
        resize_keyboard=True
    )


# --- ASOSIY MENU (Logout qo'shildi) ---
def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Papka yaratish"), KeyboardButton(text="📤 Fayl yuklash")],
            [KeyboardButton(text="📂 Fayllarim"), KeyboardButton(text="🚪 Chiqish (Logout)")]
        ],
        resize_keyboard=True
    )


# --- FOLDERS (Userga bog'langan) ---
def folders_paginated_keyboard(user_id: int, action: str, page: int = 1) -> InlineKeyboardMarkup:
    """Faqat shu user_id ga tegishli papkalarni chiqaradi"""
    PAGE_SIZE = 10
    folders = db.get_folders_paginated(user_id, page, PAGE_SIZE)
    total_folders = db.get_folders_count(user_id)

    builder = InlineKeyboardBuilder()

    # 1. Papkalar
    for f_id, f_name in folders:
        builder.button(text=f"📂 {f_name}", callback_data=f"folder:{action}:{f_id}")

    builder.adjust(2)

    # 2. Navigatsiya tugmalari
    nav_buttons = []

    # Oldingi
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"fold_nav:{action}:{page - 1}"))

    # Sahifa raqami
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}", callback_data="ignore"))

    # Keyingi
    if total_folders > page * PAGE_SIZE:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"fold_nav:{action}:{page + 1}"))

    # !!! XATOLIK TUZATILDI: row() ni faqat bir marta, oxirida chaqiramiz !!!
    builder.row(*nav_buttons)

    # 3. Qo'shimcha tugmalar
    builder.row(InlineKeyboardButton(text="🔍 Global Qidiruv", callback_data="start_global_search"))

    if action == "view":
        builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg"))

    return builder.as_markup()


# --- QIDIRUV NATIJALARI ---
def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for db_id, file_id, file_name, file_type in results:
        # Fayl turiga qarab ikonka qo'yamiz
        icon = "📄"
        if file_type == "video":
            icon = "🎥"
        elif file_type == "audio":
            icon = "🎵"
        elif file_type == "photo":
            icon = "🖼"

        builder.button(text=f"{icon} {file_name}", callback_data=f"file_dl:{db_id}")

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg"))
    return builder.as_markup()



def files_paginated_keyboard(folder_id: int, page: int = 1) -> InlineKeyboardMarkup:
    """Papka ichidagi fayllarni sahifalab chiqarish"""
    PAGE_SIZE = 10
    files = db.get_files_paginated(folder_id, page, PAGE_SIZE)
    total_files = db.get_file_count(folder_id)

    builder = InlineKeyboardBuilder()

    # 1. Fayl tugmalari
    for db_id, file_id, file_name, file_type in files:
        icon = "📄"
        if file_type == "video":
            icon = "🎥"
        elif file_type == "audio":
            icon = "🎵"
        elif file_type == "photo":
            icon = "🖼"

        # Callback: file_dl (download)
        builder.button(text=f"{icon} {file_name}", callback_data=f"file_dl:{db_id}")

    builder.adjust(1)

    # 2. Navigatsiya
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"file_nav:{folder_id}:{page - 1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"📄 {page}", callback_data="ignore"))

    if total_files > page * PAGE_SIZE:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"file_nav:{folder_id}:{page + 1}"))

    builder.row(*nav_buttons)

    # 3. Orqaga qaytish
    builder.row(InlineKeyboardButton(text="🔙 Papkalarga qaytish", callback_data="back_to_my_folders"))

    return builder.as_markup()
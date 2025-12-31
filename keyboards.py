from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Papka yaratish"), KeyboardButton(text="🎬 Video joylash")],
            [KeyboardButton(text="📂 Kinolarim")]
        ],
        resize_keyboard=True
    )


def folders_inline_keyboard(action: str) -> InlineKeyboardMarkup:
    folders = db.get_folders()
    builder = InlineKeyboardBuilder()

    for f_id, f_name in folders:
        # action: "save" yoki "view"
        builder.button(text=f"📂 {f_name}", callback_data=f"folder:{action}:{f_id}")

    builder.adjust(2)
    return builder.as_markup()


def movies_pagination_keyboard(folder_id: int, page: int = 1) -> InlineKeyboardMarkup:
    """
    Pagination va Qidiruv tugmasi bor klaviatura.
    """
    PAGE_SIZE = 10
    movies = db.get_movies_paginated(folder_id, page, PAGE_SIZE)
    total_movies = db.get_movie_count(folder_id)

    builder = InlineKeyboardBuilder()

    # 1. Kino tugmalari
    for movie_id, caption in movies:
        display_name = caption if caption else f"Kino #{movie_id}"
        builder.button(text=f"🎥 {display_name}", callback_data=f"movie:{movie_id}")

    builder.adjust(1)  # Kinolar ustun bo'lib chiqadi

    # 2. Navigatsiya tugmalari
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"nav:{folder_id}:{page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"📄 {page}-sahifa", callback_data="ignore")
    )

    if total_movies > page * PAGE_SIZE:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"nav:{folder_id}:{page + 1}")
        )

    # Navigatsiya tugmalarini qo'shamiz
    builder.row(*nav_buttons)

    # 3. Qidiruv tugmasi (YANGI)
    builder.row(InlineKeyboardButton(text="🔍 Bu papkadan qidirish", callback_data=f"start_search:{folder_id}"))

    # 4. Orqaga tugmasi
    builder.row(InlineKeyboardButton(text="🔙 Papkalar ro'yxatiga", callback_data="back_to_folders"))

    return builder.as_markup()


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """Qidiruv natijalari uchun klaviatura."""
    builder = InlineKeyboardBuilder()

    for movie_id, caption in results:
        builder.button(text=f"🎥 {caption}", callback_data=f"movie:{movie_id}")

    builder.adjust(1)

    builder.row(InlineKeyboardButton(text="❌ Qidiruvni yopish", callback_data="back_to_folders"))

    return builder.as_markup()
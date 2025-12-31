from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards import main_menu, folders_inline_keyboard, movies_pagination_keyboard, search_results_keyboard
from states import AppStates
from database import db

router = Router()


# --- START ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Xush kelibsiz! Kino botga marhamat.", reply_markup=main_menu())


# --- PAPKA YARATISH ---
@router.message(F.text == "📁 Papka yaratish")
async def ask_folder_name(message: Message, state: FSMContext):
    await message.answer("Yangi papka nomini kiriting:")
    await state.set_state(AppStates.waiting_for_folder_name)


@router.message(AppStates.waiting_for_folder_name)
async def create_folder(message: Message, state: FSMContext):
    folder_name = message.text
    db.add_folder(folder_name)
    await message.answer(f"✅ '{folder_name}' papkasi yaratildi!", reply_markup=main_menu())
    await state.clear()


# --- VIDEO JOYLASH ---
@router.message(F.text == "🎬 Video joylash")
async def ask_video(message: Message, state: FSMContext):
    await message.answer("Videoni yuboring (yoki Forward qiling):")
    await state.set_state(AppStates.waiting_for_video)


@router.message(AppStates.waiting_for_video, F.video)
async def get_video(message: Message, state: FSMContext):
    video_file_id = message.video.file_id
    caption = message.caption or message.video.file_name or "Nomsiz kino"

    await state.update_data(video_file_id=video_file_id, caption=caption)
    await message.answer("Qaysi papkaga saqlaymiz?", reply_markup=folders_inline_keyboard(action="save"))
    await state.set_state(AppStates.selecting_folder_for_video)


@router.callback_query(AppStates.selecting_folder_for_video, F.data.startswith("folder:save:"))
async def save_video_to_db(callback: CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split(":")[2])
    data = await state.get_data()

    db.add_movie(data['video_file_id'], data['caption'], folder_id)

    await callback.message.edit_text("✅ Kino muvaffaqiyatli saqlandi!")
    await state.clear()


# --- KINOLARNI KO'RISH ---
@router.message(F.text == "📂 Kinolarim")
async def show_folders(message: Message):
    await message.answer("Qaysi papkadagi kinolarni ko'rmoqchisiz?",
                         reply_markup=folders_inline_keyboard(action="view"))


@router.callback_query(F.data.startswith("folder:view:"))
async def view_folder_movies(callback: CallbackQuery):
    folder_id = int(callback.data.split(":")[2])

    # 1-sahifani chaqiramiz
    keyboard = movies_pagination_keyboard(folder_id=folder_id, page=1)

    # Agar kino bo'lmasa
    if db.get_movie_count(folder_id) == 0:
        await callback.answer("Bu papka bo'sh!", show_alert=True)
        return

    await callback.message.edit_text("🎥 Kinoni tanlang:", reply_markup=keyboard)


# Sahifalash (Navigatsiya)
@router.callback_query(F.data.startswith("nav:"))
async def navigate_pages(callback: CallbackQuery):
    _, folder_id, page = callback.data.split(":")
    folder_id = int(folder_id)
    page = int(page)

    keyboard = movies_pagination_keyboard(folder_id=folder_id, page=page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)


# Kino tanlanganda
@router.callback_query(F.data.startswith("movie:"))
async def send_selected_movie(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[1])
    movie = db.get_movie_by_id(movie_id)

    if movie:
        file_id, caption = movie
        await callback.message.answer_video(video=file_id, caption=f"🎬 {caption}")
        await callback.answer("Kino yuborilmoqda...")
    else:
        await callback.answer("Kino topilmadi.", show_alert=True)


# Qidiruvni boshlash
@router.callback_query(F.data.startswith("start_search:"))
async def start_search_mode(callback: CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split(":")[1])
    await state.update_data(search_folder_id=folder_id)
    await callback.message.answer("🔍 Kino nomini (yoki qismini) yozing:")
    await state.set_state(AppStates.waiting_for_search_query)
    await callback.answer()


# Qidiruvni bajarish
@router.message(AppStates.waiting_for_search_query)
async def perform_search(message: Message, state: FSMContext):
    query_text = message.text
    data = await state.get_data()
    folder_id = data.get('search_folder_id')

    results = db.search_movies(folder_id, query_text)

    if not results:
        await message.answer(
            f"😔 '{query_text}' bo'yicha hech narsa topilmadi.",
            reply_markup=search_results_keyboard([])
        )
        return

    await message.answer(
        f"🔍 Qidiruv natijalari ({len(results)} ta):",
        reply_markup=search_results_keyboard(results)
    )
    await state.clear()


# Orqaga qaytish
@router.callback_query(F.data == "back_to_folders")
async def back_to_folders_list(callback: CallbackQuery, state: FSMContext):
    # Qidiruvdan qaytayotgan bo'lsa, stateni tozalaymiz
    current_state = await state.get_state()
    if current_state == AppStates.waiting_for_search_query:
        await state.clear()

    await callback.message.delete()  # Eski xabarni o'chiramiz (chiroyliroq ko'rinishi uchun)
    await callback.message.answer(
        "Qaysi papkadagi kinolarni ko'rmoqchisiz?",
        reply_markup=folders_inline_keyboard(action="view")
    )
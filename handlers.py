from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ContentType

from keyboards import auth_menu, main_menu, folders_paginated_keyboard, search_results_keyboard, files_paginated_keyboard
from states import AppStates, AuthStates
from database import db

router = Router()


# ==========================================
# 1. AUTHENTICATION (KIRISH / RO'YXATDAN O'TISH)
# ==========================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # User tizimda bormi?
    user_id = db.get_user_by_telegram_id(message.from_user.id)

    if user_id:
        await message.answer(f"Xush kelibsiz! Sizning Cloud tizimingiz tayyor.", reply_markup=main_menu())
    else:
        await message.answer(
            "👋 Cloud Botga xush kelibsiz!\nFoydalanish uchun tizimga kiring yoki ro'yxatdan o'ting.",
            reply_markup=auth_menu()
        )


# --- RO'YXATDAN O'TISH ---
@router.message(F.text == "®️ Ro'yxatdan o'tish")
async def start_register(message: Message, state: FSMContext):
    await message.answer("Iltimos, o'zingizga yangi 👤 Login o'ylab toping:")
    await state.set_state(AuthStates.register_username)


@router.message(AuthStates.register_username)
async def register_get_username(message: Message, state: FSMContext):
    username = message.text
    # Loginda bo'sh joylar bo'lmasligi kerak
    if " " in username or len(username) < 3:
        await message.answer("Login juda qisqa yoki bo'sh joy bor. Boshqa login yozing:")
        return

    await state.update_data(reg_username=username)
    await message.answer("Endi 🔑 Parol o'ylab toping (kamida 6 ta belgi):")
    await state.set_state(AuthStates.register_password)


@router.message(AuthStates.register_password)
async def register_get_password(message: Message, state: FSMContext):
    password = message.text
    if len(password) < 6:
        await message.answer("Parol juda qisqa! Kamida 6 ta belgi bo'lsin.")
        return

    data = await state.get_data()
    username = data.get('reg_username')

    # Bazaga yozamiz
    success = db.register_user(message.from_user.id, username, password)

    if success:
        await message.answer(f"✅ Tabriklaymiz, {username}! Siz ro'yxatdan o'tdingiz.", reply_markup=main_menu())
        await state.clear()
    else:
        await message.answer("❌ Bu login band! Iltimos, boshqa login tanlang.")
        await state.set_state(AuthStates.register_username)


# --- TIZIMGA KIRISH (LOGIN) ---
@router.message(F.text == "🔐 Tizimga kirish")
async def start_login(message: Message, state: FSMContext):
    await message.answer("👤 Loginingizni kiriting:")
    await state.set_state(AuthStates.login_username)


@router.message(AuthStates.login_username)
async def login_get_username(message: Message, state: FSMContext):
    await state.update_data(login_username=message.text)
    await message.answer("🔑 Parolingizni kiriting:")
    await state.set_state(AuthStates.login_password)


@router.message(AuthStates.login_password)
async def login_get_password(message: Message, state: FSMContext):
    password = message.text
    data = await state.get_data()
    username = data.get('login_username')

    # Bazadan tekshiramiz
    user = db.check_login(username, password)  # Qaytaradi: (id, telegram_id)

    if user:
        user_id_db = user[0]  # Bazadagi ID sini olamiz

        # --- MUHIM O'ZGARISH: Telegram ID ni yangilaymiz ---
        db.update_user_telegram_id(user_id_db, message.from_user.id)
        # ---------------------------------------------------

        await message.answer(f"✅ Xush kelibsiz, {username}!", reply_markup=main_menu())
        await state.clear()
    else:
        await message.answer("❌ Login yoki parol xato! Qaytadan urinib ko'ring.\n/start ni bosing.")
        await state.clear()

# --- CHIQISH (LOGOUT) ---
@router.message(F.text == "🚪 Chiqish (Logout)")
async def logout(message: Message):
    # Bu yerda bazadan telegram_id ni o'chirib tashlash mumkin,
    # yoki shunchaki userga auth menyuni ko'rsatamiz.
    # Real loyihada: UPDATE users SET telegram_id=NULL WHERE telegram_id=...

    # Hozircha sodda yechim:
    await message.answer("Siz tizimdan chiqdingiz.", reply_markup=auth_menu())


# ==========================================
# 2. MAIN LOGIC (USER SPECIFIC)
# ==========================================

# --- PAPKA YARATISH ---
@router.message(F.text == "📁 Papka yaratish")
async def ask_folder_name(message: Message, state: FSMContext):
    # USERNI TEKSHIRISH
    user_id = db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("Iltimos, avval tizimga kiring!", reply_markup=auth_menu())
        return

    await message.answer("Yangi papka nomini kiriting:")
    await state.set_state(AppStates.waiting_for_folder_name)


@router.message(AppStates.waiting_for_folder_name)
async def create_folder(message: Message, state: FSMContext):
    user_id = db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("Xatolik! Tizimga kiring.")
        return

    folder_name = message.text
    db.add_folder(folder_name, user_id)  # USER_ID uzatildi!
    await message.answer(f"✅ '{folder_name}' papkasi yaratildi!", reply_markup=main_menu())
    await state.clear()


# --- FAYL YUKLASH (UNIVERSAL) ---
@router.message(F.text == "📤 Fayl yuklash")
async def ask_file(message: Message, state: FSMContext):
    user_id = db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("Iltimos, avval tizimga kiring!", reply_markup=auth_menu())
        return

    await message.answer("Istalgan faylni yuboring (Rasm, Video, Hujjat, Audio):")
    # ContentType filtrini keyingi handlerda qilamiz


# Faylni qabul qilish (Hamma turni)
@router.message(F.content_type.in_([ContentType.DOCUMENT, ContentType.VIDEO, ContentType.AUDIO, ContentType.PHOTO]))
async def receive_file(message: Message, state: FSMContext):
    user_id = db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("Auth error.")
        return

    # Fayl turini va ID sini aniqlash
    file_id = None
    file_name = "Nomsiz fayl"
    file_type = "unknown"

    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "Hujjat"
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.caption or message.video.file_name or "Video"
        file_type = "video"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "Audio"
        file_type = "audio"
    elif message.photo:
        # Photo har xil o'lchamda keladi, eng kattasini olamiz (-1)
        file_id = message.photo[-1].file_id
        file_name = message.caption or "Rasm"
        file_type = "photo"

    await state.update_data(file_id=file_id, file_name=file_name, file_type=file_type)

    # Userning papkalarini ko'rsatamiz
    await message.answer(
        f"📥 Qabul qilindi: {file_name}\nSaqlash uchun papkani tanlang:",
        reply_markup=folders_paginated_keyboard(user_id, action="save", page=1)
    )
    await state.set_state(AppStates.selecting_folder_for_file)


# Papkaga saqlash
@router.callback_query(AppStates.selecting_folder_for_file, F.data.startswith("folder:save:"))
async def save_file_to_db(callback: CallbackQuery, state: FSMContext):
    folder_id = int(callback.data.split(":")[2])
    data = await state.get_data()

    db.add_file(
        file_id=data['file_id'],
        file_name=data['file_name'],
        file_type=data['file_type'],
        folder_id=folder_id
    )

    await callback.message.edit_text("✅ Fayl muvaffaqiyatli saqlandi!")
    await state.clear()


# --- FAYLLARIM (FOLDERLARNI KO'RISH) ---
@router.message(F.text == "📂 Fayllarim")
async def show_my_folders(message: Message):
    user_id = db.get_user_by_telegram_id(message.from_user.id)
    if not user_id:
        await message.answer("Tizimga kiring!", reply_markup=auth_menu())
        return

    await message.answer(
        "Qaysi papkani ochamiz?",
        reply_markup=folders_paginated_keyboard(user_id, action="view", page=1)
    )

# --- QIDIRUV VA NAVIGATSIYA ---
# Bu qismlar oldingidek, faqat endi db.search_files(user_id, ...) chaqiriladi
# Va callback handlerlarda ham user_id ni tekshirish kerak bo'ladi.

# --- CALLBACK: FOLDER NAVIGATSIYASI (Oldingi/Keyingi) ---
@router.callback_query(F.data.startswith("fold_nav:"))
async def navigate_folders(callback: CallbackQuery):
    # data: fold_nav:action:page
    try:
        _, action, page = callback.data.split(":")
        page = int(page)

        # User ID ni aniqlash (Callbackda user_id yo'q, uni update dan olamiz)
        user_id = db.get_user_by_telegram_id(callback.from_user.id)
        if not user_id:
            await callback.answer("Sessiya tugagan. Qayta kiring.", show_alert=True)
            return

        await callback.message.edit_reply_markup(
            reply_markup=folders_paginated_keyboard(user_id, action, page)
        )
    except Exception as e:
        await callback.answer()  # Xato bo'lsa shunchaki o'tkazib yuboramiz


# --- CALLBACK: PAPKA ICHINI KO'RISH ---
@router.callback_query(F.data.startswith("folder:view:"))
async def view_folder_content(callback: CallbackQuery):
    folder_id = int(callback.data.split(":")[2])

    # Fayllarni chiqaramiz (1-sahifa)
    keyboard = files_paginated_keyboard(folder_id, page=1)

    # Xabarni yangilaymiz
    await callback.message.edit_text(
        "📂 Papka ichidagi fayllar:",
        reply_markup=keyboard
    )


# --- CALLBACK: FAYL NAVIGATSIYASI ---
@router.callback_query(F.data.startswith("file_nav:"))
async def navigate_files(callback: CallbackQuery):
    # data: file_nav:folder_id:page
    _, folder_id, page = callback.data.split(":")
    folder_id = int(folder_id)
    page = int(page)

    await callback.message.edit_reply_markup(
        reply_markup=files_paginated_keyboard(folder_id, page)
    )


# --- CALLBACK: FAYLNI YUBORISH (DOWNLOAD) ---
@router.callback_query(F.data.startswith("file_dl:"))
async def send_file_to_user(callback: CallbackQuery):
    db_id = int(callback.data.split(":")[1])
    file_data = db.get_file_by_id(db_id)

    if not file_data:
        await callback.answer("Fayl topilmadi.", show_alert=True)
        return

    file_id, file_name, file_type = file_data

    # Fayl turiga qarab yuboramiz
    try:
        if file_type == "video":
            await callback.message.answer_video(video=file_id, caption=f"🎥 {file_name}")
        elif file_type == "audio":
            await callback.message.answer_audio(audio=file_id, caption=f"🎵 {file_name}")
        elif file_type == "photo":
            await callback.message.answer_photo(photo=file_id, caption=f"🖼 {file_name}")
        else:
            await callback.message.answer_document(document=file_id, caption=f"📄 {file_name}")

        await callback.answer()
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)


# --- QIDIRUV LOGIKASI ---
@router.callback_query(F.data == "start_global_search")
async def ask_search_query(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔍 Fayl nomini (yoki qismini) yozing:")
    await state.set_state(AppStates.waiting_for_search_query)
    await callback.answer()


@router.message(AppStates.waiting_for_search_query)
async def perform_search(message: Message, state: FSMContext):
    query = message.text
    user_id = db.get_user_by_telegram_id(message.from_user.id)

    if not user_id:
        await message.answer("Sessiya tugagan. Qayta kiring.")
        return

    results = db.search_files(user_id, query)

    if not results:
        await message.answer(f"😔 '{query}' bo'yicha hech narsa topilmadi.")
        # State o'chirmaymiz, yana yozib ko'rsin
        return

    await message.answer(
        f"🔍 Qidiruv natijalari ({len(results)} ta):",
        reply_markup=search_results_keyboard(results)
    )
    await state.clear()

# --- ORQAGA QAYTISH (BACK) ---
@router.callback_query(F.data == "back_to_my_folders")
async def back_to_folders_list(callback: CallbackQuery):
    user_id = db.get_user_by_telegram_id(callback.from_user.id)
    if not user_id:
        await callback.answer("Auth error")
        return

    await callback.message.edit_text(
        "Qaysi papkani ochamiz?",
        reply_markup=folders_paginated_keyboard(user_id, action="view", page=1)
    )


# --- XABARNI O'CHIRISH (CLOSE) ---
@router.callback_query(F.data == "delete_msg")
async def delete_msg(callback: CallbackQuery):
    await callback.message.delete()
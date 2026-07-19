from aiogram.fsm.state import State, StatesGroup


class AuthStates(StatesGroup):
    register_username = State()  # Ro'yxatdan o'tish: Login kiritish
    register_password = State()  # Ro'yxatdan o'tish: Parol kiritish

    login_username = State()  # Kirish: Login kiritish
    login_password = State()  # Kirish: Parol kiritish


class AppStates(StatesGroup):
    waiting_for_folder_name = State()
    selecting_folder_for_file = State()  # O'zgardi: video emas, umumiy file
    waiting_for_search_query = State()
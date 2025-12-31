# states.py

from aiogram.fsm.state import State, StatesGroup


class AppStates(StatesGroup):
    waiting_for_folder_name = State()
    waiting_for_video = State()
    selecting_folder_for_video = State()

    # YANGI HOLAT:
    waiting_for_search_query = State()  # Qidiruv so'zini kutish holati
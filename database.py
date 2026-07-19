import sqlite3
import hashlib # Parolni shifrlash uchun
from typing import List, Tuple, Optional

class Database:
    def __init__(self, path: str = "cloud_storage.db"):
        self.path = path
        self.create_tables()

    def update_user_telegram_id(self, user_id: int, new_telegram_id: int) -> None:
        """User yangi qurilmadan kirganda uning Telegram ID sini yangilash"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # Boshqa userlarda bu ID yo'qligini tekshirishimiz mumkin (ixtiyoriy),
            # lekin hozircha to'g'ridan-to'g'ri yangilaymiz.
            cursor.execute("UPDATE users SET telegram_id = ? WHERE id = ?", (new_telegram_id, user_id))
            conn.commit()

    def create_tables(self) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()

            # 1. FOYDALANUVCHILAR JADVALI
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,  -- Telegram ID (avtomatik kirish uchun ham kerak bo'ladi)
                    username TEXT UNIQUE NOT NULL, -- Login
                    password_hash TEXT NOT NULL,   -- Parol (shifrlangan holda)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. PAPKALAR JADVALI (user_id qo'shildi)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user_id INTEGER, -- Bu papka kimniki ekanligi
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)

            # 3. FAYLLAR JADVALI (Universal)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    file_name TEXT,
                    file_type TEXT, -- video, document, audio, photo
                    folder_id INTEGER,
                    FOREIGN KEY(folder_id) REFERENCES folders(id)
                )
            """)
            conn.commit()

    # --- AUTH (RO'YXATDAN O'TISH & KIRISH) ---

    def register_user(self, telegram_id: int, username: str, password: str) -> bool:
        """Foydalanuvchini ro'yxatga olish"""
        # Parolni ochiq saqlamaymiz! Uni xeshlaymiz (MD5 yoki SHA256)
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (telegram_id, username, password_hash) VALUES (?, ?, ?)",
                    (telegram_id, username, pwd_hash)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False # Bunday login mavjud

    def check_login(self, username: str, password: str) -> Optional[Tuple[int, int]]:
        """Login va parol to'g'riligini tekshiradi. Qaytaradi: (user_id, telegram_id)"""
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, telegram_id FROM users WHERE username = ? AND password_hash = ?",
                (username, pwd_hash)
            )
            return cursor.fetchone()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[int]:
        """Telegram ID orqali tizim user_id sini oladi"""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    # --- FOLDER LOGIKASI (Userga bog'langan) ---

    def add_folder(self, name: str, user_id: int) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # Faqat shu user uchun bunday nomli papka yo'qligini tekshirish kerak aslida,
            # lekin soddalik uchun to'g'ridan-to'g'ri qo'shamiz
            cursor.execute("INSERT INTO folders (name, user_id) VALUES (?, ?)", (name, user_id))
            conn.commit()

    def get_folders_paginated(self, user_id: int, page: int = 1, page_size: int = 10) -> List[Tuple[int, str]]:
        """Faqat SHU USER ga tegishli papkalarni qaytaradi"""
        offset = (page - 1) * page_size
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM folders WHERE user_id = ? LIMIT ? OFFSET ?",
                (user_id, page_size, offset)
            )
            return cursor.fetchall()

    def get_folders_count(self, user_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM folders WHERE user_id = ?", (user_id,))
            return cursor.fetchone()[0]

    # --- FILE LOGIKASI ---

    def add_file(self, file_id: str, file_name: str, file_type: str, folder_id: int) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO files (file_id, file_name, file_type, folder_id) VALUES (?, ?, ?, ?)",
                (file_id, file_name, file_type, folder_id)
            )
            conn.commit()

    def get_files_paginated(self, folder_id: int, page: int = 1, page_size: int = 10) -> List[Tuple[int, str, str]]:
        offset = (page - 1) * page_size
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, file_id, file_name, file_type FROM files WHERE folder_id = ? LIMIT ? OFFSET ?",
                (folder_id, page_size, offset)
            )
            return cursor.fetchall()

    def get_file_count(self, folder_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files WHERE folder_id = ?", (folder_id,))
            return cursor.fetchone()[0]

    def get_file_by_id(self, db_id: int) -> Optional[Tuple[str, str, str]]:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, file_name, file_type FROM files WHERE id = ?", (db_id,))
            return cursor.fetchone()

    def search_files(self, user_id: int, query: str) -> List[Tuple[int, str, str, str]]:
        """Userning BARCHA papkalaridan fayl qidirish"""
        search_term = f"%{query}%"
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # JOIN ishlatib, faqat shu userning papkalaridagi fayllarni qidiramiz
            cursor.execute("""
                SELECT f.id, f.file_id, f.file_name, f.file_type 
                FROM files f
                JOIN folders fol ON f.folder_id = fol.id
                WHERE fol.user_id = ? AND f.file_name LIKE ? 
                LIMIT 20
            """, (user_id, search_term))
            return cursor.fetchall()

db = Database()
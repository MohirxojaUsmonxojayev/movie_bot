import sqlite3
from typing import List, Tuple, Optional

class Database:
    def __init__(self, path: str = "movies.db"):
        self.path = path
        self.create_tables()

    def create_tables(self) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    caption TEXT,
                    folder_id INTEGER,
                    FOREIGN KEY(folder_id) REFERENCES folders(id)
                )
            """)
            conn.commit()

    def add_folder(self, name: str) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO folders (name) VALUES (?)", (name,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass

    def get_folders(self) -> List[Tuple[int, str]]:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM folders")
            return cursor.fetchall()

    def add_movie(self, file_id: str, caption: str, folder_id: int) -> None:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO movies (file_id, caption, folder_id) VALUES (?, ?, ?)",
                (file_id, caption, folder_id)
            )
            conn.commit()

    def get_movies_paginated(self, folder_id: int, page: int = 1, page_size: int = 10) -> List[Tuple[int, str]]:
        """Sahifalab kinolarni qaytaradi."""
        offset = (page - 1) * page_size
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, caption FROM movies WHERE folder_id = ? LIMIT ? OFFSET ?",
                (folder_id, page_size, offset)
            )
            return cursor.fetchall()

    def get_movie_count(self, folder_id: int) -> int:
        """Papkada jami nechta kino borligini sanaydi."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM movies WHERE folder_id = ?", (folder_id,))
            return cursor.fetchone()[0]

    def get_movie_by_id(self, movie_id: int) -> Optional[Tuple[str, str]]:
        """Kino ID si bo'yicha file_id va caption ni qaytaradi."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, caption FROM movies WHERE id = ?", (movie_id,))
            return cursor.fetchone()

    def search_movies(self, folder_id: int, query: str) -> List[Tuple[int, str]]:
        """Papka ichidan qidirish."""
        search_term = f"%{query}%"
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, caption FROM movies WHERE folder_id = ? AND caption LIKE ? LIMIT 20",
                (folder_id, search_term)
            )
            return cursor.fetchall()

db = Database()
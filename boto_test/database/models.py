import os
import sqlite3
from urllib.parse import urlparse
from typing import Generator

def init_db(db_path: str) -> None:
    """
    Создает файл базы данных и таблицу для хранения ссылок, 
    если они еще не существуют.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL
            )
        """)

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Создает подключение к БД. Используется как генератор для 
    автоматического закрытия соединения после работы.
    """
    # Берем путь из переменных окружения или используем 'links.db' по умолчанию
    db_path = os.getenv("DB_URL", "links.db")
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Чтобы обращаться к колонкам по именам, а не индексам
    
    try:
        yield conn
    finally:
        conn.close()

import os
import sqlite3


def init_db(url):
    with sqlite3.connect(url) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL
            )
        """)

def get_db():
    db_path = os.getenv("DB_URL", "links.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
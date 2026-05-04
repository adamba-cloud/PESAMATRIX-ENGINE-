import sqlite3
import os

DB_NAME = "users.db"

# ---------------- CONNECTION ----------------
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()


# ---------------- CREATE TABLES ----------------
def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()


# ---------------- USER FUNCTIONS ----------------
def add_user(telegram_id: int):
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
        (telegram_id,)
    )
    conn.commit()


def get_users():
    cursor.execute("SELECT telegram_id FROM users")
    return cursor.fetchall()


# ---------------- TRADE LOGGING ----------------
def log_trade(symbol, side, entry, sl, tp, status="executed"):
    cursor.execute("""
        INSERT INTO trades (symbol, side, entry, sl, tp, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (symbol, side, entry, sl, tp, status))

    conn.commit()


def get_trades(limit=50):
    cursor.execute("""
        SELECT * FROM trades
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    return cursor.fetchall()


# ---------------- INIT ON IMPORT ----------------
init_db()

# database.py

import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "transactions.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT,
            recipient TEXT,
            amount REAL,
            currency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def record_transaction(reference, recipient, amount, currency):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (reference, recipient, amount, currency)
        VALUES (?, ?, ?, ?)
    """, (reference, recipient, amount, currency))
    conn.commit()
    conn.close()

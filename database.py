import sqlite3

import sqlite3
import pandas as pd

DB_NAME = "portfolio.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def fetch_table(table_name):
    conn = get_connection()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bonds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        principal REAL,
        interest_rate REAL,
        purchase_date TEXT
    )
    """)

    conn.commit()
    conn.close()

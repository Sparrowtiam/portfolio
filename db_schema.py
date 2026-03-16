# Portfolio Tracker Database Schema
# This file defines the SQLite schema for all supported asset classes.

import sqlite3

DB_NAME = 'portfolio.db'

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # SACCO contributions
    c.execute('''CREATE TABLE IF NOT EXISTS sacco (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        year INTEGER,
        contribution REAL,
        interest_rate REAL DEFAULT 0.13
    )''')
    # Government bonds
    c.execute('''CREATE TABLE IF NOT EXISTS bonds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        principal REAL,
        rate REAL,
        start_date TEXT,
        duration_months INTEGER
    )''')
    # Cryptocurrencies
    c.execute('''CREATE TABLE IF NOT EXISTS crypto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        amount REAL,
        purchase_price REAL
    )''')
    # Money Market Fund
    c.execute('''CREATE TABLE IF NOT EXISTS mmf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        balance REAL,
        annual_rate REAL,
        last_update TEXT
    )''')
    # Stocks
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        shares REAL,
        purchase_price REAL,
        current_price REAL
    )''')
    # Portfolio toggles
    c.execute('''CREATE TABLE IF NOT EXISTS toggles (
        asset_type TEXT PRIMARY KEY,
        enabled INTEGER DEFAULT 1
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()

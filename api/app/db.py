import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "dialer.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            pass_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'rep'
        );

        CREATE TABLE IF NOT EXISTS calls (
            sid TEXT PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            to_number TEXT NOT NULL,
            region TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            duration INTEGER,
            recording_sid TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    conn.close()

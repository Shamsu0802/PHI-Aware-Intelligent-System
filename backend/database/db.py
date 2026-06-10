import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "privacy_monitor.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Module 1 risk analysis logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        risk_level TEXT,
        composite_score REAL,
        phi_count INTEGER,
        recipient_type TEXT,
        attachment INTEGER,
        time_of_day TEXT,
        explanation TEXT
    )
    """)

    # Module 3 screen privacy logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screen_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        privacy_state TEXT,
        reason TEXT
    )
    """)

    # Unified incident log for Modules 1, 2 and 3
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incident_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        module TEXT,
        event_type TEXT,
        risk_level TEXT,
        details TEXT,
        action_taken TEXT
    )
    """)

    conn.commit()
    conn.close()
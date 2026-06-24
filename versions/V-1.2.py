# V-1.2 — baseline schema
# Creates the cri_version tracking table for the first time.
import os
import sqlite3

DB_PATH = os.getenv("APP_DB_PATH", "CRIMan.db")

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS cri_version (
        version TEXT PRIMARY KEY,
        applied_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

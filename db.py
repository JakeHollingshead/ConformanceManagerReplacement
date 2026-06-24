import os
import sqlite3

DB_PATH = os.getenv("APP_DB_PATH", "CRIMan.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA timeout=5")
    return conn


def next_cert_number(conn) -> str:
    row = conn.execute(
        "SELECT MAX(CAST(srv_cert AS INTEGER)) FROM service WHERE srv_cert GLOB '[0-9][0-9][0-9][0-9]'"
    ).fetchone()
    max_val = row[0] if row and row[0] is not None else 0
    return f"{max_val + 1:04d}"

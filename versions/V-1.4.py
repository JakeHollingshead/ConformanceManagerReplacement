# V-1.4 — Remove mfr_descr and md_description; add srv_owner to service.
import os
import sqlite3

DB_PATH = os.getenv("APP_DB_PATH", "CRIMan.db")

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript("""
    PRAGMA foreign_keys = OFF;

    -- Manufacturer: drop mfr_descr
    ALTER TABLE Manufacturer RENAME TO _manufacturer_old;
    CREATE TABLE Manufacturer (
        mfr_id TEXT PRIMARY KEY,
        mfr_name TEXT NOT NULL
    );
    INSERT INTO Manufacturer (mfr_id, mfr_name)
        SELECT mfr_id, mfr_name FROM _manufacturer_old;
    DROP TABLE _manufacturer_old;

    -- models: drop md_description
    ALTER TABLE models RENAME TO _models_old;
    CREATE TABLE models (
        md_id TEXT PRIMARY KEY,
        md_name TEXT NOT NULL,
        md_size TEXT NOT NULL,
        md_endsize TEXT NOT NULL,
        md_mfr_id TEXT NOT NULL
    );
    INSERT INTO models (md_id, md_name, md_size, md_endsize, md_mfr_id)
        SELECT md_id, md_name, md_size, md_endsize, md_mfr_id FROM _models_old;
    DROP TABLE _models_old;

    PRAGMA foreign_keys = ON;
    """)
    # service: add srv_owner (ALTER ADD COLUMN works for new nullable columns)
    try:
        conn.execute("ALTER TABLE service ADD COLUMN srv_owner TEXT")
    except Exception:
        pass  # column already exists

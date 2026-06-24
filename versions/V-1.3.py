# V-1.3 — relax NOT NULL on all *description* columns and *asset_tag* columns.
# SQLite does not support ALTER COLUMN, so each affected table is recreated.
import os
import sqlite3

DB_PATH = os.getenv("APP_DB_PATH", "CRIMan.db")

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript("""
    PRAGMA foreign_keys = OFF;

    -- service: make srv_description nullable (srv_asset_tag already nullable)
    ALTER TABLE service RENAME TO _service_old;
    CREATE TABLE service (
        srv_id TEXT PRIMARY KEY,
        srv_description TEXT,
        srv_md_id TEXT,
        srv_loc_id TEXT,
        srv_asset_tag TEXT,
        srv_user_id TEXT NOT NULL,
        srv_calibration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        srv_cert TEXT NOT NULL,
        srv_last_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        srv_next_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        srv_post_condition TEXT NOT NULL
    );
    INSERT INTO service SELECT * FROM _service_old;
    DROP TABLE _service_old;

    -- models: make md_description nullable
    ALTER TABLE models RENAME TO _models_old;
    CREATE TABLE models (
        md_id TEXT PRIMARY KEY,
        md_name TEXT NOT NULL,
        md_size TEXT NOT NULL,
        md_endsize TEXT NOT NULL,
        md_mfr_id TEXT NOT NULL,
        md_description TEXT
    );
    INSERT INTO models SELECT * FROM _models_old;
    DROP TABLE _models_old;

    -- location: make loc_description nullable
    ALTER TABLE location RENAME TO _location_old;
    CREATE TABLE location (
        loc_id TEXT PRIMARY KEY,
        loc_name TEXT NOT NULL,
        loc_description TEXT
    );
    INSERT INTO location SELECT * FROM _location_old;
    DROP TABLE _location_old;

    -- scheduler: make sched_description nullable
    ALTER TABLE scheduler RENAME TO _scheduler_old;
    CREATE TABLE scheduler (
        sched_id TEXT PRIMARY KEY,
        sched_name TEXT NOT NULL,
        sched_description TEXT,
        sched_email TEXT NOT NULL,
        sched_cron TEXT NOT NULL,
        sched_last_run TIMESTAMP,
        sched_next_run TIMESTAMP
    );
    INSERT INTO scheduler SELECT * FROM _scheduler_old;
    DROP TABLE _scheduler_old;

    PRAGMA foreign_keys = ON;
    """)

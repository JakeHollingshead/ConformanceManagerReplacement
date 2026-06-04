import sqlite3
# import uuid

# class GUID:
#     @staticmethod
#     def uuid4():
#         return str(uuid.uuid4())


def initialize_database(db_path: str = "CRIMan.db") -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS Manufacturer (
                mfr_id TEXT PRIMARY KEY,
                mfr_name TEXT NOT NULL,
                mfr_descr TEXT NOT NULL
            );
        """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS models (
                md_id TEXT PRIMARY KEY,
                md_name TEXT NOT NULL,
                md_size TEXT NOT NULL,
                md_endsize TEXT NOT NULL,
                md_mfr_id TEXT NOT NULL,
                md_description TEXT NOT NULL
            );
        """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(f"""
            CREATE TABLE IF NOT EXISTS location (
                loc_id TEXT PRIMARY KEY,
                loc_name TEXT NOT NULL,
                loc_description TEXT NOT NULL
            );
        """)
    # with sqlite3.connect(db_path) as connection:
    #     connection.executescript("""
    #     CREATE TABLE IF NOT EXISTS unit (
    #         uni_id TEXT PRIMARY KEY,
    #         uni_name TEXT NOT NULL,
    #         uni_description TEXT NOT NULL,
    #         uni_md_id TEXT NOT NULL,
    #         uni_loc_id TEXT NOT NULL,
    #         uni_asset_tag TEXT NOT NULL,
    #         uni_serial_number TEXT NOT NULL,
    #         uni_equipment_number TEXT NOT NULL,
    #         unit_create_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         unit_update_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #         unit_delete_ts TIMESTAMP,
    #         uni_deleted BOOLEAN NOT NULL DEFAULT 0
    #     );
    # """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            user_loc_id TEXT
        );
    """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS service (
            srv_id TEXT PRIMARY KEY,
            -- srv_type TEXT NOT NULL,
            srv_description TEXT NOT NULL,
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
    """)
    # Safely migrate existing databases to the canonical schema
    with sqlite3.connect(db_path) as connection:
        for col_sql in [
            "ALTER TABLE service ADD COLUMN srv_md_id TEXT",
            "ALTER TABLE service ADD COLUMN srv_loc_id TEXT",
            "ALTER TABLE service ADD COLUMN srv_asset_tag TEXT",
            "ALTER TABLE users ADD COLUMN user_loc_id TEXT",
        ]:
            try:
                connection.execute(col_sql)
            except sqlite3.OperationalError:
                pass
        # Drop legacy columns no longer in the canonical schema
        for drop_sql in [
            "ALTER TABLE service DROP COLUMN srv_uni_id",
            "ALTER TABLE models DROP COLUMN md_make",
            "ALTER TABLE models DROP COLUMN md_type",
        ]:
            try:
                connection.execute(drop_sql)
            except sqlite3.OperationalError:
                pass
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS scheduler (
            sched_id TEXT PRIMARY KEY,
            sched_name TEXT NOT NULL,
            sched_description TEXT NOT NULL,
            sched_email TEXT NOT NULL,
            sched_cron TEXT NOT NULL,
            sched_last_run TIMESTAMP,
            sched_next_run TIMESTAMP
        );
    """)

if __name__ == "__main__":
    initialize_database()

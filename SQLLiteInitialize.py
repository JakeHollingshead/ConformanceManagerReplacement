import sqlite3


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
                md_make TEXT NOT NULL,
                md_mfr_id TEXT NOT NULL,
                md_description TEXT NOT NULL
            );
        """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS location (
                loc_id TEXT PRIMARY KEY,
                loc_name TEXT NOT NULL,
                loc_description TEXT NOT NULL
            );
        """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS unit (
            uni_id TEXT PRIMARY KEY,
            uni_name TEXT NOT NULL,
            uni_description TEXT NOT NULL,
            uni_md_id TEXT NOT NULL,
            uni_loc_id TEXT NOT NULL,
            uni_serial_number TEXT NOT NULL,
            unit_create_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unit_update_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unit_delete_ts TIMESTAMP,
            uni_deleted BOOLEAN NOT NULL DEFAULT 0
        );
    """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS location (
            loc_id TEXT PRIMARY KEY,
            loc_name TEXT NOT NULL,
            loc_description TEXT NOT NULL
        );
    """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL
        );
    """)
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS service (
            srv_id TEXT PRIMARY KEY,
            srv_type TEXT NOT NULL,
            srv_description TEXT NOT NULL,
            srv_uni_id TEXT NOT NULL,
            srv_user_id TEXT NOT NULL,
            srv_last_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            srv_next_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            srv_post_condition TEXT NOT NULL
        );
    """)

if __name__ == "__main__":
    initialize_database()

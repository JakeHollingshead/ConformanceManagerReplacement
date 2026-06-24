#CRIMan.py
#---------------------------------------------------------------------------------
#Flask platform for Conformance Manager calibration and service record management
#---------------------------------------------------------------------------------
import os
import re
import runpy
import sqlite3
from datetime import datetime
from flask import Flask
from SQLLiteInitializeCRIMan import initialize_database
from db import DB_PATH

from blueprints.auth import auth_bp
from blueprints.home import home_bp
from blueprints.locations import locations_bp
from blueprints.manufacturers import manufacturers_bp
from blueprints.units import units_bp
from blueprints.users import users_bp
from blueprints.help_bp import help_bp
from blueprints.export import export_bp
from blueprints.import_bp import import_bp 
from blueprints.service import service_bp
from blueprints.add_tool import add_tool_bp
from blueprints.scheduler import scheduler_bp
from blueprints.datanormalization import datanormalization_bp

def _version_key(filename: str):
    return [int(n) for n in re.findall(r'\d+', filename)]


def run_version_migrations(db_path: str) -> None:
    versions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'versions')
    if not os.path.isdir(versions_dir):
        return
    # Bootstrap the tracking table so we can query it even on existing DBs
    # that predate versioning. V-1.2.py also creates it, but we need it first.
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cri_version (
                version TEXT PRIMARY KEY,
                applied_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        applied = {row[0] for row in conn.execute("SELECT version FROM cri_version").fetchall()}
    pending = sorted(
        [f for f in os.listdir(versions_dir) if f.startswith('V-') and f.endswith('.py')],
        key=_version_key
    )
    for filename in pending:
        version_key = filename[:-3]
        if version_key not in applied:
            runpy.run_path(os.path.join(versions_dir, filename))
            with sqlite3.connect(db_path) as conn:
                conn.execute("INSERT INTO cri_version (version) VALUES (?)", (version_key,))
                conn.commit()


CRIMan = Flask(__name__)
CRIMan.secret_key = os.getenv("APP_SECRET_KEY", "criман-dev-secret")

if not os.path.exists(DB_PATH):
    initialize_database(DB_PATH)
run_version_migrations(DB_PATH)

_TS_FORMATS = (
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d',
)

@CRIMan.context_processor
def inject_db_version():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT version FROM cri_version ORDER BY version DESC LIMIT 1"
            ).fetchone()
        return {'db_version': row[0] if row else 'unknown'}
    except Exception:
        return {'db_version': 'unknown'}


@CRIMan.template_filter('fmt_ts')
def fmt_ts(value):
    if not value:
        return ''
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime('%m/%d/%Y %I:%M %p')
        except ValueError:
            continue
    return value

CRIMan.register_blueprint(auth_bp)
CRIMan.register_blueprint(home_bp)
CRIMan.register_blueprint(locations_bp)
CRIMan.register_blueprint(manufacturers_bp)
CRIMan.register_blueprint(units_bp)
CRIMan.register_blueprint(users_bp)
CRIMan.register_blueprint(help_bp)
CRIMan.register_blueprint(export_bp)
CRIMan.register_blueprint(import_bp)
CRIMan.register_blueprint(service_bp)
CRIMan.register_blueprint(add_tool_bp)
CRIMan.register_blueprint(scheduler_bp)
CRIMan.register_blueprint(datanormalization_bp)

if __name__ == '__main__':
    CRIMan.run(debug=True)

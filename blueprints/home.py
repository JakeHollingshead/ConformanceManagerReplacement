from flask import Blueprint, render_template
from db import get_db_connection

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def home():
    conn = get_db_connection()
    srv_rows = conn.execute("""
        SELECT s.srv_id, s.srv_description,
               s.srv_md_id, mfr.mfr_name, m.md_name, s.srv_asset_tag,
               s.srv_loc_id, l.loc_name,
               s.srv_user_id, us.user_name,
               s.srv_calibration_date, s.srv_cert,
               s.srv_last_date, s.srv_next_date, s.srv_post_condition
        FROM service s
        LEFT JOIN models m ON s.srv_md_id = m.md_id
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
        LEFT JOIN location l ON s.srv_loc_id = l.loc_id
        LEFT JOIN users us ON s.srv_user_id = us.user_id
        ORDER BY s.srv_next_date ASC
    """).fetchall()
    conn.close()
    return render_template('index.html', services=srv_rows)

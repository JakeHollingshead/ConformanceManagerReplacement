import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

units_bp = Blueprint('units', __name__)


@units_bp.route('/Units')
def units():
    return redirect(url_for('service.service'))


@units_bp.route('/Units_legacy')
def units_legacy():
    conn = get_db_connection()
    unit_rows = conn.execute("""
        SELECT u.uni_id, u.uni_name, u.uni_description,
               u.uni_md_id, m.md_name,
               u.uni_loc_id, l.loc_name,
               u.uni_asset_tag, u.uni_serial_number, u.uni_equipment_number,
               u.unit_create_ts, u.unit_update_ts
        FROM unit u
        LEFT JOIN models m ON u.uni_md_id = m.md_id
        LEFT JOIN location l ON u.uni_loc_id = l.loc_id
        WHERE u.uni_deleted = 0
    """).fetchall()
    mds = conn.execute("SELECT md_id, md_name FROM models").fetchall()
    locs = conn.execute("SELECT loc_id, loc_name FROM location").fetchall()
    conn.close()
    return render_template('Units.html', units=unit_rows, models=mds, locations=locs)


@units_bp.route('/Units/add', methods=['POST'])
def units_add():
    uni_id = str(uuid.uuid4())
    uni_name = request.form['uni_name']
    uni_description = request.form['uni_description']
    uni_md_id = request.form['uni_md_id']
    uni_loc_id = request.form['uni_loc_id']
    uni_asset_tag = request.form['uni_asset_tag']
    uni_serial_number = request.form['uni_serial_number']
    uni_equipment_number = request.form['uni_equipment_number']
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO unit
           (uni_id, uni_name, uni_description, uni_md_id, uni_loc_id,
            uni_asset_tag, uni_serial_number, uni_equipment_number, uni_deleted)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (uni_id, uni_name, uni_description, uni_md_id, uni_loc_id,
         uni_asset_tag, uni_serial_number, uni_equipment_number)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('units.units'))


@units_bp.route('/Units/edit', methods=['POST'])
def units_edit():
    uni_id = request.form['uni_id']
    uni_name = request.form['uni_name']
    uni_description = request.form['uni_description']
    uni_md_id = request.form['uni_md_id']
    uni_loc_id = request.form['uni_loc_id']
    uni_asset_tag = request.form['uni_asset_tag']
    uni_serial_number = request.form['uni_serial_number']
    uni_equipment_number = request.form['uni_equipment_number']
    conn = get_db_connection()
    conn.execute(
        """UPDATE unit SET
           uni_name = ?, uni_description = ?, uni_md_id = ?, uni_loc_id = ?,
           uni_asset_tag = ?, uni_serial_number = ?, uni_equipment_number = ?,
           unit_update_ts = CURRENT_TIMESTAMP
           WHERE uni_id = ?""",
        (uni_name, uni_description, uni_md_id, uni_loc_id,
         uni_asset_tag, uni_serial_number, uni_equipment_number, uni_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('units.units'))


@units_bp.route('/Units/delete', methods=['POST'])
def units_delete():
    uni_id = request.form['uni_id']
    conn = get_db_connection()
    conn.execute(
        "UPDATE unit SET uni_deleted = 1, unit_delete_ts = CURRENT_TIMESTAMP WHERE uni_id = ?",
        (uni_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('units.units'))

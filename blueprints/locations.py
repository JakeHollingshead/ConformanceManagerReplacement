import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

locations_bp = Blueprint('locations', __name__)


@locations_bp.route('/Locations')
def locations():
    conn = get_db_connection()
    locs = conn.execute("SELECT * FROM location").fetchall()
    locscount = conn.execute("SELECT COUNT(*) FROM location").fetchone()[0]
    if locscount == 0:
        conn.executescript(f"""
            INSERT INTO location (loc_id, loc_name, loc_description) VALUES ( '{uuid.uuid4()}', 'Facility-A', 'Main Facility');
            INSERT INTO location (loc_id, loc_name, loc_description) VALUES ( '{uuid.uuid4()}', 'Facility-B', 'Secondary Facility');
            INSERT INTO location (loc_id, loc_name, loc_description) VALUES ( '{uuid.uuid4()}', 'Facility-C', 'Third Facility');
        """)
    conn.close()
    return render_template('Locations.html', locations=locs)


@locations_bp.route('/Locations/add', methods=['POST'])
def locations_add():
    loc_id = str(uuid.uuid4())
    loc_name = request.form['loc_name']
    loc_description = request.form['loc_description']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO location (loc_id, loc_name, loc_description) VALUES (?, ?, ?)",
        (loc_id, loc_name, loc_description)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('locations.locations'))


@locations_bp.route('/Locations/edit', methods=['POST'])
def locations_edit():
    loc_id = request.form['loc_id']
    loc_name = request.form['loc_name']
    loc_description = request.form['loc_description']
    conn = get_db_connection()
    conn.execute(
        "UPDATE location SET loc_name = ?, loc_description = ? WHERE loc_id = ?",
        (loc_name, loc_description, loc_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('locations.locations'))


@locations_bp.route('/Locations/delete', methods=['POST'])
def locations_delete():
    loc_id = request.form['loc_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM location WHERE loc_id = ?", (loc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('locations.locations'))

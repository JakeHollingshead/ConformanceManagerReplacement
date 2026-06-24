import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

manufacturers_bp = Blueprint('manufacturers', __name__)


@manufacturers_bp.route('/Manufacturers')
def manufacturers():
    conn = get_db_connection()
    mfrs = conn.execute("SELECT * FROM Manufacturer").fetchall()
    conn.close()
    return render_template('Manufacturers.html', manufacturers=mfrs)


@manufacturers_bp.route('/Manufacturers/add', methods=['POST'])
def mfr_add():
    mfr_id = str(uuid.uuid4())
    mfr_name = request.form['mfr_name']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO Manufacturer (mfr_id, mfr_name) VALUES (?, ?)",
        (mfr_id, mfr_name)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.manufacturers'))


@manufacturers_bp.route('/Manufacturers/edit', methods=['POST'])
def mfr_edit():
    mfr_id = request.form['mfr_id']
    mfr_name = request.form['mfr_name']
    conn = get_db_connection()
    conn.execute(
        "UPDATE Manufacturer SET mfr_name = ? WHERE mfr_id = ?",
        (mfr_name, mfr_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.manufacturers'))


@manufacturers_bp.route('/Manufacturers/delete', methods=['POST'])
def mfr_delete():
    mfr_id = request.form['mfr_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM Manufacturer WHERE mfr_id = ?", (mfr_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.manufacturers'))


@manufacturers_bp.route('/Models')
def models():
    conn = get_db_connection()
    mfrs = conn.execute("SELECT * FROM Manufacturer").fetchall()
    mds = conn.execute("""
        SELECT m.md_id, m.md_name, m.md_size, m.md_endsize,
               m.md_mfr_id, mfr.mfr_name
        FROM models m
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
    """).fetchall()
    conn.close()
    return render_template('Models.html', manufacturers=mfrs, models=mds)


@manufacturers_bp.route('/Models/add', methods=['POST'])
def md_add():
    md_id = str(uuid.uuid4())
    md_name = request.form['md_name']
    md_size = request.form['md_size']
    md_endsize = request.form['md_endsize']
    md_mfr_id = request.form['md_mfr_id']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO models (md_id, md_name, md_size, md_endsize, md_mfr_id) VALUES (?, ?, ?, ?, ?)",
        (md_id, md_name, md_size, md_endsize, md_mfr_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.models'))


@manufacturers_bp.route('/Models/edit', methods=['POST'])
def md_edit():
    md_id = request.form['md_id']
    md_name = request.form['md_name']
    md_size = request.form['md_size']
    md_endsize = request.form['md_endsize']
    md_mfr_id = request.form['md_mfr_id']
    conn = get_db_connection()
    conn.execute(
        "UPDATE models SET md_name = ?, md_size = ?, md_endsize = ?, md_mfr_id = ? WHERE md_id = ?",
        (md_name, md_size, md_endsize, md_mfr_id, md_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.models'))


@manufacturers_bp.route('/Models/delete', methods=['POST'])
def md_delete():
    md_id = request.form['md_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM models WHERE md_id = ?", (md_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers.models'))

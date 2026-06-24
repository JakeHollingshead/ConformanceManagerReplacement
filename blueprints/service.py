import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection, next_cert_number

service_bp = Blueprint('service', __name__)


@service_bp.route('/Service')
def service():
    conn = get_db_connection()
    srv_rows = conn.execute("""
        SELECT s.srv_id, s.srv_description,
               s.srv_md_id, m.md_name, mfr.mfr_name,
               s.srv_loc_id, l.loc_name,
               s.srv_asset_tag,
               s.srv_user_id, us.user_name,
               s.srv_owner,
               s.srv_calibration_date, s.srv_cert,
               s.srv_last_date, s.srv_next_date, s.srv_post_condition
        FROM service s
        LEFT JOIN models m ON s.srv_md_id = m.md_id
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
        LEFT JOIN location l ON s.srv_loc_id = l.loc_id
        LEFT JOIN users us ON s.srv_user_id = us.user_id
    """).fetchall()
    model_rows = conn.execute("""
        SELECT m.md_id, m.md_name, mfr.mfr_name
        FROM models m
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
        ORDER BY mfr.mfr_name, m.md_name
    """).fetchall()
    loc_rows = conn.execute("SELECT loc_id, loc_name FROM location ORDER BY loc_name").fetchall()
    user_rows = conn.execute("SELECT user_id, user_name FROM users").fetchall()
    next_cert = next_cert_number(conn)
    conn.close()
    return render_template('Service.html', services=srv_rows, models=model_rows,
                           locations=loc_rows, users=user_rows, next_cert=next_cert)


@service_bp.route('/Service/add', methods=['POST'])
def service_add():
    srv_id = str(uuid.uuid4())
    srv_description = request.form.get('srv_description', '')
    srv_md_id = request.form['srv_md_id']
    srv_loc_id = request.form.get('srv_loc_id') or None
    srv_asset_tag = request.form.get('srv_asset_tag', '')
    srv_user_id = request.form['srv_user_id']
    srv_owner = request.form.get('srv_owner') or None
    srv_calibration_date = request.form.get('srv_calibration_date') or None
    srv_cert = request.form.get('srv_cert', '')
    srv_last_date = request.form.get('srv_last_date') or None
    srv_next_date = request.form.get('srv_next_date') or None
    srv_post_condition = request.form['srv_post_condition']
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO service
           (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
            srv_user_id, srv_owner, srv_calibration_date, srv_cert,
            srv_last_date, srv_next_date, srv_post_condition)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
         srv_user_id, srv_owner, srv_calibration_date, srv_cert,
         srv_last_date, srv_next_date, srv_post_condition)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('service.service'))


@service_bp.route('/Service/edit', methods=['POST'])
def service_edit():
    srv_id = request.form['srv_id']
    srv_description = request.form.get('srv_description', '')
    srv_md_id = request.form['srv_md_id']
    srv_loc_id = request.form.get('srv_loc_id') or None
    srv_asset_tag = request.form.get('srv_asset_tag', '')
    srv_user_id = request.form['srv_user_id']
    srv_owner = request.form.get('srv_owner') or None
    srv_calibration_date = request.form.get('srv_calibration_date') or None
    srv_cert = request.form.get('srv_cert', '')
    srv_last_date = request.form.get('srv_last_date') or None
    srv_next_date = request.form.get('srv_next_date') or None
    srv_post_condition = request.form['srv_post_condition']
    conn = get_db_connection()
    conn.execute(
        """UPDATE service SET
           srv_description = ?, srv_md_id = ?, srv_loc_id = ?, srv_asset_tag = ?,
           srv_user_id = ?, srv_owner = ?, srv_calibration_date = ?, srv_cert = ?,
           srv_last_date = ?, srv_next_date = ?, srv_post_condition = ?
           WHERE srv_id = ?""",
        (srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
         srv_user_id, srv_owner, srv_calibration_date, srv_cert,
         srv_last_date, srv_next_date, srv_post_condition, srv_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('service.service'))


@service_bp.route('/Service/delete', methods=['POST'])
def service_delete():
    srv_id = request.form['srv_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM service WHERE srv_id = ?", (srv_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('service.service'))

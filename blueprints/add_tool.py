import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection, next_cert_number

add_tool_bp = Blueprint('add_tool', __name__)


@add_tool_bp.route('/AddTool')
def add_tool():
    conn = get_db_connection()
    manufacturers = conn.execute("SELECT mfr_id, mfr_name FROM Manufacturer ORDER BY mfr_name").fetchall()
    models = conn.execute("SELECT md_id, md_name, md_size, md_endsize, md_mfr_id FROM models ORDER BY md_name").fetchall()
    locations = conn.execute("SELECT loc_id, loc_name FROM location ORDER BY loc_name").fetchall()
    users = conn.execute("SELECT user_id, user_name FROM users ORDER BY user_name").fetchall()
    next_cert = next_cert_number(conn)
    conn.close()
    return render_template('AddTool.html',
                           manufacturers=manufacturers, models=models,
                           locations=locations, users=users, next_cert=next_cert)


@add_tool_bp.route('/AddTool/submit', methods=['POST'])
def add_tool_submit():
    conn = get_db_connection()

    mfr_mode = request.form.get('mfr_mode', 'existing')
    if mfr_mode == 'new':
        mfr_id = str(uuid.uuid4())
        mfr_name = request.form['new_mfr_name']
        conn.execute(
            "INSERT INTO Manufacturer (mfr_id, mfr_name) VALUES (?, ?)",
            (mfr_id, mfr_name)
        )
    else:
        mfr_id = request.form['existing_mfr_id']
        row = conn.execute("SELECT mfr_name FROM Manufacturer WHERE mfr_id = ?", (mfr_id,)).fetchone()
        mfr_name = row['mfr_name'] if row else ''

    md_mode = request.form.get('md_mode', 'existing')
    if md_mode == 'new':
        md_id = str(uuid.uuid4())
        md_name = request.form['new_md_name']
        conn.execute(
            "INSERT INTO models (md_id, md_name, md_size, md_endsize, md_mfr_id) VALUES (?, ?, ?, ?, ?)",
            (md_id, md_name, request.form.get('new_md_size', ''),
             request.form.get('new_md_endsize', ''), mfr_id)
        )
    else:
        md_id = request.form['existing_md_id']
        row = conn.execute("SELECT md_name FROM models WHERE md_id = ?", (md_id,)).fetchone()
        md_name = row['md_name'] if row else ''

    conn.execute(
        """INSERT INTO service
           (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
            srv_user_id, srv_owner, srv_calibration_date, srv_cert,
            srv_last_date, srv_next_date, srv_post_condition)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), request.form.get('srv_description', ''),
         md_id, request.form.get('uni_loc_id') or None, request.form.get('uni_asset_tag', ''),
         request.form['srv_user_id'],
         request.form.get('srv_owner') or None,
         request.form.get('srv_calibration_date') or None,
         request.form.get('srv_cert', ''),
         request.form.get('srv_last_date') or None,
         request.form.get('srv_next_date') or None,
         request.form.get('srv_post_condition', 'New'))
    )

    conn.commit()
    conn.close()
    return redirect(url_for('service.service'))

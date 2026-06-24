import uuid
from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

users_bp = Blueprint('users', __name__)


@users_bp.route('/Users')
def users():
    conn = get_db_connection()
    user_rows = conn.execute("""
        SELECT u.user_id, u.user_name, u.user_loc_id, l.loc_name
        FROM users u
        LEFT JOIN location l ON u.user_loc_id = l.loc_id
        ORDER BY u.user_name
    """).fetchall()
    loc_rows = conn.execute("SELECT loc_id, loc_name FROM location ORDER BY loc_name").fetchall()
    conn.close()
    return render_template('Users.html', users=user_rows, locations=loc_rows)


@users_bp.route('/Users/add', methods=['POST'])
def users_add():
    user_id = str(uuid.uuid4())
    user_name = request.form['user_name']
    user_loc_id = request.form.get('user_loc_id') or None
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO users (user_id, user_name, user_loc_id) VALUES (?, ?, ?)",
        (user_id, user_name, user_loc_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('users.users'))


@users_bp.route('/Users/edit', methods=['POST'])
def users_edit():
    user_id = request.form['user_id']
    user_name = request.form['user_name']
    user_loc_id = request.form.get('user_loc_id') or None
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET user_name = ?, user_loc_id = ? WHERE user_id = ?",
        (user_name, user_loc_id, user_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('users.users'))


@users_bp.route('/Users/delete', methods=['POST'])
def users_delete():
    user_id = request.form['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('users.users'))

#CRIMan.py
#---------------------------------------------------------------------------------
#Flask criit platform for Manager Operations System Network
#---------------------------------------------------------------------------------
import io
import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from SQLLiteInitializeCRIMan import initialize_database
from smtptosms import send_message

DB_PATH = os.getenv("CRIIT_DB_PATH", "CRIMan.db")
APP_USERNAME = os.getenv("APP_USERNAME", "ISO")
APP_PASSWORD = os.getenv("APP_PASSWORD", "A123456!")

CRIMan = Flask(__name__)
CRIMan.secret_key = os.getenv("APP_SECRET_KEY", "criман-dev-secret")

# Initialize the database tables on startup (CREATE TABLE IF NOT EXISTS — safe to call every time)
initialize_database(DB_PATH)


@CRIMan.before_request
def require_login():
    if request.endpoint not in ('login', 'logout', 'static') and 'user' not in session:
        return redirect(url_for('login'))


@CRIMan.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if (request.form.get('username') == APP_USERNAME and
                request.form.get('password') == APP_PASSWORD):
            session['user'] = APP_USERNAME
            return redirect(url_for('home'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@CRIMan.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


_TS_FORMATS = (
    '%Y-%m-%d %H:%M:%S.%f',  # SQLite with microseconds
    '%Y-%m-%d %H:%M:%S',     # SQLite default CURRENT_TIMESTAMP
    '%Y-%m-%dT%H:%M:%S',     # ISO-8601 with seconds
    '%Y-%m-%dT%H:%M',        # datetime-local input (no seconds)
    '%Y-%m-%d %H:%M',        # space-separated, no seconds
    '%Y-%m-%d',              # date only
)

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


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA timeout=5")
    return conn


def next_cert_number(conn) -> str:
    row = conn.execute(
        "SELECT MAX(CAST(srv_cert AS INTEGER)) FROM service WHERE srv_cert GLOB '[0-9][0-9][0-9][0-9]'"
    ).fetchone()
    max_val = row[0] if row and row[0] is not None else 0
    return f"{max_val + 1:04d}"


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@CRIMan.route('/')
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


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

@CRIMan.route('/Locations')
def locations():
    conn = get_db_connection()
    locs = conn.execute("SELECT * FROM location").fetchall()
    locscount = conn.execute("SELECT COUNT(*) FROM location").fetchone()[0]
    if locscount == 0:
        conn.executescript(f"""
            INSERT INTO location (loc_id, loc_name, loc_description) VALUES ( '{uuid.uuid4()}', 'Machining', 'Machining');
        """)
    conn.close()
    return render_template('Locations.html', locations=locs)


@CRIMan.route('/Locations/add', methods=['POST'])
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
    return redirect(url_for('locations'))


@CRIMan.route('/Locations/edit', methods=['POST'])
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
    return redirect(url_for('locations'))


@CRIMan.route('/Locations/delete', methods=['POST'])
def locations_delete():
    loc_id = request.form['loc_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM location WHERE loc_id = ?", (loc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('locations'))


# ---------------------------------------------------------------------------
# Manufacturers & Models
# ---------------------------------------------------------------------------

@CRIMan.route('/Manufacturers')
def manufacturers():
    conn = get_db_connection()
    mfrs = conn.execute("SELECT * FROM Manufacturer").fetchall()
    conn.close()
    return render_template('Manufacturers.html', manufacturers=mfrs)


@CRIMan.route('/Manufacturers/add', methods=['POST'])
def mfr_add():
    mfr_id = str(uuid.uuid4())
    mfr_name = request.form['mfr_name']
    mfr_descr = request.form['mfr_descr']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO Manufacturer (mfr_id, mfr_name, mfr_descr) VALUES (?, ?, ?)",
        (mfr_id, mfr_name, mfr_descr)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers'))


@CRIMan.route('/Manufacturers/edit', methods=['POST'])
def mfr_edit():
    mfr_id = request.form['mfr_id']
    mfr_name = request.form['mfr_name']
    mfr_descr = request.form['mfr_descr']
    conn = get_db_connection()
    conn.execute(
        "UPDATE Manufacturer SET mfr_name = ?, mfr_descr = ? WHERE mfr_id = ?",
        (mfr_name, mfr_descr, mfr_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers'))


@CRIMan.route('/Manufacturers/delete', methods=['POST'])
def mfr_delete():
    mfr_id = request.form['mfr_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM Manufacturer WHERE mfr_id = ?", (mfr_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manufacturers'))


@CRIMan.route('/Models')
def models():
    conn = get_db_connection()
    mfrs = conn.execute("SELECT * FROM Manufacturer").fetchall()
    mds = conn.execute("""
        SELECT m.md_id, m.md_name, m.md_size, m.md_endsize,
               m.md_mfr_id, mfr.mfr_name, m.md_description
        FROM models m
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
    """).fetchall()
    conn.close()
    return render_template('Models.html', manufacturers=mfrs, models=mds)


@CRIMan.route('/Models/add', methods=['POST'])
def md_add():
    md_id = str(uuid.uuid4())
    md_name = request.form['md_name']
    md_size = request.form['md_size']
    md_endsize = request.form['md_endsize']
    md_mfr_id = request.form['md_mfr_id']
    md_description = request.form['md_description']
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO models (md_id, md_name, md_size, md_endsize, md_mfr_id, md_description) VALUES (?, ?, ?, ?, ?, ?)",
        (md_id, md_name, md_size, md_endsize, md_mfr_id, md_description)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('models'))


@CRIMan.route('/Models/edit', methods=['POST'])
def md_edit():
    md_id = request.form['md_id']
    md_name = request.form['md_name']
    md_size = request.form['md_size']
    md_endsize = request.form['md_endsize']
    md_mfr_id = request.form['md_mfr_id']
    md_description = request.form['md_description']
    conn = get_db_connection()
    conn.execute(
        "UPDATE models SET md_name = ?, md_size = ?, md_endsize = ?, md_mfr_id = ?, md_description = ? WHERE md_id = ?",
        (md_name, md_size, md_endsize, md_mfr_id, md_description, md_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('models'))


@CRIMan.route('/Models/delete', methods=['POST'])
def md_delete():
    md_id = request.form['md_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM models WHERE md_id = ?", (md_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('models'))


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

@CRIMan.route('/Units')
def units():
    return redirect(url_for('service'))

@CRIMan.route('/Units_legacy')
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


@CRIMan.route('/Units/add', methods=['POST'])
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
    return redirect(url_for('units'))


@CRIMan.route('/Units/edit', methods=['POST'])
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
    return redirect(url_for('units'))


@CRIMan.route('/Units/delete', methods=['POST'])
def units_delete():
    uni_id = request.form['uni_id']
    conn = get_db_connection()
    conn.execute(
        "UPDATE unit SET uni_deleted = 1, unit_delete_ts = CURRENT_TIMESTAMP WHERE uni_id = ?",
        (uni_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('units'))


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@CRIMan.route('/Users')
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


@CRIMan.route('/Users/add', methods=['POST'])
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
    return redirect(url_for('users'))


@CRIMan.route('/Users/edit', methods=['POST'])
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
    return redirect(url_for('users'))


@CRIMan.route('/Users/delete', methods=['POST'])
def users_delete():
    user_id = request.form['user_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('users'))


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

@CRIMan.route('/Help')
def help_page():
    return render_template('Help.html')


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@CRIMan.route('/Export')
def export():
    return render_template('Export.html')

#downloadOld
@CRIMan.route('/Export/downloadOld')
def export_downloadOld():
    conn = get_db_connection()
    sheets = {
        'Service': conn.execute("""
            SELECT mfr.mfr_name AS manufacturer, m.md_name AS model,
                   l.loc_name AS location, s.srv_asset_tag AS gauge_SN,
                   s.srv_description, us.user_name AS user,
                   s.srv_calibration_date, s.srv_cert,
                   s.srv_last_date, s.srv_next_date, s.srv_post_condition
            FROM service s
            LEFT JOIN models m ON s.srv_md_id = m.md_id
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
            LEFT JOIN location l ON s.srv_loc_id = l.loc_id
            LEFT JOIN users us ON s.srv_user_id = us.user_id
            WHERE s.srv_post_condition = 'Bad'
            ORDER BY s.srv_next_date ASC
        """).fetchall(),
    }
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='A99A6F')
    header_align = Alignment(horizontal='center', vertical='center')

    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)

        if not rows:
            ws.append(['No data'])
            continue

        headers = list(rows[0].keys())
        ws.append(headers)

        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for row in rows:
            ws.append(list(row))

        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                len(str(ws.cell(row=r, column=col_idx).value or ''))
                for r in range(1, ws.max_row + 1)
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"CRIMan_ExportDamagedUnits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

#downloadService
@CRIMan.route('/Export/downloadService')
def export_downloadService():
    conn = get_db_connection()
    sheets = {
        'Service': conn.execute("""
            SELECT mfr.mfr_name AS manufacturer, m.md_name AS model,
                   l.loc_name AS location, s.srv_asset_tag AS gauge_SN,
                   s.srv_description, us.user_name AS user,
                   s.srv_calibration_date, s.srv_cert,
                   s.srv_last_date, s.srv_next_date, s.srv_post_condition
            FROM service s
            LEFT JOIN models m ON s.srv_md_id = m.md_id
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
            LEFT JOIN location l ON s.srv_loc_id = l.loc_id
            LEFT JOIN users us ON s.srv_user_id = us.user_id
            WHERE s.srv_post_condition != 'Bad'
            ORDER BY s.srv_next_date ASC
        """).fetchall(),
    }
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='A99A6F')
    header_align = Alignment(horizontal='center', vertical='center')

    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)

        if not rows:
            ws.append(['No data'])
            continue

        headers = list(rows[0].keys())
        ws.append(headers)

        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for row in rows:
            ws.append(list(row))

        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                len(str(ws.cell(row=r, column=col_idx).value or ''))
                for r in range(1, ws.max_row + 1)
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"CRIMan_ExportService_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@CRIMan.route('/Export/download')
def export_download():
    conn = get_db_connection()

    sheets = {
        'Models': conn.execute("""
            SELECT m.md_name, m.md_size, m.md_endsize,
                   mfr.mfr_name AS manufacturer, m.md_description
            FROM models m
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
        """).fetchall(),
        'Service': conn.execute("""
            SELECT mfr.mfr_name AS manufacturer, m.md_name AS model,
                   l.loc_name AS location, s.srv_asset_tag AS gauge_SN,
                   s.srv_description, us.user_name AS user,
                   s.srv_calibration_date, s.srv_cert,
                   s.srv_last_date, s.srv_next_date, s.srv_post_condition
            FROM service s
            LEFT JOIN models m ON s.srv_md_id = m.md_id
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
            LEFT JOIN location l ON s.srv_loc_id = l.loc_id
            LEFT JOIN users us ON s.srv_user_id = us.user_id
            WHERE s.srv_post_condition != 'Bad'
            ORDER BY s.srv_next_date ASC
        """).fetchall(),
    }
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='A99A6F')
    header_align = Alignment(horizontal='center', vertical='center')

    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)

        if not rows:
            ws.append(['No data'])
            continue

        headers = list(rows[0].keys())
        ws.append(headers)

        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for row in rows:
            ws.append(list(row))

        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                len(str(ws.cell(row=r, column=col_idx).value or ''))
                for r in range(1, ws.max_row + 1)
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"CRIMan_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@CRIMan.route('/Export/downloadBackup')
def export_downloadBackup():
    conn = get_db_connection()

    sheets = {
        'Models': conn.execute("""
            SELECT * FROM models 
        """).fetchall(),
        'Service': conn.execute("""
            SELECT * FROM service
        """).fetchall(),
        'Manufacturers': conn.execute("""
            SELECT * FROM Manufacturer
        """).fetchall(),
        'Locations': conn.execute("""
            SELECT * FROM location
        """).fetchall(),
        'Users': conn.execute("""
            SELECT * FROM users
        """).fetchall(),
        'Locations': conn.execute("""
            SELECT * FROM location
        """).fetchall(),
    }
    conn.close()

    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='A99A6F')
    header_align = Alignment(horizontal='center', vertical='center')

    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)

        if not rows:
            ws.append(['No data'])
            continue

        headers = list(rows[0].keys())
        ws.append(headers)

        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        for row in rows:
            ws.append(list(row))

        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                len(str(ws.cell(row=r, column=col_idx).value or ''))
                for r in range(1, ws.max_row + 1)
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"CRIMan_Export_Backup{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

IMPORT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CRIMan_Import.xlsx')

_IMPORT_SHEETS = {
    'Manufacturers': {
        'table': 'Manufacturer',
        'columns': ['mfr_id', 'mfr_name', 'mfr_descr'],
    },
    'Models': {
        'table': 'models',
        'columns': ['md_id', 'md_name', 'md_size', 'md_endsize', 'md_mfr_id', 'md_description'],
    },
    'Locations': {
        'table': 'location',
        'columns': ['loc_id', 'loc_name', 'loc_description'],
    },
    'Users': {
        'table': 'users',
        'columns': ['user_id', 'user_name', 'user_loc_id'],
    },
    'Service': {
        'table': 'service',
        'columns': ['srv_id', 'srv_description', 'srv_md_id', 'srv_loc_id',
                    'srv_asset_tag', 'srv_user_id', 'srv_calibration_date',
                    'srv_cert', 'srv_last_date', 'srv_next_date', 'srv_post_condition'],
    },
}


@CRIMan.route('/Import')
def import_page():
    return render_template('Import.html')


@CRIMan.route('/Import/template')
def import_template():
    return send_file(IMPORT_TEMPLATE_PATH, as_attachment=True,
                     download_name='CRIMan_Import.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@CRIMan.route('/Import/upload', methods=['POST'])
def import_upload():
    if 'file' not in request.files or not request.files['file'].filename:
        return render_template('Import.html', error='No file selected.')

    file = request.files['file']
    if not file.filename.lower().endswith('.xlsx'):
        return render_template('Import.html', error='Please upload an .xlsx file.')

    try:
        wb = load_workbook(file, data_only=True)
    except Exception as e:
        return render_template('Import.html', error=f'Could not read file: {e}')

    conn = get_db_connection()
    counts = {}

    for sheet_name, cfg in _IMPORT_SHEETS.items():
        if sheet_name not in wb.sheetnames:
            counts[sheet_name] = 0
            continue
        ws = wb[sheet_name]
        columns = cfg['columns']
        table = cfg['table']

        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        col_indices = {col: headers.index(col) for col in columns if col in headers}

        n = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(v is not None for v in row):
                continue
            values = [row[col_indices[col]] if col in col_indices else None for col in columns]
            if values[0] is None:
                continue
            placeholders = ', '.join('?' for _ in columns)
            col_list = ', '.join(columns)
            conn.execute(
                f'INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})',
                values
            )
            n += 1
        counts[sheet_name] = n

    conn.commit()
    conn.close()
    return render_template('Import.html', counts=counts)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

@CRIMan.route('/Service')
def service():
    conn = get_db_connection()
    srv_rows = conn.execute("""
        SELECT s.srv_id, s.srv_description,
               s.srv_md_id, m.md_name, mfr.mfr_name,
               s.srv_loc_id, l.loc_name,
               s.srv_asset_tag,
               s.srv_user_id, us.user_name,
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
    return render_template('Service.html', services=srv_rows, models=model_rows, locations=loc_rows, users=user_rows, next_cert=next_cert)


@CRIMan.route('/Service/add', methods=['POST'])
def service_add():
    srv_id = str(uuid.uuid4())
    # srv_type = request.form['srv_type']
    srv_description = request.form['srv_description']
    srv_md_id = request.form['srv_md_id']
    srv_loc_id = request.form.get('srv_loc_id') or None
    srv_asset_tag = request.form.get('srv_asset_tag', '')
    srv_user_id = request.form['srv_user_id']
    srv_calibration_date = request.form.get('srv_calibration_date') or None
    srv_cert = request.form.get('srv_cert', '')
    srv_last_date = request.form.get('srv_last_date') or None
    srv_next_date = request.form.get('srv_next_date') or None
    srv_post_condition = request.form['srv_post_condition']
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO service
           (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
            srv_user_id, srv_calibration_date, srv_cert, srv_last_date, srv_next_date, srv_post_condition)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
         srv_user_id, srv_calibration_date, srv_cert, srv_last_date, srv_next_date, srv_post_condition)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('service'))


@CRIMan.route('/Service/edit', methods=['POST'])
def service_edit():
    srv_id = request.form['srv_id']
    # srv_type = request.form['srv_type']
    srv_description = request.form['srv_description']
    srv_md_id = request.form['srv_md_id']
    srv_loc_id = request.form.get('srv_loc_id') or None
    srv_asset_tag = request.form.get('srv_asset_tag', '')
    srv_user_id = request.form['srv_user_id']
    srv_calibration_date = request.form.get('srv_calibration_date') or None
    srv_cert = request.form.get('srv_cert', '')
    srv_last_date = request.form.get('srv_last_date') or None
    srv_next_date = request.form.get('srv_next_date') or None
    srv_post_condition = request.form['srv_post_condition']
    conn = get_db_connection()
    conn.execute(
        """UPDATE service SET
           srv_description = ?, srv_md_id = ?, srv_loc_id = ?, srv_asset_tag = ?,
           srv_user_id = ?, srv_calibration_date = ?, srv_cert = ?,
           srv_last_date = ?, srv_next_date = ?, srv_post_condition = ?
           WHERE srv_id = ?""",
        (srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
         srv_user_id, srv_calibration_date, srv_cert,
         srv_last_date, srv_next_date, srv_post_condition, srv_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('service'))


@CRIMan.route('/Service/delete', methods=['POST'])
def service_delete():
    srv_id = request.form['srv_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM service WHERE srv_id = ?", (srv_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('service'))


# ---------------------------------------------------------------------------
# Add Tool Wizard
# ---------------------------------------------------------------------------

@CRIMan.route('/AddTool')
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


@CRIMan.route('/AddTool/submit', methods=['POST'])
def add_tool_submit():
    conn = get_db_connection()

    # Manufacturer
    mfr_mode = request.form.get('mfr_mode', 'existing')
    if mfr_mode == 'new':
        mfr_id = str(uuid.uuid4())
        mfr_name = request.form['new_mfr_name']
        conn.execute(
            "INSERT INTO Manufacturer (mfr_id, mfr_name, mfr_descr) VALUES (?, ?, ?)",
            (mfr_id, mfr_name, request.form.get('new_mfr_descr', ''))
        )
    else:
        mfr_id = request.form['existing_mfr_id']
        row = conn.execute("SELECT mfr_name FROM Manufacturer WHERE mfr_id = ?", (mfr_id,)).fetchone()
        mfr_name = row['mfr_name'] if row else ''

    # Model
    md_mode = request.form.get('md_mode', 'existing')
    if md_mode == 'new':
        md_id = str(uuid.uuid4())
        md_name = request.form['new_md_name']
        conn.execute(
            "INSERT INTO models (md_id, md_name, md_size, md_endsize, md_mfr_id, md_description) VALUES (?, ?, ?, ?, ?, ?)",
            (md_id, md_name, request.form.get('new_md_size', ''),
             request.form.get('new_md_endsize', ''), mfr_id, request.form.get('new_md_description', ''))
        )
    else:
        md_id = request.form['existing_md_id']
        row = conn.execute("SELECT md_name FROM models WHERE md_id = ?", (md_id,)).fetchone()
        md_name = row['md_name'] if row else ''

    # Service record — references model directly, no unit intermediary
    conn.execute(
        """INSERT INTO service
           (srv_id, srv_description, srv_md_id, srv_loc_id, srv_asset_tag,
            srv_user_id, srv_calibration_date, srv_cert, srv_last_date, srv_next_date, srv_post_condition)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), request.form.get('srv_description', ''),
         md_id, request.form.get('uni_loc_id') or None, request.form.get('uni_asset_tag', ''),
         request.form['srv_user_id'],
         request.form.get('srv_calibration_date') or None,
         request.form.get('srv_cert', ''),
         request.form.get('srv_last_date') or None,
         request.form.get('srv_next_date') or None,
         request.form.get('srv_post_condition', 'New'))
    )

    conn.commit()
    conn.close()
    return redirect(url_for('service'))


# ---------------------------------------------------------------------------
# Add Scheduler
# ---------------------------------------------------------------------------
@CRIMan.route('/Scheduler')
def scheduler():
    conn = get_db_connection()
    sched_rows = conn.execute("""
        SELECT sch.sched_id, sch.sched_name, sch.sched_description, sch.sched_email,
               sch.sched_cron, sch.sched_last_run, sch.sched_next_run
        FROM scheduler sch
        ORDER BY sch.sched_name ASC
    """).fetchall()
    users = conn.execute("SELECT user_id, user_name FROM users ORDER BY user_name").fetchall()
    conn.close()
    return render_template('Scheduler.html', schedulers=sched_rows, users=users)

@CRIMan.route('/Scheduler/add', methods=['POST'])
def scheduler_add():
    sched_id = str(uuid.uuid4())
    sched_name = request.form['sched_name']
    sched_description = request.form['sched_description']
    sched_email = request.form['sched_email']
    sched_cron = request.form['sched_cron']
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO scheduler
           (sched_id, sched_name, sched_description, sched_email, sched_cron)
           VALUES (?, ?, ?, ?, ?)""",
        (sched_id, sched_name, sched_description, sched_email, sched_cron)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('scheduler'))


@CRIMan.route('/Scheduler/delete', methods=['POST'])
def scheduler_delete():
    sched_id = request.form['sched_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM scheduler WHERE sched_id = ?", (sched_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('scheduler'))

@CRIMan.route('/Scheduler/run')
def scheduler_run():
    conn = get_db_connection()

    schedules = conn.execute(
        "SELECT sched_id, sched_name, sched_email FROM scheduler ORDER BY sched_name"
    ).fetchall()

    sheets = {
        'Users': conn.execute("SELECT * FROM users").fetchall(),
        'Service': conn.execute("""
            SELECT s.srv_id, mfr.mfr_name AS manufacturer, m.md_name AS model,
                   l.loc_name AS location, s.srv_asset_tag AS gauge_SN,
                   s.srv_description, us.user_name AS user,
                   s.srv_calibration_date, s.srv_cert,
                   s.srv_last_date, s.srv_next_date, s.srv_post_condition
            FROM service s
            LEFT JOIN models m ON s.srv_md_id = m.md_id
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
            LEFT JOIN location l ON s.srv_loc_id = l.loc_id
            LEFT JOIN users us ON s.srv_user_id = us.user_id
            WHERE s.srv_post_condition != 'Bad'
            ORDER BY s.srv_next_date ASC
        """).fetchall(),
    }

    # Build Excel workbook
    wb = Workbook()
    wb.remove(wb.active)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='A99A6F')
    header_align = Alignment(horizontal='center', vertical='center')

    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)
        if not rows:
            ws.append(['No data'])
            continue
        headers = list(rows[0].keys())
        ws.append(headers)
        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
        for row in rows:
            ws.append(list(row))
        for col_idx in range(1, len(headers) + 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(
                len(str(ws.cell(row=r, column=col_idx).value or ''))
                for r in range(1, ws.max_row + 1)
            )
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

    buf = io.BytesIO()
    wb.save(buf)
    attachment_bytes = buf.getvalue()
    filename = f"CRIMan_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    body = (
        f"CRI Scheduled Service Report\n"
        f"Generated: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
        "See the attached Excel file for Units, Users, and Service records."
    )

    now = datetime.now()
    for sched in schedules:
        send_message(
            recipient=sched['sched_email'],
            subject=sched['sched_name'],
            body=body,
            isoutlook=True,
            attachment_data=attachment_bytes,
            attachment_filename=filename,
        )
        conn.execute(
            "UPDATE scheduler SET sched_last_run = ?, sched_next_run = ? WHERE sched_id = ?",
            (now, now, sched['sched_id'])
        )

    conn.commit()
    conn.close()
    return redirect(url_for('scheduler'))


if __name__ == '__main__':
    CRIMan.run(debug=True)

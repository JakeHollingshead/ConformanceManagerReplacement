import io
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from db import get_db_connection
from smtptosms import send_message

scheduler_bp = Blueprint('scheduler', __name__)


@scheduler_bp.route('/Scheduler')
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


@scheduler_bp.route('/Scheduler/add', methods=['POST'])
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
    return redirect(url_for('scheduler.scheduler'))


@scheduler_bp.route('/Scheduler/delete', methods=['POST'])
def scheduler_delete():
    sched_id = request.form['sched_id']
    conn = get_db_connection()
    conn.execute("DELETE FROM scheduler WHERE sched_id = ?", (sched_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('scheduler.scheduler'))


@scheduler_bp.route('/Scheduler/run')
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
        f"Conformance Manager Scheduled Service Report\n"
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
    return redirect(url_for('scheduler.scheduler'))

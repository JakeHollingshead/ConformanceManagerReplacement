from flask import Blueprint, render_template, request, redirect, url_for
from db import get_db_connection

datanormalization_bp = Blueprint('datanormalization', __name__)


# ---------------------------------------------------------------------------
# Manufacturer helpers
# ---------------------------------------------------------------------------

def _find_duplicate_manufacturers(conn):
    """Return groups of manufacturers sharing the same name (case-insensitive)."""
    groups = conn.execute("""
        SELECT LOWER(TRIM(mfr_name)) AS norm_name
        FROM Manufacturer
        GROUP BY LOWER(TRIM(mfr_name))
        HAVING COUNT(*) > 1
        ORDER BY norm_name
    """).fetchall()

    duplicates = []
    for g in groups:
        members = conn.execute("""
            SELECT mfr_id, mfr_name,
                   (SELECT COUNT(*) FROM models WHERE md_mfr_id = Manufacturer.mfr_id) AS model_count
            FROM Manufacturer
            WHERE LOWER(TRIM(mfr_name)) = ?
            ORDER BY model_count DESC, mfr_id ASC
        """, (g['norm_name'],)).fetchall()
        duplicates.append(members)
    return duplicates


def normalize_manufacturers(conn):
    """Merge duplicate manufacturers, remapping md_mfr_id to the canonical record."""
    duplicates = _find_duplicate_manufacturers(conn)
    merged = []

    for members in duplicates:
        canonical = members[0]
        to_remove = members[1:]

        for dup in to_remove:
            conn.execute(
                "UPDATE models SET md_mfr_id = ? WHERE md_mfr_id = ?",
                (canonical['mfr_id'], dup['mfr_id'])
            )
            conn.execute("DELETE FROM Manufacturer WHERE mfr_id = ?", (dup['mfr_id'],))

        merged.append({
            'kept': canonical['mfr_name'],
            'removed': [d['mfr_name'] for d in to_remove],
        })

    conn.commit()
    return merged


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def _find_duplicate_models(conn):
    """Return groups of models sharing the same md_name, md_size, md_endsize, md_mfr_id."""
    groups = conn.execute("""
        SELECT md_name, md_size, md_endsize, md_mfr_id
        FROM models
        GROUP BY md_name, md_size, md_endsize, md_mfr_id
        HAVING COUNT(*) > 1
        ORDER BY md_name, md_size, md_endsize
    """).fetchall()

    duplicates = []
    for g in groups:
        members = conn.execute("""
            SELECT m.md_id, m.md_name, m.md_size, m.md_endsize, m.md_mfr_id, mfr.mfr_name,
                   (SELECT COUNT(*) FROM service WHERE srv_md_id = m.md_id) AS service_count
            FROM models m
            LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
            WHERE m.md_name = ? AND m.md_size = ? AND m.md_endsize = ? AND m.md_mfr_id = ?
            ORDER BY service_count DESC, m.md_id ASC
        """, (g['md_name'], g['md_size'], g['md_endsize'], g['md_mfr_id'])).fetchall()
        duplicates.append(members)
    return duplicates


def normalize_models(conn):
    """Merge duplicate models, remapping srv_md_id in service to the canonical record."""
    duplicates = _find_duplicate_models(conn)
    merged = []

    for members in duplicates:
        canonical = members[0]
        to_remove = members[1:]

        for dup in to_remove:
            conn.execute(
                "UPDATE service SET srv_md_id = ? WHERE srv_md_id = ?",
                (canonical['md_id'], dup['md_id'])
            )
            conn.execute("DELETE FROM models WHERE md_id = ?", (dup['md_id'],))

        merged.append({
            'kept': canonical['md_name'],
            'removed': len(to_remove),
        })

    conn.commit()
    return merged


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@datanormalization_bp.route('/DataNormalization')
def datanormalization():
    conn = get_db_connection()

    manufacturers = conn.execute(
        "SELECT mfr_id, mfr_name FROM Manufacturer ORDER BY mfr_name"
    ).fetchall()

    models = conn.execute("""
        SELECT m.md_id, m.md_name, m.md_size, m.md_endsize, mfr.mfr_name
        FROM models m
        LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
        ORDER BY mfr.mfr_name, m.md_name
    """).fetchall()

    service_count = conn.execute("SELECT COUNT(*) FROM service").fetchone()[0]

    mfr_duplicates = _find_duplicate_manufacturers(conn)
    model_duplicates = _find_duplicate_models(conn)
    conn.close()

    return render_template('DataNormalization.html',
                           manufacturers=manufacturers,
                           models=models,
                           service_count=service_count,
                           mfr_duplicates=mfr_duplicates,
                           model_duplicates=model_duplicates,
                           normalized=request.args.get('normalized'),
                           normalized_models=request.args.get('normalized_models'))


@datanormalization_bp.route('/DataNormalization/normalize', methods=['POST'])
def datanormalization_normalize():
    conn = get_db_connection()
    results = normalize_manufacturers(conn)
    conn.close()
    return redirect(url_for('datanormalization.datanormalization', normalized=len(results)))


@datanormalization_bp.route('/DataNormalization/normalize-models', methods=['POST'])
def datanormalization_normalize_models():
    conn = get_db_connection()
    if _find_duplicate_manufacturers(conn):
        conn.close()
        return redirect(url_for('datanormalization.datanormalization'))
    results = normalize_models(conn)
    conn.close()
    return redirect(url_for('datanormalization.datanormalization', normalized_models=len(results)))

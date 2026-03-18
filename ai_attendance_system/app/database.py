import os
import sqlite3
import pickle
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'attendance.db')
FACES_DIR = os.path.join(BASE_DIR, '..', 'known_faces')


def init_db():
    os.makedirs(FACES_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT NOT NULL UNIQUE,
            email TEXT,
            encoding BLOB,
            photo_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migrate existing DBs that don't have the email column yet
    try:
        c.execute('ALTER TABLE students ADD COLUMN email TEXT')
    except Exception:
        pass  # Column already exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT "Present",
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')
    # Migrate: add pin column if not present (default = roll_no)
    try:
        c.execute('ALTER TABLE students ADD COLUMN pin TEXT')
        # Set default PIN = roll_no for existing students
        c.execute('UPDATE students SET pin = roll_no WHERE pin IS NULL')
    except Exception:
        pass  # Column already exists
    conn.commit()
    conn.close()


def add_student(name, roll_no, encoding, photo_path, email=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    encoding_blob = pickle.dumps(encoding)
    try:
        c.execute(
            'INSERT INTO students (name, roll_no, email, encoding, photo_path, pin) VALUES (?, ?, ?, ?, ?, ?)',
            (name, roll_no, email or '', encoding_blob, photo_path, roll_no)  # default PIN = roll_no
        )
        conn.commit()
        student_id = c.lastrowid
        return {'success': True, 'id': student_id}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Roll number already exists'}
    finally:
        conn.close()


def get_all_students():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, roll_no, email, encoding, photo_path, created_at FROM students')
    rows = c.fetchall()
    conn.close()
    students = []
    for row in rows:
        enc = pickle.loads(row[4]) if row[4] else None
        students.append({
            'id': row[0],
            'name': row[1],
            'roll_no': row[2],
            'email': row[3] or '',
            'encoding': enc,
            'photo_path': row[5],
            'created_at': row[6],
        })
    return students


def get_student_by_id(student_id):
    """Returns a single student dict by ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, roll_no, email, photo_path, created_at FROM students WHERE id=?', (student_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'name': row[1], 'roll_no': row[2],
            'email': row[3] or '', 'photo_path': row[4], 'created_at': row[5]}


def authenticate_student(roll_no, pin):
    """Validate student credentials. Returns student dict on success, None on failure."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, roll_no, email FROM students WHERE roll_no=? AND pin=?',
              (roll_no.strip(), pin.strip()))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {'id': row[0], 'name': row[1], 'roll_no': row[2], 'email': row[3] or ''}


def update_student_pin(student_id, new_pin):
    """Update a student's login PIN."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE students SET pin=? WHERE id=?', (new_pin, student_id))
    conn.commit()
    conn.close()
    return {'success': True}


def get_all_students_with_stats():
    """Returns all students with days_present, percentage, and last_seen."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT date) FROM attendance')
    total_days = c.fetchone()[0] or 1
    c.execute('''
        SELECT s.id, s.name, s.roll_no, s.email, s.photo_path, s.created_at,
               COUNT(a.id) as days_present,
               MAX(a.date) as last_seen
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        ORDER BY s.name ASC
    ''')
    rows = c.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'name': row[1],
            'roll_no': row[2],
            'email': row[3] or '',
            'photo_path': row[4],
            'created_at': row[5],
            'days_present': row[6],
            'last_seen': row[7] or 'Never',
            'percentage': round((row[6] / total_days) * 100, 1) if total_days else 0,
        }
        for row in rows
    ]


def update_student(student_id, name, roll_no, email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            'UPDATE students SET name=?, roll_no=?, email=? WHERE id=?',
            (name, roll_no, email or '', student_id)
        )
        conn.commit()
        return {'success': True}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Roll number already used by another student.'}
    finally:
        conn.close()


def add_manual_attendance(student_id, date_str, status='Present'):
    """Manually add an attendance record. Returns False if already exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM attendance WHERE student_id=? AND date=?', (student_id, date_str))
    if c.fetchone():
        conn.close()
        return False
    from datetime import datetime
    time_str = datetime.now().strftime('%H:%M:%S') if date_str == datetime.now().strftime('%Y-%m-%d') else '00:00:00'
    c.execute('INSERT INTO attendance (student_id, date, time, status) VALUES (?, ?, ?, ?)',
              (student_id, date_str, time_str, status))
    conn.commit()
    conn.close()
    return True


def remove_attendance(student_id, date_str):
    """Remove an attendance record for a student on a specific date."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM attendance WHERE student_id=? AND date=?', (student_id, date_str))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_student_attendance_history(student_id, limit=30):
    """Returns last N attendance records for a specific student."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT date, time, status FROM attendance
        WHERE student_id=?
        ORDER BY date DESC, time DESC
        LIMIT ?
    ''', (student_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{'date': r[0], 'time': r[1], 'status': r[2]} for r in rows]



def delete_student(student_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # First get the photo path to delete the image file
    c.execute('SELECT photo_path FROM students WHERE id = ?', (student_id,))
    row = c.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        try:
            os.remove(row[0])
        except Exception:
            pass
            
    # Delete student records from both tables
    c.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
    c.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    return {'success': True}


def mark_attendance(student_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    # Avoid duplicate marking for same day
    c.execute('SELECT id FROM attendance WHERE student_id=? AND date=?', (student_id, date_str))
    if c.fetchone():
        conn.close()
        return False  # Already marked
    c.execute(
        'INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)',
        (student_id, date_str, time_str)
    )
    conn.commit()
    conn.close()
    return True


def get_today_attendance():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT s.name, s.roll_no, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time DESC
    ''', (today,))
    rows = c.fetchall()
    conn.close()
    return [{'name': r[0], 'roll_no': r[1], 'time': r[2], 'status': r[3]} for r in rows]


def get_attendance_report(date_from=None, date_to=None, student_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = '''
        SELECT s.name, s.roll_no, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    '''
    params = []
    if date_from:
        query += ' AND a.date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND a.date <= ?'
        params.append(date_to)
    if student_id:
        query += ' AND a.student_id = ?'
        params.append(student_id)
    query += ' ORDER BY a.date DESC, a.time DESC'
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [{'name': r[0], 'roll_no': r[1], 'date': r[2], 'time': r[3], 'status': r[4]} for r in rows]


def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM students')
    total_students = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT student_id) FROM attendance WHERE date=?', (today,))
    present_today = c.fetchone()[0]
    # Last 7 days trend
    c.execute('''
        SELECT date, COUNT(DISTINCT student_id) as cnt
        FROM attendance
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    ''')
    trend = c.fetchall()
    conn.close()
    return {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': max(total_students - present_today, 0),
        'trend': [{'date': r[0], 'count': r[1]} for r in reversed(trend)]
    }


def get_student_attendance_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT s.id, s.name, s.roll_no,
               COUNT(a.id) as days_present,
               s.created_at
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
    ''')
    rows = c.fetchall()
    c.execute('SELECT COUNT(DISTINCT date) FROM attendance')
    total_days = c.fetchone()[0] or 1
    conn.close()
    return [
        {
            'id': r[0],
            'name': r[1],
            'roll_no': r[2],
            'days_present': r[3],
            'percentage': round((r[3] / total_days) * 100, 1) if total_days else 0,
        }
        for r in rows
    ]

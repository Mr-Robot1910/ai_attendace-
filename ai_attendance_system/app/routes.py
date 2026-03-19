import os
import base64
import threading
import cv2
import numpy as np
from functools import wraps
from flask import (
    Blueprint, render_template, request, jsonify, Response,
    session, redirect, url_for, flash
)
from . import database as db
from . import face_module as fm
from . import email_service as mailer

try:
    from config import ADMIN_PIN
except ImportError:
    ADMIN_PIN = '1234'

routes = Blueprint('routes', __name__)

# Global state for attendance session
session_state = {
    'active': False,
    'camera': None,
    'lock': threading.Lock(),
    'recognized_today': {},   # student_id -> {'name': ..., 'roll_no': ...}
    'known_encodings': [],
    'known_meta': [],          # list of {'id': ..., 'name': ..., 'roll_no': ...}
    'pending_matches': {},     # student_id -> consecutive frame match count
    'last_quality_msg': 'Waiting for session to start',
}

FACES_DIR = os.path.join(os.path.dirname(__file__), '..', 'known_faces')


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_required(f):
    """Admin-only access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            if session.get('student_id'):
                return redirect(url_for('routes.student_portal'))
            return redirect(url_for('routes.login_page'))
        return f(*args, **kwargs)
    return decorated


def student_login_required(f):
    """Student OR admin access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('student_id') and not session.get('logged_in'):
            return redirect(url_for('routes.login_page'))
        return f(*args, **kwargs)
    return decorated


@routes.route('/login', methods=['GET', 'POST'])
def login_page():
    # Already logged in — redirect to right place
    if session.get('logged_in'):
        return redirect(url_for('routes.index'))
    if session.get('student_id'):
        return redirect(url_for('routes.student_portal'))

    admin_error   = None
    student_error = None
    active_tab    = request.form.get('tab', 'admin')

    if request.method == 'POST':
        role = request.form.get('role', 'admin')

        if role == 'admin':
            pin = request.form.get('pin', '').strip()
            if pin == ADMIN_PIN:
                session['logged_in'] = True
                session.pop('student_id', None)
                return redirect(url_for('routes.index'))
            admin_error = 'Incorrect admin PIN.'
            active_tab  = 'admin'

        elif role == 'student':
            roll_no = request.form.get('roll_no', '').strip()
            pin     = request.form.get('student_pin', '').strip()
            student = db.authenticate_student(roll_no, pin)
            if student:
                session['student_id'] = student['id']
                session.pop('logged_in', None)
                return redirect(url_for('routes.student_portal'))
            student_error = 'Incorrect roll number or PIN.'
            active_tab    = 'student'

    return render_template('login.html',
                           admin_error=admin_error,
                           student_error=student_error,
                           active_tab=active_tab)


@routes.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.login_page'))


# ─── Pages ───────────────────────────────────────────────────────────────────

@routes.route('/')
@login_required
def index():
    stats = db.get_dashboard_stats()
    today_records = db.get_today_attendance()
    return render_template('dashboard.html', stats=stats, today_records=today_records)


@routes.route('/register')
@login_required
def register_page():
    return render_template('register.html')


@routes.route('/attendance')
@login_required
def attendance_page():
    return render_template('attendance.html')


@routes.route('/reports')
@login_required
def reports_page():
    students = [{'id': s['id'], 'name': s['name'], 'roll_no': s['roll_no']}
                for s in db.get_all_students()]
    return render_template('reports.html', students=students)


@routes.route('/students')
@login_required
def students_page():
    students = db.get_all_students_with_stats()
    return render_template('students.html', students=students)


# ─── Student Portal ───────────────────────────────────────────────────────────

@routes.route('/portal')
@student_login_required
def student_portal():
    if session.get('logged_in'):
        # Admin visiting /portal — just redirect to dashboard
        return redirect(url_for('routes.index'))
    student = db.get_student_by_id(session['student_id'])
    if not student:
        session.clear()
        return redirect(url_for('routes.login_page'))
    history    = db.get_student_attendance_history(student['id'], limit=60)
    all_stats  = db.get_all_students_with_stats()
    my_stats   = next((s for s in all_stats if s['id'] == student['id']), {})
    return render_template('portal.html', student=student, history=history, stats=my_stats)


@routes.route('/api/user/update', methods=['PATCH'])
@student_login_required
def api_user_update():
    if session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Admins use /api/students/<id> instead.'})
    student_id = session['student_id']
    data    = request.get_json()
    name    = data.get('name', '').strip()
    roll_no = data.get('roll_no', '').strip()
    email   = data.get('email', '').strip()
    new_pin = data.get('new_pin', '').strip()
    if not name or not roll_no:
        return jsonify({'success': False, 'error': 'Name and roll number are required.'})
    result = db.update_student(student_id, name, roll_no, email)
    if result.get('success') and new_pin:
        db.update_student_pin(student_id, new_pin)
    return jsonify(result)



# ─── API: Register student ────────────────────────────────────────────────────

@routes.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    name = data.get('name', '').strip()
    roll_no = data.get('roll_no', '').strip()
    email = data.get('email', '').strip()
    images = data.get('images', [])  # list of base64 data URLs

    if not name or not roll_no or not images:
        return jsonify({'success': False, 'error': 'Name, roll number and photos are required.'})

    valid_embeddings = []
    first_valid_frame = None

    for i, image_data in enumerate(images):
        try:
            header, encoded = image_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # Save first frame for debug if needed, but not necessary inside the loop in production
        except Exception as e:
            continue # skip invalid images

        # Extract embedding
        embedding, error = fm.get_embedding(frame)
        if not error and embedding is not None:
            valid_embeddings.append(embedding)
            if first_valid_frame is None:
                first_valid_frame = frame

    if not valid_embeddings:
        return jsonify({'success': False, 'error': 'No face detected in any of the captured frames. Please look directly at the camera.'})

    # Average the embeddings for a much more robust representation
    avg_embedding = np.mean(valid_embeddings, axis=0)

    # Prevent Duplicate Registration
    students = db.get_all_students()
    known_encodings = [s['encoding'] for s in students if s['encoding'] is not None]
    known_ids = [s['id'] for s in students if s['encoding'] is not None]
    
    if known_encodings:
        known_arr = np.array(known_encodings, dtype=np.float32)
        emb_norm = np.linalg.norm(avg_embedding)
        known_norms = np.linalg.norm(known_arr, axis=1)
        
        denom = known_norms * emb_norm
        denom[denom == 0] = 1e-10
        
        dot_products = np.dot(known_arr, avg_embedding)
        dists = 1 - (dot_products / denom)
        
        best_idx = int(np.argmin(dists))
        if dists[best_idx] <= fm.THRESHOLD:
            matched_student = next((s for s in students if s['id'] == known_ids[best_idx]), None)
            if matched_student:
                return jsonify({'success': False, 'error': f'This face is already registered as {matched_student["name"]} (Roll No: {matched_student["roll_no"]}).'})

    # Save the first valid photo as the profile picture
    os.makedirs(FACES_DIR, exist_ok=True)
    safe_roll = roll_no.replace('/', '_').replace('\\', '_')
    photo_path = os.path.join(FACES_DIR, f'{safe_roll}.jpg')
    cv2.imwrite(photo_path, first_valid_frame)

    result = db.add_student(name, roll_no, avg_embedding, photo_path, email=email)
    if result.get('success'):
        result['frames_used'] = len(valid_embeddings)
    return jsonify(result)

@routes.route('/api/students/<int:student_id>', methods=['DELETE'])
def api_delete_student(student_id):
    result = db.delete_student(student_id)
    return jsonify(result)


@routes.route('/api/students/<int:student_id>', methods=['PATCH'])
def api_update_student(student_id):
    data = request.get_json()
    name    = data.get('name', '').strip()
    roll_no = data.get('roll_no', '').strip()
    email   = data.get('email', '').strip()
    if not name or not roll_no:
        return jsonify({'success': False, 'error': 'Name and roll number are required.'})
    return jsonify(db.update_student(student_id, name, roll_no, email))


@routes.route('/api/students/<int:student_id>/history')
def api_student_history(student_id):
    history = db.get_student_attendance_history(student_id)
    return jsonify(history)


@routes.route('/api/attendance/manual', methods=['POST'])
def api_manual_attendance():
    data       = request.get_json()
    student_id = data.get('student_id')
    date_str   = data.get('date')
    action     = data.get('action', 'add')   # 'add' or 'remove'
    if not student_id or not date_str:
        return jsonify({'success': False, 'error': 'student_id and date are required.'})
    if action == 'remove':
        removed = db.remove_attendance(student_id, date_str)
        return jsonify({'success': True, 'removed': removed})
    added = db.add_manual_attendance(student_id, date_str)
    if not added:
        return jsonify({'success': False, 'error': 'Attendance already recorded for this date.'})
    return jsonify({'success': True})



# ─── API: Attendance session ──────────────────────────────────────────────────

@routes.route('/api/attendance/start', methods=['POST'])
def api_start_attendance():
    with session_state['lock']:
        if session_state['active']:
            return jsonify({'success': True, 'message': 'Session already active'})

        students = db.get_all_students()
        session_state['known_encodings'] = [
            s['encoding'] for s in students if s['encoding'] is not None
        ]
        session_state['known_meta'] = [
            {'id': s['id'], 'name': s['name'], 'roll_no': s['roll_no'], 'email': s.get('email', '')}
            for s in students if s['encoding'] is not None
        ]
        session_state['recognized_today'] = {}
        session_state['pending_matches'] = {}
        session_state['last_quality_msg'] = 'Session started — show your face to the camera'
        session_state['active'] = True

    return jsonify({'success': True, 'student_count': len(session_state['known_meta'])})


@routes.route('/api/attendance/stop', methods=['POST'])
def api_stop_attendance():
    with session_state['lock']:
        session_state['active'] = False

    # Send absent emails to everyone not marked present today
    recognized_ids = set(session_state['recognized_today'].keys())
    all_meta = session_state.get('known_meta', [])
    for meta in all_meta:
        if meta['id'] not in recognized_ids and meta.get('email'):
            mailer.send_absent_email(meta['email'], meta['name'], meta['roll_no'])

    return jsonify({'success': True, 'recognized': list(session_state['recognized_today'].values())})


@routes.route('/api/attendance/recognize_frame', methods=['POST'])
def api_recognize_frame():
    """Accept a base64 JPEG frame from the browser, run face recognition, return result."""
    if not session_state['active']:
        return jsonify({'active': False, 'quality': 'No active session. Please start a session first.'})

    data = request.get_json(silent=True) or {}
    image_data = data.get('image', '')
    if not image_data:
        return jsonify({'active': True, 'quality': 'No image received', 'newly_marked': []})

    try:
        _, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame     = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError('Could not decode image')
    except Exception:
        return jsonify({'active': True, 'quality': 'Invalid frame — retrying…', 'newly_marked': []})

    known_encs = session_state['known_encodings']
    known_meta = session_state['known_meta']
    known_ids  = [m['id'] for m in known_meta]

    _, matched_ids, quality_msg = fm.recognize_faces_in_frame(frame, known_encs, known_ids)
    session_state['last_quality_msg'] = quality_msg

    newly_marked = []
    FRAMES_REQUIRED = 2  # require 2 consistent matches to prevent false positives

    with session_state['lock']:
        for sid in matched_ids:
            if sid not in session_state['recognized_today']:
                session_state['pending_matches'][sid] = session_state['pending_matches'].get(sid, 0) + 1
                if session_state['pending_matches'][sid] >= FRAMES_REQUIRED:
                    meta = next((m for m in known_meta if m['id'] == sid), None)
                    if meta:
                        db.mark_attendance(sid)
                        record = {'id': sid, 'name': meta['name'], 'roll_no': meta['roll_no']}
                        session_state['recognized_today'][sid] = record
                        session_state['pending_matches'].pop(sid, None)
                        newly_marked.append(record)
                        if meta.get('email'):
                            mailer.send_present_email(meta['email'], meta['name'], meta['roll_no'])

        # Decay pending counts for IDs not seen this frame
        for sid in list(session_state['pending_matches'].keys()):
            if sid not in matched_ids:
                session_state['pending_matches'][sid] = max(0, session_state['pending_matches'][sid] - 1)

    return jsonify({
        'active':    True,
        'quality':   quality_msg,
        'matched':   len(matched_ids) > 0,
        'newly_marked': newly_marked,
        'recognized_count': len(session_state['recognized_today']),
        'recognized': list(session_state['recognized_today'].values()),
    })


@routes.route('/api/attendance/status')
def api_attendance_status():
    return jsonify({
        'active': session_state['active'],
        'recognized': list(session_state['recognized_today'].values())
    })


@routes.route('/api/attendance/quality')
def api_attendance_quality():
    return jsonify({'message': session_state.get('last_quality_msg', 'Waiting...')})


def _generate_frames():
    """Generator for MJPEG stream with face recognition overlay."""
    known_encs  = []
    known_ids   = []
    known_meta  = []
    annotated   = None

    try:
        while True:
            with session_state['lock']:
                active = session_state['active']
                cam    = session_state['camera']
            if not active or cam is None:
                break

            ret, frame = cam.read()
            if not ret:
                break

            # Run recognition every 5th frame for performance
            frame_skip_val = getattr(_generate_frames, '_skip', 0) + 1
            _generate_frames._skip = frame_skip_val

            if frame_skip_val % 5 == 0:
                known_encs = session_state['known_encodings']
                known_meta = session_state['known_meta']
                known_ids  = [m['id'] for m in known_meta]

                annotated, matched_ids, quality_msg = fm.recognize_faces_in_frame(frame, known_encs, known_ids)
                session_state['last_quality_msg'] = quality_msg

                FRAMES_REQUIRED = 2  # require 2 consistent matches
                for sid in matched_ids:
                    if sid not in session_state['recognized_today']:
                        session_state['pending_matches'][sid] = session_state['pending_matches'].get(sid, 0) + 1
                        if session_state['pending_matches'][sid] >= FRAMES_REQUIRED:
                            meta = next((m for m in known_meta if m['id'] == sid), None)
                            if meta:
                                db.mark_attendance(sid)
                                session_state['recognized_today'][sid] = {
                                    'id':      sid,
                                    'name':    meta['name'],
                                    'roll_no': meta['roll_no'],
                                }
                                session_state['pending_matches'].pop(sid, None)
                                if meta.get('email'):
                                    mailer.send_present_email(meta['email'], meta['name'], meta['roll_no'])

                # Decay pending counts for IDs not seen in this frame
                for sid in list(session_state['pending_matches'].keys()):
                    if sid not in matched_ids:
                        session_state['pending_matches'][sid] = max(0, session_state['pending_matches'][sid] - 1)
            else:
                annotated = frame.copy()

            if annotated is None:
                annotated = frame.copy()

            _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    finally:
        _generate_frames._skip = 0
        with session_state['lock']:
            session_state['active'] = False
            if session_state['camera']:
                session_state['camera'].release()
                session_state['camera'] = None



@routes.route('/api/attendance/feed')
def video_feed():
    if not session_state['active']:
        return jsonify({'error': 'No active session'}), 400
    return Response(_generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ─── API: Reports ─────────────────────────────────────────────────────────────

@routes.route('/api/reports')
def api_reports():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    student_id = request.args.get('student_id')
    records = db.get_attendance_report(date_from, date_to, student_id)
    summary = db.get_student_attendance_summary()
    return jsonify({'records': records, 'summary': summary})


@routes.route('/api/students')
def api_students():
    students = [{'id': s['id'], 'name': s['name'], 'roll_no': s['roll_no']}
                for s in db.get_all_students()]
    return jsonify(students)


# ─── API: Server-Sent Events (SSE) ────────────────────────────────────────────

@routes.route('/api/stream')
def api_stream():
    """Streams live dashboard stats and today's attendance records."""
    import time
    import json
    
    def event_stream():
        last_present = -1
        while True:
            try:
                stats = db.get_dashboard_stats()
                # Only push an update if the number of present students changes or on first connect
                if stats['present_today'] != last_present:
                    last_present = stats['present_today']
                    today_records = db.get_today_attendance()
                    data = {
                        'stats': stats,
                        'records': today_records,
                        'active_session': session_state['active']
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    # Keep-alive ping
                    yield ": ping\n\n"
                time.sleep(2)
            except Exception as e:
                # Client disconnected or error
                break
                
    return Response(event_stream(), mimetype="text/event-stream")

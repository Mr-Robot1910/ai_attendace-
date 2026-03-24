import sqlite3
import numpy as np

def cosine(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0: return 1.0
    return 1 - np.dot(a, b) / denom

db_path = "d:/first_antigravity/ai_attendance_system/attendance.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, name, roll_no, encoding FROM students")
rows = c.fetchall()

import pickle

students = []
for row in rows:
    if row[3]:
        emb = pickle.loads(row[3])
        students.append({'id': row[0], 'name': row[1], 'roll': row[2], 'emb': emb})

print(f"Loaded {len(students)} students with encodings.")

for i in range(len(students)):
    print(f"--- {students[i]['name']} ({students[i]['roll']}) [norm: {np.linalg.norm(students[i]['emb']):.4f}] ---")
    for j in range(i+1, len(students)):
        dist = cosine(students[i]['emb'], students[j]['emb'])
        print(f"  vs {students[j]['name']}: {dist:.4f}")

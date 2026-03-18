import numpy as np
import sqlite3
import pickle

db_path = "d:/first_antigravity/ai_attendance_system/attendance.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name, encoding FROM students")
rows = cursor.fetchall()

if not rows:
    print("No students found.")

for row in rows:
    name = row["name"]
    encoding_blob = row["encoding"]
    if encoding_blob:
        encoding = pickle.loads(encoding_blob)
        print(f"Student: {name}")
        print(f"Embedding shape: {encoding.shape}")
        print(f"Embedding norm (L2 length): {np.linalg.norm(encoding)}")
        
conn.close()

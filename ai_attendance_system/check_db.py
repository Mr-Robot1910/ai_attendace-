import sqlite3

db_path = "d:/first_antigravity/ai_attendance_system/attendance.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("SELECT id, name, roll_no FROM students")
rows = c.fetchall()
print("Students in DB:", rows)

# Do we have the actual error?

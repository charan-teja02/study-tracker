import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS badges(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
badge_name TEXT
)
""")

conn.commit()
conn.close()

print("Badges table created successfully")
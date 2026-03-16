import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create users table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
xp INTEGER DEFAULT 0,
level INTEGER DEFAULT 1
)
""")

# Create study sessions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
date TEXT,
minutes INTEGER
)
""")

# Create game sessions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS game_sessions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
date TEXT,
minutes INTEGER
)
""")

conn.commit()
conn.close()

print("Database upgraded successfully!")
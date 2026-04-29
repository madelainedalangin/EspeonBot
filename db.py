import sqlite3

db = sqlite3.connect("tracker.db")

db.execute("PRAGMA foreign_keys = ON")

db.execute("""
  CREATE TABLE IF NOT EXISTS tasks (
    name TEXT,
    remind_after_minutes INTEGER,
    channel_id INTEGER,
    remind_hour INTEGER,
    user_id INTEGER,
    PRIMARY KEY (name, user_id)
  )
""")

db.execute("""
  CREATE TABLE IF NOT EXISTS logs (
    task_name TEXT,
    user_id INTEGER,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
""")

db.execute("""
  CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    label TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP
  )
""")

db.execute("""
  CREATE TABLE IF NOT EXISTS skips (
    class_name TEXT,
    user_id INTEGER,
    skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
""")

db.execute("""
  CREATE TABLE IF NOT EXISTS roasts (
    message TEXT
  )
""")

db.commit()
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
    message TEXT,
    guild_id INTEGER
  )
""")

count = db.execute("SELECT COUNT(*) FROM roasts").fetchone()[0]
if count == 0:
  defaults = [
    "That's {count} skip(s) for {name}. You're building a habit. Careful...",
    "You stink.",
    "You said you wouldn't skip {name} again. You lied.",
    "Nobody's impressed by {count} skip(s) for {name}.",
    "Your ancestors are shaking their heads at you rn.",
    "That's {count}. But who's counting? Oh wait, I am.",
  ]
  for msg in defaults:
    db.execute("INSERT INTO roasts (message) VALUES (?)", (msg,))

db.commit()
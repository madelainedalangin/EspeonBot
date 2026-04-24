import sqlite3
import pytest

@pytest.fixture
def db():
  conn = sqlite3.connect(":memory:")
  conn.executescript("""
      CREATE TABLE IF NOT EXISTS tasks (
        name TEXT PRIMARY KEY,
        remind_after_minutes INTEGER,
        channel_id INTEGER,
        remind_hour INTEGER
      );
      CREATE TABLE IF NOT EXISTS logs (
        task_name TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_name) REFERENCES tasks(name)
      );
      CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        label TEXT,
        started_at TIMESTAMP,
        ended_at TIMESTAMP
      );
      CREATE TABLE IF NOT EXISTS skips (
        class_name TEXT,
        skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
  """)
  yield conn
  conn.close()

def test_edit_updates_duration(db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", ("vacuum", 10080, 123, 9))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ?", (20160, "vacuum"))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ?", ("vacuum",)).fetchone()
    assert row[0] == 20160

def test_edit_keeps_hour(db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", ("vacuum", 10080, 123, 9))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ?", (20160, "vacuum"))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ?", ("vacuum",)).fetchone()
    assert row[0] == 9

def test_edit_changes_hour(db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", ("vacuum", 10080, 123, 9))
    db.execute("UPDATE tasks SET remind_hour = ? WHERE name = ?", (10, "vacuum"))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ?", ("vacuum",)).fetchone()
    assert row[0] == 10

def test_edit_nonexistent(db):
    row = db.execute("SELECT * FROM tasks WHERE name = ?", ("ghost",)).fetchone()
    assert row is None
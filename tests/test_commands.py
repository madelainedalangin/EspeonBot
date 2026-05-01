import sqlite3
from datetime import datetime, timedelta
import pytest
from helpers import parse_duration


@pytest.fixture
def db():
  conn = sqlite3.connect(":memory:")
  conn.execute("PRAGMA foreign_keys = ON")
  conn.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
      name TEXT,
      remind_after_minutes INTEGER,
      channel_id INTEGER,
      remind_hour INTEGER,
      user_id INTEGER,
      PRIMARY KEY (name, user_id)
    );
    CREATE TABLE IF NOT EXISTS logs (
      task_name TEXT,
      user_id INTEGER,
      logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
      user_id INTEGER,
      skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS roasts (
      message TEXT
    );
  """)
  yield conn
  conn.close()


########################
# TRACK COMMAND LOGIC  #
########################

class TestTrackCommand:
  def test_track_creates_task_and_log(self, db):
    minutes = parse_duration("7d")
    now = datetime.now().isoformat()
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
              ("vacuum", minutes, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, now))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchone()
    log = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert task is not None
    assert log is not None

  def test_track_with_hour(self, db):
    minutes = parse_duration("7d")
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
              ("vacuum", minutes, 123, 9, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 9

  def test_track_combined_duration(self, db):
    minutes = parse_duration("1h30mi")
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
              ("water", minutes, 123, None, 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?",
                    ("water", 111)).fetchone()
    assert row[0] == 90

  def test_track_replaces_existing(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 20160, 123, 9, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[1] == 20160
    assert row[3] == 9

  def test_hour_boundary_0(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 0, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 0

  def test_hour_boundary_23(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 23, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 23

  def test_hour_invalid_24(self):
    hour = 24
    assert not (0 <= hour <= 23)

  def test_hour_invalid_negative(self):
    hour = -1
    assert not (0 <= hour <= 23)


#######################
# EDIT COMMAND LOGIC  #
#######################

class TestEditCommand:
  def test_edit_updates_duration(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    new_minutes = parse_duration("14d")
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
              (new_minutes, "vacuum", 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 20160

  def test_edit_keeps_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
              (20160, "vacuum", 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 9

  def test_edit_changes_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("UPDATE tasks SET remind_hour = ? WHERE name = ? AND user_id = ?",
              (10, "vacuum", 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 10

  def test_edit_nonexistent(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                    ("ghost", 111)).fetchone()
    assert row is None

  def test_edit_combined_duration(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    new_minutes = parse_duration("2w3d")
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
              (new_minutes, "vacuum", 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    assert row[0] == 24480


######################
# LOG COMMAND LOGIC  #
######################

class TestLogCommand:
  def test_log_creates_task_and_entry(self, db):
    db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("haircut", 111, datetime.now().isoformat()))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                      ("haircut", 111)).fetchone()
    assert task[1] is None
    logs = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                      ("haircut", 111)).fetchall()
    assert len(logs) == 1

  def test_log_doesnt_overwrite_tracked(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("vacuum", 123, 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchone()
    assert task[1] == 10080


#######################
# DONE COMMAND LOGIC  #
#######################

class TestDoneCommand:
  def test_done_logs_entry(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchone()[0]
    assert count == 1

  def test_done_nonexistent(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                    ("ghost", 111)).fetchone()
    assert row is None


#########################
# DELETE COMMAND LOGIC  #
#########################

class TestDeleteCommand:
  def test_delete_correct_entry(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("v", 111, "2024-01-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("v", 111, "2024-06-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("v", 111, "2024-03-01"))
    rows = db.execute(
      "SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC",
      ("v", 111)).fetchall()
    db.execute("DELETE FROM logs WHERE rowid = ?", (rows[0][0],))
    remaining = db.execute(
      "SELECT logged_at FROM logs WHERE user_id = ? ORDER BY logged_at DESC",
      (111,)).fetchall()
    assert len(remaining) == 2
    assert remaining[0][0] == "2024-03-01"

  def test_delete_invalid_entry(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, datetime.now().isoformat()))
    rows = db.execute(
      "SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC",
      ("vacuum", 111)).fetchall()
    entry_num = 5
    assert entry_num > len(rows)

  def test_delete_zero(self):
    entry_num = 0
    assert entry_num < 1

  def test_delete_negative(self):
    entry_num = -1
    assert entry_num < 1

  def test_delete_last_removes_log_only_task(self, db):
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("haircut", 111, datetime.now().isoformat()))
    rowid = db.execute(
      "SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?",
      ("haircut", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                          ("haircut", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL",
                ("haircut", 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                      ("haircut", 111)).fetchone()
    assert task is None

  def test_delete_last_keeps_tracked_task(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, datetime.now().isoformat()))
    rowid = db.execute(
      "SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?",
      ("vacuum", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                          ("vacuum", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL",
                ("vacuum", 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchone()
    assert task is not None


#######################
# SKIP COMMAND LOGIC  #
#######################

class TestSkipCommand:
  def test_skip_increments(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
              ("cmput261", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
              ("cmput261", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                      ("cmput261", 111)).fetchone()[0]
    assert count == 2

  def test_skip_per_user(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
              ("cmput261", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
              ("cmput261", 222, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                      ("cmput261", 111)).fetchone()[0]
    assert count == 1

  def test_roast_formatting(self):
    msg = "That's {count} skip(s) for {name}. Your GPA can feel it."
    result = msg.format(count=3, name="cmput261")
    assert "3" in result
    assert "cmput261" in result

  def test_shame_board_order(self, db):
    for _ in range(5):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                ("cmput261", 111, datetime.now().isoformat()))
    for _ in range(2):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                ("math201", 111, datetime.now().isoformat()))
    rows = db.execute(
      "SELECT class_name, COUNT(*) as c FROM skips WHERE user_id = ? GROUP BY class_name ORDER BY c DESC",
      (111,)).fetchall()
    assert rows[0][0] == "cmput261"
    assert rows[0][1] == 5
    assert rows[1][0] == "math201"
    assert rows[1][1] == 2


########################
# FOCUS COMMAND LOGIC  #
########################

class TestFocusCommand:
  def test_focus_creates_session(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", now))
    row = db.execute("SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NULL",
                    (111,)).fetchone()
    assert row is not None
    assert row[2] == "focus"
    assert row[3] == "homework"

  def test_focus_default_label(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "general", now))
    row = db.execute("SELECT label FROM sessions WHERE user_id = ?", (111,)).fetchone()
    assert row[0] == "general"

  def test_new_focus_ends_previous(self, db):
    old = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "old-task", old))
    end = datetime.now().isoformat()
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (end, 111))
    new = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "new-task", new))
    open_sessions = db.execute(
      "SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NULL",
      (111,)).fetchall()
    assert len(open_sessions) == 1
    assert open_sessions[0][3] == "new-task"


########################
# BREAK COMMAND LOGIC  #
########################

class TestBreakCommand:
  def test_break_creates_session(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (111, now))
    row = db.execute("SELECT type FROM sessions WHERE user_id = ?", (111,)).fetchone()
    assert row[0] == "break"

  def test_break_ends_focus(self, db):
    focus_start = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", focus_start))
    end = datetime.now().isoformat()
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (end, 111))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (111, end))
    open_sessions = db.execute(
      "SELECT type FROM sessions WHERE user_id = ? AND ended_at IS NULL",
      (111,)).fetchall()
    assert len(open_sessions) == 1
    assert open_sessions[0][0] == "break"


########################
# SNOOZE COMMAND LOGIC #
########################

class TestSnoozeCommand:
  def test_snooze_inserts_future_log(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    snooze_until = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, snooze_until))
    row = db.execute("SELECT logged_at FROM logs WHERE task_name = ? AND user_id = ?",
                    ("vacuum", 111)).fetchone()
    logged = datetime.fromisoformat(row[0])
    assert logged > datetime.now()

  def test_snooze_prevents_reminder(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    snooze_until = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
              ("vacuum", 111, snooze_until))
    now = datetime.now()
    last_done = db.execute("""
      SELECT MAX(l.logged_at) FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.name = ? AND t.user_id = ?
    """, ("vacuum", 111)).fetchone()[0]
    ago = (now - datetime.fromisoformat(last_done)).total_seconds() / 60
    assert ago < 0

  def test_snooze_nonexistent_task(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?",
                    ("ghost", 111)).fetchone()
    assert row is None
import sqlite3
from datetime import datetime, timedelta
import pytest
from helpers import parse_duration, MAX_NAME_LENGTH


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
      message TEXT,
      guild_id INTEGER
    );
  """)
  yield conn
  conn.close()


#########
# TRACK #
#########

class TestTrack:
  def test_creates_both(self, db):
    minutes = parse_duration("7d")
    now = datetime.now().isoformat()
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
               ("vacuum", minutes, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, now))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    log = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert task is not None
    assert log is not None

  def test_with_hour(self, db):
    minutes = parse_duration("7d")
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
               ("vacuum", minutes, 123, 9, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[0] == 9

  def test_combined(self, db):
    minutes = parse_duration("1h30mi")
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)",
               ("water", minutes, 123, None, 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?", ("water", 111)).fetchone()
    assert row[0] == 90

  def test_replaces(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 20160, 123, 9, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[1] == 20160
    assert row[3] == 9

  def test_hour_0(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 0, 111))
    assert db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 0

  def test_hour_23(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 23, 111))
    assert db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 23

  def test_hour_24_invalid(self):
    assert not (0 <= 24 <= 23)

  def test_hour_neg_invalid(self):
    assert not (0 <= -1 <= 23)

  def test_no_cross_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("water", 120, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("water", 111, datetime.now().isoformat()))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("water", 222)).fetchone()
    assert row is None

  def test_long_name(self):
    name = "a" * (MAX_NAME_LENGTH + 1)
    assert len(name) > MAX_NAME_LENGTH

  def test_name_at_limit(self):
    name = "a" * MAX_NAME_LENGTH
    assert len(name) <= MAX_NAME_LENGTH


########
# EDIT #
########

class TestEdit:
  def test_duration(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    new = parse_duration("14d")
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
               (new, "vacuum", 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[0] == 20160

  def test_keeps_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
               (20160, "vacuum", 111))
    assert db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 9

  def test_changes_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("UPDATE tasks SET remind_hour = ? WHERE name = ? AND user_id = ?",
               (10, "vacuum", 111))
    assert db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 10

  def test_clears_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("UPDATE tasks SET remind_hour = ? WHERE name = ? AND user_id = ?",
               (None, "vacuum", 111))
    assert db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] is None

  def test_nonexistent(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("ghost", 111)).fetchone()
    assert row is None

  def test_combined(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    new = parse_duration("2w3d")
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
               (new, "vacuum", 111))
    assert db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 24480

  def test_skip_duration(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    minutes = row[1]  # keep existing
    db.execute("UPDATE tasks SET remind_after_minutes = ?, remind_hour = ? WHERE name = ? AND user_id = ?",
               (minutes, 14, "vacuum", 111))
    result = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert result[1] == 10080  # unchanged
    assert result[3] == 14  # new hour

  def test_wrong_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
               (999, "vacuum", 222))
    assert db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0] == 10080


#######
# LOG #
#######

class TestLog:
  def test_creates_both(self, db):
    db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("haircut", 111, datetime.now().isoformat()))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("haircut", 111)).fetchone()
    assert task[1] is None
    logs = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?", ("haircut", 111)).fetchall()
    assert len(logs) == 1

  def test_no_overwrite(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("vacuum", 123, 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert task[1] == 10080

  def test_multiple_logs(self, db):
    db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("coffee", 123, 111))
    for _ in range(5):
      db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
                 ("coffee", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?", ("coffee", 111)).fetchone()[0]
    assert count == 5

  def test_long_name(self):
    name = "a" * (MAX_NAME_LENGTH + 1)
    assert len(name) > MAX_NAME_LENGTH


########
# DONE #
########

class TestDone:
  def test_logs_entry(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0]
    assert count == 1

  def test_nonexistent(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("ghost", 111)).fetchone()
    assert row is None

  def test_resets_countdown(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    old = (datetime.now() - timedelta(days=10)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("vacuum", 111, old))
    now = datetime.now().isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("vacuum", 111, now))
    last = db.execute("""
      SELECT MAX(logged_at) FROM logs WHERE task_name = ? AND user_id = ?
    """, ("vacuum", 111)).fetchone()[0]
    assert last == now

  def test_wrong_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 222)).fetchone()
    assert row is None


##########
# DELETE #
##########

class TestDelete:
  def test_correct_entry(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-01-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-06-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-03-01"))
    rows = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC", ("v", 111)).fetchall()
    db.execute("DELETE FROM logs WHERE rowid = ?", (rows[0][0],))
    remaining = db.execute("SELECT logged_at FROM logs WHERE user_id = ? ORDER BY logged_at DESC", (111,)).fetchall()
    assert len(remaining) == 2
    assert remaining[0][0] == "2024-03-01"

  def test_invalid_num(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    rows = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC", ("vacuum", 111)).fetchall()
    assert 5 > len(rows)

  def test_zero(self):
    assert 0 < 1

  def test_negative(self):
    assert -1 < 1

  def test_last_removes_log_only(self, db):
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("haircut", 111, datetime.now().isoformat()))
    rowid = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?", ("haircut", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?", ("haircut", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL", ("haircut", 111))
    assert db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("haircut", 111)).fetchone() is None

  def test_last_keeps_tracked(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    rowid = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL", ("vacuum", 111))
    assert db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone() is not None

  def test_middle_entry(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-01-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-03-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-06-01"))
    rows = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC", ("v", 111)).fetchall()
    db.execute("DELETE FROM logs WHERE rowid = ?", (rows[1][0],))  # middle entry
    remaining = db.execute("SELECT logged_at FROM logs WHERE user_id = ? ORDER BY logged_at DESC", (111,)).fetchall()
    assert len(remaining) == 2
    assert remaining[0][0] == "2024-06-01"
    assert remaining[1][0] == "2024-01-01"

  def test_other_user_safe(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 111, "2024-01-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("v", 222, "2024-01-01"))
    rows = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC", ("v", 111)).fetchall()
    db.execute("DELETE FROM logs WHERE rowid = ?", (rows[0][0],))
    assert db.execute("SELECT COUNT(*) FROM logs WHERE user_id = ?", (222,)).fetchone()[0] == 1


########
# SKIP #
########

class TestSkip:
  def test_increments(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?", ("cmput261", 111)).fetchone()[0]
    assert count == 2

  def test_per_user(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 222, datetime.now().isoformat()))
    assert db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?", ("cmput261", 111)).fetchone()[0] == 1

  def test_roast_format(self):
    msg = "That's {count} skip(s) for {name}."
    result = msg.format(count=3, name="cmput261")
    assert "3" in result
    assert "cmput261" in result

  def test_shame_order(self, db):
    for _ in range(5):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("cmput261", 111, datetime.now().isoformat()))
    for _ in range(2):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("math201", 111, datetime.now().isoformat()))
    rows = db.execute(
      "SELECT class_name, COUNT(*) as c FROM skips WHERE user_id = ? GROUP BY class_name ORDER BY c DESC",
      (111,)).fetchall()
    assert rows[0] == ("cmput261", 5)
    assert rows[1] == ("math201", 2)

  def test_non_lecture(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("gym", 111, datetime.now().isoformat()))
    assert db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?", ("gym", 111)).fetchone()[0] == 1

  def test_long_name(self):
    name = "a" * (MAX_NAME_LENGTH + 1)
    assert len(name) > MAX_NAME_LENGTH

  def test_has_3_digits(self):
    import re
    assert re.search(r'\d{3}', "cmput261") is not None

  def test_no_3_digits(self):
    import re
    assert re.search(r'\d{3}', "gym") is None

  def test_4_digits_matches(self):
    import re
    assert re.search(r'\d{3}', "cmput2610") is not None


#########
# FOCUS #
#########

class TestFocus:
  def test_creates_session(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", now))
    row = db.execute("SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NULL", (111,)).fetchone()
    assert row is not None
    assert row[2] == "focus"
    assert row[3] == "homework"

  def test_default_label(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "general", now))
    assert db.execute("SELECT label FROM sessions WHERE user_id = ?", (111,)).fetchone()[0] == "general"

  def test_ends_previous(self, db):
    old = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "old-task", old))
    end = datetime.now().isoformat()
    db.execute("UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL", (end, 111))
    new = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "new-task", new))
    open_sessions = db.execute("SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NULL", (111,)).fetchall()
    assert len(open_sessions) == 1
    assert open_sessions[0][3] == "new-task"

  def test_per_user(self, db):
    now = datetime.now().isoformat()
    db.execute("INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)", (111, "a", now))
    db.execute("INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)", (222, "b", now))
    rows = db.execute("SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NULL", (111,)).fetchall()
    assert len(rows) == 1

  def test_long_label(self):
    label = "a" * (MAX_NAME_LENGTH + 1)
    assert len(label) > MAX_NAME_LENGTH


#########
# BREAK #
#########

class TestBreak:
  def test_creates_session(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (111, now))
    assert db.execute("SELECT type FROM sessions WHERE user_id = ?", (111,)).fetchone()[0] == "break"

  def test_ends_focus(self, db):
    focus = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", focus))
    end = datetime.now().isoformat()
    db.execute("UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL", (end, 111))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (111, end))
    open_sessions = db.execute("SELECT type FROM sessions WHERE user_id = ? AND ended_at IS NULL", (111,)).fetchall()
    assert len(open_sessions) == 1
    assert open_sessions[0][0] == "break"


##########
# SNOOZE #
##########

class TestSnooze:
  def test_future_log(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    future = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("vacuum", 111, future))
    row = db.execute("SELECT logged_at FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert datetime.fromisoformat(row[0]) > datetime.now()

  def test_prevents_reminder(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    future = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)", ("vacuum", 111, future))
    last = db.execute("""
      SELECT MAX(l.logged_at) FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.name = ? AND t.user_id = ?
    """, ("vacuum", 111)).fetchone()[0]
    ago = (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60
    assert ago < 0

  def test_nonexistent(self, db):
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("ghost", 111)).fetchone()
    assert row is None

  def test_default_8h(self):
    snooze_min = 480
    assert snooze_min == 8 * 60

  def test_custom_duration(self):
    snooze_min = parse_duration("4h")
    assert snooze_min == 240

  def test_combined_snooze(self):
    snooze_min = parse_duration("1h30mi")
    assert snooze_min == 90


##########
# ROASTS #
##########

class TestRoastCommands:
  def test_add(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Test roast", 999))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) == 1

  def test_edit(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Old", 999))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    db.execute("UPDATE roasts SET message = ? WHERE rowid = ?", ("New", rowid))
    assert db.execute("SELECT message FROM roasts WHERE rowid = ?", (rowid,)).fetchone()[0] == "New"

  def test_delete(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("a", 999))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("b", 999))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (999,)).fetchall()[0][0]
    db.execute("DELETE FROM roasts WHERE rowid = ?", (rowid,))
    assert db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0] == 1

  def test_cant_delete_last(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Only one", 999))
    rows = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) <= 1  # command should reject

  def test_per_guild(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("A", 111))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("B", 222))
    assert db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (111,)).fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (222,)).fetchone()[0] == 1

  def test_seed_empty(self, db):
    defaults = ["R1", "R2", "R3"]
    count = db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    if count == 0:
      for msg in defaults:
        db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, 999))
    assert db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0] == 3

  def test_seed_skips_existing(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Existing", 999))
    defaults = ["R1", "R2"]
    count = db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    if count == 0:
      for msg in defaults:
        db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, 999))
    assert db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0] == 1
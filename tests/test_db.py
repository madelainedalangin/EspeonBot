import sqlite3
from datetime import datetime, timedelta
import pytest


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


################
# TASKS TABLE  #
################

class TestTasks:
  def test_insert(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row == ("vacuum", 10080, 123, None, 111)

  def test_with_hour(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 9, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[0] == 9

  def test_log_only(self, db):
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("haircut", 111)).fetchone()
    assert row[1] is None
    assert row[3] is None

  def test_same_name_diff_users(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("water", 120, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("water", 60, 123, None, 222))
    rows = db.execute("SELECT * FROM tasks WHERE name = ?", ("water",)).fetchall()
    assert len(rows) == 2

  def test_replace(self, db):
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 20160, 123, 9, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[1] == 20160
    assert row[3] == 9

  def test_update(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("UPDATE tasks SET remind_after_minutes = ?, remind_hour = ? WHERE name = ? AND user_id = ?",
               (20160, 10, "vacuum", 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[1] == 20160
    assert row[3] == 10

  def test_update_wrong_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("UPDATE tasks SET remind_after_minutes = ? WHERE name = ? AND user_id = ?",
               (20160, "vacuum", 222))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?",
                     ("vacuum", 111)).fetchone()
    assert row[0] == 10080

  def test_delete(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row is None

  def test_delete_wrong_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 222))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row is not None

  def test_empty(self, db):
    rows = db.execute("SELECT * FROM tasks").fetchall()
    assert rows == []

  def test_list_per_user(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("mop", 20160, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 222))
    rows = db.execute("SELECT * FROM tasks WHERE user_id = ?", (111,)).fetchall()
    assert len(rows) == 2

  def test_duplicate_pk_fails(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    with pytest.raises(sqlite3.IntegrityError):
      db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 999, 456, 5, 111))

  def test_hour_zero(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 0, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[0] == 0

  def test_hour_23(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, 23, 111))
    row = db.execute("SELECT remind_hour FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row[0] == 23

  def test_zero_duration(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("test", 0, 123, None, 111))
    row = db.execute("SELECT remind_after_minutes FROM tasks WHERE name = ? AND user_id = ?", ("test", 111)).fetchone()
    assert row[0] == 0

  def test_case_sensitive(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("Vacuum", 10080, 123, None, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert row is None

  def test_hyphen_in_name(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("posture-check", 60, 123, None, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("posture-check", 111)).fetchone()
    assert row is not None

  def test_number_in_name(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("cmput291", 10080, 123, None, 111))
    row = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("cmput291", 111)).fetchone()
    assert row is not None


###############
# LOGS TABLE  #
###############

class TestLogs:
  def test_insert(self, db):
    now = datetime.now().isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, now))
    rows = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchall()
    assert len(rows) == 1

  def test_multiple(self, db):
    for _ in range(3):
      db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
                 ("vacuum", 111, datetime.now().isoformat()))
    rows = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchall()
    assert len(rows) == 3

  def test_per_user(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 222, datetime.now().isoformat()))
    rows = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                      ("vacuum", 111)).fetchall()
    assert len(rows) == 1

  def test_order_desc(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("v", 111, "2024-01-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("v", 111, "2024-06-01"))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("v", 111, "2024-03-01"))
    rows = db.execute(
      "SELECT logged_at FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC",
      ("v", 111)).fetchall()
    assert rows[0][0] == "2024-06-01"
    assert rows[2][0] == "2024-01-01"

  def test_delete_by_rowid(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    rows = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC",
                      ("vacuum", 111)).fetchall()
    db.execute("DELETE FROM logs WHERE rowid = ?", (rows[0][0],))
    remaining = db.execute("SELECT * FROM logs WHERE user_id = ?", (111,)).fetchall()
    assert len(remaining) == 1

  def test_delete_all_for_task(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("mop", 111, datetime.now().isoformat()))
    db.execute("DELETE FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111))
    remaining = db.execute("SELECT * FROM logs WHERE user_id = ?", (111,)).fetchall()
    assert len(remaining) == 1
    assert remaining[0][0] == "mop"

  def test_empty_history(self, db):
    rows = db.execute("SELECT * FROM logs WHERE task_name = ? AND user_id = ?",
                      ("ghost", 111)).fetchall()
    assert rows == []

  def test_future_timestamp(self, db):
    future = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, future))
    row = db.execute("SELECT logged_at FROM logs WHERE task_name = ? AND user_id = ?",
                     ("vacuum", 111)).fetchone()
    assert datetime.fromisoformat(row[0]) > datetime.now()

  def test_same_task_diff_users_delete(self, db):
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 222, datetime.now().isoformat()))
    db.execute("DELETE FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111))
    remaining = db.execute("SELECT * FROM logs WHERE task_name = ?", ("vacuum",)).fetchall()
    assert len(remaining) == 1
    assert remaining[0][1] == 222


#####################
# OVERDUE / STATUS  #
#####################

class TestOverdue:
  def test_not_overdue(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    now = datetime.now().isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, now))
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.remind_after_minutes IS NOT NULL AND t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    name, minutes, last_done = rows[0]
    ago = (datetime.now() - datetime.fromisoformat(last_done)).total_seconds() / 60
    assert ago < minutes

  def test_overdue(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    old = (datetime.now() - timedelta(days=10)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, old))
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.remind_after_minutes IS NOT NULL AND t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    name, minutes, last_done = rows[0]
    ago = (datetime.now() - datetime.fromisoformat(last_done)).total_seconds() / 60
    assert ago >= minutes

  def test_never_done(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.remind_after_minutes IS NOT NULL AND t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    assert rows[0][2] is None

  def test_log_only_excluded(self, db):
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    rows = db.execute("""
      SELECT * FROM tasks WHERE remind_after_minutes IS NOT NULL AND user_id = ?
    """, (111,)).fetchall()
    assert len(rows) == 0

  def test_most_recent_used(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    old = (datetime.now() - timedelta(days=10)).isoformat()
    recent = (datetime.now() - timedelta(days=1)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, old))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, recent))
    rows = db.execute("""
      SELECT MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.name = 'vacuum' AND t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    assert rows[0][0] == recent

  def test_other_user_ignored(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 222, datetime.now().isoformat()))
    rows = db.execute("""
      SELECT t.name, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    assert rows[0][1] is None

  def test_snooze_prevents_overdue(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    future = (datetime.now() + timedelta(hours=8)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, future))
    rows = db.execute("""
      SELECT MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.name = 'vacuum' AND t.user_id = ?
    """, (111,)).fetchall()
    ago = (datetime.now() - datetime.fromisoformat(rows[0][0])).total_seconds() / 60
    assert ago < 0

  def test_multiple_tasks_mixed(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("water", 120, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    now = datetime.now().isoformat()
    old = (datetime.now() - timedelta(days=10)).isoformat()
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, old))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("water", 111, now))
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name AND l.user_id = t.user_id
      WHERE t.remind_after_minutes IS NOT NULL AND t.user_id = ?
      GROUP BY t.name
    """, (111,)).fetchall()
    assert len(rows) == 2


###################
# SESSIONS TABLE  #
###################

class TestSessions:
  def test_insert_focus(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", now))
    row = db.execute("SELECT * FROM sessions WHERE user_id = ?", (111,)).fetchone()
    assert row[2] == "focus"
    assert row[3] == "homework"
    assert row[5] is None

  def test_insert_break(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (111, now))
    row = db.execute("SELECT type FROM sessions WHERE user_id = ?", (111,)).fetchone()
    assert row[0] == "break"

  def test_end_session(self, db):
    start = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "homework", start))
    end = datetime.now().isoformat()
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (end, 111))
    row = db.execute("SELECT ended_at FROM sessions WHERE user_id = ?", (111,)).fetchone()
    assert row[0] is not None

  def test_end_only_open(self, db):
    old_start = (datetime.now() - timedelta(hours=2)).isoformat()
    old_end = (datetime.now() - timedelta(hours=1)).isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "old-task", old_start, old_end))
    new_start = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "new-task", new_start))
    new_end = datetime.now().isoformat()
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (new_end, 111))
    rows = db.execute("SELECT label, ended_at FROM sessions ORDER BY started_at").fetchall()
    assert rows[0][1] == old_end
    assert rows[1][1] == new_end

  def test_per_user(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "task-a", now))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (222, "task-b", now))
    rows = db.execute("SELECT * FROM sessions WHERE user_id = ?", (111,)).fetchall()
    assert len(rows) == 1
    assert rows[0][3] == "task-a"

  def test_incomplete_excluded(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "in-progress", now))
    rows = db.execute(
      "SELECT * FROM sessions WHERE user_id = ? AND ended_at IS NOT NULL",
      (111,)).fetchall()
    assert len(rows) == 0

  def test_stats_math(self, db):
    start1 = datetime(2024, 1, 1, 9, 0).isoformat()
    end1 = datetime(2024, 1, 1, 9, 50).isoformat()
    start2 = datetime(2024, 1, 1, 9, 50).isoformat()
    end2 = datetime(2024, 1, 1, 10, 0).isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "work", start1, end1))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'break', 'break', ?, ?)",
      (111, start2, end2))
    rows = db.execute("""
      SELECT type, started_at, ended_at FROM sessions
      WHERE user_id = ? AND ended_at IS NOT NULL
    """, (111,)).fetchall()
    focus_mins = 0
    break_mins = 0
    for stype, s, e in rows:
      mins = (datetime.fromisoformat(e) - datetime.fromisoformat(s)).total_seconds() / 60
      if stype == "focus":
        focus_mins += mins
      else:
        break_mins += mins
    assert focus_mins == pytest.approx(50, abs=1)
    assert break_mins == pytest.approx(10, abs=1)
    total = focus_mins + break_mins
    pct = round(focus_mins / total * 100)
    assert pct == 83

  def test_stats_by_label(self, db):
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "math", "2024-01-01T09:00", "2024-01-01T09:30"))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "math", "2024-01-01T10:00", "2024-01-01T10:20"))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "reading", "2024-01-01T11:00", "2024-01-01T11:15"))
    rows = db.execute("""
      SELECT label, started_at, ended_at FROM sessions
      WHERE user_id = ? AND type = 'focus' AND ended_at IS NOT NULL
    """, (111,)).fetchall()
    by_label = {}
    for label, s, e in rows:
      mins = (datetime.fromisoformat(e) - datetime.fromisoformat(s)).total_seconds() / 60
      by_label[label] = by_label.get(label, 0) + mins
    assert by_label["math"] == 50
    assert by_label["reading"] == 15

  def test_concurrent_users(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "task-a", now))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (222, "task-b", now))
    end = datetime.now().isoformat()
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (end, 111))
    open_sessions = db.execute("SELECT * FROM sessions WHERE ended_at IS NULL").fetchall()
    assert len(open_sessions) == 1
    assert open_sessions[0][1] == 222

  def test_autoincrement(self, db):
    now = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "a", now))
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (111, "b", now))
    rows = db.execute("SELECT id FROM sessions ORDER BY id").fetchall()
    assert rows[0][0] == 1
    assert rows[1][0] == 2

  def test_zero_duration(self, db):
    start = datetime.now().isoformat()
    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at, ended_at) VALUES (?, 'focus', ?, ?, ?)",
      (111, "quick", start, start))
    row = db.execute("SELECT started_at, ended_at FROM sessions WHERE user_id = ?", (111,)).fetchone()
    mins = (datetime.fromisoformat(row[1]) - datetime.fromisoformat(row[0])).total_seconds() / 60
    assert mins == 0


################
# SKIPS TABLE  #
################

class TestSkips:
  def test_insert(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                       ("cmput261", 111)).fetchone()[0]
    assert count == 1

  def test_multiple(self, db):
    for _ in range(3):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("cmput261", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                       ("cmput261", 111)).fetchone()[0]
    assert count == 3

  def test_per_user(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 222, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                       ("cmput261", 111)).fetchone()[0]
    assert count == 1

  def test_shame_board(self, db):
    for _ in range(5):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("cmput261", 111, datetime.now().isoformat()))
    for _ in range(2):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("math201", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput261", 222, datetime.now().isoformat()))
    rows = db.execute(
      "SELECT class_name, COUNT(*) as c FROM skips WHERE user_id = ? GROUP BY class_name ORDER BY c DESC",
      (111,)).fetchall()
    assert rows[0] == ("cmput261", 5)
    assert rows[1] == ("math201", 2)

  def test_empty(self, db):
    rows = db.execute("SELECT * FROM skips WHERE user_id = ?", (111,)).fetchall()
    assert rows == []

  def test_non_lecture(self, db):
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("gym", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                       ("gym", 111)).fetchone()[0]
    assert count == 1


#################
# ROASTS TABLE  #
#################

class TestRoasts:
  def test_insert(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("You suck.", 999))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) == 1

  def test_multiple(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Roast 1", 999))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Roast 2", 999))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) == 2

  def test_edit(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Old roast", 999))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    db.execute("UPDATE roasts SET message = ? WHERE rowid = ?", ("New roast", rowid))
    row = db.execute("SELECT message FROM roasts WHERE rowid = ?", (rowid,)).fetchone()
    assert row[0] == "New roast"

  def test_delete(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Delete me", 999))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    db.execute("DELETE FROM roasts WHERE rowid = ?", (rowid,))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert rows == []

  def test_placeholders(self, db):
    msg = "That's {count} skip(s) for {name}. Embarrassing."
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, 999))
    row = db.execute("SELECT message FROM roasts WHERE guild_id = ?", (999,)).fetchone()
    result = row[0].format(count=3, name="cmput261")
    assert "3" in result
    assert "cmput261" in result

  def test_per_guild(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Guild A roast", 111))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Guild B roast", 222))
    rows_a = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (111,)).fetchall()
    rows_b = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (222,)).fetchall()
    assert len(rows_a) == 1
    assert len(rows_b) == 1
    assert rows_a[0][0] == "Guild A roast"
    assert rows_b[0][0] == "Guild B roast"

  def test_guild_edit_isolated(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Original", 111))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Original", 222))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (111,)).fetchone()[0]
    db.execute("UPDATE roasts SET message = ? WHERE rowid = ?", ("Changed", rowid))
    row_a = db.execute("SELECT message FROM roasts WHERE guild_id = ?", (111,)).fetchone()
    row_b = db.execute("SELECT message FROM roasts WHERE guild_id = ?", (222,)).fetchone()
    assert row_a[0] == "Changed"
    assert row_b[0] == "Original"

  def test_guild_delete_isolated(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Delete me", 111))
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Keep me", 222))
    rowid = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (111,)).fetchone()[0]
    db.execute("DELETE FROM roasts WHERE rowid = ?", (rowid,))
    rows_a = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (111,)).fetchall()
    rows_b = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (222,)).fetchall()
    assert len(rows_a) == 0
    assert len(rows_b) == 1

  def test_seed_defaults(self, db):
    defaults = ["Roast 1", "Roast 2", "Roast 3"]
    count = db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    if count == 0:
      for msg in defaults:
        db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, 999))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) == 3

  def test_seed_skips_existing(self, db):
    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", ("Existing", 999))
    defaults = ["Roast 1", "Roast 2"]
    count = db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (999,)).fetchone()[0]
    if count == 0:
      for msg in defaults:
        db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, 999))
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "Existing"

  def test_empty_guild(self, db):
    rows = db.execute("SELECT * FROM roasts WHERE guild_id = ?", (999,)).fetchall()
    assert rows == []


#####################
# CROSS-TABLE TESTS #
#####################

class TestCrossTable:
  def test_untrack_cleans_both(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("DELETE FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111))
    db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111))
    assert db.execute("SELECT * FROM tasks WHERE user_id = ?", (111,)).fetchall() == []
    assert db.execute("SELECT * FROM logs WHERE user_id = ?", (111,)).fetchall() == []

  def test_untrack_other_user_safe(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 222))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 222, datetime.now().isoformat()))
    db.execute("DELETE FROM logs WHERE task_name = ? AND user_id = ?", ("vacuum", 111))
    db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111))
    assert db.execute("SELECT * FROM tasks WHERE user_id = ?", (222,)).fetchone() is not None
    assert db.execute("SELECT * FROM logs WHERE user_id = ?", (222,)).fetchone() is not None

  def test_log_only_cleanup(self, db):
    db.execute("INSERT INTO tasks VALUES (?, NULL, ?, NULL, ?)", ("haircut", 123, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("haircut", 111, datetime.now().isoformat()))
    rowid = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?",
                       ("haircut", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                           ("haircut", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL",
                 ("haircut", 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("haircut", 111)).fetchone()
    assert task is None

  def test_tracked_survives_cleanup(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    rowid = db.execute("SELECT rowid FROM logs WHERE task_name = ? AND user_id = ?",
                       ("vacuum", 111)).fetchone()[0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    remaining = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                           ("vacuum", 111)).fetchone()[0]
    if remaining == 0:
      db.execute("DELETE FROM tasks WHERE name = ? AND user_id = ? AND remind_after_minutes IS NULL",
                 ("vacuum", 111))
    task = db.execute("SELECT * FROM tasks WHERE name = ? AND user_id = ?", ("vacuum", 111)).fetchone()
    assert task is not None

  def test_all_tables_empty(self, db):
    assert db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM logs").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM skips").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM roasts").fetchone()[0] == 0

  def test_user_data_isolated(self, db):
    db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", ("vacuum", 10080, 123, None, 111))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("vacuum", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
               (111, "work", datetime.now().isoformat()))
    db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
               ("cmput291", 111, datetime.now().isoformat()))
    assert db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (222,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM logs WHERE user_id = ?", (222,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?", (222,)).fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM skips WHERE user_id = ?", (222,)).fetchone()[0] == 0
import sqlite3
from datetime import datetime
import pytest
from helpers import MAX_NAME_LENGTH


############################
# MESSAGE CHUNKING TESTS   #
############################

class TestMessageChunking:
  def test_short_message_no_split(self):
    text = "This is a short message."
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 1

  def test_long_message_splits(self):
    lines = [f"Line {i}" for i in range(300)]
    text = "\n".join(lines)
    assert len(text) > 1900
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) > 1
    for chunk in chunks:
      assert len(chunk) <= 1900

  def test_exactly_1900_no_split(self):
    text = "a" * 1900
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 1

  def test_1901_splits(self):
    text = "a" * 1901
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 2

  def test_splits_on_newline(self):
    text = "a" * 1000 + "\n" + "b" * 1000
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 1000
    assert chunks[1] == "b" * 1000

  def test_no_data_lost(self):
    lines = [f"Entry {i}: some data here" for i in range(200)]
    original = "\n".join(lines)
    chunks = []
    text = original
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    reassembled = "\n".join(chunks)
    assert reassembled == original

  def test_empty_string(self):
    text = ""
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 0

  def test_no_newlines_in_long_text(self):
    text = "a" * 5000
    chunks = []
    max_length = 1900
    while len(text) > max_length:
      split_at = text.rfind('\n', 0, max_length)
      if split_at == -1:
        split_at = max_length
      chunks.append(text[:split_at])
      text = text[split_at:].lstrip('\n')
    if text:
      chunks.append(text)
    assert len(chunks) == 3
    for chunk in chunks:
      assert len(chunk) <= 1900


############################
# NAME LENGTH CAP TESTS    #
############################

class TestNameLength:
  def test_valid_short_name(self):
    name = "vacuum"
    assert len(name) <= MAX_NAME_LENGTH

  def test_valid_at_limit(self):
    name = "a" * MAX_NAME_LENGTH
    assert len(name) <= MAX_NAME_LENGTH

  def test_invalid_over_limit(self):
    name = "a" * (MAX_NAME_LENGTH + 1)
    assert len(name) > MAX_NAME_LENGTH

  def test_single_char(self):
    name = "x"
    assert len(name) <= MAX_NAME_LENGTH

  def test_exactly_30(self):
    name = "abcdefghijklmnopqrstuvwxyz1234"
    assert len(name) == 30
    assert len(name) <= MAX_NAME_LENGTH

  def test_31_rejected(self):
    name = "abcdefghijklmnopqrstuvwxyz12345"
    assert len(name) == 31
    assert len(name) > MAX_NAME_LENGTH

  def test_name_with_numbers(self):
    name = "cmput261"
    assert len(name) <= MAX_NAME_LENGTH

  def test_name_with_hyphens(self):
    name = "air-filter-replacement"
    assert len(name) <= MAX_NAME_LENGTH

  def test_very_long_name(self):
    name = "a" * 100
    assert len(name) > MAX_NAME_LENGTH


############################
# DATABASE SPAM TESTS      #
############################

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
    CREATE TABLE IF NOT EXISTS skips (
      class_name TEXT,
      user_id INTEGER,
      skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  """)
  yield conn
  conn.close()

class TestDatabaseSpam:
  def test_many_logs_same_task(self, db):
    for i in range(100):
      db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
                 ("test", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM logs WHERE task_name = ? AND user_id = ?",
                       ("test", 111)).fetchone()[0]
    assert count == 100

  def test_many_different_tasks(self, db):
    for i in range(100):
      name = f"task{i}"
      db.execute("INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)",
                 (name, 123, 111))
    count = db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?",
                       (111,)).fetchone()[0]
    assert count == 100

  def test_many_skips(self, db):
    for i in range(100):
      db.execute("INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
                 ("cmput261", 111, datetime.now().isoformat()))
    count = db.execute("SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
                       ("cmput261", 111)).fetchone()[0]
    assert count == 100

  def test_spam_doesnt_affect_other_users(self, db):
    for i in range(100):
      db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
                 ("test", 111, datetime.now().isoformat()))
    db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
               ("test", 222, datetime.now().isoformat()))
    count_111 = db.execute("SELECT COUNT(*) FROM logs WHERE user_id = ?",
                           (111,)).fetchone()[0]
    count_222 = db.execute("SELECT COUNT(*) FROM logs WHERE user_id = ?",
                           (222,)).fetchone()[0]
    assert count_111 == 100
    assert count_222 == 1

  def test_history_output_length(self, db):
    for i in range(100):
      db.execute("INSERT INTO logs (task_name, user_id, logged_at) VALUES (?, ?, ?)",
                 ("test", 111, datetime.now().isoformat()))
    rows = db.execute(
      "SELECT rowid, logged_at FROM logs WHERE task_name = ? AND user_id = ? ORDER BY logged_at DESC",
      ("test", 111)).fetchall()
    lines = [f"test -- {len(rows)} entries:"]
    for index, (rowid, ts) in enumerate(rows, 1):
      dt = datetime.fromisoformat(ts)
      unix = int(dt.timestamp())
      lines.append(f"`{index}.` <t:{unix}:F>")
    message = "\n".join(lines)
    assert len(message) > 1900  # confirms that chunking is def needed
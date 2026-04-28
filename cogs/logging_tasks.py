from discord.ext import commands, tasks
from db import db
from helpers import parse_duration
from datetime import datetime, timedelta

class Logging(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  async def log(self, context, name=None):
    """
    Log anything you want to track without any reminders.
    - Creates a task if it doesnt exist.

    Args:
        context: Discord message context, passed automatically
        name: what user describes that they want logged (e.g. haircut)
    
    Returns:
      None. Sends a confirmation message instead to the discord channel.
    """
    
    if not name:
      await context.send("Usage: `!log <name>`\nExample: `!log drawing`")
      return
    
    db.execute(
      "INSERT OR IGNORE INTO tasks VALUES (?, NULL, ?, NULL, ?)",
      (name, context.channel.id, context.author.id)
    )
    db.execute(
    "INSERT INTO logs (task_name, logged_at) VALUES (?, ?)",
    (name, datetime.now().isoformat())
    )
    db.commit()
    await context.send(f"Logged {name}")
    
  @commands.command()
  async def done(self, context, name=None):
    """
    Log a tracked task. This resets the reminder countdown

    Args:
      context: Discord message context, passed automatically.
      name: Name of the task being tracked.
    Returns:
      None. Sends a confirmation or error message to the Discord channel.
    """
    
    if not name:
      await context.send("Usage: `!done <name>`\nExample: `!done drinkwater`")
      return
    
    row = db.execute(
      "SELECT * FROM tasks WHERE name = ? AND user_id = ?",
      (name, context.author.id)
    ).fetchone()
    if not row:
      await context.send(f"{name} doesn't exist. Use `!track {name} <duration>\nOr if you cannot remember, type `!list` to see your list of tracked entries.")
      return
    
    db.execute(
      "INSERT INTO logs (task_name, logged_at) VALUES (?, ?)",
      (name, datetime.now().isoformat())
    )
    db.commit()
    await context.send(f"Logged {name}")
  
  @commands.command()
  async def history(self, context, name=None):
    """
    Show all numbered entries for the task

    Args:
      context: Discord message context that's passed automatically
      name: Name of the task user wanna see history on
    
    Returns: None, sends a list of entries to the Discord channel
    """
    
    if not name:
      await context.send("Usage: `!history <name>\nExample: `!history shower`")
      return
    
    rows = db.execute(
      "SELECT rowid, logged_at FROM logs WHERE task_name = ? ORDER BY logged_at DESC",
      (name,)
    ).fetchall()
    if not rows:
      await context.send(f"No history for {name}.")
      return
    
    lines = [f"{name}-- {len(rows)} entries: "]
    for index, (rowid, ts) in enumerate(rows, 1):
      dt = datetime.fromisoformat(ts)
      lines.append(f"  `{index}.` {dt.strftime('%B %d, %Y at %-I:%M %p')}")
    await context.send("\n".join(lines))
    
  @commands.command()
  async def delete(self, context, name=None, entry_num=None):
    """
    Delete a specific log entry by its number from history.

    Args:
      context: Discord message context, passed automatically.
      name: Name of the task.
      entry_num: Entry number from !history to delete.

    Returns:
      None. Sends a confirmation or error message to the Discord channel.
    """
    if not name or not entry_num:
      await context.send(
        "Usage: `!delete <name> <entry_number>`\n"
        "Use `!history <name>` to see entry numbers."
      )
      return

    try:
      entry_num = int(entry_num)
    except ValueError:
      await context.send("Entry number must be a number.")
      return

    rows = db.execute(
      "SELECT rowid FROM logs WHERE task_name = ? ORDER BY logged_at DESC",
      (name,)
    ).fetchall()

    if not rows or entry_num < 1 or entry_num > len(rows):
      await context.send(f"Invalid entry number. Use `!history {name}` to check.")
      return

    rowid = rows[entry_num - 1][0]
    db.execute("DELETE FROM logs WHERE rowid = ?", (rowid,))
    
    #if after delete theres no more logs left, remove the task too
    whats_left = db.execute(
      "SELECT COUNT (*) FROM logs WHERE task_name = ?", (name,)
    ).fetchone()[0]
    if whats_left == 0:
      db.execute(
        "DELETE FROM tasks WHERE name = ? and user_id = ? AND remind_after_minutes IS NULL",
        (name, context.author.id)
      )
      
    db.commit()
    await context.send(f"Deleted entry {entry_num} from {name}.")

async def setup(bot):
  await bot.add_cog(Logging(bot))
from discord.ext import commands, tasks
from db import db
from helpers import parse_duration
from datetime import datetime, timedelta

class Tracking(commands.Cog):
  
  def __init__(self, bot):
    self.bot = bot
    self.check_reminders.start()
    
  @commands.command()
  async def track(self, context, name=None, duration=None, hour=None):
    """
    Create a new task to track with a reminder duration and optional hour to ping.
    
    Args:
      context: Discord message context, passed automatically.
      name: Name of the task to track (e.g. "vacuum").
      duration: How often to remind, as a string (e.g. "7d", "2w", "6mo").
      hour: Optional hour (0-23) to send reminders. None means any time.
    
    Returns:
      None. Sends a confirmation message to the Discord channel.
    """
    
    if not name or not duration:
      await context.send(
        "Usage: `!track <name> <duration> [hour]`\n"
        "Example: `!track vacuum 5d` or `!track vacuum 5d 14` (24 hr format)"
      )
      return
    
    try:
      minutes = parse_duration(duration)
    except ValueError as e:
      await context.send(str(e))
      return
    
    if hour is not None:
      try:
        hour = int(hour)
      except ValueError:
        await context.send("Hour must be a number 0-23.")
        return
      if not (0 <= hour <= 23):
        await context.send("Hour must be 0-23.")
        return
    
    db.execute(
      "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?)",
      (name, minutes, context.channel.id, hour)
    )
    db.execute(
      "INSERT INTO logs (task_name, logged_at) VALUES (?, ?)",
      (name, datetime.now().isoformat())
    )
    db.commit()
    
    if hour is not None:
      hour_string = f" at {str(hour)}:00"
    else:
      hour_string = ""
      
    await context.send(f"Tracking {name} -- ping me after {duration}{hour_string}")
  
  @commands.command()
  async def edit(self, context, name=None, duration=None, hour=None):
    """
    Edit an existing task's duration and/or reminder hour.
    
    Args:
      context: Discord message context, passed automatically.
      name: Name of the task to edit.
      duration: New duration string, or "-" to keep the existing one.
      hour: New reminder hour (0-23), or None to keep the existing one.
      
    Returns:
      None. Sends a confirmation or error message to the Discord channel.
    """
    if not name or not duration:
      await context.send(
        "Usage: `!edit <name> <duration> [hour]`\n"
        "Use `-` to skip a field.\n"
        "Examples:\n"
        "`!edit vacuum 14d` --> change duration, keep hour\n"
        "`!edit vacuum - 10` --> keep duration, change hour\n"
        "`!edit vacuum 14d 10` --> change both"
      )
      return
    
    #fetch row in db. ? is placeholder for name
    row = db.execute("SELECT * FROM tasks WHERE name = ?", (name,)).fetchone()
    
    if not row:
      await context.send(f"{name} doesn't exist.")
      return
    
    if duration == "-":
      minutes = row[1] # keep existing duration
    else:
      try:
        minutes = parse_duration(duration)
        
      except ValueError as e:
        await context.send(str(e))
        
        return
    
    if hour is not None: #user put in hr
      try:
        hour = int(hour)
      except ValueError:
        await context.send("Hour should be a number between 0-23")
        return
      
      if not (0 <= hour <= 23):
        await context.send("Hour must be 0-23")
        return
    else:
      hour = row[3] #keep existing hr
    
    db.execute(
      "UPDATE tasks SET remind_after_minutes = ?, remind_hour = ? WHERE name = ?",
      (minutes, hour, name)
    )
    db.commit()
    
    if hour is not None:
      hour_string = f" at {hour}:00"
    else:
      hour_string = ""
    await context.send(f"Updated {name} --> now {duration}{hour_string}")         
  
  @commands.command()
  async def untrack(self, context, name=None):
    """
    Remove a task and all its log entries from the database.
    
    Args:
      context: Discord message context, passed automatically.
      name: Name of the task to remove.
    
    Returns:
      None. Sends a confirmation or error message to the Discord channel.
    """
    
    if not name:
      await context.send("Usage: `!untrack <name>`")
      return
    
    row = db.execute("SELECT * FROM tasks WHERE name = ?", (name,)).fetchone()
    if not row:
      await context.send(f"{name} doesn't exist.")
      return
    
    db.execute("DELETE FROM logs WHERE task_name = ?", (name,))
    db.execute("DELETE FROM tasks WHERE name = ?", (name,))
    db.commit()
    await context.send(f"Removed {name} and all its entries.")
  
  @commands.command()
  async def status(self, context):
    """
    Show all tracked tasks and whether they're overdue.
    
    Args:
      context: Discord message context, passed automatically.
      
    Returns:
      None. Sends a list of tracked tasks with overdue status to the Discord channel.
    """
    
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name
      GROUP BY t.name
    """).fetchall()
    if not rows:
      await context.send("Nothing tracked yet.")
      return
    lines = []
    for name, minutes, last_done in rows:
      if minutes is None:
        continue  # skip log-only tasks
      if last_done:
        ago = datetime.now() - datetime.fromisoformat(last_done)
        ago_minutes = ago.total_seconds() / 60
        if ago_minutes >= minutes:
            lines.append(f"**{name}** -- OVERDUE (last done {int(ago_minutes / 1440)}d ago)")
        else:
          lines.append(f"**{name}** -- done {int(ago_minutes / 1440)}d ago")
      else:
          lines.append(f"**{name}** -- never done, OVERDUE")
    if not lines:
      await context.send("No tracked tasks. Use `!list` to see log-only tasks.")
      return
    await context.send("\n".join(lines))

  @commands.command(name="list")
  async def list_tasks(self, context):
    """
    Show all tasks, both tracked and log-only.
    
    Args:
      context: Discord message context, passed automatically.
      
    Returns:
      None. Sends a list of all tasks to the Discord channel.
    """
    
    rows = db.execute("SELECT name, remind_after_minutes, remind_hour FROM tasks").fetchall()
    
    if not rows:
      await context.send("Nothing tracked or logged yet.")
      return
    
    lines = []
    for name, minutes, hour in rows:
      if minutes is not None:
        if hour is not None:
          lines.append(f"[track] {name} -- every {minutes}min at {hour}:00")
        else:
          lines.append(f"[track] {name} -- every {minutes}min")
      else:
        lines.append(f"[log] {name} -- log only")

    await context.send("\n".join(lines))
  
  @commands.command()
  async def snooze(self, context, name=None, duration=None):
    """
    Delay a task's reminder at a specified duration

    Args:
      context: Discord message context, passed automatically.
      name: Name of task to snooze
      duration (3h, 8d, 2w, 1mo): how long to snooze
    
    Returns: None. Sends confirmation message to the Discord channel instead.
    """
    if not name:
      await context.send("Usage: `!snooze <name> [duration]`\nExample: `!snooze vacuum 8h`")
      return
    
    row = db.execute("SELECT * FROM tasks WHERE name = ?", (name,)).fetchone()
    if not row:
      await context.send(f"{name} doesn't exist.")
      return
    
    if duration:
      try:
        snooze_min = parse_duration(duration)
      except ValueError as e:
        await context.send(str(e))
        return
    else:
      snooze_min = 480 #8 hours
    
    snooze_until = datetime.now() + timedelta(minutes=snooze_min)
    db.execute(
      "INSERT INTO log (task_name, logged_at) VALUES (?, ?)",
      (name, snooze_until.isoformat())
    )
    db.commit()
    await context.send(f"Snoozed {name}. Won't ping you until {snooze_until.strftime('%I:%M %p')}")

  @tasks.loop(hours=3)
  async def check_reminders(self):
    """
    Background loop that checks for overdue tasks and sends reminders.
    Runs every minute. Respects remind_hour if set.
    
    Args:
      None.
      
    Returns:
      None. Sends reminder messages to the appropriate Discord channels.
    """
    now = datetime.now()
    #print(f"checking reminders at {now}")
    rows = db.execute("""
      SELECT t.name, t.remind_after_minutes, t.channel_id, t.remind_hour, MAX(l.logged_at) as last_done
      FROM tasks t
      LEFT JOIN logs l ON t.name = l.task_name
      WHERE t.remind_after_minutes IS NOT NULL
      GROUP BY t.name
    """).fetchall()

    for name, minutes, channel_id, remind_hour, last_done in rows:
      #print(f"  {name}: minutes={minutes}, remind_hour={remind_hour}, last_done={last_done}")
      if remind_hour is not None and now.hour != remind_hour:
        print(f"  Skipping {name} -- wrong hour")
        continue
      if last_done:
        ago = (now - datetime.fromisoformat(last_done)).total_seconds() / 60
        #print(f"  {name}: ago={ago} minutes")
        if ago < minutes:
          continue
      channel = self.bot.get_channel(channel_id)
      if channel:
        await channel.send(f"Hey! It's been a while since you **{name}**. Go do it.")
  
  @check_reminders.before_loop
  async def before_check_reminders(self):
    """
    Wait for the bot to be fully connected before starting the reminder loop.
    
    Args:
      None.
      
    Returns:
      None.
    """
    await self.bot.wait_until_ready()
  
async def setup(bot):
  await bot.add_cog(Tracking(bot))
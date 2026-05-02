import asyncio
from discord.ext import commands
from db import db
from datetime import datetime

active_timers = {}


class Focus(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def focus(self, context, label="general", minutes: int = 25):
    """
    Start a focus session with an optional label and duration.

    Args:
      context: Discord message context, passed automatically.
      label: What you're focusing on (e.g. "homework").
      minutes: Duration in minutes. Defaults to 25.

    Returns:
      None. Sends a confirmation and later a notification.
    """
    user_id = context.author.id

    if user_id in active_timers:
      active_timers[user_id]["task"].cancel()
      await self.end_session(user_id)

    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'focus', ?, ?)",
      (user_id, label, datetime.now().isoformat())
    )
    db.commit()

    await context.reply(f"Focusing on **{label}** -- {minutes} min. Go!")

    async def notify():
      await asyncio.sleep(minutes * 60)
      await self.end_session(user_id)
      del active_timers[user_id]
      await context.reply(f"{context.author.mention} Focus done! Worked on **{label}** for {minutes} min.")

    active_timers[user_id] = {"task": self.bot.loop.create_task(notify())}

  @commands.command(name="break")
  async def take_break(self, context, minutes: int = 5):
    """
    Start a break session.

    Args:
      context: Discord message context, passed automatically.
      minutes: Duration in minutes. Defaults to 5.

    Returns:
      None. Sends a confirmation and later a notification.
    """
    user_id = context.author.id

    if user_id in active_timers:
      active_timers[user_id]["task"].cancel()
      await self.end_session(user_id)

    db.execute(
      "INSERT INTO sessions (user_id, type, label, started_at) VALUES (?, 'break', 'break', ?)",
      (user_id, datetime.now().isoformat())
    )
    db.commit()

    await context.reply(f"Break -- {minutes} min. Relax!")

    async def notify():
      await asyncio.sleep(minutes * 60)
      await self.end_session(user_id)
      del active_timers[user_id]
      await context.reply(f"{context.author.mention} Break over! Use `!focus <task>` to go again.")

    active_timers[user_id] = {"task": self.bot.loop.create_task(notify())}

  @commands.command()
  async def stop(self, context):
    """
    End the current focus or break session early.

    Args:
      context: Discord message context, passed automatically.

    Returns:
      None. Sends a confirmation message.
    """
    user_id = context.author.id

    if user_id in active_timers:
      active_timers[user_id]["task"].cancel()
      await self.end_session(user_id)
      del active_timers[user_id]
      await context.reply("Session ended.")
    else:
      await context.reply("No active session.")

  @commands.command()
  async def sessions(self, context):
    """
    Show recent focus and break entries for the user.

    Args:
      context: Discord message context, passed automatically.

    Returns:
      None. Sends a list of recent sessions.
    """
    rows = db.execute("""
      SELECT type, label, started_at, ended_at
      FROM sessions WHERE user_id = ?
      ORDER BY started_at DESC LIMIT 15
    """, (context.author.id,)).fetchall()

    if not rows:
      await context.reply("No sessions yet.")
      return

    lines = []
    for stype, label, start, end in rows:
      tag = "[F]" if stype == "focus" else "[B]"
      dt = datetime.fromisoformat(start)
      unix = int(dt.timestamp())
      if end:
        mins = round((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60)
        lines.append(f"{tag} **{label}** -- {mins} min (<t:{unix}:F>)")
      else:
        lines.append(f"{tag} **{label}** -- in progress (<t:{unix}:F>)")
    await context.reply("\n".join(lines))

  @commands.command()
  async def stats(self, context):
    """
    Show focus vs break totals and breakdown by task for the user.

    Args:
      context: Discord message context, passed automatically.

    Returns:
      None. Sends stats summary.
    """
    rows = db.execute("""
      SELECT type, label, started_at, ended_at
      FROM sessions
      WHERE user_id = ? AND ended_at IS NOT NULL
    """, (context.author.id,)).fetchall()

    if not rows:
      await context.reply("No completed sessions yet.")
      return

    focus_total = 0
    break_total = 0
    focus_by_label = {}

    for stype, label, start, end in rows:
      mins = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60
      if stype == "focus":
        focus_total += mins
        focus_by_label[label] = focus_by_label.get(label, 0) + mins
      else:
        break_total += mins

    total = focus_total + break_total
    focus_pct = round(focus_total / total * 100) if total > 0 else 0
    focus_count = sum(1 for r in rows if r[0] == "focus")
    break_count = sum(1 for r in rows if r[0] == "break")

    lines = [
      f"**Focus:** {round(focus_total)} min across {focus_count} sessions",
      f"**Breaks:** {round(break_total)} min across {break_count} sessions",
      f"**Ratio:** {focus_pct}% focus / {100 - focus_pct}% break",
      "",
      "**By task:**",
    ]
    for label, mins in sorted(focus_by_label.items(), key=lambda x: -x[1]):
      lines.append(f"  **{label}** -- {round(mins)} min")
    await context.reply("\n".join(lines))

  async def end_session(self, user_id):
    """
    Mark the current session as ended in the database.

    Args:
      user_id: Discord user ID.

    Returns:
      None.
    """
    db.execute(
      "UPDATE sessions SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
      (datetime.now().isoformat(), user_id)
    )
    db.commit()

  @commands.Cog.listener()
  async def on_message(self, message):
    """
    Auto-reply when someone mentions a user who is currently focusing.

    Args:
      message: Discord message object, passed automatically.

    Returns:
      None. Sends a reply if the mentioned user is focusing.
    """
    if message.author == self.bot.user:
      return

    for user in message.mentions:
      if user.id in active_timers:
        label = db.execute(
          "SELECT label FROM sessions WHERE user_id = ? AND ended_at IS NULL",
          (user.id,)
        ).fetchone()
        task = f" on **{label[0]}**" if label else ""
        await message.channel.send(
          f"{user.display_name} is focusing{task}. They'll get back to you!"
        )


async def setup(bot):
  await bot.add_cog(Focus(bot))
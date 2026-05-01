import re
import random
from discord.ext import commands
from db import db
from datetime import datetime

LECTURE_MESSAGES = [
  "What's the excuse this time? I'm not having it.",
  "Another day of building bad habits 😊",
  "You say to yourself now, 'I'll do it tmr,' but it will keep piling up.",
  "Getting closer and closer to academic probation 😊",
  "Hmmm...This isn't something Jared would do tbh",
]


class Skips(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def skip(self, context, name=None):
    """
    Log a skipped activity and get roasted for it.
    If the name contains a 3-digit number, assumes it's a lecture
    and adds lecture-specific roasts.

    Args:
      context: Discord message context, passed automatically.
      name: Name of what was skipped (e.g. "cmput261", "gym").

    Returns:
      None. Sends a roast message to the Discord channel.
    """
    if not name:
      await context.reply("Usage: `!skip <name>`\nExample: `!skip cmput261` or `!skip gym`")
      return

    db.execute(
      "INSERT INTO skips (class_name, user_id, skipped_at) VALUES (?, ?, ?)",
      (name, context.author.id, datetime.now().isoformat())
    )
    db.commit()

    count = db.execute(
      "SELECT COUNT(*) FROM skips WHERE class_name = ? AND user_id = ?",
      (name, context.author.id)
    ).fetchone()[0]

    custom = db.execute("SELECT message FROM roasts").fetchall()
    all_messages = []
    for r in custom:
      all_messages.append(r[0])

    has_course_number = re.search(r'\d{3}', name)
    if has_course_number:
      for msg in LECTURE_MESSAGES:
        all_messages.append(msg)

    msg = random.choice(all_messages).format(count=count, name=name)
    await context.reply(msg)

  @commands.command()
  async def skips(self, context, name=None):
    """
    Show skip history for a specific item or the shame board for all.

    Args:
      context: Discord message context, passed automatically.
      name: Optional name. If provided, shows all skip dates.
            If not, shows total skips per item.

    Returns:
      None. Sends skip history or shame board to the Discord channel.
    """
    if name:
      rows = db.execute(
        "SELECT skipped_at FROM skips WHERE class_name = ? AND user_id = ? ORDER BY skipped_at DESC",
        (name, context.author.id)
      ).fetchall()
      if not rows:
        await context.reply(f"No skips for {name}. Good.")
        return
      lines = [f"{name} -- {len(rows)} skip(s):"]
      for i, (ts,) in enumerate(rows, 1):
        dt = datetime.fromisoformat(ts)
        lines.append(f"`{i}.` {dt.strftime('%B %d, %Y at %-I:%M %p')}")
      await context.reply("\n".join(lines))
    else:
      rows = db.execute(
        "SELECT class_name, COUNT(*) as c FROM skips WHERE user_id = ? GROUP BY class_name ORDER BY c DESC",
        (context.author.id,)
      ).fetchall()
      if not rows:
        await context.reply("No skips. Proud of you.")
        return
      lines = ["**Skip count:**"]
      for name, count in rows:
        lines.append(f"  {name} -- {count}")
      await context.reply("\n".join(lines))

  @commands.command()
  async def addroast(self, context, *, message=None):
    """
    Add a custom roast message for skipping.
    Use {count} and {name} as placeholders.

    Args:
      context: Discord message context, passed automatically.
      message: The roast message to add.

    Returns:
      None. Sends a confirmation message.
    """
    if not message:
      await context.reply(
        "Usage: `!addroast <message>`\n"
        "Use `{count}` for skip count and `{name}` for what was skipped.\n"
        "Example: `!addroast {count} skips in {name}? Impressive failure.`"
      )
      return

    db.execute("INSERT INTO roasts (message) VALUES (?)", (message,))
    db.commit()
    await context.reply("Roast added.")

  @commands.command()
  async def listroasts(self, context):
    """
    Show all custom roast messages with their numbers.

    Args:
      context: Discord message context, passed automatically.

    Returns:
      None. Sends a numbered list of custom roasts.
    """
    rows = db.execute("SELECT rowid, message FROM roasts").fetchall()
    if not rows:
      await context.reply("No custom roasts yet. Use `!addroast` to add one.")
      return

    lines = ["**Custom roasts:**"]
    for i, (rowid, msg) in enumerate(rows, 1):
      lines.append(f"`{i}.` {msg}")
    await context.reply("\n".join(lines))

  @commands.command()
  async def editroast(self, context, num=None, *, message=None):
    """
    Edit a custom roast message by its number.

    Args:
      context: Discord message context, passed automatically.
      num: Roast number from !listroasts.
      message: New roast message.

    Returns:
      None. Sends a confirmation or error message.
    """
    if not num or not message:
      await context.reply(
        "Usage: `!editroast <number> <new message>`\n"
        "Use `!listroasts` to see numbers."
      )
      return

    try:
      num = int(num)
    except ValueError:
      await context.reply("Number must be a number.")
      return

    rows = db.execute("SELECT rowid FROM roasts").fetchall()
    if not rows or num < 1 or num > len(rows):
      await context.reply("Invalid number. Use `!listroasts` to check.")
      return

    rowid = rows[num - 1][0]
    db.execute("UPDATE roasts SET message = ? WHERE rowid = ?", (message, rowid))
    db.commit()
    await context.reply(f"Roast {num} updated.")

  @commands.command()
  async def deleteroast(self, context, num=None):
    """
    Delete a custom roast message by its number.

    Args:
      context: Discord message context, passed automatically.
      num: Roast number from !listroasts.

    Returns:
      None. Sends a confirmation or error message.
    """
    if not num:
      await context.reply(
        "Usage: `!deleteroast <number>`\n"
        "Use `!listroasts` to see numbers."
      )
      return

    try:
      num = int(num)
    except ValueError:
      await context.reply("Number must be a number.")
      return

    rows = db.execute("SELECT rowid FROM roasts").fetchall()
    if not rows or num < 1 or num > len(rows):
      await context.reply("Invalid number. Use `!listroasts` to check.")
      return

    rowid = rows[num - 1][0]
    db.execute("DELETE FROM roasts WHERE rowid = ?", (rowid,))
    db.commit()
    await context.reply(f"Roast {num} deleted.")


async def setup(bot):
  await bot.add_cog(Skips(bot))
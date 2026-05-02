import re
import random
from discord.ext import commands
from db import db
from datetime import datetime
from helpers import send_chunked, check_name

LECTURE_MESSAGES = [
  "What's the excuse this time? I'm not having it.",
  "Another day of building bad habits 😊",
  "You say to yourself now, 'I'll do it tmr,' but it will keep piling up.",
  "Getting closer and closer to academic probation 😊",
  "Hmmm...This isn't something Jared would do tbh",
  "another F incoming!",
  "You wanna email the Dean again begging? If yes, keep skipping",
]

DEFAULT_ROASTS = [
  "That's {count} skip(s) for {name}. You're building a habit. Careful...",
  "You stink.",
  "You said you wouldn't skip {name} again. You lied.",
  "Nobody's impressed by {count} skip(s) for {name}.",
  "Your ancestors are shaking their heads at you rn.",
  "That's {count}. But who's counting? Oh wait, I am.",
]


class Skips(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  def seed_defaults(self, guild_id):
    """
    Seed default roast messages for a server if it has none.

    Args:
      guild_id: Discord server ID.

    Returns:
      None.
    """
    count = db.execute("SELECT COUNT(*) FROM roasts WHERE guild_id = ?", (guild_id,)).fetchone()[0]
    if count == 0:
      for msg in DEFAULT_ROASTS:
        db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (msg, guild_id))
      db.commit()

  @commands.command()
  @commands.cooldown(3, 10, commands.BucketType.user)
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
    
    if not await check_name(context, name):
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

    self.seed_defaults(context.guild.id)
    custom = db.execute("SELECT message FROM roasts WHERE guild_id = ?", (context.guild.id,)).fetchall()
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
        unix = int(dt.timestamp())
        lines.append(f"`{i}.` <t:{unix}:F>")
      await send_chunked(context, "\n".join(lines))
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
      await send_chunked(context, "\n".join(lines))

  @commands.command()
  @commands.cooldown(3, 10, commands.BucketType.user)
  async def addroast(self, context, *, message=None):
    """
    Add a custom roast message for this server.
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

    db.execute("INSERT INTO roasts (message, guild_id) VALUES (?, ?)", (message, context.guild.id))
    db.commit()
    await context.reply("Roast added.")

  @commands.command()
  async def listroasts(self, context):
    """
    Show all roast messages for this server with their numbers.

    Args:
      context: Discord message context, passed automatically.

    Returns:
      None. Sends a numbered list of roasts.
    """
    self.seed_defaults(context.guild.id)
    rows = db.execute("SELECT rowid, message FROM roasts WHERE guild_id = ?", (context.guild.id,)).fetchall()
    if not rows:
      await context.reply("No roasts yet. Use `!addroast` to add one.")
      return

    lines = ["**Roasts:**"]
    for i, (rowid, msg) in enumerate(rows, 1):
      lines.append(f"`{i}.` {msg}")
    await send_chunked(context, "\n".join(lines))

  @commands.command()
  async def editroast(self, context, num=None, *, message=None):
    """
    Edit a roast message by its number for this server.

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

    rows = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (context.guild.id,)).fetchall()
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
    Delete a roast message by its number for this server.

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

    rows = db.execute("SELECT rowid FROM roasts WHERE guild_id = ?", (context.guild.id,)).fetchall()
    if not rows or num < 1 or num > len(rows):
      await context.reply("Invalid number. Use `!listroasts` to check.")
      return

    if len(rows) <= 1:
      await context.reply("Can't delete the last roast. Edit it instead.")
      return

    rowid = rows[num - 1][0]
    db.execute("DELETE FROM roasts WHERE rowid = ?", (rowid,))
    db.commit()
    await context.reply(f"Roast {num} deleted.")


async def setup(bot):
  await bot.add_cog(Skips(bot))
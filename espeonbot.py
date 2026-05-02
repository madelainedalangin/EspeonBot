import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")


@bot.command()
async def help(context):
    await context.reply(
    "**-- Tracking --**\n"
    "`!track <name> <duration> [hour]` -- track + pester\n"
    "`!edit <name> <duration> [hour]` -- change duration/hour (use `-` to skip)\n"
    "`!untrack <name>` -- stop tracking\n"
    "`!status` -- see what's overdue\n"
    "`!list` -- see all tasks\n"
    "`!snooze <name> [duration]` -- delay reminders (default 8h)\n\n"
    "**-- Logging --**\n"
    "`!log <name>` -- log something (no reminders)\n"
    "`!done <name>` -- log a tracked task (resets countdown)\n"
    "`!history <name>` -- see all entries\n"
    "`!delete <name> <entry_number>` -- delete an entry\n\n"
    "**-- Skips --**\n"
    "`!skip <name>` -- log a skip (and get roasted)\n"
    "`!skips` -- see skip counts for everything\n"
    "`!skips <name>` -- see skip dates for one thing\n\n"
    "**-- Roasts --**\n"
    "`!addroast <message>` -- add a custom roast\n"
    "`!listroasts` -- see all custom roasts\n"
    "`!editroast <number> <new message>` -- edit a roast\n"
    "`!deleteroast <number>` -- delete a roast\n\n"
    "**-- Focus --**\n"
    "`!focus <label> [duration]` -- start focus (default 25mi)\n"
    "`!break [duration]` -- take a break (default 5mi)\n"
    "`!stop` -- end current session\n"
    "`!sessions` -- see recent focus/break entries\n"
    "`!stats` -- focus vs break totals\n\n"
    "**Durations:** `5mi`, `3h`, `7d`, `2w`, `6mo`, or combined like `1h30mi`\n"
    "**Hour:** 0-23 (24hr format). 9 = 9 AM, 14 = 2 PM, 21 = 9 PM"
    )

@bot.event
async def cooldown_error_msg(context, error):
    if isinstance(error, commands.CommandOnCooldown):
        await context.reply(f" Bruh slow down 🤨. Try again in {round(error.retry_after)}s.")
    else:
        raise error

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.tracking")
    await bot.load_extension("cogs.logging_tasks")
    await bot.load_extension("cogs.focus")
    await bot.load_extension("cogs.skips")

@bot.event
async def on_ready():
    print(f"Bot running as {bot.user}")

bot.run(TOKEN)
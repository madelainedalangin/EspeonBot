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
async def help(ctx):
    await ctx.send(
        "**-- Tracking --**\n"
        "`!track <name> <duration> [hour]` -- track + pester\n"
        "`!edit <name> <duration> [hour]` -- change duration/hour (use `-` to skip)\n"
        "`!untrack <name>` -- stop tracking\n"
        "`!status` -- see what's overdue\n"
        "`!list` -- see all tasks\n"
        "`!snooze <name> [duration]` -- delay reminders (default 8h)\n\n"
        "**Durations:** `5mi`, `3h`, `7d`, `2w`, `6mo`\n"
        "**Hour:** 0-23 (24hr format). Reminders only fire at that hour.\n\n"
        "**-- Logging --**\n"
        "`!log <name>` -- log something (no reminders)\n"
        "`!done <name>` -- log a tracked task (resets countdown)\n"
        "`!history <name>` -- see all entries\n"
        "`!delete <name> <entry_number>` -- delete an entry\n\n"
        )


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.tracking")
    await bot.load_extension("cogs.logging_tasks")
    #await bot.load_extension("cogs.focus")
    #await bot.load_extension("cogs.skips")

@bot.event
async def on_ready():
    print(f"Bot running as {bot.user}")

bot.run(TOKEN)
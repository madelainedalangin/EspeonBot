import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")


@bot.command()
async def help(ctx):
    await ctx.send("Hello Madelaine!")


@bot.event
async def on_ready():
    print(f"Bot running as {bot.user}")


bot.run(TOKEN)
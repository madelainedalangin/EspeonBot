from discord.ext import commands, tasks
from db import db
from helpers import parse_duration
from datetime import datetime, timedelta

class Logging(commands.cog):
  
  def __init__(self, bot):
    self.bot = bot
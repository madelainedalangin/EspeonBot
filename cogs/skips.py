import random
from discord.ext import commands
from db import db
from datetime import datetime

MEAN_MESSAGES_TO_MYSELF = [
  "Academic comeback? LMAO you funny",
  "you have time to play ow but not go to class? are you serious?",
  "putting yourself in debt just to stay in bed you bet",
  "What's the excuse this time? lame. still lame. Nope. I'm not having it.",
  "Another day of learning nothing and building bad habits :3",
  "You say to yourself now, 'I'll grind it this weekend' but you will not be",
  "Are you dying? There's still time just get up for heck sake",
  "Getting closer and closer to academic probation :D",
  "Hmmm...This isn't something Jared would do tbh"
]

class Skips(commands.Cog):
  
  def __injt__(self, bot):
    self.bot = bot
  
  @commands.command()
  async def skip(self, context, name=None):
    pass
  
  @commands.command()
  async def skips(self, context, name=None):
    pass
  
async def setup(bot):
  await bot.add_cog(Skips(bot))
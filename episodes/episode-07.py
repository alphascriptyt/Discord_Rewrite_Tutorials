import aiofiles
import discord
from discord.ext import commands

intents = discord.Intents.default() # get the default intents where members and presence are disabled
intents.members = True # enable the members intent
bot = commands.Bot(command_prefix = "£", intents=intents)

@bot.event
async def on_ready():
    print("Your bot is ready.")

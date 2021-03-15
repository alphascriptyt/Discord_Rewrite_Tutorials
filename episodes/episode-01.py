import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "£")

@bot.event
async def on_ready():
    print("Your bot is ready.")

@bot.command()
async def hello(ctx):
    await ctx.channel.send("Hi! " + str(ctx.author.mention))

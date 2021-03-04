# THE DM_ALL WAS REMOVED DUE TO DISCORD PY API RESTRICTIONS AND RULES

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "£")

@bot.event
async def on_ready():
    print("Your bot is ready.")

@bot.command()
async def dm(ctx, user_id=None, *, args=None):
    if user_id != None and args != None:
        try:
            target = await bot.fetch_user(user_id)
            await target.send(args)

            await ctx.channel.send("'" + args + "' sent to: " + target.name)

        except:
            await ctx.channel.send("Couldn't dm the given user.")
        

    else:
        await ctx.channel.send("You didn't provide a user's id and/or a message.")

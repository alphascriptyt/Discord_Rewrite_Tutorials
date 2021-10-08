import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "£")

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready.")

@bot.command()
async def convo(ctx):
    msg = await ctx.channel.send("Yo! Are you going to subscribe? (YES/NO)")
    await msg.add_reaction(u"\u2705")
    await msg.add_reaction(u"\U0001F6AB")

    try:
        reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in [u"\u2705", u"\U0001F6AB"], timeout=30.0)


    except asyncio.TimeoutError:
        await ctx.channel.send("Ouch you ignored me.")

    else:
        if reaction.emoji == u"\u2705":
            await ctx.channel.send("You're an alpha male!")

        else:
            await ctx.channel.send("Ouch, that's just harsh...")    

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "£", help_command=None)

async def get_help_embed():
    em = discord.Embed(title="Help!", description="", color=discord.Color.green())
    em.description += f"**{bot.command_prefix}set_reaction <role> <msg> <emoji>** : Sets the reaction role for the given role, message and emoji.\n"
    em.description += f"**{bot.command_prefix}set_welcome_channel <new-channel> <welcome-message>** : Sets the guild's welcome channel to the given channel and the welcome message to the given message.\n"
    em.set_footer(text="Thanks for using me!", icon_url=bot.user.avatar_url)
    return em

@bot.event
async def on_ready():
    print("Your bot is ready.")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        em = await get_help_embed()
        await message.channel.send(embed=em)

    await bot.process_commands(message)

@bot.command()
async def help(ctx):
    em = await get_help_embed()
    await ctx.send(embed=em)

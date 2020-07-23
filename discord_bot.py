import discord
from discord.ext import commands

bot = commands.Bot(command_prefix = "£")

class BotData:
    def __init__(self):
        self.welcome_channel = None
        self.goodbye_channel = None

botdata = BotData()

#bot events
@bot.event
async def on_ready():
    print("Your bot is ready.")
    bot.reaction_roles = []

@bot.event
async def on_raw_reaction_add(payload):
    for role, msg, emoji in bot.reaction_roles:
        if msg.id == payload.message_id and emoji == payload.emoji.name:
            await payload.member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    for role, msg, emoji in bot.reaction_roles:
        if msg.id == payload.message_id and emoji == payload.emoji:
            await bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(role)

@bot.event
async def on_member_join(member):
    if botdata.welcome_channel != None:
        await botdata.welcome_channel.send(f"Welcome! {member.mention}")

    else:
        print("Welcome channel was not set.")

@bot.event
async def on_member_remove(member):
    if botdata.goodbye_channel != None:
        await botdata.goodbye_channel.send(f"Goodbye! {member.mention}")

    else:
        print("Goodbye channel was not set.")

#bot commands
@bot.command()
async def set_reaction(ctx, role: discord.Role, msg: discord.Message, emoji):
    # Optional for custom emojis, not tested.
    if emoji.isdigit():
        try:
            emoji = bot.get_emoji(emoji).name
        except:
            emoji = None
    
    if role != None and msg != None and emoji != None:
        await msg.add_reaction(emoji)
        bot.reaction_roles.append((role, msg, emoji))
        
    else:
        await ctx.send("Invalid arguments.")

@bot.command()
async def set_welcome_channel(ctx, channel_name=None):
    if channel_name != None:
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.welcome_channel = channel
                await ctx.channel.send(f"Welcome channel has been set to: {channel.name}")
                await channel.send("This is the new welcome channel!")

    else:
        await ctx.channel.send("You didn't include the name of a welcome channel.")

@bot.command()
async def set_goodbye_channel(ctx, channel_name=None):
    if channel_name != None:
        for channel in ctx.guild.channels:
            if channel.name == channel_name:
                botdata.goodbye_channel = channel
                await ctx.channel.send(f"Goodbye channel has been set to: {channel.name}")
                await channel.send("This is the new goodbye channel!")

    else:
        await ctx.channel.send("You didn't include the name of a goodbye channel.")

@bot.command()
async def hello(ctx):
    channel = ctx.channel
    await channel.send("Hi! " + str(ctx.author.mention))

@bot.command()
async def ping(ctx, arg=None, option=1):
    if arg == "pong":
        await ctx.channel.send("You've already ponged yourself!")

    else:
        await ctx.channel.send(str(ctx.author.mention) + " Pong!")

    if option == 1:
        await ctx.channel.send("You chose option one!")

    else:
        await ctx.channel.send("You chose option " + str(option))

@bot.command()
async def repeat(ctx, *, arg=None):
    if arg == None:
        await ctx.channel.send("You forgot to include an argument.")
    else:
        await ctx.channel.send(str(ctx.author.mention) + " " + str(arg))

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

@bot.command()
async def dm_all(ctx, *, args=None):
    if args != None:
        members = ctx.guild.members
        for member in members:
            try:
                await member.send(args)
                print("'" + args + "' sent to: " + member.name)

            except:
                print("Couldn't send '" + args + "' to: " + member.name)

    else:
        await ctx.channel.send("A message was not provided.")

bot.run("token")

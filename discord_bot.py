import asyncio
import math
import aiosqlite
import aiofiles
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "£", intents=intents)

#bot events
@bot.event
async def on_ready():
    bot.reaction_roles = []
    bot.welcome_channels = {} # store like {guild_id : (channel_id, message)}
    bot.goodbye_channels = {}
    bot.sniped_messages = {}
    bot.ticket_configs = {}
    bot.warnings = {}
    bot.multiplier = 1
    
    async with aiosqlite.connect("guilddata.db") as db:
        for guild in bot.guilds:
            async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
                pass

            await db.execute(f"CREATE TABLE IF NOT EXISTS guild_{guild.id} (user_id int PRIMARY KEY, exp int)")


        bot.warnings[guild.id] = {}
    
    for file in ["reaction_roles.txt", "welcome_channels.txt", "goodbye_channels.txt", "ticket_configs.txt"]:
        async with aiofiles.open(file, mode="a") as temp:
            pass

    async with aiofiles.open("reaction_roles.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.reaction_roles.append((int(data[0]), int(data[1]), data[2].strip("\n")))

    async with aiofiles.open("welcome_channels.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.welcome_channels[int(data[0])] = (int(data[1]), " ".join(data[2:]).strip("\n"))

    async with aiofiles.open("goodbye_channels.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.goodbye_channels[int(data[0])] = (int(data[1]), " ".join(data[2:]).strip("\n"))

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        lines = await file.readlines()
        for line in lines:
            data = line.split(" ")
            bot.ticket_configs[int(data[0])] = [int(data[1]), int(data[2]), int(data[3])]

    for guild in bot.guilds:
        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(admin_id, reason)]]
                    
    print("Your bot is ready.")

@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}
    async with aiosqlite.connect("guilddata.db") as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS guild_{guild.id} (user_id int PRIMARY KEY, exp int)")

@bot.event
async def on_guild_remove(guild):
    async with aiosqlite.connect("guilddata.db") as db:
        await db.execute(f"DROP TABLE IF EXISTS guild_{guild.id}")

@bot.event
async def on_raw_reaction_add(payload):
    for role_id, msg_id, emoji in bot.reaction_roles:
        if msg_id == payload.message_id and emoji == str(payload.emoji.name.encode("utf-8")):
            await payload.member.add_roles(bot.get_guild(payload.guild_id).get_role(role_id))
            return

    if payload.member.id != bot.user.id and str(payload.emoji) == u"\U0001F3AB":
        msg_id, channel_id, category_id = bot.ticket_configs[payload.guild_id]

        if payload.message_id == msg_id:
            guild = bot.get_guild(payload.guild_id)

            for category in guild.categories:
                if category.id == category_id:
                    break

            channel = guild.get_channel(channel_id)

            ticket_num = 1 if len(category.channels) == 0 else int(category.channels[-1].name.split("-")[1]) + 1
            ticket_channel = await category.create_text_channel(f"ticket {ticket_num}", topic=f"A channel for ticket number {ticket_num}.", permission_synced=True)

            await ticket_channel.set_permissions(payload.member, read_messages=True, send_messages=True)

            message = await channel.fetch_message(msg_id)
            await message.remove_reaction(payload.emoji, payload.member)

            await ticket_channel.send(f"{payload.member.mention} Thank you for creating a ticket! Use **'-close'** to close your ticket.")

            try:
                await bot.wait_for("message", check=lambda m: m.channel == ticket_channel and m.author == payload.member and m.content == "-close", timeout=3600)

            except asyncio.TimeoutError:
                await ticket_channel.delete()

            else:
                await ticket_channel.delete()

@bot.event
async def on_raw_reaction_remove(payload):
    for role_id, msg_id, emoji in bot.reaction_roles:
        if msg_id == payload.message_id and emoji == str(payload.emoji.name.encode("utf-8")):
            guild = bot.get_guild(payload.guild_id)
            await guild.get_member(payload.user_id).remove_roles(guild.get_role(role_id))
            return

@bot.event
async def on_member_join(member):
    for guild_id in bot.welcome_channels:
        if guild_id == member.guild.id:
            channel_id, message = bot.welcome_channels[guild_id]
            await bot.get_guild(guild_id).get_channel(channel_id).send(f"{message} {member.mention}")
            return

@bot.event
async def on_member_remove(member):
    for guild_id in bot.goodbye_channels:
        if guild_id == member.guild.id:
            channel_id, message = bot.goodbye_channels[guild_id]
            await bot.get_guild(guild_id).get_channel(channel_id).send(f"{message} {member.mention}")
            return

@bot.event
async def on_message_delete(message):
    bot.sniped_messages[message.guild.id] = (message.content, message.author, message.channel.name, message.created_at)

@bot.event
async def on_message(message):
    if not message.author.bot:
        async with aiosqlite.connect("guilddata.db") as db:
            cursor = await db.execute(f"INSERT OR IGNORE INTO guild_{message.guild.id} (user_id, exp) VALUES (?,?)", (message.author.id, 1)) 

            if cursor.rowcount == 0:
                await db.execute(f"UPDATE guild_{message.guild.id} SET exp = exp + 1 WHERE user_id = ?", (message.author.id,))
                cur = await db.execute(f"SELECT exp FROM guild_{message.guild.id} WHERE user_id = ?", (message.author.id,))
                data = await cur.fetchone()
                exp = data[0]
                lvl = math.sqrt(exp) / bot.multiplier
            
                if lvl.is_integer():
                    await message.channel.send(f"{message.author.mention} well done! You're now level: {int(lvl)}.")

            await db.commit()

    await bot.process_commands(message)

#bot commands
@bot.command()
async def stats(ctx, member: discord.Member=None):
    if member is None: member = ctx.author

    # get user exp
    async with aiosqlite.connect("guilddata.db") as db:
        async with db.execute(f"SELECT exp FROM guild_{ctx.guild.id} WHERE user_id = ?", (member.id,)) as cursor:
            data = await cursor.fetchone()
            exp = data[0]

        # calculate rank
        async with db.execute(f"SELECT exp FROM guild_{ctx.guild.id}") as cursor:
            rank = 1
            async for value in cursor:
                if exp < value[0]:
                    rank += 1

    lvl = int(math.sqrt(exp)//bot.multiplier)

    current_lvl_exp = (bot.multiplier*(lvl))**2
    next_lvl_exp = (bot.multiplier*((lvl+1)))**2

    lvl_percentage = ((exp-current_lvl_exp) / (next_lvl_exp-current_lvl_exp)) * 100

    embed = discord.Embed(title=f"Stats for {member.name}", colour=discord.Colour.gold())
    embed.add_field(name="Level", value=str(lvl))
    embed.add_field(name="Exp", value=f"{exp}/{next_lvl_exp}")
    embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}")
    embed.add_field(name="Level Progress", value=f"{round(lvl_percentage, 2)}%")

    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx): 
    buttons = {}
    for i in range(1, 6):
        buttons[f"{i}\N{COMBINING ENCLOSING KEYCAP}"] = i # only show first 5 pages

    previous_page = 0
    current = 1
    index = 1
    entries_per_page = 10

    embed = discord.Embed(title=f"Leaderboard Page {current}", description="", colour=discord.Colour.gold())
    msg = await ctx.send(embed=embed)

    for button in buttons:
        await msg.add_reaction(button)

    async with aiosqlite.connect("guilddata.db") as db:
        while True:
            if current != previous_page:
                embed.title = f"Leaderboard Page {current}"
                embed.description = ""

                async with db.execute(f"SELECT * FROM guild_{ctx.guild.id} ORDER BY exp DESC LIMIT ? OFFSET ?", (entries_per_page, entries_per_page*(current-1),)) as cursor:
                    index = entries_per_page*(current-1)

                    async for entry in cursor:
                        index += 1
                        member_id, exp = entry
                        member = ctx.guild.get_member(member_id)
                        embed.description += f"{index}) {member.mention} : {exp}\n"

                    await msg.edit(embed=embed)

            try:
                reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)

            except asyncio.TimeoutError:
                return await msg.clear_reactions()

            else:
                previous_page = current
                await msg.remove_reaction(reaction.emoji, ctx.author)
                current = buttons[reaction.emoji]
                
@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")
    
    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
    try:
        i = 1
        for admin_id, reason in bot.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError: # no warnings
        await ctx.send("This user has no warnings.")
        
@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member=None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")
        
    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    except KeyError:
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{member.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")

@bot.command()
async def configure_ticket(ctx, msg: discord.Message=None, category: discord.CategoryChannel=None):
    if msg is None or category is None:
        await ctx.channel.send("Failed to configure the ticket as an argument was not given or was invalid.")
        return

    bot.ticket_configs[ctx.guild.id] = [msg.id, msg.channel.id, category.id] # this resets the configuration

    async with aiofiles.open("ticket_configs.txt", mode="r") as file:
        data = await file.readlines()

    async with aiofiles.open("ticket_configs.txt", mode="w") as file:
        await file.write(f"{ctx.guild.id} {msg.id} {msg.channel.id} {category.id}\n")

        for line in data:
            if int(line.split(" ")[0]) != ctx.guild.id:
                await file.write(line)
                

    await msg.add_reaction(u"\U0001F3AB")
    await ctx.channel.send("Succesfully configured the ticket system.")

@bot.command()
async def ticket_config(ctx):
    try:
        msg_id, channel_id, category_id = bot.ticket_configs[ctx.guild.id]

    except KeyError:
        await ctx.channel.send("You have not configured the ticket system yet.")

    else:
        embed = discord.Embed(title="Ticket System Configurations", color=discord.Color.green())
        embed.description = f"**Reaction Message ID** : {msg_id}\n"
        embed.description += f"**Ticket Category ID** : {category_id}\n\n"

        await ctx.channel.send(embed=embed)
        
@bot.command()
async def snipe(ctx):
    try:
        contents, author, channel_name, time = bot.sniped_messages[ctx.guild.id]
        
    except:
        await ctx.channel.send("Couldn't find a message to snipe!")
        return

    embed = discord.Embed(description=contents, color=discord.Color.purple(), timestamp=time)
    embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar_url)
    embed.set_footer(text=f"Deleted in : #{channel_name}")

    await ctx.channel.send(embed=embed)
    
@bot.command()
async def set_reaction(ctx, role: discord.Role=None, msg: discord.Message=None, emoji=None):
    if role != None and msg != None and emoji != None:
        await msg.add_reaction(emoji)
        bot.reaction_roles.append((role.id, msg.id, str(emoji.encode("utf-8"))))
        
        async with aiofiles.open("reaction_roles.txt", mode="a") as file:
            emoji_utf = emoji.encode("utf-8")
            await file.write(f"{role.id} {msg.id} {emoji_utf}\n")

        await ctx.channel.send("Reaction has been set.")
        
    else:
        await ctx.send("Invalid arguments.")

@bot.command()
async def set_welcome_channel(ctx, new_channel: discord.TextChannel=None, *, message=None):
    if new_channel != None and message != None:
        for channel in ctx.guild.channels:
            if channel == new_channel:
                bot.welcome_channels[ctx.guild.id] = (channel.id, message)
                await ctx.channel.send(f"Welcome channel has been set to: {channel.name} with the message {message}")
                await channel.send("This is the new welcome channel!")
                
                async with aiofiles.open("welcome_channels.txt", mode="a") as file:
                    await file.write(f"{ctx.guild.id} {new_channel.id} {message}\n")

                return

        await ctx.channel.send("Couldn't find the given channel.")

    else:
        await ctx.channel.send("You didn't include the name of a welcome channel or a welcome message.")

@bot.command()
async def set_goodbye_channel(ctx, new_channel: discord.TextChannel=None, *, message=None):
    if new_channel != None and message != None:
        for channel in ctx.guild.channels:
            if channel == new_channel:
                bot.goodbye_channels[ctx.guild.id] = (channel.id, message)
                await ctx.channel.send(f"Goodbye channel has been set to: {channel.name} with the message {message}")
                await channel.send("This is the new goodbye channel!")
                
                async with aiofiles.open("goodbye_channels.txt", mode="a") as file:
                    await file.write(f"{ctx.guild.id} {new_channel.id} {message}\n")

                return

        await ctx.channel.send("Couldn't find the given channel.")

    else:
        await ctx.channel.send("You didn't include the name of a goodbye channel or a goodbye message.")

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

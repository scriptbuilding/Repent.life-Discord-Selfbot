import os
import discord
from discord.ext import commands
import asyncio
import json
import aiohttp
import time
import random

command_history = []
start_time = time.time()

with open("token.json", "r") as f:
    config = json.load(f)
    TOKEN = config["token"]

bot = commands.Bot(command_prefix=",", self_bot=True)

targets = {}
auto_replies = {}
message_logs = {}
autoping_task = None
chatpack_target = None
chatpack_index = 0
chatpack_active = False

def print_banner(last_command=None):
    global command_history
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[91m" + r"""
         ██▀███  ▓█████  ██▓███  ▓█████  ███▄    █ ▄▄▄█████▓
        ▓██ ▒ ██▒▓█   ▀ ▓██░  ██▒▓█   ▀  ██ ▀█   █ ▓  ██▒ ▓▒
        ▓██ ░▄█ ▒▒███   ▓██░ ██▓▒▒███   ▓██  ▀█ ██▒▒ ▓██░ ▒░
        ▒██▀▀█▄  ▒▓█  ▄ ▒██▄█▓▒ ▒▒▓█  ▄ ▓██▒  ▐▌██▒░ ▓██▓ ░
        ░██▓ ▒██▒░▒████▒▒██▒ ░  ░░▒████▒▒██░   ▓██░  ▒██▒ ░
        ░ ▒▓ ░▒▓░░░ ▒░ ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒░   ▒ ▒   ▒ ░░
          ░▒ ░ ▒░ ░ ░  ░░▒ ░      ░ ░  ░░ ░░   ░ ▒░    ░
          ░░   ░    ░   ░░          ░      ░   ░ ░   ░
           ░        ░  ░            ░  ░         ░
""" + "\033[0m")
    print("""
                          Hidden • Truth
             lightweight | reactive | full-featured
    ------------------------------------------------------
    """)
    if last_command:
        command_history.append(last_command)
    if command_history:
        print("Last commands:")
        for cmd in command_history[-10:]:
            print(f"- {cmd}")

@bot.event
async def on_ready():
    if os.name == 'nt':
        os.system(f"title Welcome @ {bot.user} ")
    else:
        print(f"\33]0;Welcome @ {bot.user} • discord.py-self\a", end='', flush=True)
    print_banner()

@bot.event
async def on_message(message):
    if message.author.id == bot.user.id and message.content.startswith(","):
        print_banner(last_command=message.content)
        await bot.process_commands(message)
        await asyncio.sleep(3)
        try:
            await message.delete()
        except Exception:
            pass
        return
    if message.author.id in targets:
        for emoji in targets[message.author.id]:
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                print(f"Failed to react with {emoji}: {e}")
    global chatpack_target, chatpack_active
    if message.author.id == chatpack_target and chatpack_active:
        try:
            with open("pack.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            if lines:
                line = random.choice(lines)
                await message.channel.send(f"{line} {message.author.mention}")
            else:
                await message.channel.send("⚠️ pack.txt is empty.")
                chatpack_target = None
                chatpack_active = False
        except Exception as e:
            print(f"chatpack error: {e}")
    for trigger, reply in auto_replies.items():
        if trigger in message.content.lower():
            await message.channel.send(reply)
            break
    message_logs.setdefault(message.channel.id, []).append((message.author.id, message.content))
    await bot.process_commands(message)

@bot.command()
async def react(ctx, user: discord.User, *emojis):
    if not emojis:
        await ctx.send("Please provide at least one emoji.")
        return
    if user.id not in targets:
        targets[user.id] = []
    targets[user.id].extend(emojis)
    await ctx.send(f"Will react to user {user} with {', '.join(emojis)}")

@bot.command()
async def stop(ctx, user: discord.User):
    if user.id in targets:
        targets.pop(user.id)
        await ctx.send(f"Stopped reacting to user {user}")
    else:
        await ctx.send(f"Not reacting to user {user}")

@bot.command()
async def stop2(ctx, user: discord.User, emoji):
    if user.id in targets and emoji in targets[user.id]:
        targets[user.id].remove(emoji)
        await ctx.send(f"Removed {emoji} from {user}")
    else:
        await ctx.send(f"{emoji} not found for {user}")

@bot.command()
async def clear(ctx):
    targets.clear()
    await ctx.send("Cleared all reaction targets")

@bot.command()
async def spam(ctx, *, args):
    try:
        parts = args.rsplit(maxsplit=1)
        message = parts[0]
        count = int(parts[1])
        if count > 30:
            await ctx.send("Max is 30 messages.")
            return
        for i in range(count):
            await ctx.send(message)
            if i % 2 == 0:
                await asyncio.sleep(0.2)
    except:
        await ctx.send("Usage: ,spam <message> <count>")

@bot.command()
async def removereply(ctx, trigger: str):
    if trigger.lower() in auto_replies:
        auto_replies.pop(trigger.lower())
        await ctx.send(f"Removed auto-reply trigger '{trigger}'")
    else:
        await ctx.send(f"No such trigger '{trigger}'")

@bot.command()
async def showlogs(ctx, channel_id: int = None):
    channel_id = channel_id or ctx.channel.id
    logs = message_logs.get(channel_id, [])
    if not logs:
        await ctx.send("No logs for this channel")
        return
    msg = "\n".join(f"<@{uid}>: {content}" for uid, content in logs[-20:])
    await ctx.send(f"Last 20 messages:\n{msg}")

@bot.command()
async def edit(ctx, msg_id: int, *, content):
    try:
        msg = await ctx.channel.fetch_message(msg_id)
        if msg.author.id == bot.user.id:
            await msg.edit(content=content)
            await ctx.send("Message edited.", delete_after=5)
        else:
            await ctx.send("I can only edit my own messages.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command()
async def p(ctx, amount: int):
    if isinstance(ctx.channel, discord.DMChannel):
        def is_me(m):
            return m.author.id == bot.user.id
        deleted_count = 0
        async for message in ctx.channel.history(limit=amount):
            if is_me(message):
                try:
                    await message.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"Failed to delete message: {e}")
        await ctx.send(f"Deleted {deleted_count} dms.", delete_after=5)
    else:
        def is_me(m):
            return m.author.id == bot.user.id
        deleted = await ctx.channel.purge(limit=amount, check=is_me)
        await ctx.send(f"```Deleted {len(deleted)} messages.```", delete_after=5)

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
async def embed(ctx, *, content):
    try:
        parts = content.split("|", 1)
        if len(parts) < 2:
            raise ValueError("Missing '|' separator between title and description.")
        title, description = parts
        embed = discord.Embed(title=title.strip(), description=description.strip(), color=0x00FFFF)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Usage: ,embed <title> | <description>\nError: {e}")

@bot.command()
async def dm(ctx, user: discord.User, *, message):
    try:
        await user.send(message)
        await ctx.send(f"Sent DM to {user}")
    except Exception as e:
        await ctx.send(f"Failed to send DM: {e}")

@bot.command()
async def copy(ctx, msg_id: int):
    try:
        msg = await ctx.channel.fetch_message(msg_id)
        await ctx.send(f"{msg.author.display_name} said: {msg.content}")
    except Exception as e:
        await ctx.send(f"Error copying message: {e}")

@bot.command()
async def autoping(ctx, user: discord.User, interval: int):
    global autoping_task
    if autoping_task and not autoping_task.done():
        autoping_task.cancel()
    async def ping_loop():
        while True:
            await ctx.send(f"{user.mention}")
            await asyncio.sleep(interval)
    autoping_task = asyncio.create_task(ping_loop())
    await ctx.send(f"Started auto pinging {user} every {interval} seconds.")

@bot.command()
async def chatpack(ctx, user: discord.User):
    global chatpack_target, chatpack_index, chatpack_active
    chatpack_target = user.id
    chatpack_index = 0
    chatpack_active = True
    await ctx.send(f"flaming that bitch ass nigga {user.mention}")

@bot.command()
async def end(ctx):
    global chatpack_active, chatpack_target
    chatpack_active = False
    chatpack_target = None
    await ctx.send("oh aight then")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def stopautoping(ctx):
    global autoping_task
    if autoping_task and not autoping_task.done():
        autoping_task.cancel()
        await ctx.send("Stopped auto pinging.")
    else:
        await ctx.send("No active auto ping.")

@bot.command()
async def status(ctx, *, text):
    try:
        await bot.change_presence(activity=discord.CustomActivity(name=text))
        await ctx.send(f"Status updated to: {text}")
    except Exception as e:
        await ctx.send(f"Failed to update status: {e}")

@bot.command()
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await bot.close()

@bot.command()
async def massdm(ctx, *, arg):
    try:
        relationships = await bot.http.get_relationships()
        if not relationships:
            await ctx.send("No relationships found.")
            return
        print(f"Found {len(relationships)} relationships.")
        friends = []
        for rel in relationships:
            if rel['type'] == 1:
                user_id = int(rel['id'])
                user = bot.get_user(user_id)
                if not user:
                    user = User(state=bot._connection, data={'id': user_id})
                friends.append(user)
        if not friends:
            await ctx.send("You have no friends to DM.")
            return
        await ctx.send(f"Sending to {len(friends)} friends. bypassing Captchas + avoiding ratelimits since 1998")
        count = 0
        for friend in friends:
            try:
                await friend.send(arg)
                count += 1
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to DM {friend}: {e}")
        await ctx.send(f"Done! Successfully sent DMs to {count}/{len(friends)} friends.")
    except Exception as e:
        await ctx.send(f"Error during massdm: {e}")

@bot.command(aliases=['ui'])
async def userinfo(ctx, user: discord.User = None):
    user = user or ctx.author
    try:
        member = await ctx.guild.fetch_member(user.id)
    except:
        member = None
    created_str = user.created_at.strftime('%m/%d/%Y, %I:%M %p')
    created_ago = (discord.utils.utcnow() - user.created_at).days
    joined_str = "N/A"
    joined_ago = "N/A"
    if member and member.joined_at:
        joined_str = member.joined_at.strftime('%m/%d/%Y, %I:%M %p')
        joined_ago = (discord.utils.utcnow() - member.joined_at).days
    roles = []
    if member:
        roles = [role.name for role in member.roles if role.name != "@everyone"]
    key_perms = []
    if member:
        perms = member.guild_permissions
        if perms.kick_members: key_perms.append("Kick Members")
        if perms.ban_members: key_perms.append("Ban Members")
        if perms.manage_messages: key_perms.append("Manage Messages")
        if perms.manage_nicknames: key_perms.append("Manage Nicknames")
    text = f"""
ini
[User Info]
Name      : {user.name}
ID        : {user.id}

[Account Dates]
Created   : {created_str} ({created_ago} days ago)
Joined    : {joined_str} ({joined_ago} days ago)

[Roles ({len(roles)})]
{", ".join(roles) if roles else "None"}

[Key Permissions]
{", ".join(key_perms) if key_perms else "None"}
"""
    await ctx.send(text)

@bot.command()
async def setpfp(ctx, url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("Failed to download image.")
            data = await resp.read()
            try:
                await bot.user.edit(avatar=data)
                await ctx.send("✅ Profile picture updated.")
            except Exception as e:
                await ctx.send(f"❌ Failed to update profile picture: {e}")

@bot.command()
async def stream(ctx, *, text: str):
    streaming = discord.Streaming(name=text, url="https://repent.life")
    try:
        await bot.change_presence(activity=streaming)
        await ctx.send(f"✅ Status set to streaming: **{text}**")
    except Exception as e:
        await ctx.send(f"❌ Failed to set status: {e}")

@bot.command()
async def uptime(ctx):
    seconds = time.time() - start_time
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    await ctx.send(f"⏱ Uptime: {hours}h {minutes}m {secs}s")

@bot.command(aliases=['av'])
async def avatar(ctx, user: discord.User = None):
    user = user or ctx.author
    await ctx.send(f"🖼 Avatar for {user}: {user.avatar.url if user.avatar else 'No avatar.'}")

@bot.command()
async def pp(ctx, user: str):
    try:
        user_id = int(user.strip("<@!>"))
    except ValueError:
        await ctx.send("Invalid user ID or mention.")
        return
    member = ctx.guild.get_member(user_id)
    if not member:
        await ctx.send("User not found in this server.")
        return
    percent = random.randint(0, 100)
    length = percent // 10
    shaft = "=" * length
    await ctx.send(f"{member.mention}'s pp size:\n8{shaft}D ({percent}%)")



@bot.command()
async def cmds(ctx):
    help_text = """```
Repent.life
lightweight • reactive • full-featured
━━━━━━━━━━━━━━━━━━━━━━━━━━

Reaction
- react <user_id> <emoji>
- stop <user_id>
- clear

Messaging
- spam <msg> <count>
- chatpack <user>
- massdm <msg> or <filename>
- say <msg>
- embed <title> | <desc>
- dm <user_id > <msg>
- loop <msg> <count> <delay>
- type <msg>
- emoji <emoji>

Control
- edit <msg_id> <new>
- end (will end chatpack)
- delete <msg_id>
- purge <amount>
- copy <msg_id>
- vanish

Logs & Auto
- removereply <trigger>
- showlogs [channel_id]

Utilities
- autoping <user_id > <interval>
- stopautoping
- status <text>
- ping
- userinfo [user]
- serverinfo
- cloak <new_name>
- hack <user>

━━━━━━━━━━━━━━━━━━━━━━━━━━
repent.life
```"""
    msg = await ctx.send(help_text)
    await asyncio.sleep(10)
    try:
        await msg.delete()
    except:
        pass

bot.run(TOKEN)

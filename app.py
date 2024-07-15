#https://discord.com/oauth2/authorize?client_id=1255362560128188446&permissions=139855211584&scope=bot
import os
import asyncio
import datetime
#from datetime import *
import json
import discord
from discord.ext import commands, tasks
from utilities import *
import dateparser
from reset import reset
#https://discordpy.readthedocs.io/en/stable/intro.html

client = commands.Bot(command_prefix="/", intents=discord.Intents.all())


@tasks.loop(minutes=1)
async def sendReminder():
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    servers = await get_serverinfo()
    global_info = await get_globalinfo()
    #print(f'Sending reminders: {now}')
    await send_console_message(client, f'Sending reminders: {now}')
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)
            #print(f'user_id: {user_id}')

            index = 0
            while index < len(user["sessions"]):
                session = user["sessions"][index]

                scheduled_time = dateparser.parse(session["datetime"])
                scheduled_time_display = await utc_to_current(scheduled_time, user["timezone"])
                scheduled_time_display = scheduled_time_display.strftime("%a, %b %d, %Y, %I:%M %p")
                #Convert from utc to current***************************************

                reminder_time = datetime.timedelta(minutes=session["reminder_ahead_mins"])
                duration_time = datetime.timedelta(minutes=session["duration_mins"])
                if scheduled_time + duration_time < now:
                    #print(f'Deleting session and adding numbers to their profile.')
                    points = global_info["points_per_min"] * session["attended_mins"]
                    user["points"] += points
                    month = await get_current_month(user)
                    if month == "":
                        month = await get_default_month()
                        user["months"].append(month)
                        month["date"] = now.strftime("%b %Y")

                    if session["attended_mins"] > 0:
                        month["completed_sessions"] += 1
                    else:
                        month["failed_sessions"] += 1

                    month["mins_studied"] += session["attended_mins"]
                    month["mins_scheduled"] += session["duration_mins"]
                    user["sessions"].remove(session)

                    await save_userinfo(user_id, user)

                    await dm(client, user_id, f'Your study session at {scheduled_time_display} which was scheduled for {session["duration_mins"]} mins in server {client.get_guild(int(session["server_id"])).name} ({session["server_id"]}) has ended. You studied for {session["attended_mins"]} mins and gained {points} points.')
                elif scheduled_time - reminder_time <= now and bool(session["reminder"]):
                    #print(f'Reminder for {user_id}: {scheduled_time}')
                    await send_message(client, session["server_id"], f'<@{user_id}> is starting a {session["duration_mins"]} min study session in {session["reminder_ahead_mins"]} mins (at {scheduled_time_display}).')
                    session["reminder"] = False
                    await save_userinfo(user_id, user)
                    index += 1
                elif scheduled_time <= now:
                    #print(f'Getting voicestate info')
                    server = client.get_guild(int(session["server_id"])) #Cannot get voicestate info using client.fetch_guild(id)
                    member = server.get_member(int(user_id)) #Cannot get voicestate info using server.fetch_member(id)
                    channel = member.voice.channel
                    
                    if channel is not None:
                        current_vc_id = channel.id
                        if current_vc_id in servers[str(session["server_id"])]["study_vc_ids"]:
                            session["attended_mins"] += 1
                            await save_userinfo(user_id, user)

                    index += 1
                else:
                    break


@tasks.loop(time=[datetime.time(hour=12, minute=0, tzinfo=datetime.timezone.utc)])
async def dailyReset():
    global_info = await get_globalinfo()

    if global_info["new_day_delay"] > 0:
        global_info["new_day_delay"] -= 1
        await save_globalinfo(global_info)
    else:
        await reset(client)

@client.event
async def on_ready():
    await client.tree.sync()
    print("Bot is connected to Discord")
    dailyReset.start()
    sendReminder.start()


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            print(f"{filename[:-3]} is loaded!")


async def main():
    async with client:
        await load()

        with open("config.json", "r") as file:
            config = json.load(file)

        await client.start(config['token'])

asyncio.run(main())


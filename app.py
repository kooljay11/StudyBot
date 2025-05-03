#https://discord.com/oauth2/authorize?client_id=1255362560128188446&permissions=139855211584&scope=bot
import os
import asyncio
import datetime
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
    #servers = await get_serverinfo()
    global_info = await get_globalinfo()
    last_bot_active = dateparser.parse(global_info["last_active"])
    time_lost = now - last_bot_active
    if time_lost >= datetime.timedelta(minutes=2):
        bot_was_down = True
        print(f'time_lost: {time_lost}')
    else:
        bot_was_down = False
        print(f'time_interval: {time_lost}')

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

                reminder_time = datetime.timedelta(minutes=session["reminder_ahead_mins"])
                duration_time = datetime.timedelta(minutes=session["duration_mins"])

                # 1) If the bot was last active before the scheduled time and the current time is before the scheduled time then skip
                # 2) If the bot was last active before the scheduled time and the current time is before the scheduled endpoint then calculate time missed as current time - scheduled time
                # 3) If the bot was last active before the scheduled time and the current time is after the scheduled endpoint then time missed = session duration
                # 4) If the bot was last active after the scheduled time, but before the scheduled endpoint, and the current time is before the scheduled endpoint then calculate time missed as current time - time bot last active
                # 5) If the bot was last active after the scheduled time, but before the scheduled endpoint, and the current time is after the scheduled endpoint then calculate time missed as scheduled endpoint - time bot last active
                # 6) If the bot was last active after the scheduled endpoint (and the current time is after the scheduled endpoint) then skip

                # If the current session has ended then check if there was any missed time and end the session if possible
                if scheduled_time + duration_time < now:
                    if bot_was_down:
                        time_missed = datetime.timedelta(minutes=0)

                        # If the bot was last active before the scheduled start time and the session has ended (the current time is beyond the scheduled endpoint)
                        # Then set the time missed to the duration of the scheduled session
                        if last_bot_active <= scheduled_time:
                            time_missed = duration_time
                        # Otherwise if the bot was last active after the scheduled start time, but before the scheduled endpoint, and the session has ended (the current time is beyond the scheduled endpoint)
                        # Then set the tiime missed to scheduled endpoint - time bot last active
                        elif last_bot_active < scheduled_time + duration_time:
                            time_missed = scheduled_time + duration_time - last_bot_active

                        # For any time missed due to the bot being down, reduce the scheduled duration and move up the start time to compensate, allowing for the end point of the session to remain the same
                        session["duration_mins"] -= time_missed.total_seconds() // 60
                        scheduled_time += time_missed
                        session["datetime"] = scheduled_time.strftime("%a, %b %d, %Y, %I:%M %p")

                    is_studying = await user_is_studying(client, session["server_id"], int(user_id))

                    try:
                        next_session_scheduled_time = dateparser.parse(user["sessions"][index+1]["datetime"])
                        time_left = next_session_scheduled_time - now
                    except:
                        time_left = datetime.timedelta(minutes=1)

                    # If still in vc then keep the session going unless the next session is coming up
                    if is_studying and time_left > datetime.timedelta(minutes=0):
                        session["attended_mins"] += 1
                        session["duration_mins"] += 1
                        await save_userinfo(user_id, user)
                        index += 1
                        continue

                    #print(f'Deleting session and adding numbers to their profile.')
                    points = global_info["points_per_min"] * session["attended_mins"]
                    user["points"] += points
                    month = await get_current_month(user)

                    # Session is considered completed if some minutes were completed in it
                    if session["attended_mins"] > 0:
                        month["completed_sessions"] += 1
                    # Otherwise will be considered failed if no minutes were completed in it and the bot was NOT down
                    elif not bot_was_down:
                        month["failed_sessions"] += 1

                    month["mins_studied"] += session["attended_mins"]
                    month["mins_scheduled"] += session["duration_mins"]
                    month["sessions"].append(session)
                    user["sessions"].remove(session)

                    await save_userinfo(user_id, user)
                    message = f'Your study session at {scheduled_time_display} which was scheduled for {session["duration_mins"]} mins in server {client.get_guild(int(session["server_id"])).name} ({session["server_id"]}) has ended. '

                    if session["description"] != "":
                        message += f'\nDescription: {session["description"]}.'

                    message += f'\nYou studied for {session["attended_mins"]} mins and gained {points} points.'

                    await dm(client, user_id, message)
                # If the session is about to start then send a reminder to the user that its going to start
                elif scheduled_time - reminder_time <= now and bool(session["reminder"]):
                    #print(f'Reminder for {user_id}: {scheduled_time}')
                    await send_message(client, session["server_id"], f'<@{user_id}> is starting a {session["duration_mins"]} min study session in {session["reminder_ahead_mins"]} mins (at {scheduled_time_display}).')
                    session["reminder"] = False
                    await save_userinfo(user_id, user)

                    # Copied from the "elif scheduled_time <= now:" section below
                    if bot_was_down:
                        time_missed = datetime.timedelta(minutes=0)
                        # If the bot was last active before the scheduled time and the current time is before the scheduled endpoint then calculate time missed as current time - scheduled time
                        if last_bot_active <= scheduled_time:
                            time_missed = now - scheduled_time
                        # If the bot was last active after the scheduled time, but before the scheduled endpoint, and the current time is before the scheduled endpoint then calculate time missed as current time - time bot last active
                        elif last_bot_active < scheduled_time + duration_time:
                            time_missed = now - last_bot_active

                        # For any time missed due to the bot being down, reduce the scheduled duration and move up the start time to compensate, allowing for the end point of the session to remain the same
                        session["duration_mins"] -= time_missed.total_seconds() // 60
                        scheduled_time += time_missed
                        session["datetime"] = scheduled_time.strftime("%a, %b %d, %Y, %I:%M %p")
                        await save_userinfo(user_id, user)

                    index += 1
                # If the session is in progress then keep track of how many minutes the user is in the study vc
                elif scheduled_time <= now:
                    if bot_was_down:
                        time_missed = datetime.timedelta(minutes=0)
                        # If the bot was last active before the scheduled time and the current time is before the scheduled endpoint then calculate time missed as current time - scheduled time
                        if last_bot_active <= scheduled_time:
                            time_missed = now - scheduled_time
                        # If the bot was last active after the scheduled time, but before the scheduled endpoint, and the current time is before the scheduled endpoint then calculate time missed as current time - time bot last active
                        elif last_bot_active < scheduled_time + duration_time:
                            time_missed = now - last_bot_active

                        # For any time missed due to the bot being down, reduce the scheduled duration and move up the start time to compensate, allowing for the end point of the session to remain the same
                        session["duration_mins"] -= time_missed.total_seconds() // 60
                        scheduled_time += time_missed
                        session["datetime"] = scheduled_time.strftime("%a, %b %d, %Y, %I:%M %p")
                        await save_userinfo(user_id, user)

                    #print(f'Getting voicestate info')
                    is_studying = await user_is_studying(client, session["server_id"], int(user_id))
                    if is_studying:
                        session["attended_mins"] += 1
                        await save_userinfo(user_id, user)

                    index += 1
                else:
                    break
    
    global_info["last_active"] = str(now)
    await save_globalinfo(global_info)


@tasks.loop(time=[datetime.time(hour=1, minute=0, tzinfo=datetime.timezone.utc)])
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

        config = await get_config()

        await client.start(config['token'])

asyncio.run(main())


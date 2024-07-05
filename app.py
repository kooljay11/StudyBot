#https://discord.com/oauth2/authorize?client_id=1255362560128188446&permissions=139855211584&scope=bot
import os
import asyncio
import datetime
import json
import discord
from discord.ext import commands, tasks
from utilities import *
from reset import reset
#https://discordpy.readthedocs.io/en/stable/intro.html

client = commands.Bot(command_prefix="/", intents=discord.Intents.all())


@tasks.loop(minutes=1)
async def sendReminder():
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)
            now = datetime.now()

            for task in user["task_list"]:
                if task["reminder_ahead"] + task["datetime"] > now:
                    break
                else:
                    await send_message(client, task["server_id"], f'<@{user_id}> is starting a {task["duration"]} min study session in {task["reminder_ahead"]} mins (at {task["datetime"]}).')


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


import json
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta as td
import dateparser

async def current_to_utc(current: dt, user_tz: int):
    delta = td(hours=user_tz)
    utc = current - delta

    return utc

async def utc_to_current(utc: dt, user_tz: int):
    delta = td(hours=user_tz)
    current = utc + delta

    return current

async def get_default_session():
    with open("./default_data/session.json", "r") as file:
        session = json.load(file)
    
    return session

# Cannot name get_userinfo due to no function overloading in Python
async def get_userinfo_by_nick(self_user, target):
    if str(target).isnumeric():
        target_user_id = target
    else:
        target_user_id = self_user["nicknames"].get(target, 0)
    
    user = await get_userinfo(target_user_id)
    
    return user

async def get_userinfo(user_id):
    with open(f"./data/user_data/{user_id}.json", "r") as file:
        user = json.load(file)

    # Get the default userinfo
    default_user = await get_default_userinfo()

    for attr, value in default_user.items():
        if user.get(attr, None) is None:
            user[attr] = default_user[attr]
            await save_userinfo(user_id, user)
    
    return user

async def save_userinfo(user_id, user):
    with open(f"./data/user_data/{user_id}.json", "w") as file:
        json.dump(user, file, indent=4)

async def get_default_userinfo():
    with open("./default_data/user.json", "r") as file:
        user = json.load(file)
    
    return user

async def get_config():
    with open("config.json", "r") as file:
        config = json.load(file)
    
    return config

async def get_globalinfo():
    with open("./data/global_info.json", "r") as file:
        global_info = json.load(file)
    
    return global_info

async def save_globalinfo(global_info):
    with open("./data/global_info.json", "w") as file:
        json.dump(global_info, file, indent=4)

async def get_default_server():
    with open("./default_data/server.json", "r") as file:
        server = json.load(file)
    
    return server

async def get_serverinfo():
    with open("./data/servers.json", "r") as file:
        server_info = json.load(file)
    
    return server_info

async def save_serverinfo(server_info):
    with open("./data/servers.json", "w") as file:
        json.dump(server_info, file, indent=4)

async def create_user_profile(user_id):
    default_user = await get_default_userinfo()

    await save_userinfo(user_id, default_user)

    return default_user

async def get_nickname(self_user, target_id):
    for nickname, id in self_user["nicknames"].items():
        if id == target_id:
            return nickname
    
    return ""

async def get_id_nickname(client, self_user, target: str):
    if target.isnumeric():
        target_id = int(target)
        target_name = await get_nickname(self_user, target_id)
        if target_name == "":
            target_name = str(await client.fetch_user(target_id))
    else:
        target_id = int(self_user["nicknames"][target])
        target_name = target
    
    return {"id": target_id, "name": target_name}

async def print_month(month):
    global_info = await get_globalinfo()

    if month["rank"] != "":
        emoji = global_info["monthly_emojis"][month["rank"]]
    else:
        emoji = ""
    
    total_sessions = month["completed_sessions"]+month["failed_sessions"]

    if total_sessions != 0:
        percent_sessions = round(month["completed_sessions"]/total_sessions * 100)
    else:
        percent_sessions = 'NA'

    if month["mins_scheduled"] != 0:
        percent_hours = round(month["mins_studied"]/month["mins_scheduled"] * 100)
    else:
        percent_hours = 'NA'

    message = f'**{month["date"]}** {emoji} '
    #print(f'message post calc: {message}')
    #message += f'\nRank: {current_month["rank"]}'
    message += f'\nCompleted sessions: {month["completed_sessions"]} ({percent_sessions}%)'
    message += f'\nFailed sessions: {month["failed_sessions"]}'

    #message += f'\n% sessions completed: {percent_sessions}%'

    message += f'\nTime studied: {int(month["mins_studied"]/60)} hrs {month["mins_studied"]%60} mins ({percent_hours}%)'
    message += f'\nTime scheduled: {int(month["mins_scheduled"]/60)} hrs {month["mins_scheduled"]%60} mins'

    #message += f'\n% hours studied: {percent_hours}%'

    return message

async def get_current_month(user):
    now = dt.now()
    date = now.strftime("%b %Y")

    current_month = ""

    for month in user["months"]:
        if month["date"] == date:
            current_month = month
            break
        
    if current_month == "":
        current_month = await get_default_month()
        user["months"].append(current_month)
        current_month["date"] = date
    
    return current_month

async def get_current_year(user):
    now = dt.now()
    year = now.strftime("%Y")

    current_year = []

    for month in user["months"]:
        if month["date"].find(year) > -1:
            current_year.append(month)
    
    return current_year

async def get_default_month():
    with open("./default_data/month.json", "r") as file:
        month = json.load(file)
    
    return month

async def send_message(client, server_id, message):
    try:
        server_info = await get_serverinfo()
        await send_channel_message(client, int(server_info[str(server_id)]["reminder_channel_id"]), message)
    except:
        #print(f'Server {server_id} not found. Message: {message}')
        await send_console_message(client, f'Server {server_id} not found. Message: {message}')
        return

async def send_channel_message(client, channel_id: int, message):
    try:
        channel = await client.fetch_channel(channel_id)

        if len(message) <= 2000:
            await channel.send(message)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    await channel.send(message_to_send)
                    message_to_send = message_fragments[x-1]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    await channel.send(message_to_send)
                else:
                    await channel.send('Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        #print(f'Channel {channel_id} not found. Message: {message}')
        await send_console_message(client, f'Channel {channel_id} not found. Message: {message}')
        return

async def send_console_message(client, message):
    try:
        global_info = await get_globalinfo()
    except:
        print(f'Console channel not set in global_info.json')

    await send_channel_message(client, global_info["console_channel_id"], message)

async def dm(client, user_id, message):
    try:
        user = await client.fetch_user(int(user_id))
        #user = await client.fetch_user(107886996365508608)
        if len(message) <= 2000:
            await user.send(message)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    await user.send(message_to_send)
                    message_to_send = message_fragments[x-1]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    await user.send(message_to_send)
                else:
                    await user.send('Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        print(f'{user_id} not found. Message: {message}')
        return

async def reply(client, interaction, message):
    try: 
        if len(message) <= 2000:
            await interaction.response.send_message(message)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            first_reply_sent = False
            channel = await client.fetch_channel(interaction.channel_id)
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x]) < 2000:
                    message_to_send += "\n" + message_fragments[x]
                else:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send)
                        first_reply_sent = True
                    else:
                        await channel.send(message_to_send)
                    message_to_send = message_fragments[x]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send)
                    else:
                        await channel.send(message_to_send)
                else:
                    await reply(interaction, 'Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        print(f'Unable to send message: {message}')

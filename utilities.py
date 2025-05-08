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

async def get_time_str(mins: int):
    r_mins = mins%60
    hrs = int(mins/60)

    if hrs > 0 and r_mins > 0:
        return f'{hrs} hrs {r_mins} mins'
    elif hrs > 0:
        return f'{hrs} hrs'
    elif r_mins > 0:
        return f'{r_mins} mins'

async def get_top_5_ranks(ranks):
    global_info = await get_globalinfo()
    emoji_list = list(global_info["monthly_emojis"].values())
    top_rank = emoji_list[len(global_info["monthly_rank"].keys())-1]
    #print(f'top_rank: {top_rank}')

    top_marks = True

    # If any of the top 5 ranks gained are not from the top rank, then only the top 5 will be counted
    for rank in ranks[:5]:
        if rank != top_rank:
            #print(f'ranks precull: {ranks}')
            ranks = ranks[:5]
            top_marks = False
            #print(f'ranks postcull: {ranks}')
            return ranks
        

    index = 0
    # Otherwise keep entries of the top rank in the list only
    if top_marks:
        while index < len(ranks):
            if ranks[index] != top_rank:
                ranks.pop(index)
            else:
                index += 1

        ranks = ranks[:index]

        blackbelt1 = top_rank
        blackbelt10 = emoji_list[len(global_info["monthly_rank"])]
        blackbelt100 = emoji_list[len(global_info["monthly_rank"])+1]
        base = 10

        while True:
            #print(f'ranks.count(blackbelt1): {ranks.count(blackbelt1)}')
            if ranks.count(blackbelt1) >= base:
                for a in range(base):
                    ranks.remove(blackbelt1)
                ranks.append(blackbelt10)
            elif ranks.count(blackbelt10) >= base:
                for a in range(base):
                    ranks.remove(blackbelt10)
                ranks.append(blackbelt100)
            else:
                ranks.sort(reverse=True)
                return ranks

#Takes a list of custom emojis for input
async def get_rank_value(ranks):
    global_info = await get_globalinfo()

    value = 0
    emojis_list = list(global_info["monthly_emojis"].values())
    number_of_base_ranks = len(global_info["monthly_rank"].values())

    #By default the lowest rank grants 0 score
    for rank in ranks:
        if rank in emojis_list[:number_of_base_ranks]:
            value += emojis_list.index(rank)
        elif rank == emojis_list[number_of_base_ranks]:
            value += (number_of_base_ranks - 1) * 10
        elif rank == emojis_list[number_of_base_ranks+1]:
            value += (number_of_base_ranks - 1) * 100

    return value

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
    message += f'\nPoints earned solo: {month["points_earned_solo"]}'
    message += f'\nPoints lost solo: {month["points_lost_solo"]} (rate: {global_info["%_missed_penalty"]})'

    # Get partner name
    if month["partner_name"] != "":
        partner_name = month["partner_name"]
    else:
        if month["partner_id"] != 0:
            partner_name = f"partner (id: {month["partner_id"]})"
        else:
            partner_name = "partner"

    message += f'\nPoints earned from {partner_name}: {month["points_earned_from_partner"]} (rate: {global_info["%_partner_earnings"]})'
    message += f'\nPoints lost because of {partner_name}: {month["points_penalized_by_partner"]} (rate: {global_info["%_partner_penalty"]})'

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

async def user_is_studying(client, server_id: int, user_id: int):
    servers = await get_serverinfo()
    server = client.get_guild(server_id) #Cannot get voicestate info using client.fetch_guild(id)
    member = server.get_member(user_id) #Cannot get voicestate info using server.fetch_member(id)
    voice_state = member.voice
    
    if voice_state is not None:
        current_vc_id = voice_state.channel.id
        if current_vc_id in servers[str(server_id)]["study_vc_ids"]:
            return True

    return False

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

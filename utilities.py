import json
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta as td
#import dateparser
import os

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

async def get_guildinfo(guild_name):
    with open(f"./data/guild_data/{guild_name}.json", "r") as file:
        guild = json.load(file)

    # Get the default guildinfo
    default_guild = await get_default_guildinfo()

    for attr, value in default_guild.items():
        if guild.get(attr, None) is None:
            guild[attr] = default_guild[attr]
            await save_guildinfo(guild_name, guild)
    
    return guild

async def save_guildinfo(guild_name, guild):
    with open(f"./data/guild_data/{guild_name}.json", "w") as file:
        json.dump(guild, file, indent=4)

async def get_default_guildinfo():
    with open("./default_data/guild.json", "r") as file:
        guild = json.load(file)
    
    return guild

async def get_perm_list_by_user_id(guild, user_id):
    perms = deepcopy(guild["perms"]["everyone"])

    # # Check if the user is the owner first
    # if user_id == guild["owner_id"]:
    #     perms += await get_perm_list_by_role(guild, "owner")
    # else:
    #     # Look for the user in each of the roles
    #     for role, user_list in guild["role_user_ids"].items():
    #         # If the user is in that role then get the perms for that role
    #         if user_id in user_list:
    #             perms += await get_perm_list_by_role(guild, role)
    
    # Get the user's role
    roles = await get_guild_roles(guild, user_id)
    #print(f'roles: {roles}')

    # Get the perms for each role they have
    for role in roles:
        perms += await get_perm_list_by_role(guild, role)
    #print(f'roles: {roles}')
    #print(f'perms: {perms}')
    
    # Remove all duplicates
    perms = list(set(perms))

    return perms

async def get_perm_list_by_role(guild, role):
    perms = deepcopy(guild["perms"][role])
    index = 0

    # If another role is mentioned in the perms then delete that entry and add that role's perms to the list
    while index < len(perms):
        for role in guild["perms"].keys():
            if perms[index] == role:
                perms.remove(perms[index])
                perms += await get_perm_list_by_role(guild, role)

                # Make sure the checker doesn't miss the first perm of the newly appended permlist
                index -= 1

        index += 1
    
    # If the perm starts with - then remove all perms that have the same name (allows for negative perms)
    index = 0
    while index < len(perms):
        if perms[index][0] == "-":
            perm_to_remove = perms[index][1:]
            perms.remove(perms[index])
            while perm_to_remove in perms:
                perms.remove(perm_to_remove)
            
            # Start the search over again because perms may have been removed before or after the index
            index = -1

        index += 1

    # Remove all duplicates
    perms = list(set(perms))

    return perms

async def get_guild_list():
    guild_list = []
            
    for filename in os.listdir("./data/guild_data"):
        if filename.endswith(".json"):
            target_guild_name = os.path.splitext(filename)[0]
            target_guild = await get_guildinfo(target_guild_name)

            guild_list.append((target_guild_name, target_guild["points_total"]))

    # Order the list (descending) according to the points total
    guild_list.sort(key=lambda x: x[1], reverse=True)

    return guild_list

async def get_guild_abbr_list():
    abbr_list = []
            
    for filename in os.listdir("./data/guild_data"):
        if filename.endswith(".json"):
            target_guild_name = os.path.splitext(filename)[0]
            target_guild = await get_guildinfo(target_guild_name)

            abbr_list.append(target_guild["abbreviation"])

    return abbr_list

async def get_guild_index(guild_name):
    guild_list = await get_guild_list()

    return [y[0] for y in guild_list].index(guild_name)

async def get_guild_leaderboard(client, user, guild):
    leaderboard = []

    #user_list = await get_formatted_user_list(client, user, list(guild["points_tracker"].items()))
    user_list = list(guild["points_tracker"].items())
    #print(f'user_list: {user_list}')
    index = 0

    for user_id, score in user_list:
        index += 1
        roles = await get_guild_roles(guild, user_id)
        #print(f'{user_id} roles: {", ".join(roles)}')
        try:
            roles.remove("member")
        except:
            print()
        rank = await get_guild_rank(score)
        #print(f'{user_id} rank: {rank}')
        user_name = (await get_id_nickname(client, user, user_id))["name"]
        msg = f'{index}) {rank} {user_name} (id: {user_id}) '
        #print(f'msg: {msg}')
        
        if roles:
            msg += f'[{", ".join(roles)}] '
        
        msg += f'--- {score}'
        leaderboard.append(msg)

    return leaderboard

async def get_guild_roles(guild, user_id):
    roles = []
    user_id = int(user_id)

    if user_id == guild["owner_id"]:
        roles.append("owner")
        #print(f'owner')
    #print(f'roles: {roles}')

    # Look for the user in each of the roles
    for role, user_list in guild["role_user_ids"].items():
        # If the user is in that role then add that role to the list
        if user_id in user_list:
            roles.append(role)

    return roles

async def remove_guild_roles(guild, user_id):
    roles = await get_guild_roles(guild, user_id)

    for role in roles:
        guild["role_user_ids"][role].remove(user_id)
    
    guild["all_member_ids"].remove(user_id)
    
    return

# Returns max for owner, 0 for non-member, 1 for member, increasing numbers for higher ppl
async def get_guild_user_role_value(guild, user_id):
    role_value = 0
    
    if user_id not in guild["all_member_ids"]:
        return role_value
    else:
        member_roles = await get_guild_roles(guild, user_id)
        roles = list(guild["perms"].keys())
        roles.reverse()

        for role in member_roles:
            # Get the reverse index of the role in the perms list
            new_role_value = roles.index(role)

            if new_role_value > role_value:
                role_value = new_role_value
    
    return role_value

# Gets the name of the role using it's value
async def get_guild_role_by_value(guild, role_value):
    if role_value == 0:
        return ""
    else:
        roles = list(guild["perms"].keys())
        roles.reverse()
        return roles[role_value]


async def get_guild_rank(score):
    global_info = await get_globalinfo()

    user_rank = ""

    # Give each user the guild rank that corresponds to the amount of points they've donated
    for rank, hours in global_info["all_time_rank"].items():
        #print(f"Checking to give {rank}")
        
        # If the user has more/equal hours required, give them the rank
        if score / 60 >= hours:
            user_rank = rank
        else:
            break
    
    if user_rank == "":
        return user_rank
    # Get the rank name and put the rank number in front of it
    else:
        rank_number = list(global_info["all_time_rank"].keys()).index(user_rank) + 1
        return f'{rank_number}{user_rank}'

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

async def create_user_profile(client, user_id):
    default_user = await get_default_userinfo()
    default_user["nicknames"][str(await client.fetch_user(user_id))] = user_id

    await save_userinfo(user_id, default_user)

    return default_user

async def get_nickname(self_user, target_id):
    for nickname, id in self_user["nicknames"].items():
        if id == target_id:
            return nickname
    
    return ""

async def get_id_nickname(client, self_user, target: str):
    #print(f'Getting id and nick for {target}')
    target = str(target)
    if target.isnumeric():
        #print(f'target: {target}')
        #print(f'int(target): {int(target)}')
        target_id = int(target)
        #print(f'target_id: {target_id}')
        target_name = await get_nickname(self_user, target_id)
        #print(f'target_name 1: {target_name}')
        if target_name == "":
            target_name = str(await client.fetch_user(target_id))
            #print(f'target_name 2: {target_name}')
    else:
        target_id = int(self_user["nicknames"][target])
        #print(f'target: {target}')
        target_name = target
    
    return {"id": target_id, "name": target_name}

# user_list is a list of tuples with the format (user_id, num)
# async def get_formatted_user_list(client, self_user, user_list):
#     formatted_user_list = []
#     for user_id, num in user_list:
#         formatted_user_list.append((((await get_id_nickname(client, self_user, user_id))["name"] + f' (id: {user_id})'), num))
    
#     return formatted_user_list

# user_list is a list of ids
async def get_formatted_user_list(client, self_user, user_list):
    formatted_user_list = []
    for user_id in user_list:
        formatted_user_list.append((await get_id_nickname(client, self_user, user_id))["name"] + f' (id: {user_id})')
    
    return formatted_user_list

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

async def get_prev_month(user):
    now = dt.now()
    # Change it to the first of the month
    target = now.replace(day=1)

    # Roll back 2 days
    target -= td(days=1)

    date = target.strftime("%b %Y")

    prev_month = ""

    for month in user["months"]:
        if month["date"] == date:
            prev_month = month
            break
        
    if prev_month == "":
        prev_month = await get_default_month()
        user["months"].append(prev_month)
        prev_month["date"] = date
    
    return prev_month

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

async def send_message(client, server_id, message, silent: bool = False):
    try:
        server_info = await get_serverinfo()
        await send_channel_message(client, int(server_info[str(server_id)]["reminder_channel_id"]), message, silent)
    except:
        #print(f'Server {server_id} not found. Message: {message}')
        await send_console_message(client, f'Server {server_id} not found. Message: {message}', silent)
        return

async def send_channel_message(client, channel_id: int, message, silent: bool = False):
    try:
        channel = await client.fetch_channel(channel_id)

        if len(message) <= 2000:
            await channel.send(message, silent = silent)
        else:
            new_message = deepcopy(message)
            message_fragments = new_message.split("\n")
            message_to_send = ""
            for x in range(len(message_fragments)):
                if len(message_to_send) + len(message_fragments[x-1]) < 2000:
                    message_to_send += "\n" + message_fragments[x-1]
                else:
                    await channel.send(message_to_send, silent = silent)
                    message_to_send = message_fragments[x-1]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    await channel.send(message_to_send, silent = silent)
                else:
                    await channel.send('Last message fragment too long to send. Ask developer to include more linebreaks in output.', silent = silent)
    except:
        #print(f'Channel {channel_id} not found. Message: {message}')
        await send_console_message(client, f'Channel {channel_id} not found. Message: {message}', silent)
        return

async def send_console_message(client, message, silent: bool = False):
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

async def reply(client, interaction, message, silent: bool = False):
    try: 
        if len(message) <= 2000:
            await interaction.response.send_message(message, silent = silent)
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
                        await interaction.response.send_message(message_to_send, silent = silent)
                        first_reply_sent = True
                    else:
                        await channel.send(message_to_send, silent = silent)
                    message_to_send = message_fragments[x]
            
            if len(message_to_send) > 0:
                if len(message_to_send) < 2000:
                    if not first_reply_sent:
                        await interaction.response.send_message(message_to_send, silent = silent)
                    else:
                        await channel.send(message_to_send, silent = silent)
                else:
                    await reply(interaction, 'Last message fragment too long to send. Ask developer to include more linebreaks in output.')
    except:
        print(f'Unable to send message: {message}')

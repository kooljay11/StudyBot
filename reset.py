from utilities import *
import os
import discord

async def reset(client):
    global_info = await get_globalinfo()
    servers = await get_serverinfo()
    now = dt.now()

    # If it is the start of a new month, remove all current partners and try to give everyone their preferred partners
    if now.day == 1:
        await remove_all_partners()
        await remove_all_inactive()
        await give_preferred_partners()

    # Assemble a list of all the user files as a list of all user ids
    user_id_list = []
    
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            # Skip users who already have a partner or who have opted out of the auto partnership
            if user["partner_id"] != 0 or not user["auto_partner"]:
                continue

            #print(f'Assembling {user_id}')
            prev_month = await get_prev_month(user)
            #print(f'(os.path.splitext(filename)[0], prev_month["mins_studied"]): {(os.path.splitext(filename)[0], prev_month["mins_studied"])}')
            user_id_list.append((os.path.splitext(filename)[0], prev_month["mins_studied"]))
    #print(f'user_id_list (assembled): {user_id_list}')

    # Order the list (descending) according to the mins studied last month
    user_id_list.sort(key=lambda x: x[1], reverse=True)
    #print(f'user_id_list (sorted): {user_id_list}')

    for user_id, score in user_id_list:
        # Make this user partners with whoever is next in the leaderboard that still needs a partner and wasn't able to have their preferred partner
        #print(f'Searching for the best partner')

        user = await get_userinfo(user_id)

        if user["partner_id"] == 0:
            index = [y[0] for y in user_id_list].index(user_id)

            try:
                partner_id = user_id_list[index + 1][0]
            except IndexError:
                continue

            partner = await get_userinfo(partner_id)

            user["partner_id"] = int(partner_id)
            partner["partner_id"] = int(user_id)

            #print(f'{user_id} and {partner_id} are now partners')

            await save_userinfo(user_id, user)
            await save_userinfo(partner_id, partner)

            # DM both users
            partner_id_nick = await get_id_nickname(client, user, partner_id)
            user_id_nick = await get_id_nickname(client, partner, user_id)
            await dm(client, user_id, f'You are now partners with {partner_id_nick["name"]} (id: {partner_id})')
            await dm(client, partner_id, f'You are now partners with {user_id_nick["name"]} (id: {user_id})')

    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)
            current_month = await get_current_month(user)
            

            # if current_month == "":
            #     current_month = await get_default_month()
            #     user["months"].append(current_month)
            #     current_month["date"] = now.strftime("%b %Y")

            # OLD: Assign new partners if it is the start of a new month and they don't already have a partner
            #if now.day == 1 and user["partner_id"] != 0:
            # Assign new partners if they don't already have a partner
            # If this user and their preferred partner both want to be a partners then make them partners
            if user["partner_id"] != 0 and user["next_partner_id"] != 0:
                potential_partner = await get_userinfo(user["next_partner_id"])

                if potential_partner["partner_id"] == 0 and potential_partner["next_partner_id"] == user_id:
                    user["partner_id"] = user["next_partner_id"]
                    user["next_partner_id"] = 0
                    potential_partner["partner_id"] = potential_partner["next_partner_id"]
                    potential_partner["next_partner_id"] = 0

                    await save_userinfo(user_id, user)
                    await save_userinfo(user["partner_id"], potential_partner)

            await give_monthly_rank(client, global_info, now, current_month, user_id, user, servers)

    # Check through all the guilds in the list for election stuff
    for filename in os.listdir("./data/guild_data"):
        if filename.endswith(".json"):
            guild_name = os.path.splitext(filename)[0]
            guild = await get_guildinfo(guild_name)

            # If there is an ongoing election
            if guild["election_days_left"] > 0:
                guild["election_days_left"] -= 1

                non_voters = deepcopy(guild["all_member_ids"])

                for candidate_id, voter_ids in guild["election"].items():
                    for voter_id in voter_ids:
                        if voter_id in non_voters:
                            non_voters.remove(voter_id)

                # If the guild election has come to the end or all members have cast a vote, then set the new owner, set election days to 0, and set election to {} 
                if guild["election_days_left"] == 0 or len(non_voters) <= 0:
                    # Convert the guild["election"] from a candidate list with lists of voters TO a candidate list with numbers of voters
                    election = {k:len(v) for k, v in guild["election"].items()}
                    # Get the key(s) for the leading candidate(s)
                    lead_candidate_ids = [kv[0] for kv in election.items() if kv[1] == max(election.values())]

                    # If there is a tie, then start a runoff election, removing all the candidates who didnt have the max
                    if len(lead_candidate_ids) > 1:
                        guild["election_days_left"] = global_info["runoff_election_days_length"]
                        new_election = {}

                        for candidate_id in lead_candidate_ids:
                            new_election[candidate_id] = guild["election"][candidate_id]

                        guild["election"] = new_election
                        
                        for member_id in guild["all_member_ids"]:
                            await dm(client, member_id, f'A runoff election was called since there was a tie between candidates. Votes for the lead candidates remain, {guild["election_days_left"]} days have been given for members to change their votes.')
                    # Otherwise set the new owner, set the election days to 0, and clear the election
                    else:
                        winner_id = int(lead_candidate_ids[0])
                        guild["role_user_ids"]["member"].append(guild["owner_id"])
                        guild["role_user_ids"]["member"] = list(set(guild["role_user_ids"]["member"]))

                        guild["owner_id"] = winner_id

                        guild["election_days_left"] = 0
                        guild["election"] = {}

                await save_guildinfo(guild_name, guild)
                
            # If the guild has enough recall voters then start an election
            elif len(guild["recall_voters"]) >= global_info["recall_threshold"] * len(guild["all_member_ids"]):
                guild["recall_voters"] = []
                guild["election_days_left"] = global_info["election_days_length"]
                guild["election"] = {}

                await save_guildinfo(guild_name, guild)

                for member_id in guild["all_member_ids"]:
                    await dm(client, member_id, f'An election has been called. Voting will continue for {guild["election_days_left"]} days.')


async def give_monthly_rank(client, global_info, now, current_month, user_id, user, servers):
    message = f'Your rank is unchanged.'
    # Give each user the monthly rank that corresponds to the amount of hours they studied this month
    for rank, hours in global_info["monthly_rank"].items():
        print(f"Checking to give {rank}")
        # Dont check this rank if the user is of higher/equal rank AND it is not the first day of the month
        if global_info["monthly_rank"].get(current_month["rank"], -1) >= hours and now.day != 1:
            continue
        # If the user has more/equal hours required, give them the rank
        elif current_month["mins_studied"] / 60 >= hours:
            print(f'Assigning {user_id} rank of {rank}')
            #Assign new rank roles for each server
            for server_id, server in servers.items():

                server = client.get_guild(int(server_id)) #Cannot get voicestate info using client.fetch_guild(id)
                member = server.get_member(int(user_id)) #Cannot get voicestate info using server.fetch_member(id)
                # print(f'member.roles: {member.roles}')

                #Remove old role if not the first of the month
                if now.day != 1:
                    old_role = discord.utils.get(server.roles, name=current_month["rank"])
                    # print(f'old_role: {old_role}')
                    try:
                        await member.remove_roles(old_role)
                    except:
                        print(f'')
                #Otherwise remove all old rank roles
                else:
                    for rank_name, value in global_info["monthly_rank"].items():
                        old_role = discord.utils.get(server.roles, name=rank_name)
                        try:
                            # print(f'Attempting to remove {rank_name}')
                            if old_role in member.roles:
                                await member.remove_roles(old_role)
                            # else:
                            #     print(f'Did\'t remove {rank_name}')
                        except:
                            print(f'Couldn\'t remove {rank_name} from user {user_id}')

                new_role = discord.utils.get(server.roles, name=rank)
                # print(f'new_role: {new_role}')
                await member.add_roles(new_role)

            #Remove current month's rank role
            current_month["rank"] = rank
            print(f'current_month["rank"] = rank: {rank}')
            #Give new rank role
            message = f'You were promoted to the rank of {rank} this month!'
            await save_userinfo(user_id, user)
            await dm(client, user_id, message)
        else:
            break
    
    return message

async def remove_all_partners():
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            user["partner_id"] = 0
            await save_userinfo(user_id, user)
    return

# Remove all inactive users
async def remove_all_inactive():
    index = 0
    file_list = os.listdir("./data/user_data")

    # Remove any user who has no minutes studied
    while index < len(file_list):
        filename = file_list[index]
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            total_mins = 0

            for month in user["months"]:
                if month["mins_studied"] > 0:
                    total_mins = month["mins_studied"]
                    break
            
            if total_mins > 0:
                index += 1
            else:
                os.remove("./data/user_data/" + filename)

    return

async def give_preferred_partners():
    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)

            # If this user and their preferred partner both want to be a partners then make them partners
            if user["partner_id"] != 0 and user["next_partner_id"] != 0:
                potential_partner = await get_userinfo(user["next_partner_id"])

                if potential_partner["partner_id"] == 0 and potential_partner["next_partner_id"] == user_id:
                    user["partner_id"] = user["next_partner_id"]
                    user["next_partner_id"] = 0
                    potential_partner["partner_id"] = potential_partner["next_partner_id"]
                    potential_partner["next_partner_id"] = 0

                    await save_userinfo(user_id, user)
                    await save_userinfo(user["partner_id"], potential_partner)
    return
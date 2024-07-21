from utilities import *
import os
import discord

async def reset(client):
    global_info = await get_globalinfo()
    servers = await get_serverinfo()

    for filename in os.listdir("./data/user_data"):
        if filename.endswith(".json"):
            user_id = os.path.splitext(filename)[0]
            user = await get_userinfo(user_id)
            current_month = await get_current_month(user)
            now = dt.now()

            if current_month == "":
                current_month = await get_default_month()
                user["months"].append(current_month)
                current_month["date"] = now.strftime("%b %Y")

            # Give each user the monthly rank that corresponds to the amount of hours they studied this month
            for rank, hours in global_info["monthly_rank"].items():
                # Dont check this rank if the user is of higher/equal rank AND it is not the first day of the month
                if global_info["monthly_rank"].get(current_month["rank"], 0) >= hours and now.day != 1:
                    continue
                # If the user has more/equal hours required, give them the rank
                elif current_month["mins_studied"] / 60 >= hours:
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
                    #Give new rank role
                    await save_userinfo(user_id, user)
                    await dm(client, user_id, f'You were promoted to the rank of {rank} this month!')
                else:
                    break
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import os

class GuildParty(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="guild", description="Show your guild stats .")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Show guild info", value="info"),
        app_commands.Choice(name="Join guild", value="join"),
        app_commands.Choice(name="Create guild", value="create"),
        app_commands.Choice(name="List guilds (20 per page)", value="list"),
        app_commands.Choice(name="Show the member leaderboard in a guild", value="lb"),
        app_commands.Choice(name="Donate to the guild", value="donate"),
        app_commands.Choice(name="Leave guild", value="leave"),
        app_commands.Choice(name="Show election progress", value="election"),
        app_commands.Choice(name="Recall the owner", value="recall"),
        app_commands.Choice(name="Vote for a candidate to be guild owner", value="vote"),
        app_commands.Choice(name="Remove all your votes in the ongoing election", value="unvote"),
        app_commands.Choice(name="Accept applicant (helper+)", value="accept"),
        app_commands.Choice(name="Deny applicant (helper+)", value="deny"),
        app_commands.Choice(name="Promote member (mod+)", value="promote"),
        app_commands.Choice(name="Demote member (mod+)", value="demote"),
        app_commands.Choice(name="Kick member (mod+)", value="kick"),
        app_commands.Choice(name="Ban user (admin+)", value="ban"),
        app_commands.Choice(name="Toggle new applicants (admin+)", value="toggle_applicants"),
        app_commands.Choice(name="Toggle new members (admin+)", value="toggle_new_members"),
        app_commands.Choice(name="Rename guild - letters, numbers, -, _, and space allowed (owner)", value="rename"),
        app_commands.Choice(name="Set guild abbreviation (owner)", value="set_abbr"),
        app_commands.Choice(name="Delete guild (owner)", value="del"),
        app_commands.Choice(name="Unban user (owner)", value="unban"),
        app_commands.Choice(name="Start an election (owner)", value="start_election"),
        app_commands.Choice(name="Toggle logs to owner (owner)", value="toggle_logs_to_owner")
    ])
    async def guild(self, interaction: discord.Interaction, mode: str = "info", target: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        # If the user is part of a guild then get the guild
        try:
            guild = await get_guildinfo(user["guild_name"])
        except:
            guild = None
        
        message = f''
        
        if mode == "info":
            # If the user is specifying a guild then overwrite guild with that one
            if target != "":
                try:
                    guild = await get_guildinfo(target)
                except:
                    guild = None

            # Make sure the guild exists
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return

            # Show the guild name, users for each role (don't show empty lists), total points, global guild rank
            message = f'__**{guild["name"]}**__'

            # Assemble a list of all the guild files as a list of all guild names
            # guild_list = []
            
            # for filename in os.listdir("./data/guild_data"):
            #     if filename.endswith(".json"):
            #         target_guild_name = os.path.splitext(filename)[0]
            #         target_guild = await get_guildinfo(target_guild_name)

            #         guild_list.append((target_guild_name, target_guild["points_total"]))

            # # Order the list (descending) according to the points total
            # guild_list.sort(key=lambda x: x[1], reverse=True)
            
            # # Get the guild global rank
            # guild_rank = 1 + [y[0] for y in guild_list].index(user["guild_name"])
            guild_rank = 1 + await get_guild_index(guild["name"])

            message += f'\nRank: {guild_rank}'
            message += f'\nPoints: {guild["points_total"]}'
            owner_name = await get_id_nickname(self.client, user, guild["owner_id"])
            message += f'\nOwner: {owner_name["name"]} (id: {guild["owner_id"]})'
            message += f'\nTotal members: {len(guild["all_member_ids"])}'

            for role, user_list in guild["role_user_ids"].items():
                formatted_user_list = await get_formatted_user_list(self.client, user, user_list)
                
                # If there are users in the user_list then print out each user who belongs to this role
                if user_list:
                    message += f'\n{role}: {", ".join(formatted_user_list)}'

            perms = await get_perm_list_by_user_id(guild, user_id)

            # If user is part of this guild then also show: applicant list, if an election is occurring
            if "applicant_list" in perms:
                formatted_user_list = await get_formatted_user_list(self.client, user, guild["applicant_ids"])
                if formatted_user_list:
                    message += f'\n\nApplicant list: {", ".join(formatted_user_list)}'

            # If the user is an admin or higher then also show: banned list
            if "banned_list" in perms:
                formatted_user_list = await get_formatted_user_list(self.client, user, guild["banned_ids"])
                if formatted_user_list:
                    message += f'\n\nBanned list: {", ".join(formatted_user_list)}'

        elif mode == "join":
            # If the user is specifying a guild then overwrite guild with that one
            if target != "":
                try:
                    guild = await get_guildinfo(target)
                except:
                    guild = None

            # Make sure the guild exists
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the guild is allowing new applicants
            if not guild["new_applicants"]:
                await reply(self.client, interaction, f'This guild is not accepting any new applicants.')
                return

            # Make sure the guild hasn't banned this user
            if user_id in guild["banned_ids"]:
                await reply(self.client, interaction, f'You have been banned from rejoining this guild.')
                return
            
            # Make sure the user isn't already on the applicant list
            if user_id in guild["applicant_ids"]:
                await reply(self.client, interaction, f'You are already on the applicant list for this guild.')
                return

            # Add user to the applicant list
            guild["applicant_ids"].append(user_id)

            await save_guildinfo(target, guild)
            message = f'You\'ve joined the applicant list for {target}'
        elif mode == "create":
            # Make sure the user isn't already part of a guild
            if guild != None:
                await reply(self.client, interaction, f'You are already part of a guild. You must leave this guild in order to create a new one.')
                return
            
            guild_list = await get_guild_list()
            
            # Make sure the guild name is 1-50 characters long
            if not (len(target) > 1 and len(target) <= 50):
                await reply(self.client, interaction, f'You must choose a guild name that is 1-50 characters long.')
                return
            
            # Make sure the new guild name will be a valid file name (only letters, numbers, -, _, and space allowed)
            guild_name = "".join( x for x in target if (x.isalnum() or x in "_- "))

            # Make sure the guild name is unique
            try:
                if [y[0] for y in guild_list].index(guild_name):
                    await reply(self.client, interaction, f'A guild with this name already exists.')
                    return
            except:
                print()

            # Create a new guild with this user as the owner
            new_guild = await get_default_guildinfo()
            new_guild["owner_id"] = user_id
            new_guild["name"] = guild_name
            new_guild["all_member_ids"].append(user_id)
            await save_guildinfo(guild_name, new_guild)
            user["guild_name"] = guild_name
            await save_userinfo(user_id, user)

            guild = new_guild

            message = f'You\'ve successfully added a new guild called {guild_name}.'
        elif mode == "list":
            message = f'__**Guilds**__'

            # List all available guilds in descending order of total points
            guild_list = await get_guild_list()

            # If no page number is given then set it to the first page
            if target == "":
                target = 1

            # Make sure the target is a valid page number (integer)
            try:
                target = int(target)
            except:
                await reply(self.client, interaction, f'You must input a valid integer page number.')
                return
            
            # Make sure the index is within what is allowed
            try:
                # Set the index to be searched according to the page number
                num_pages = 20
                index = (target - 1) * num_pages

                if len(guild_list) > index+num_pages:
                    guild_list = guild_list[index:index+num_pages]
                else:
                    guild_list = guild_list[index:]
            except:
                await reply(self.client, interaction, f'Something went wrong with the indexing of the guilds.')
                return

            for guild_name, points in guild_list:
                message += f'\n{index + 1}) {guild_name} --- {points}'
                index += 1
        elif mode == "lb":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            message = f'__**{user["guild_name"]} Leaderboard**__\n'

            # Show all users in the guild in descending order of points donated and shows their guild rank in front of their name
            # Eg. 1) 2He Waxer (id:000) --- points
            message += "\n".join(await get_guild_leaderboard(self.client, user, guild))
        elif mode == "donate":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # If target is empty, then by default set it to 0
            if target == "":
                target = 0
            
            # Make sure the number is valid (integer, >= 0)
            try:
                target = int(target)

                if target < 0:
                    await reply(self.client, interaction, f'You must input a valid integer that is greater/equal to zero.')
                    return
            except:
                await reply(self.client, interaction, f'You must input a valid integer that is greater/equal to zero.')
                return
            
            # Make sure the user has enough points to donate (minus the guild_points_spent counter)
            if user["guild_points_donated"] >= user["points"]:
                await reply(self.client, interaction, f'You\'ve already donated all you\'re points! Your points total: {user["points"]}.')
                return
            
            # Make sure the user isn't donating more than what they have
            if user["guild_points_donated"] + target > user["points"]:
                await reply(self.client, interaction, f'You can only donate up to your maximum point total. Your points total: {user["points"]}. Your spent points: {user["guild_points_donated"]}.')
                return

            # Add the points to the guild balance and to the guild_points_spent counter
            guild["points_total"] += target
            try:
                guild["points_tracker"][user_id] += target
            except:
                guild["points_tracker"][user_id] = target
            user["guild_points_donated"] += target

            await save_guildinfo(user["guild_name"], guild)

            message = f'You donated {target} points to {user["guild_name"]}. Your points total: {user["points"]}. Your spent points: {user["guild_points_donated"]}. The guild now has {guild["points_total"]} total points. So far you have donated {user["guild_points_donated"]} points to the guild.'

        elif mode == "leave":
            print(f'Leaving guild')
            # name = await self.client.fetch_user(107886996365508608)
            # print(f'name: {name}')
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Remove the user from the owner_id, admin_ids, mod_ids, helper_ids, or member_ids list
            roles = await get_guild_roles(guild, user_id)
            for role in roles:
                if role == "owner":
                    guild["owner_id"] = 0
                else:
                    guild["role_user_ids"][role].remove(user_id)
            user["guild_name"] = ""
            guild["all_member_ids"].remove(user_id)

            global_info = await get_globalinfo()

            # If was the owner and there are more than 1 member left then start an election and reset recall votes
            if len(guild["all_member_ids"]) > 1:
                # If there is already an election going on, then keep going but remove this user from the candidacy list
                if guild["election_days_left"] > 0:
                    if user_id in guild["election"].keys():
                        del guild["election"][user_id]
                else:
                    guild["election_days_left"] = global_info["election_days_length"]
                    guild["recall_voters"] = []

            # If was the owner and there is only 1 member left then make that person the owner, remove their other roles, and end any ongoing election and reset recall votes
            if len(guild["all_member_ids"]) > 1:
                roles = await get_guild_roles(guild, user_id)
                for role in roles:
                    guild["role_user_ids"][role].remove(user_id)
                
                guild["owner_id"] = user_id
                guild["election"] = []
                guild["election_days_left"] = 0
                guild["recall_voters"] = []

            # If the person voted in an ongoing election, then remove their vote and recall votes
            if guild["election_days_left"] > 0:
                for candidate, votees in guild["election"]:
                    if user_id in votees:
                        votees.remove(user_id)
            
            if user_id in guild["recall_voters"]:
                guild["recall_voters"].remove(user_id)
            
            # Save the guild and the user
            await save_guildinfo(guild["name"], guild)
            await save_userinfo(user_id, user)

            message = f'You left {guild["name"]}. '

            # If there's nobody left in the guild then delete the guild
            if len(guild["all_member_ids"]) <= 0:
                os.remove(f'./data/guild_data/{guild["name"]}.json')
                message += f'Because there was no one left in the guild, the guild was disbanded.'

        elif mode == "election":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            votes = []
            # Show how many votes each candidate has so far in descending order and how many days are left to vote
            if guild["election_days_left"] > 0:
                message = f'__**Interim Election Results**__'
                message += f'\nDays left in the vote: {guild["election_days_left"]}'

                for candidate_id, voters in guild["election"].items():
                    candidate = await get_id_nickname(self.client, user, candidate_id)
                    votes.append((candidate["name"], len(voters)))
                
                # Sort the list of tuples (name, num voters) in descending order
                votes.sort(key=lambda tup: tup[1], reverse=True)

                for candidate_name, num_votes in votes:
                    message += f'\n{candidate_name}: {num_votes}'

            # If there is no election active, then show how many recall voters there are
            else:
                # Calculate the number of recall votes needed to trigger an election
                global_info = await get_globalinfo()
                num_recall_votes_needed = global_info["recall_threshold"] * len(guild["all_member_ids"])
                
                message = f'__**Recall Election Progress**__'
                message += f'\nRecall voters: {len(guild["recall_voters"])}'
                message += f'\nTotal members: {len(guild["all_member_ids"])}'
                message += f'\nRecall voters needed: {num_recall_votes_needed}'
        elif mode == "recall":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there isn't an active election right now
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot cast a recall vote during an active election.')
                return
            
            # Make sure the user hasn't already voted in the recall election
            if user_id in guild["recall_voters"]:
                await reply(self.client, interaction, f'You\'ve already cast a recall vote.')
                return
            
            # Add the user_id to the recall voters list
            guild["recall_voters"].append(user_id)
            await save_guildinfo(user["guild_name"], guild)

            message = f'You\'ve added a recall vote.'
            message += f'\nRecall voters: {len(guild["recall_voters"])}'
            message += f'\nTotal members: {len(guild["all_member_ids"])}'

            # Calculate the number of recall votes needed to trigger an election
            global_info = await get_globalinfo()
            num_recall_votes_needed = global_info["recall_threshold"] * len(guild["all_member_ids"])

            message += f'\nRecall voters needed: {num_recall_votes_needed}'

        elif mode == "vote":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there is an active election right now
            if guild["election_days_left"] <= 0:
                await reply(self.client, interaction, f'There is no active election right now.')
                return
            
            # If the target is empty then set it to the user
            if target == "":
                target = user_id
            
            # Get the candidate name
            candidate = await get_id_nickname(self.client, user, target)
            
            # Make sure the user hasn't already voted for this candidate
            try:
                if user_id in guild["election"][candidate["id"]]:
                    await reply(self.client, interaction, f'You\'ve already votes for that candidate.')
                    return
            except:
                print()

            # Make sure the candidate they are voting for is an actual member of the guild
            if candidate["id"] not in guild["all_member_ids"]:
                await reply(self.client, interaction, f'The candidate must be a member of this guild.')
                return

            # Add their user_id to the list of user_ids voting for that candidate id
            try:
                guild["election"][candidate["id"]].append(user_id)
            except:
                guild["election"][candidate["id"]] = [user_id]
            await save_guildinfo(user["guild_name"], guild)

            message = f'You voted for {candidate["name"]}. Use /guild mode=election to see the election progress.'

            # If a majority has been reached then automatically resolve -- NOT REQUIRED
        elif mode == "unvote":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there is an active election right now
            if guild["election_days_left"] <= 0:
                await reply(self.client, interaction, f'There is no active election right now.')
                return

            removal_ids = []

            # Remove all entries of this user's vote for all candidates
            for candidate_id, voters in guild["election"].items():
                if user_id in voters:
                    voters.remove(user_id)
                
                if len(voters) <= 0:
                    removal_ids.append(candidate_id)
            
            # Remove all empty candidate lists
            for candidate_id in removal_ids:
                guild["election"].pop(candidate_id)
            
            await save_guildinfo(user["guild_name"], guild)

            message = f'You\'ve removed all your votes in the current election.'

            # If a majority has been reached then automatically resolve -- NOT REQUIRED
        elif mode == "accept":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return

            # Make sure the guild is accepting new members
            if not guild["new_members"]:
                await reply(self.client, interaction, f'This guild isn\'t currently accepting any new members.')
                return

            # Make sure there isn't an election occuring right now in the guild
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot accept any new members during an active election.')
                return

            # Make sure the target applicant exists and is actually in the applicant list
            try:
                applicant = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target applicant doesn\'t exist.')
                return

            if applicant["id"] not in guild["applicant_ids"]:
                await reply(self.client, interaction, f'The user must be on the applicant list before you can accept them.')
                return

            # Make sure the target applicant isn't part of another guild already
            applicant_user = await get_userinfo(applicant["id"])
            if applicant_user["guild_name"] != "":
                await reply(self.client, interaction, f'The user must not be part of another guild before they can join this guild.')
                return

            # Make sure the target applicant hasn't been banned already (if they are then remove them from the applicant list)
            if applicant["id"] in guild["banned_ids"]:
                await reply(self.client, interaction, f'This user has been banned from the guild.')
                guild["applicant_ids"].remove(applicant["id"])
                await save_guildinfo(user["guild_name"], guild)
                return

            # Remove the target applicant from the list
            guild["applicant_ids"].remove(applicant["id"])

            # Add the target applicant to the member list and change their user info's guild to this guild
            guild["all_member_ids"].append(applicant["id"])
            guild["role_user_ids"]["member"].append(applicant["id"])
            await save_guildinfo(user["guild_name"], guild)

            applicant_user["guild_name"] = guild["name"]
            await save_userinfo(applicant["id"], applicant_user)

            message = f'You accepted {applicant["name"]} into the guild.'

            # DM the applicant that they've been accepted into the guild
            await dm(self.client, applicant["id"], f'You\'ve been accepted into {guild["name"]}.')

        elif mode == "deny":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure the target applicant exists and is actually in the applicant list
            try:
                applicant = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target applicant doesn\'t exist.')
                return
            
            if applicant["id"] not in guild["applicant_ids"]:
                await reply(self.client, interaction, f'The user must be on the applicant list before you can accept them.')
                return

            # Remove the target applicant from the list
            guild["applicant_ids"].remove(applicant["id"])
            await save_guildinfo(user["guild_name"], guild)

            message = f'{applicant["name"]} (id:{applicant["id"]}) was removed from the applicant list.'

        elif mode == "promote":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure the target is a member of the guild
            try:
                member = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return

            if member["id"] not in guild["all_member_ids"]:
                await reply(self.client, interaction, f'The user must be a member of the guild.')
                return
            
            # Make sure the target future role is lower than the current users role in the guild
            user_role_value = await get_guild_user_role_value(guild, user_id)
            member_role_value = await get_guild_user_role_value(guild, member["id"])
            new_member_role_value = member_role_value + 1

            if new_member_role_value >= user_role_value:
                await reply(self.client, interaction, f'Error. Member\'s new role would be higher than/equal to your role.')
                return

            # Remove the target member from their role list and add them to the targetted role list
            member_role = await get_guild_role_by_value(guild, member_role_value)
            new_member_role = await get_guild_role_by_value(guild, new_member_role_value)
            guild["role_user_ids"][member_role].remove(member["id"])
            guild["role_user_ids"][new_member_role].append(member["id"])

            await save_guildinfo(user["guild_name"], guild)

            await dm(self.client, member["id"], f'You\'ve been promoted in {guild["name"]} from {member_role} to {new_member_role}.')

            message = f'{member["name"]} (id: {member["id"]}) was promoted from {member_role} to {new_member_role}.'
        elif mode == "demote":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure the target is a member of the guild
            try:
                member = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return

            if member["id"] not in guild["all_member_ids"]:
                await reply(self.client, interaction, f'The user must be a member of the guild.')
                return

            # Make sure the target current role is lower than the current users role in the guild
            user_role_value = await get_guild_user_role_value(guild, user_id)
            member_role_value = await get_guild_user_role_value(guild, member["id"])
            new_member_role_value = member_role_value - 1

            if member_role_value >= user_role_value:
                await reply(self.client, interaction, f'Error. Member\'s current role is higher than/equal to your role.')
                return
            
            # Make sure the target role is not lower than 0
            if new_member_role_value <= 0:
                await reply(self.client, interaction, f'This member is already the lowest role.')
                return
            
            # Remove the target member from their role list and add them to the targetted role list
            member_role = await get_guild_role_by_value(guild, member_role_value)
            new_member_role = await get_guild_role_by_value(guild, new_member_role_value)
            guild["role_user_ids"][member_role].remove(member["id"])
            guild["role_user_ids"][new_member_role].append(member["id"])

            await save_guildinfo(user["guild_name"], guild)

            await dm(self.client, member["id"], f'You\'ve been demoted in {guild["name"]} from {member_role} to {new_member_role}.')

            message = f'{member["name"]} (id: {member["id"]}) was demoted from {member_role} to {new_member_role}.'
        elif mode == "kick":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there isn't an election occuring right now in the guild
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot kick members during an active election.')
                return

            # Make sure the target is a member of the guild
            try:
                member = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return

            if member["id"] not in guild["all_member_ids"]:
                await reply(self.client, interaction, f'The user must be a member of the guild.')
                return

            # Make sure the target current role is lower than the current users role in the guild
            user_role_value = await get_guild_user_role_value(guild, user_id)
            member_role_value = await get_guild_user_role_value(guild, member["id"])
            new_member_role_value = member_role_value - 1

            if member_role_value >= user_role_value:
                await reply(self.client, interaction, f'Error. Member\'s current role is higher than/equal to your role.')
                return
            
            # Remove the target member from the role list and full memberlist
            await remove_guild_roles(guild, member["id"])
            await save_guildinfo(user["guild_name"], guild)

            # Remove the target user's guild in their user info
            member_user = await get_userinfo(member["id"])
            member_user["guild_name"] = ""
            await save_userinfo(member["id"], member_user)

            await dm(self.client, member["id"], f'You were kicked from {guild["name"]}.')

            message = f'{member["name"]} (id: {member["id"]}) was kicked from {guild["name"]}.'
        elif mode == "ban":
            message = f''
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there isn't an election occuring right now in the guild
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot ban members during an active election.')
                return
            
            # Make sure the target is a member of the guild
            try:
                member = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target member doesn\'t exist.')
                return

            # If the target is a member of the guild then do some checks
            if member["id"] in guild["all_member_ids"]:
                # Make sure the target current role is lower than the current users role in the guild
                user_role_value = await get_guild_user_role_value(guild, user_id)
                member_role_value = await get_guild_user_role_value(guild, member["id"])
                new_member_role_value = member_role_value - 1

                if member_role_value >= user_role_value:
                    await reply(self.client, interaction, f'Error. Member\'s current role is higher than/equal to your role.')
                    return
                
                # Remove the target member from the role list and full memberlist
                await remove_guild_roles(guild, member["id"])

                # Remove the target user's guild in their user info
                member_user = await get_userinfo(member["id"])
                member_user["guild_name"] = ""
                await save_userinfo(member["id"], member_user)

            # Add the target user to the ban list
            guild["banned_ids"].append(member["id"])

            await save_guildinfo(user["guild_name"], guild)

            await dm(self.client, member["id"], f'You were banned from {guild["name"]}.')
            
            message = f'{member["name"]} (id: {member["id"]}) was banned from {guild["name"]}.'
        elif mode == "toggle_applicants":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Toggle new_applicants
            guild["new_applicants"] = not guild["new_applicants"]
            await save_guildinfo(user["guild_name"], guild)

            if guild["new_applicants"]:
                message = f'The applicant list for this guild is now open.'
            else:
                message = f'The applicant list for this guild is now closed.'
        elif mode == "toggle_new_members":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Toggle new_members
            guild["new_members"] = not guild["new_members"]
            await save_guildinfo(user["guild_name"], guild)

            if guild["new_members"]:
                message = f'This guild is now accepting new members from the applicant list.'
            else:
                message = f'This guild is no longer accepting new members from the applicant list.'
        elif mode == "rename":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            old_guild_name = user["guild_name"]
            
            guild_list = await get_guild_list()
            
            # Make sure the new guild name will be a valid file name (only letters, numbers, -, _, and space allowed)
            guild_name = "".join( x for x in target if (x.isalnum() or x in "_- "))

            # Make sure the guild name is 1-50 characters long
            if not (len(guild_name) >= 1 and len(guild_name) <= 50):
                await reply(self.client, interaction, f'You must choose a guild name that is 1-50 characters long.')
                return
            
            # Make sure the guild name is different from before
            if guild_name == guild["name"]:
                await reply(self.client, interaction, f'The guild is already called {guild["name"]}.')
                return
            
            # Make sure the guild name is unique
            try:
                if [y[0] for y in guild_list].index(guild_name) >= 0:
                    await reply(self.client, interaction, f'A guild with this name already exists.')
                    return
            except:
                print()
            
            # Rename the file and the listed guild name in all of the user info files
            os.rename(f'./data/guild_data/{old_guild_name}.json', f'./data/guild_data/{guild_name}.json')

            guild["name"] = guild_name
            await save_guildinfo(guild_name, guild)

            for member_id in guild["all_member_ids"]:
                member = await get_userinfo(member_id)
                member["guild_name"] = guild_name
                await save_userinfo(member_id, member)

            message = f'The guild has been renamed from {old_guild_name} to {guild_name}.'
            
        elif mode == "set_abbr":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure the abbreviation is letters, numbers, -, _, and space only
            abbr = "".join( x for x in target if (x.isalnum() or x in "_- "))

            # Make sure the abbreviation is 1-4 characters long
            if not (len(abbr) >= 1 and len(abbr) <= 4):
                await reply(self.client, interaction, f'You must choose an abbreviation that is 1-4 characters long.')
                return
            
            # Make sure the guild abbreviation is different from before
            if abbr == guild["abbreviation"]:
                await reply(self.client, interaction, f'The guild abbreviation is already {guild["abbreviation"]}.')
                return
            
            # Make sure the abbreviation hasn't already been taken
            abbr_list = await get_guild_abbr_list()

            if abbr in abbr_list:
                await reply(self.client, interaction, f'A guild with this abbreviation already exists.')
                return

            # Set the new abbreviation
            guild["abbreviation"] = abbr
            await save_guildinfo(guild["name"], guild)

            message = f'The guild\'s abbreviation has been set to {abbr}.'

        elif mode == "del":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return

            # Make sure there isn't an election occuring right now in the guild
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'You cannot delete a guild during an active election.')
                return
            
            # Make sure there isn't a recall election that has reached the recall threshold
            global_info = await get_globalinfo()
            if len(guild["recall_voters"])/len(guild["all_member_ids"]) >= global_info["recall_threshold"]:
                await reply(self.client, interaction, f'You cannot delete a guild when a recall election has been voted for.')
                return
            
            # Remove all members, including changing each one of their guild joined in user info (and delete the file?)
            for member_id in guild["all_member_ids"]:
                member = await get_userinfo(member_id)
                member["guild_name"] = ""
                await save_userinfo(member_id, member)
                user_name = await get_id_nickname(self.client, member, user_id)
                await dm(self.client, member_id, f'{guild["name"]} has been deleted by {user_name["name"]} (id: {user_id}).')

            os.remove(f'./data/guild_data/{guild["name"]}.json')
            message = f'{guild["name"]} has been deleted.'

        elif mode == "unban":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure the target user is part of the ban list
            try:
                member = await get_id_nickname(self.client, user, target)
            except:
                await reply(self.client, interaction, f'Target user doesn\'t exist.')
                return
            
            if member["id"] not in guild["banned_ids"]:
                await reply(self.client, interaction, f'This user is not on the ban list.')
                return

            # Remove the target user from the ban list
            guild["banned_ids"].remove(member["id"])
            await save_guildinfo(user["guild_name"], guild)

            message = f'{member["name"]} (id: {member["id"]}) was removed from the banned list of {guild["name"]}.'

        elif mode == "start_election":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Make sure there isn't an election occuring right now in the guild
            if guild["election_days_left"] > 0:
                await reply(self.client, interaction, f'An election is already in progress.')
                return
            
            # Set the recall voters to 100%
            guild["recall_voters"] = guild["all_member_ids"]
            await save_guildinfo(guild["name"], guild)

            message = f'Recall vote has been set to 100%. An election for a new guild leader will be triggered tomorrow.'

            # Tell all members that a new election will be called
            for member_id in guild["all_member_ids"]:
                member = await get_userinfo(member_id)
                user_name = await get_id_nickname(self.client, member, user_id)
                await dm(self.client, member_id, f'{user_name["name"]} (id: {user_id}) has called for an election for a new leader for {guild["name"]} which will begin tomorrow.')
            
            # Reset the recall voters - NOT NEEDED
            # Set the election timer - NOT NEEDED
        elif mode == "toggle_logs_to_owner":
            # Make sure the user is part of a guild
            if guild == None:
                await reply(self.client, interaction, f'Guild not found.')
                return
            
            # Make sure the user has the proper perms
            perms = await get_perm_list_by_user_id(guild, user_id)
            if mode not in perms:
                await reply(self.client, interaction, f'You don\'t have the sufficient permissions to use that command.')
                return
            
            # Toggle logs of most actions being sent to the guild owner
            guild["logs_to_owner"] = not guild["logs_to_owner"]
            await save_guildinfo(guild["name"], guild)

            if guild["logs_to_owner"]:
                message = f'This guild is now sending logs to the owner.'
            else:
                message = f'This guild is no longer sending logs to the owner.'
        
        # For all successful actions send a message to the guild owner except info, list, lb, election, recall, vote, unvote, applicant_list IF this is toggled on 
        try:
            if mode not in ["info", "list", "lb", "election", "recall", "vote", "unvote", "applicant_list"] and guild["logs_to_owner"]:
                owner = await get_userinfo(guild["owner_id"])
                #print(f'owner: {owner["points"]}')

                this_user = await get_id_nickname(self.client, owner, user_id) 
                #print(f'this_user: {this_user["name"]}')

                await dm(self.client, guild["owner_id"], f'[{guild["name"]}] [{this_user["name"]}]: {message}')
                #print(f'guild["owner_id"]: {guild["owner_id"]}')
        except:
            print(f'{guild["name"]} has no owner to send logs to.')

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(GuildParty(client))
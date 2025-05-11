import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

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
        app_commands.Choice(name="Info", value="info"),
        app_commands.Choice(name="Join", value="join"),
        app_commands.Choice(name="Create", value="create"),
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Leaderboard", value="lb"),
        app_commands.Choice(name="Donate", value="donate"),
        app_commands.Choice(name="Leave", value="leave"),
        app_commands.Choice(name="Election", value="election"),
        app_commands.Choice(name="Recall", value="recall"),
        app_commands.Choice(name="Vote", value="vote"),
        app_commands.Choice(name="Accept (helper+)", value="accept"),
        app_commands.Choice(name="Deny (helper+)", value="deny"),
        app_commands.Choice(name="Promote (mod+)", value="promote"),
        app_commands.Choice(name="Demote (mod+)", value="demote"),
        app_commands.Choice(name="Kick (mod+)", value="kick"),
        app_commands.Choice(name="Ban (admin+)", value="ban"),
        app_commands.Choice(name="Toggle new applicants (admin+)", value="toggle_applicants"),
        app_commands.Choice(name="Toggle new members (admin+)", value="toggle_new_members"),
        app_commands.Choice(name="Rename (owner)", value="rename"),
        app_commands.Choice(name="Delete (owner)", value="del"),
        app_commands.Choice(name="Unban (owner)", value="unban")
    ])
    async def guild_party(self, interaction: discord.Interaction, mode: str = "info", target: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if mode == "info":
            message = f'__**INSERT GUILD NAME**__'
            # By default show the guild is the user is in
            # Otherwise ask the user to specify a guild
            # If the guild exists, then...
            # Show the guild name, users for each role (don't show empty lists), total points, global guild rank
            # If user is part of this guild then also show: applicant list, if an election is occurring
            # If the user is an admin or higher then also show: banned list


        elif mode == "join":
            message = f''
            # Make sure the guild exists
            # Make sure the guild is allowing new applicants
            # Make sure the guild hasn't banned this user
            # Add user to the applicant list
        elif mode == "create":
            message = f''
            # Make sure the user isn't already part of a guild
            # Make sure the guild name doesn't exist yet
            # Create a new guild with this user as the owner
        elif mode == "list":
            message = f''
            # List all available guilds
            # Sort guilds in descending order of total points
            # Use target to pick a page
        elif mode == "lb":
            message = f''
            # Make sure the user is part of a guild
            # Show all users in the guild in descending order of points donated and shows their guild rank in front of their name
            # Eg. 1) 2He Waxer (id:000): points
        elif mode == "donate":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user has enough points to donate (minus the guild_points_spent counter)
            # Add the points to the guild balance and to the guild_points_spent counter
        elif mode == "leave":
            message = f''
            # Make sure the user is part of a guild
            # Remove the user from the owner_id, admin_ids, mod_ids, helper_ids, or member_ids list
            # If was the owner and there are more than 1 member left then start an election
            # If was the owner and there is only 1 member left then make that person the owner
            # If the person voted in an ongoing election, then remove their vote
            # If there's nobody left in the guild then delete the guild
        elif mode == "election":
            message = f''
            # Make sure the user is part of a guild
            # Show how many votes each candidate has so far in descending order and how many days are left to vote
            # If there is no election active, then show how many recall voters there are
        elif mode == "recall":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user hasn't already voted in the recall election
            # Make sure there isn't an active election right now
            # Add the user_id to the recall voters list
        elif mode == "vote":
            message = f''
            # Make sure the user is part of a guild
            # Make sure there is an active election right now
            # Make sure the user hasn't already voted for this candidate
            # Make sure the candidate they are voting for is an actual member of the guild
            # Add their user_id to the list of user_ids voting for that candidate id

            # If a majority has been reached then automatically resolve
        elif mode == "accept":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a helper or higher role
            # OR make sure the user has the perms

            # Make sure the guild is accepting new members
            # Make sure there isn't an election occuring right now in the guild
            # Make sure the target applicant exists and is actually in the applicant list
            # Make sure the target applicant isn't part of another guild already
            # Make sure the target applicant hasn't been banned already (if they are then remove them from the applicant list)
            # Remove the target applicant from the list
            # Add the target applicant to the member list and change their user info's guild to this guild
        elif mode == "deny":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a helper or higher role
            # OR make sure the user has the perms
            
            # Make sure the target applicant is actually in the applicant list
            # Remove the target applicant from the list
        elif mode == "promote":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the applicant is mod or higher role
            # OR make sure the user has the perms
            
            # Make sure the target is a member of the club
            # Make sure the target future role is lower than the current users role in the guild
            # Remove the target member from their role list and add them to the targetted role list
        elif mode == "demote":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a mod or higher role
            # OR make sure the user has the perms
            
            # Make sure the target is a member of the club
            # Make sure the target current role is lower than the current users role in the guild
            # Remove the target member from their role list and add them to the targetted role list
        elif mode == "kick":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a mod or higher role
            # OR make sure the user has the perms
            
            # Make sure there isn't an election occuring right now in the guild
            # Make sure the target is a member of the club
            # Make sure the target current role is lower than the current users role in the guild
            # Remove the target member from the role list
            # Remove the target user's guild in their user info
        elif mode == "ban":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a admin or higher role
            # OR make sure the user has the perms
            
            # Make sure there isn't an election occuring right now in the guild
            # Make sure the target is a member of the club
            # Make sure the target current role is lower than the current users role in the guild
            # Remove the target member from the role list
            # Remove the target user's guild in their user info
            # Add the target user to the ban list
        elif mode == "toggle_applicants":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a admin or higher role
            # OR make sure the user has the perms
            
            # Toggle new_applicants
        elif mode == "toggle_new_members":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a admin or higher role
            # OR make sure the user has the perms
            
            # Toggle new_members
        elif mode == "rename":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a owner (or higher role?)
            # OR make sure the user has the perms
            
            # Make sure the name hasn't already been taken
            # Rename the file and the listed guild name in all of the user info files
        elif mode == "del":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a owner (or higher role?)
            # OR make sure the user has the perms
            
            # Can't do if there is an election going on or if the recall election is more than 50% towards its goal
            # Remove all members, including changing each one of their guild joined in user info (and delete the file?)
        elif mode == "unban":
            message = f''
            # Make sure the user is part of a guild
            # Make sure the user is a owner (or higher role?)
            # OR make sure the user has the perms
            
            # Make sure the target user is part of the ban list
            # Remove the target user from the ban list
        
        #For all successful actions send a message to the guild owner, except voting and recall voting
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(GuildParty(client))
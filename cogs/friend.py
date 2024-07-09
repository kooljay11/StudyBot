import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class Friend(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="friend", description="Add/remove/list your friends.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    async def friend(self, interaction: discord.Interaction, mode: str = "list", friend: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if mode == "list":
            message = f'__**Friends**__'
            for friend_id in user["friends"]:
                friend_id_nick = await get_id_nickname(self.client, user, str(friend_id))

                # Make sure the friend exists
                try:
                    friend_info = await get_userinfo(friend_id)
                except:
                    await reply(self.client, interaction, f'{friend_id_nick["name"]} not found (id: {friend_id_nick["id"]}).')
                    return
                
                current_month = await get_current_month(friend_info)

                message += f'\n'

                if current_month != "" and current_month["rank"] != "":
                    message += f'[{current_month["rank"]}] '
                
                message += f'{friend_id_nick["name"]} (id: {friend_id_nick["id"]})'


        elif mode == "add":
            # Make sure the user exists
            try:
                friend_info = await get_userinfo_by_nick(user, friend)
            except:
                await reply(self.client, interaction, f'Target user not found.')
                return
            
            friend_id_nick = await get_id_nickname(self.client, user, friend)

            # Make sure they aren't already friends
            if friend_id_nick["id"] in user["friends"]:
                await reply(self.client, interaction, f'You are already friends with that user.')
                return
            
            
            user["friends"].append(friend_id_nick["id"])

            # Remove duplicate friends
            user["friends"] = list(set(user["friends"]))

            #Add friend's name to the nickname list if it's not there already
            user["nicknames"][friend_id_nick["name"]] = friend_id_nick["id"]
            
            await save_userinfo(user_id, user)

            message = f'Added {friend_id_nick["name"]} to your friend list.'
        elif mode == "remove":
            try:
                friend_id_nick = await get_id_nickname(self.client, user, friend)
                user["friends"].remove(friend_id_nick["id"])
                await save_userinfo(user_id, user)
                message = f'{friend_id_nick["name"]} was removed from your friend list.'
            except:
                await reply(self.client, interaction, f'Friend not found.')
                return
            
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(Friend(client))
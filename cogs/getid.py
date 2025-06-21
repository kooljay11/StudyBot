import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class GetId(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="getuserid", description="Get a Discord user's id.")
    async def getuserid(self, interaction: discord.Interaction, name: discord.Member):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        message = f'User id = {name.id}'
            
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(GetId(client))
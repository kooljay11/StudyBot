import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    @app_commands.command(name="help", description="See the help guide.")
    async def help(self, interaction: discord.Interaction):
        global_info = await get_globalinfo()
        message = f'{global_info["help_message"]}'
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Help(client))
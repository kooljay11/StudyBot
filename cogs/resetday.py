import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
from reset import reset

class ResetDay(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="resetday", description="Dev: Reset the day.")
    @app_commands.default_permissions(administrator=True)
    async def resetday(self, interaction: discord.Interaction):
        await reset(self.client)

        message = f'Day reset'
            
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(ResetDay(client))
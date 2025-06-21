import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
from reset import reset, give_monthly_rank

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
        global_info = await get_globalinfo()

        user_id = interaction.user.id

        if user_id not in global_info["dev_list"]:
            await reply(self.client, interaction, f'Only developers can use this command.')
            return
        await reset(self.client)

        message = f'Day reset'
            
        await reply(self.client, interaction, message)


    @app_commands.command(name="getrole", description="Manually check if you can rank up this month (usually done automatically at the end of every day).")
    async def getrole(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        global_info = await get_globalinfo()
        servers = await get_serverinfo()
        now = dt.now()

        user = await get_userinfo(user_id)
        current_month = await get_current_month(user)

        message = await give_monthly_rank(self.client, global_info, now, current_month, user_id, user, servers)
            
        await reply(self.client, interaction, message)

async def setup(client):
    await client.add_cog(ResetDay(client))
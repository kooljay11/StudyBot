import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import dateparser #pip install dateparser
#https://github.com/scrapinghub/dateparser

class Sessions(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="sessions", description="Lists all sessions scheduled by the user.")
    async def list_sessions(self, interaction: discord.Interaction, user_id: str = ""):
        if user_id == "":
            user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        # Stop if the user has no scheduled sessions
        if len(user["sessions"]) <= 0:
            await reply(self.client, interaction, f'Session list is empty.')
            return
        
        global_info = await get_globalinfo()
        now = datetime.now()

        message = f'__**Sessions**__'
        
        for session in user["sessions"]:
            scheduled_datetime = dateparser.parse(session["datetime"])

            duration_hours = int(session["duration_mins"]/60)
            duration_mins = session["duration_mins"]%60

            message += f'\n{user["sessions"].index(session)}: {session["datetime"]} for '

            if duration_hours == 0:
                message += f'{duration_mins} mins '
            elif duration_mins == 0:
                message += f'{duration_hours} hrs '
            else:
                message += f'{duration_hours} hrs and {duration_mins} mins '

            message += f'with a reminder {session["reminder_ahead_mins"]} mins beforehand. '

            # Get the points required for penalty
            current_delta = scheduled_datetime - now

            penalty_cost = 0

            for penalty in global_info["cancellation_penalty"]:
                delta = timedelta(hours=int(penalty["hrs_limit"]))
                if current_delta < delta:
                    penalty_cost = penalty["cost"]
                    break

            if penalty_cost > 0:
                message += f'Cancellation penalty: {penalty_cost}.'
            


        
        
        

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(Sessions(client))
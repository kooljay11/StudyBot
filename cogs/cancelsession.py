import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import dateparser #pip install dateparser
#https://github.com/scrapinghub/dateparser

class CancelSession(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="cancelsession", description="Cancels a scheduled session.")
    async def cancel_session(self, interaction: discord.Interaction, index: int):
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(user_id)
            await reply(self.client, interaction, f'Session list is empty.')
            return
        
        # Stop if the user has no scheduled sessions
        if len(user["sessions"]) <= 0:
            await reply(self.client, interaction, f'Session list is empty.')
            return
        
        # Stop if the user doesn't have enough points to pay for that
        global_info = await get_globalinfo()

        now = datetime.now(UTC).replace(tzinfo=None)
        scheduled_datetime = dateparser.parse(user["sessions"][index]["datetime"])

        current_delta = scheduled_datetime - now

        penalty_cost = 0

        for penalty in global_info["cancellation_penalty"]:
            delta = timedelta(hours=int(penalty["hrs_limit"]))
            if current_delta < delta:
                # Remove the points if they have it
                if user["points"] < penalty["cost"]:
                    await reply(self.client, interaction, f'You don\'t have the required points {penalty["cost"]} to cancel that session. Your balance is {user["points"]}.')
                    return
                
                user["points"] -= penalty["cost"]
                penalty_cost = penalty["cost"]
                break
        
        # Remove the session
        try:
            cancelled_session = user["sessions"].pop(index)
        except:
            await reply(self.client, interaction, f'Session not found.')
            return

        # Save changes
        await save_userinfo(user_id, user)
        
        scheduled_datetime_display = await utc_to_current(dateparser.parse(cancelled_session["datetime"]), user["timezone"])
        session_date_formatted = scheduled_datetime_display.strftime("%a, %b %d, %Y, %I:%M %p")
        duration_hours = int(cancelled_session["duration_mins"]/60)
        duration_mins = cancelled_session["duration_mins"]%60

        message = f'Session cancelled @ {session_date_formatted} for '

        if duration_hours == 0:
            message += f'{duration_mins} mins '
        elif duration_mins == 0:
            message += f'{duration_hours} hrs '
        else:
            message += f'{duration_hours} hrs and {duration_mins} mins '

        message += f'with a reminder {cancelled_session["reminder_ahead_mins"]} mins beforehand. '

        if penalty_cost > 0:
            message += f'Because of how close it was to the scheduled time, you paid a penalty cost of {penalty_cost} points to cancel it.'

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(CancelSession(client))
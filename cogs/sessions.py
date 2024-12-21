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

    
    
    @app_commands.command(name="editsession", description="Edit a session.")
    @app_commands.describe(attr="Mode")
    @app_commands.choices(attr=[
        app_commands.Choice(name="Description", value="desc")
    ])
    async def edit_session(self, interaction: discord.Interaction, attr: str, index: int, value: str = ""):
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
        
        # Get the session
        try:
            session = user["sessions"][index]
        except:
            await reply(self.client, interaction, f'Session not found. Make sure you are using the correct index number.')
            return
        
        if attr == "desc":
            session["description"] = value
        
        # Save changes
        await save_userinfo(user_id, user)

        scheduled_datetime_display = await utc_to_current(dateparser.parse(session["datetime"]), user["timezone"])
        session_date_formatted = scheduled_datetime_display.strftime("%a, %b %d, %Y, %I:%M %p")
        time_str = await get_time_str(session["duration_mins"])

        message = f'Session edited @ {session_date_formatted} for {time_str} with a reminder {session["reminder_ahead_mins"]} mins beforehand. \nDescription: {session["description"]}'

        await reply(self.client, interaction, message)
        
    
    @app_commands.command(name="sessions", description="Lists all sessions scheduled by the user.")
    async def list_sessions(self, interaction: discord.Interaction, target: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if target != user_id and target != "":
            target_id_nick = await get_id_nickname(self.client, user, target)
            target_info = await get_userinfo(target_id_nick["id"])
            user_name = target_id_nick["name"]
        else:
            target_info = user
            user_name = str(await self.client.fetch_user(user_id))
        
        # Stop if the user has no scheduled sessions
        if len(target_info["sessions"]) <= 0:
            await reply(self.client, interaction, f'Session list is empty.')
            return
        
        global_info = await get_globalinfo()
        now = datetime.now(UTC).replace(tzinfo=None)

        message = f'__**{user_name}\'s Sessions**__'
        
        for session in target_info["sessions"]:
            scheduled_datetime = dateparser.parse(session["datetime"])
            scheduled_datetime_display = await utc_to_current(scheduled_datetime, user["timezone"])
            formatted_scheduled_datetime = scheduled_datetime_display.strftime("%a, %b %d, %Y, %I:%M %p")
            time_str = await get_time_str(session["duration_mins"])
            
            message += f'\n{target_info["sessions"].index(session)}: {formatted_scheduled_datetime} for {time_str} with a reminder {session["reminder_ahead_mins"]} mins beforehand. '
            if session["description"] != "":
                message += f'Description: {session["description"]}'
                
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
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import dateparser #pip install dateparser
#https://github.com/scrapinghub/dateparser

class AddSession(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="addsession", description="Schedules a new session.")
    async def add_session(self, interaction: discord.Interaction, date: str, duration_hours: int = 0, duration_mins: int = 0, reminder_mins: int = -1, description: str = ""):
        try:
            session_date = dateparser.parse(date)
        except:
            await reply(self.client, interaction, f'Couldn\'t parse that date, sorry. Please check the external module documentation for further information: https://github.com/scrapinghub/dateparser')
            return
        
        # Prevent the date being in the past
        now = datetime.now()
        if now >= session_date:
            await reply(self.client, interaction, f'You must schedule a session in the future.')
            return
        
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(user_id)
            user = await get_userinfo(user_id)
        
        # Get the current server id
        try:
            server_id = interaction.guild_id
        except:
            if user["default_guild_id"] > 0:
                try: 
                    self.client.fetch_guild(user["default_guild_id"])
                except:
                    message = f'Default server_id not found.'
                    await reply(self.client, interaction, message)
                    return
            else:
                message = f'Either set a default server_id or submit this command in a server.'
                await reply(self.client, interaction, message)
                return

        duration_total_mins = duration_mins + duration_hours * 60
        
        # Prevent the duration being 0 or negative overall
        if duration_total_mins <= 0:
            duration_total_mins = user["default_duration"]

        # Prevent the reminder being negative
        if reminder_mins < 0:
            reminder_mins = user["default_reminder_ahead"]

        # Check through every pre-scheduled session and make sure the new session doesn't overlap with any of them
        for session in user["sessions"]:
            scheduled_session_date = dateparser.parse(session["datetime"])
            scheduled_delta = timedelta(minutes=session["duration_mins"])
            delta = timedelta(minutes=duration_total_mins)

            # Make sure the new session's starting point is either after/equal to the pre-scheduled ending point
            # OR the new session's ending point is either before/equal to the pre-scheduled starting point
            # Otherwise send an error message
            if not ((session_date >= scheduled_session_date + scheduled_delta) or (scheduled_session_date >= session_date + delta)):
                await reply(self.client, interaction, f'New sessions cannot overlap with other scheduled sessions.')
                return
        
        # Add the session to the user's session list
        session = await get_default_session()
        session["datetime"] = session_date.strftime("%a, %b %d, %Y, %I:%M %p")
        session["reminder_ahead_mins"] = reminder_mins
        session["server_id"] = server_id
        session["duration_mins"] = duration_total_mins
        session["description"] = description

        user["sessions"].append(session)

        # Sort the sessions in chronological order
        user["sessions"].sort(key=lambda x:dateparser.parse(x["datetime"]))

        # Save changes
        await save_userinfo(user_id, user)
        
        session_date_formatted = session_date.strftime("%a, %b %d, %Y, %I:%M %p")
        duration_hours = int(session["duration_mins"]/60)
        duration_mins = session["duration_mins"]%60

        message = f'New session added @ {session_date_formatted} for '

        if duration_hours == 0:
            message += f'{duration_mins} mins '
        elif duration_mins == 0:
            message += f'{duration_hours} hrs '
        else:
            message += f'{duration_hours} hrs and {duration_mins} mins '

        message += f'with a reminder {reminder_mins} mins beforehand.'

        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(AddSession(client))
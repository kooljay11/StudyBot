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

        
    @app_commands.command(name="testdatetime", description="Schedules a new session.")
    @app_commands.default_permissions(administrator=True)
    async def test_date_time(self, interaction: discord.Interaction, date_time: str, timezone: float = 99.0):        
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(self.client, user_id)
            user = await get_userinfo(user_id)

        if timezone >= 99:
            user_tz = deepcopy(user["timezone"])
        else:
            user_tz = timezone

        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            local_now = await utc_to_current(now, user_tz)
            session_date_display = dateparser.parse(f'{date_time}', settings={'RELATIVE_BASE': local_now})
        except Exception as err:
            print(f'Error: {err}')

        session_date = await current_to_utc(session_date_display, user["timezone"])

        session_date_formatted = session_date_display.strftime("%a, %b %d, %Y, %I:%M %p")
        message = f'Input: {date_time}'
        message += f'\nOutput (UTC): {session_date}'
        message += f'\nOutput (formatted, local): {session_date_formatted}'

        await reply(self.client, interaction, message)

        return
    
    @app_commands.command(name="addsession", description="Schedules a new session.")
    async def add_session(self, interaction: discord.Interaction, date_time: str, duration_hours: int = 0, duration_mins: int = 0, reminder_mins: int = -1, description: str = ""):        
        try:
            # Add a new user profile if necessary
            user_id = interaction.user.id
            try:
                user = await get_userinfo(user_id)
            except:
                await create_user_profile(self.client, user_id)
                user = await get_userinfo(user_id)

            try:
                user_tz = deepcopy(user["timezone"])
                now = datetime.now(UTC).replace(tzinfo=None)
                local_now = await utc_to_current(now, user_tz)
                session_date_display = dateparser.parse(f'{date_time}', settings={'RELATIVE_BASE': local_now})
                
                session_date = await current_to_utc(session_date_display, user["timezone"])
            except:
                await reply(self.client, interaction, f'Couldn\'t parse that date, sorry. Please check the external module documentation for further information: https://github.com/scrapinghub/dateparser')
                return
            
            # Prevent the date being in the past
            now = datetime.now(UTC).replace(tzinfo=None)
            if now >= session_date:
                await reply(self.client, interaction, f'You must schedule a session in the future.')
                return
            #print(f'now: {now}')
            
            # Get the current server id
            try:
                server_id = interaction.guild_id
                if user["default_guild_id"] < 0:
                    user["default_guild_id"] = server_id
                    await save_userinfo(user_id,user)
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
            
            session_date_formatted = session_date_display.strftime("%a, %b %d, %Y, %I:%M %p")
            time_str = await get_time_str(session["duration_mins"])

            message = f'New session added @ {session_date_formatted} for {time_str} with a reminder {reminder_mins} mins beforehand. '

            if session["description"] != "":
                message += f'Description: {session["description"]}'

            await reply(self.client, interaction, message)
        except Exception as err:
            print(f'Error: {err}')
            await send_console_message(self.client, err)


async def setup(client):
    await client.add_cog(AddSession(client))
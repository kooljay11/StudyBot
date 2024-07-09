import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class SetDefault(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="setdefault", description="Set different defaults.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Reminder time ahead of session (mins)", value="default_reminder_ahead"),
        app_commands.Choice(name="Duration of each session (mins)", value="default_duration"),
        app_commands.Choice(name="Server id", value="default_guild_id")
    ])
    async def setdefault(self, interaction: discord.Interaction, mode: str, value: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if mode == "default_reminder_ahead":
            # Make sure it is a number
            if not (value.isnumeric() and int(value) >= 0):
                await reply(self.client, interaction, f'Value must be a number >= 0.')
                return

            user["default_reminder_ahead"] = int(value)
            await save_userinfo(user_id, user)
            message = f'You will now be reminded {value} mins before an upcoming session.'

        elif mode == "default_duration":
            # Make sure it is a number
            if not (value.isnumeric() and int(value) >= 0):
                await reply(self.client, interaction, f'Value must be a number >= 0.')
                return
            
            user["default_duration"] = int(value)
            await save_userinfo(user_id, user)
            message = f'Default session duration has been set to {value} mins.'
        elif mode == "default_guild_id":
            # Make sure it is a valid guild
            try:
                guild = await self.client.fetch_guild(int(value))
            except:
                await reply(self.client, interaction, f'Invalid guild id.')
                return

            await save_userinfo(user_id, user)
            message = f'{guild.name} (id: {value}) was set as your default server.'
            
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(SetDefault(client))
import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class Nickname(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="nickname", description="Add/remove/list your nickname list.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="List", value="list"),
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    async def nickname(self, interaction: discord.Interaction, mode: str = "list", name: str = "", target_id: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if mode == "list":
            message = f'__**Nickname List**__'
            for nickname, id in user["nicknames"].items():
                message += f'\n{nickname}: {id}'

        elif mode == "add":
            user["nicknames"][name] = target_id
            
            await save_userinfo(user_id, user)

            message = f'Added {name} (id: {target_id}) to your nickname list.'
        elif mode == "remove":
            try:
                target_id = user["nicknames"].pop(name)
                await save_userinfo(user_id, user)
                message = f'{name} (id: {target_id}) was removed from your nickname list.'
            except:
                await reply(self.client, interaction, f'Nickname not found.')
                return
            
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(Nickname(client))
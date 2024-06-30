import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *

class Ping(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="ping", description="Sends a test message.")
    async def ping(self, interaction: discord.Interaction):
        bot_latency = round(self.client.latency * 1000)
        message = f'Pong! {bot_latency} ms.'
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Ping(client))
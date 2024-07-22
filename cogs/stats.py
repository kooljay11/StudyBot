import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class Stats(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="stats", description="Check the monthly/yearly/all-time stats of a user.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Monthly", value="monthly"),
        app_commands.Choice(name="Yearly", value="yearly"),
        app_commands.Choice(name="All-time", value="all-time")
    ])
    async def stats(self, interaction: discord.Interaction, mode: str = "monthly", target: str = ""):
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(user_id)
            user = await get_userinfo(user_id)

        if target != user_id and target != "":
            target_id_nick = await get_id_nickname(self.client, user, target)
            target_info = await get_userinfo(target_id_nick["id"])
            user_name = target_id_nick["name"]
        else:
            target_info = user
            user_name = str(await self.client.fetch_user(user_id))
        
        message = f'__**{user_name}\'s Stats ({mode})**__'

        message += f'\nTimezone UTC offset: {target_info["timezone"]}'
        message += f'\nPoints: {target_info["points"]}'

        if target_info["partner_id"] != 0:
            partner_id_nick = await get_id_nickname(self.client, user, target_info["partner_id"])
            partner_name = partner_id_nick["name"]
            partner_id = f'({partner_id_nick["id"]})'
        else:
            partner_name = 'None'
            partner_id = ''

        if target_info["next_partner_id"] != 0:
            next_partner_id_nick = await get_id_nickname(self.client, user, target_info["partner_id"])
            next_partner_name = next_partner_id_nick["name"]
            next_partner_id = f'({next_partner_id_nick["id"]})'
        else:
            next_partner_name = 'None'
            next_partner_id = ''

        message += f'\nPartner: {partner_name} {partner_id}'
        message += f'\nNext partner: {next_partner_name} {next_partner_id}'
        #message += f'\nGuild id: {target_info["guild_id"]}'
        server_name = await self.client.fetch_guild(target_info["default_guild_id"])
        message += f'\nDefault server: {server_name.name} ({target_info["default_guild_id"]})'
        message += f'\nDefault reminder ahead of session (mins): {target_info["default_reminder_ahead"]}'
        message += f'\nDefault session duration (mins): {target_info["default_duration"]}'
        message += f'\n\n'

        global_info = await get_globalinfo()

        if mode == "monthly":
            current_month = await get_current_month(target_info)
            message += await print_month(current_month)

        elif mode == "yearly":
            current_year = await get_current_year(target_info)
            year = await get_default_month()
            now = dt.now()
            year["date"] = now.strftime("%Y")

            for month in current_year:
                for attr, value in month.items():
                    if attr not in ["date", "rank", "sessions"]:
                        year[attr] += value

            message += await print_month(year)

            for month in current_year:
                message += '\n\n'
                message += await print_month(month)

        elif mode == "all-time":
            all_months = target_info["months"]
            all = await get_default_month()
            all["date"] = 'All-time'
            
            for month in all_months:
                for attr, value in month.items():
                    if attr not in ["date", "rank", "sessions"]:
                        all[attr] += value
            
            message += await print_month(all)

            for month in all_months:
                message += '\n\n'
                message += await print_month(month)

        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Stats(client))
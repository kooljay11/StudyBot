import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class Partner(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="partner", description="Show your partnership stats or set/remove your preferred partner for next month. Or toggle auto partnership on/off.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Show partnership", value="show"),
        app_commands.Choice(name="Set", value="set"),
        app_commands.Choice(name="Remove", value="remove"),
        app_commands.Choice(name="Toggle auto partnership", value="autopartner")
    ])
    async def partner(self, interaction: discord.Interaction, mode: str = "show", partner: str = ""):
        user_id = interaction.user.id

        # Make sure the user exists
        try:
            user = await get_userinfo(user_id)
        except:
            await reply(self.client, interaction, f'User not found.')
            return
        
        if mode == "show":
            # CHECK THIS
            message = f'__**Partnership**__'
            if user["partner_id"] != 0:
                partner_id_nick = await get_id_nickname(self.client, user, str(user["partner_id"]))
                partner_name = partner_id_nick["name"]
                partner_id = f'({partner_id_nick["id"]})'
            else:
                partner_name = 'None'
                partner_id = ''

            if user["next_partner_id"] != 0:
                next_partner_id_nick = await get_id_nickname(self.client, user, str(user["next_partner_id"]))
                next_partner_name = next_partner_id_nick["name"]
                next_partner_id = f'({next_partner_id_nick["id"]})'
            else:
                next_partner_name = 'None'
                next_partner_id = ''

            message += f'\nPartner: {partner_name} {partner_id}'
            message += f'\nNext partner: {next_partner_name} {next_partner_id}'
            
            # Get the user's current month
            current_month = await get_current_month(user)

            # Get the global_info config
            global_info = await get_globalinfo()

            if current_month["rank"] != "":
                emoji = global_info["monthly_emojis"][current_month["rank"]]
            else:
                emoji = ""

            message += f'\n\n**{current_month["date"]}** {emoji} '
            message += f'\nPoints earned solo: {current_month["points_earned_solo"]}'
            message += f'\nPoints lost solo: {current_month["points_lost_solo"]} (rate: {global_info["%_missed_penalty"]})'

            # Set partner name
            if partner_name == "None":
                if partner_id != 0:
                    partner_name = f"partner (id: {partner_id})"
                else:
                    partner_name = "partner"

            message += f'\nPoints earned from {partner_name}: {current_month["points_earned_from_partner"]} (rate: {global_info["%_partner_earnings"]})'
            message += f'\nPoints lost because of {partner_name}: {current_month["points_penalized_by_partner"]} (rate: {global_info["%_partner_penalty"]})'


        elif mode == "set":
            # Make sure the user exists
            try:
                partner_info = await get_userinfo_by_nick(user, partner)
            except:
                await reply(self.client, interaction, f'Target user not found.')
                return
            
            partner_id_nick = await get_id_nickname(self.client, user, partner)

            # Make sure they aren't already preferred partners
            if partner_id_nick["id"] == user["next_partner_id"]:
                await reply(self.client, interaction, f'You have already set that user as your preferred partner for next month.')
                return
            
            user["next_partner_id"] = partner_id_nick["id"]

            #Add partner's name to the nickname list if it's not there already
            user["nicknames"][partner_id_nick["name"]] = partner_id_nick["id"]
            
            await save_userinfo(user_id, user)

            message = f'Set {partner_id_nick["name"]} as your preferred partner for next month.'
        elif mode == "remove":
            try:
                partner_id_nick = await get_id_nickname(self.client, user, partner)
                message = f'{partner_id_nick["name"]} is no longer your preferred partner for next month.'
            except:
                message = f'You\'ve removed your preferred partner for next month.'
            
            user["next_partner_id"] = 0
            await save_userinfo(user_id, user)
        elif mode == "autopartner":
            user["auto_partner"] = not user["auto_partner"]
            message = f'Auto partnership is now: {user["auto_partner"]}.'
            await save_userinfo(user_id, user)
            
        await reply(self.client, interaction, message)



async def setup(client):
    await client.add_cog(Partner(client))
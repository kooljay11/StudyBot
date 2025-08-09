import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class SetTimeZone(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')

    # UTC +14 Christmas Island/Kiribati	+14
    # UTC +13 Tonga and 3 more	+13
    # UTC +12:45 Chatham Islands/New Zealand	+12.75
    # UTC +12 New Zealand with exceptions and 9 more	+12
    # UTC +11 small region of Russia and 6 more	+11
    # UTC +10:30 Lord Howe Island/Australia	+10.5
    # UTC +10 much of Australia and 6 more	+10
    # UTC +9:30 some regions of Australia	+9.5
    # UTC +9 Japan, South Korea and 5 more	+9
    # UTC +8:45 Western Australia/Australia	+8.75
    # UTC +8 China, Philippines and 11 more	+8
    # UTC +7 much of Indonesia, Thailand and 7 more	+7
    # UTC +6:30 Myanmar and Cocos Islands	+6.5
    # UTC +6 Bangladesh and 5 more	+6
    # UTC +5:45 Nepal	+5.75
    # UTC +5:30 India and Sri Lanka	+5.5
    # UTC +5 Pakistan and 9 more	+5
    # UTC +4:30 Afghanistan	+4.5
    # UTC +4 Azerbaijan and 8 more	+4
    # UTC +3:30 Iran	+3.5
    # UTC +3 Greece and 37 more	+3
    # UTC +2 Germany and 47 more	+2
    # UTC +1 United Kingdom and 22 more	+1
    # UTC +0 Iceland and 17 more	+0
    # UTC -1 most of Greenland and Cabo Verde	-1
    # UTC -2 Pernambuco/Brazil and 2 more	-2
    # UTC -2:30 Newfoundland and Labrador/Canada	-2.5
    # UTC -3 most of Brazil, Argentina and 9 more	-3
    # UTC -4 regions of USA and 34 more	-4
    # UTC -5 regions of USA and 9 more	-5
    # UTC -6 small region of USA and 10 more	-6
    # UTC -7 regions of USA and 2 more	-7
    # UTC -8 Alaska/USA and 2 more	-8
    # UTC -9 Alaska/USA and regions of French Polynesia	-9
    # UTC -9:30 Marquesas Islands/French Polynesia	-9.5
    # UTC -10 Hawaii/USA and 3 more	-10
    # UTC -11 regions of US Minor Outlying Islands and 2 more	-11
    # UTC -12 regions of US Minor Outlying Islands	-12

    # @app_commands.command(name="gettimezone", description="OBSOLETE: Get the current time zone from your computer.")
    # async def get_timezone(self, interaction: discord.Interaction):
    #     now = datetime.now()
    #     utc_now = datetime.now(timezone.utc)
    #     tz_now = utc_now.astimezone()

    #     message = f'now: {now}\nutc_now: {utc_now}\ntz_now: {tz_now}'
    #     await reply(self.client, interaction, message)

    
    @app_commands.command(name="settimezone", description="Set your time zone.")
    async def set_timezone(self, interaction: discord.Interaction, utc_offset: float):
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(self.client, user_id)
            user = await get_userinfo(user_id)
        
        # Don't let the user set a decimal timezone
        if utc_offset % 1 > 0:
            await reply(self.client, interaction, f'Decimal UTC offsets do not work with the current dateparser module. Please select a whole number UTC offset for now.')
            return
        
        user["timezone"] = utc_offset

        await save_userinfo(user_id, user)

        utc_now = datetime.now(timezone.utc)
        utc_string = utc_now.strftime("%a, %b %d, %Y, %I:%M %p")

        tz_now = await utc_to_current(utc_now, utc_offset)
        tz_string = tz_now.strftime("%a, %b %d, %Y, %I:%M %p")
        
        message = f'UTC time: {utc_string}\nYour time: {tz_string}'
        await reply(self.client, interaction, message)

    @app_commands.command(name="checktimezone", description="Check if your time zone is correct.")
    async def check_timezone(self, interaction: discord.Interaction):
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(self.client, user_id)
            user = await get_userinfo(user_id)

        utc_now = datetime.now(timezone.utc)
        utc_string = utc_now.strftime("%a, %b %d, %Y, %I:%M %p")

        tz_now = await utc_to_current(utc_now, user["timezone"])
        tz_string = tz_now.strftime("%a, %b %d, %Y, %I:%M %p")
        
        message = f'UTC time: {utc_string}\nYour time (UTC {user["timezone"]}): {tz_string}'
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(SetTimeZone(client))
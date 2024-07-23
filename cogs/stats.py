import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *
import os

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



    @app_commands.command(name="lb", description="Check the monthly/yearly/all-time leaderboard.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Monthly", value="monthly"),
        app_commands.Choice(name="Yearly", value="yearly"),
        app_commands.Choice(name="All-time", value="all-time")
    ])
    @app_commands.describe(scope="Scope")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Friends", value="friends"),
        app_commands.Choice(name="Guild", value="guild"),
        app_commands.Choice(name="Server", value="server"),
        app_commands.Choice(name="All", value="all")
    ])
    @app_commands.describe(stat="Stat")
    @app_commands.choices(stat=[
        app_commands.Choice(name="Number of completed sessions", value="completed_sessions"),
        app_commands.Choice(name="Time studied", value="mins_studied"),
        app_commands.Choice(name="Ranks", value="rank")
    ])
    @app_commands.describe(users_per_page="Number of users to display per page (max 50)")
    async def leaderboard(self, interaction: discord.Interaction, mode: str = "monthly", scope: str = "server", stat: str = "mins_studied", users_per_page: int = 10, page_number: int = -1):
        # Add a new user profile if necessary
        user_id = interaction.user.id
        try:
            user = await get_userinfo(user_id)
        except:
            await create_user_profile(user_id)
            user = await get_userinfo(user_id)

        users = []

        if scope == "friends":
            users = user["friends"]
        elif scope == "guild":
            await reply(self.client, interaction, f'Guilds are not implemented yet.')
            return
        elif scope == "server":
            server_id = interaction.guild.id
            
            for filename in os.listdir("./data/user_data"):
                if filename.endswith(".json"):
                    server_user_id = os.path.splitext(filename)[0]
                    server_user = await get_userinfo(server_user_id)

                    if server_user["default_guild_id"] == server_id:
                        users.append(server_user_id)
        elif scope == "all":
            for filename in os.listdir("./data/user_data"):
                if filename.endswith(".json"):
                    server_user_id = os.path.splitext(filename)[0]
                    users.append(server_user_id)
        
        target_list = []

        global_info = await get_globalinfo()
        #print(f'target_list: {target_list}')


        for target_id in users:
            target_data = await get_default_month()
            target = await get_userinfo(target_id)
            target_data["ranks"] = []
            target_id_nick = await get_id_nickname(self.client, user, target_id)
            #print(f'target_data["ranks"]: {target_data["ranks"]}')
            target_data["user_name"] = target_id_nick["name"]
            target_data["user_id"] = target_id
            #print(f'target_data["user_id"]: {target_data["user_id"]}')
            all_months = []

            if mode == "monthly":
                current_month = await get_current_month(target)
                all_months.append(current_month)
                #print(f'target_data["ranks"] post: {target_data["ranks"]}')
            elif mode == "yearly":
                all_months = await get_current_year(target)
            elif mode == "all-time":
                all_months = target["months"]
            #print(f'target_id_nick: {target_id_nick}')
            
                
            for month in all_months:
                for attr, value in month.items():
                    if stat == "completed_sessions" and attr in ["completed_sessions", "failed_sessions"]:
                        target_data[attr] += value
                    elif stat == "mins_studied" and attr in ["mins_studied", "mins_scheduled"]:
                        target_data[attr] += value
                    elif attr == "rank":
                        target_data["ranks"].append(global_info["monthly_emojis"][value])
            
            if stat == "completed_sessions":
                total_sessions = target_data["completed_sessions"]+target_data["failed_sessions"]

                if total_sessions != 0:
                    target_data["percent"] = round(target_data["completed_sessions"]/total_sessions * 100)
                else:
                    target_data["percent"] = 'NA'
            elif stat == "mins_studied":
                if target_data["mins_scheduled"] != 0:
                    target_data["percent"] = round(target_data["mins_studied"]/target_data["mins_scheduled"] * 100)
                else:
                    target_data["percent"] = 'NA'
            elif stat == "rank":
                #print(f'target_data["ranks"] presort: {target_data["ranks"]}')
                target_data["ranks"].sort(reverse=True)
                #print(f'target_data["ranks"] postsort: {target_data["ranks"]}')

                target_data["ranks"] = await get_top_5_ranks(target_data["ranks"])
                #print(f'target_data["ranks"] postcull: {target_data["ranks"]}')
                
                #Assign a rank score for easy sorting
                target_data["rank"] = await get_rank_value(target_data["ranks"])
                #print(f'target_data["rank"]: {target_data["rank"]}')
            
            target_list.append(target_data)


        target_list.sort(key=lambda x:x[stat],reverse=True)

        #print(f'target_list: {target_list}')

        leaderboard = []

        #If stat = rank
        user_name = str(await self.client.fetch_user(target_id))
        #print(f'user_name: {user_name}')
        user_index = 0
        index = 0
        while index < len(target_list):
            target = target_list[index]
            #print(f'index: {index}')
            if stat in ["completed_sessions"]:
                
                leaderboard.append(f'{index+1}\t{target["user_name"]} --- {target[stat]} ({target["percent"]}%)')
                #print(f'leaderboard[index]: {leaderboard[index]}')
            elif stat == "mins_studied":
                time_str = await get_time_str(target[stat])
                leaderboard.append(f'{index+1}\t{target["user_name"]} --- {time_str} ({target["percent"]}%)')
            elif stat == "rank":
                leaderboard.append(f'{index+1}\t{target["user_name"]} --- {" ".join(target["ranks"])}')
            
            if target["user_name"] == user_name:
                user_index = index
            
            index += 1
        
        #print(f'leaderboard: {leaderboard}')

        if page_number < 0:
            page_number = 1
            #Find which page the user is on
            while user_index > users_per_page:
                page_number += 1
                user_index -= users_per_page
        
        target_page = leaderboard[(page_number-1)*users_per_page : page_number*users_per_page]
        #print(f'target_page: {target_page}')
        message = f'__**Leaderboard ({stat})**__ (Page {page_number})'
        message += f'\n{"\n".join(target_page)}'

        await reply(self.client, interaction, message)

async def setup(client):
    await client.add_cog(Stats(client))
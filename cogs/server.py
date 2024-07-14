import discord
from discord import app_commands
from discord.ext import commands, tasks
from utilities import *
from datetime import *

class Server(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        print(f'{__name__} loaded successfully!')
    
    @app_commands.command(name="server", description="Set/add/remove/list entries from your server's options.")
    @app_commands.describe(mode="Mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Set", value="set"),
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove"),
        app_commands.Choice(name="List", value="list")
    ])
    @app_commands.describe(attribute="Attribute to be edited")
    @app_commands.choices(attribute=[
        app_commands.Choice(name="Server name", value="name"),
        app_commands.Choice(name="Server's 2-4 letter abbreviation", value="4L_abbr"),
        app_commands.Choice(name="Reminder channel id", value="reminder_channel_id"),
        app_commands.Choice(name="Bot updates channel id (not implemented)", value="updates_channel_id"),
        app_commands.Choice(name="Commands channel ids (not implemented)", value="commands_channel_ids"),
        app_commands.Choice(name="Admin channel ids (not implemented)", value="admin_commands_channel_id"),
        app_commands.Choice(name="Study VCs checked by the bot", value="study_vc_ids")
    ])
    @app_commands.default_permissions(administrator=True)
    async def server(self, interaction: discord.Interaction, mode: str = "list", attribute: str = "", value: str = ""):
        server_id = interaction.guild_id

        servers = await get_serverinfo()

        # Make sure the server exists, otherwise create a new server profile
        try:
            server = servers[str(server_id)]
        except:
            server = await get_default_server()
            server["id"] = server_id
            server["name"] = interaction.guild.name
            servers[str(server_id)] = server
            await save_serverinfo(servers)
        
        if mode == "list":
            message = f'__**Server Options List**__'
            if server["4L_abbr"] != "":
                message += f'\n[Abbr] Name (id): [{server["4L_abbr"]}] {server["name"]} ({server["id"]})'
            else:
                message += f'\nName (id): {server["name"]} ({server["id"]})'
            
            if server["reminder_channel_id"] != 0:
                message += f'\nReminder channel: {self.client.get_channel(server["reminder_channel_id"]).name} ({server["reminder_channel_id"]})'

            if server["updates_channel_id"] != 0:
                message += f'\nUpdates channel: {self.client.get_channel(server["reminder_channel_id"]).name} ({server["reminder_channel_id"]})'

            command_channels = []

            for id in server["commands_channel_ids"]:
                command_channels.append(f'{self.client.get_channel(id).name} ({id})')
            
            if command_channels != []:
                message += f'\nCommand channel ids: {', '.join(command_channels)}'
            
            if server["admin_commands_channel_id"] != 0:
                message += f'\nAdmin commands channel: {self.client.get_channel(server["admin_commands_channel_id"]).name} ({server["admin_commands_channel_id"]})'

            study_vcs = []

            for id in server["study_vc_ids"]:
                study_vcs.append(f'{self.client.get_channel(id).name} ({id})')
            
            message += f'\nStudy VCs: {', '.join(study_vcs)}'

        elif mode == "set":
            #Works with all attributes except commands_channel_ids and study_vc_ids
            if attribute == "name":
                server["name"] = value
                await save_serverinfo(servers)
                message = f'Set server nickname to: {value}'
            elif attribute == "4L_abbr":
                if 2 <= len(value) <= 4:
                    server["4L_abbr"] = value
                    await save_serverinfo(servers)
                    message = f'Set server abbreviation to: {value}'
                elif value == "":
                    server["4L_abbr"] = ""
                    await save_serverinfo(servers)
                    message = f'Cleared server abbreviation.'
                else:
                    message = f'Invalid input. Server abbreviation must be between 2 to 4 characters long.'
            elif attribute == "reminder_channel_id":
                if value.isnumeric() and str(self.client.get_channel(int(value)).type) == 'text':
                    server["reminder_channel_id"] = int(value)
                    await save_serverinfo(servers)
                    message = f'Set reminder channel to {value}.'
                elif value == "":
                    server["reminder_channel_id"] = 0
                    await save_serverinfo(servers)
                    message = f'Cleared reminder channel.'
                else:
                    message = f'Invalid channel id. Make sure it is a text channel.'
            elif attribute == "updates_channel_id":
                if value.isnumeric() and str(self.client.get_channel(int(value)).type) == 'text':
                    server["updates_channel_id"] = int(value)
                    await save_serverinfo(servers)
                    message = f'Set updates channel to {value}.'
                elif value == "":
                    server["updates_channel_id"] = 0
                    await save_serverinfo(servers)
                    message = f'Cleared updates channel.'
                else:
                    message = f'Invalid channel id. Make sure it is a text channel.'
            elif attribute == "admin_commands_channel_id":
                if value.isnumeric() and str(self.client.get_channel(int(value)).type) == 'text':
                    server["admin_commands_channel_id"] = int(value)
                    await save_serverinfo(servers)
                    message = f'Set admin commands channel to {value}.'
                elif value == "":
                    server["admin_commands_channel_id"] = 0
                    await save_serverinfo(servers)
                    message = f'Cleared admin commands channel.'
                else:
                    message = f'Invalid channel id. Make sure it is a text channel.'
            else:
                message = f'Invalid mode or attribute. Set mode can only be used with the following attributes: name, 4L_abbr, reminder_channel_id, updates_channel_id, updates_channel_id, admin_commands_channel_id.'

        elif mode == "add":
            #Works with only commands_channel_ids and study_vc_ids
            if attribute == "commands_channel_ids":
                #Make sure the channel is a valid text channel
                #print(f'self.client.get_channel(int(value)).type: {self.client.get_channel(int(value)).type}')
                if value.isnumeric() and str(self.client.get_channel(int(value)).type) == 'text':
                    server["commands_channel_ids"].append(int(value))
                    await save_serverinfo(servers)
                    message = f'Added channel {value} to the list of command channels.'
                else:
                    message = f'Invalid channel id. Make sure it is a text channel.'
            elif attribute == "study_vc_ids":
                if value.isnumeric() and str(self.client.get_channel(int(value)).type) == 'voice':
                    server["study_vc_ids"].append(int(value))
                    await save_serverinfo(servers)
                    message = f'Added channel {value} to the list of study vcs.'
                else:
                    message = f'Invalid channel id. Make sure it is a voice channel.'
            else:
                message = f'Invalid mode or attribute. Add mode can only be used with the following attributes: commands_channel_ids, study_vc_ids.'
        elif mode == "remove":
            #Works with only commands_channel_ids and study_vc_ids
            if attribute == "commands_channel_ids":
                #Make sure the channel is in the list
                if value.isnumeric() and int(value) in server["commands_channel_ids"]:
                    server["commands_channel_ids"].remove(int(value))
                    await save_serverinfo(servers)
                    message = f'Removed channel {value} from the list of command channels.'
                else:
                    message = f'Invalid channel id. Make sure it is in the command channel list.'
            elif attribute == "study_vc_ids":
                if value.isnumeric() and int(value) in server["study_vc_ids"]:
                    server["study_vc_ids"].remove(int(value))
                    await save_serverinfo(servers)
                    message = f'Removed channel {value} from the list of study vcs.'
                else:
                    message = f'Invalid channel id. Make sure it is in the study vc list.'
            else:
                message = f'Invalid mode or attribute. Remove mode can only be used with the following attributes: commands_channel_ids, study_vc_ids.'
        
        await reply(self.client, interaction, message)


async def setup(client):
    await client.add_cog(Server(client))
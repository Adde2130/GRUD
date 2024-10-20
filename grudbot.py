import discord
import os

from discord.ext.commands import Bot
from discord.errors import HTTPException, LoginFailure, NotFound

class GRUDBot(Bot):
    def __init__(self, replay_channel_id: int):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)
        self.replay_channel_id = replay_channel_id
        self.connected = False
        self.error = ""


    # Poor man's multithreading exception handling
    def run(self, apikey: str):
        try:
            super().run(apikey)
        except LoginFailure as e:
            self.error = "LoginFailure"
            raise e # We still WANT the thread to crash

    async def on_ready(self):
        try:
            self.replay_channel = self.get_channel(self.replay_channel_id)
            if self.replay_channel is None:
                self.replay_channel = await self.fetch_channel(self.replay_channel_id)
                if self.replay_channel is None:
                    self.error = "ChannelNotFound"
                    print("\033[91mWARNING: We didn't find a channel, yet an error wasn't raised???\033[0m")

        except (NotFound, HTTPException) as e:
            self.error = "ChannelNotFound"
            raise e

        if self.error == "": 
            self.connected = True
            print("GRUDBot logged in")


    async def send_file(self, file_path: str):
        try:
            with open(file_path, "rb") as file:
                discord_file = discord.File(file, filename=os.path.basename(file_path))
                await self.replay_channel.send(file=discord_file)

        except FileNotFoundError:
            print(f"\033[91mFile not found: {file_path}\033[0m")
        except HTTPException as e:
            if e.status == 413:
                # TODO: Handle payload too large
                print(f"\033[91mUh oh! Payload too large! Adde made a mistake somewhere. Payload: {file_path}\033[0m")
            else:
                raise e

    async def send_message(self, message: str):
        if message == "":
            return

        if "@" in message:
            for member in self.replay_channel.guild.members:
                if f"@{member.display_name}" in message:
                    message = message.replace(f"@{member.display_name}", member.mention)
            
            for role in self.replay_channel.guild.roles:
                if f"@{role.name}" in message:
                    message = message.replace(f"@{role.name}", role.mention)

        if "@Everyone" in message.lower():
            message = message.replace(f"@Everyone", "@everyone")


        await self.replay_channel.send(content=message)


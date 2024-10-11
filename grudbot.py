import discord
import os

from discord.ext.commands import Bot
from discord.errors import HTTPException

class GRUDBot(Bot):
    def __init__(self, replay_channel_id: int):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.replay_channel_id = replay_channel_id


    async def on_ready(self):
        self.replay_channel = self.get_channel(self.replay_channel_id)
        if self.replay_channel is None:
            self.replay_channel = await self.fetch_channel(self.replay_channel_id)
            if self.replay_channel is None:
                print("WARNING: GRUDBot could not fetch the replay channel!!!")

        print("GRUDBot logged in")


    async def send_file(self, file_path: str):
        try:
            with open(file_path, "rb") as file:
                discord_file = discord.File(file, filename=os.path.basename(file_path))
                await self.replay_channel.send(file=discord_file)

        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except HTTPException as e:
            if e.status == 413:
                # TODO: Handle payload too large
                print(f"\033[91mUh oh! Payload too large! Adde made a mistake somewhere. Payload: {file_path}\033[0m")
                pass
            else:
                raise e

    async def send_message(self, message: str):
        await self.replay_channel.send(content=message)

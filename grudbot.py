import discord
import os
import argparse
import json

from discord.ext.commands import Bot
from discord.errors import HTTPException, LoginFailure, NotFound
from aiohttp.client_exceptions import ClientConnectorDNSError

class GRUDBot(Bot):
    def __init__(self, replay_channel_id: int):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)
        self.connected = False
        self.error = ""
        self.replay_channel_id = replay_channel_id


    # Poor man's multithreading exception handling
    def run(self, apikey: str, message="", file=""):
        self.message = message
        self.file = file

        try:
            if message or file:
                super().run(apikey)
            else:
                super().run(apikey, log_handler=None)
        except LoginFailure as e:
            self.error = "LoginFailure"
            raise e # We still WANT the thread to crash
        except ClientConnectorDNSError as e:
            print(type(e))
            self.error = "NoInternet"
            raise e

    async def on_ready(self):
        try:
            self.replay_channel = self.get_channel(self.replay_channel_id)
            if self.replay_channel is None:
                self.replay_channel = await self.fetch_channel(self.replay_channel_id)
                if self.replay_channel is None:
                    self.error = "ChannelNotFound"
                    print("\033[91mWARNING: We didn't find a channel, yet an error wasn't raised???\033[0m")
                    return

        except (NotFound, HTTPException) as e:
            self.error = "ChannelNotFound"
            raise e

        self.connected = True
        print("GRUDBot logged in")

        if self.message or self.file:
            if self.message:
                await self.send_message(self.message)
            if self.file:
                await self.send_file(self.file)
            await self.close()


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

        if message[0:2] == "rm":
            try:
                msgs = int(message[2:].strip())
                await self.remove_msgs(msgs)
                return
            except ValueError as e:
                pass

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


    async def remove_msgs(self, message_count: int):
        try:
            if self.replay_channel:
                messages = [message async for message in self.replay_channel.history(limit=message_count)]
                if messages:
                    await self.replay_channel.delete_messages(messages)
                    print(f"Successfully deleted {message_count} messages.")
                else:
                    print(f"No messages found to delete.")
        except HTTPException as e:
            print(f"Failed to delete messages: {e}")



if __name__ == "__main__":
    if not os.path.exists("settings.json"):
        print("\033[91msettings.json not found\033[0m")
        exit(-1)

    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", type=str)
    parser.add_argument("--file", "-f", type=str, help="Path to file to send")

    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"\033[91mFile {args.file} not found\033[0m")
            exit(-1)
            
    if not args.message and not args.file:
            print(f"\033[91mNeither message nor file specified\033[0m")
            exit(-1)

    with open("settings.json", "r") as f:
        settings = json.load(f)
    
    grud = GRUDBot(settings["ReplayChannelID"])
    grud.run(settings["GRUDBot_APIKEY"], file=args.file, message=args.message)

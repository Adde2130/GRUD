import discord
import os
import argparse
import json
import time
import sys
import logging

from discord.ext.commands import Bot
from discord.errors import HTTPException, LoginFailure, NotFound, Forbidden
from aiohttp.client_exceptions import ClientConnectorDNSError

# Make the logger stop clogging the log file
discord_logger = logging.getLogger('discord')
discord_logger.propagate = False

for handler in discord_logger.handlers[:]:
    discord_logger.removeHandler(handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

discord_logger.addHandler(stream_handler)


# Ref: https://discordpy.readthedocs.io/en/stable/api.html
class GRUDBot(Bot):
    def __init__(self, replay_channel_id: int):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)
        self.connected = False
        self.error = ""
        self.replay_channel_id = replay_channel_id


    # Poor man's multithreading exception handling
    def run(self, apikey: str, start_func=None, logging=False):
        self.start_func = start_func

        try:
            super().run(apikey, log_handler=handler)

        except LoginFailure as e:
            self.error = "LoginFailure"
            raise e # We still WANT the thread to crash
        except ClientConnectorDNSError as e:
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

        if self.start_func is not None:
            await self.start_func
            await self.close()


    async def send_file(self, file_path: str):
        try:
            with open(file_path, "rb") as file:
                discord_file = discord.File(file, filename=os.path.basename(file_path))
                await self.replay_channel.send(file=discord_file)

        except FileNotFoundError:
            print(f"\033[91mFile not found: {file_path}\033[0m")
        except HTTPException as e:
            raise e

    async def send_message(self, message: str, reply_message_id=None):
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


        if reply_message_id:
            _message = await self.replay_channel.fetch_message(reply_message_id)
            await _message.reply(content=message)

        else:
            await self.replay_channel.send(content=message)


    async def remove_message(self, message_id: int, channel_id=None) -> None:
        if channel_id is None:
            channel = self.replay_channel
        else:
            channel = self.get_channel(channel_id)

        try:
            msg = await channel.fetch_message(message_id)
        except NotFound:
            print("Message not found!")
            return
        except Forbidden:
            print("Insufficient permissions!")
            return


        try:
            await msg.delete()
        except Forbidden:
            print("You don't have permission to remove this message")
            


    async def remove_messages(self, message_count: int) -> None:
        try:
            if self.replay_channel:
                messages = [
                        message async for message in self.replay_channel.history(limit=100)
                        if message.author.id == self.user.id
                ]

                messages = messages[:message_count]

                if not messages:
                    print(f"No messages found to delete.")
                    return

                for message in messages:
                    await message.delete()

                print(f"Successfully deleted {message_count} messages.")
        except HTTPException as e:
            print(f"Failed to delete message: {e}")



if __name__ == "__main__":
    if not os.path.exists("settings.json"):
        print("\033[91msettings.json not found\033[0m")
        exit(-1)

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--message", "-m", type=str, help="Send a message")
    group.add_argument("--file", "-f", type=str, help="Send a file")
    group.add_argument("--remove-message", "-rm", type=int, help="Remove message with the provided messageID")
    group.add_argument("--reply", "-r", nargs=2, help="Remove message with the provided messageID")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        print(f"\033[91mNo args passed\033[0m")
        exit(-1)


    if args.file:
        if not os.path.exists(args.file):
            print(f"\033[91mFile {args.file} not found\033[0m")
            exit(-1)

    with open("settings.json", "r") as f:
        settings = json.load(f)


    grud = GRUDBot(settings["ReplayChannelID"])

    if args.file:
        coroutine = grud.send_file(args.file)
    elif args.message:
        coroutine = grud.send_message(args.message)
    elif args.remove_message:
        coroutine = grud.remove_message(args.remove_message)
    elif args.reply:
        coroutine = grud.send_message(args.reply[0], reply_message_id=args.reply[1])
    
    grud.run(settings["GRUDBot_APIKEY"], coroutine, logging=True)

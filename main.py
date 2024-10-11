import tkinter as tk
from tkinter import filedialog

import os
import string
import subprocess
import argparse
import json
import asyncio
import shutil
import zipfile
import compress
import time

from concurrent.futures import ProcessPoolExecutor 
from threading import Thread

from grudbot import GRUDBot 

drives = []
drive_path = []
drive_number = []
slippiFolders = {}

class GRUDApp:
    def __init__(self, settings, gui=True):
        self.drives = []
        self.drive_path = []
        self.listbox = None
        self.gui = gui 

        self.settings = settings

        self.tourney_name = settings["TourneyName"]
        self.edition = settings["Edition"] 

        self.start_grudbot()

        # Check for windows
        if os.name == "nt":
            self.drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            print("Only Windows is supported in this version of GRUD")
            exit(1)


        if gui:
            self.initGUI()

        self.refresh_drives()

        
    def initGUI(self):
        self.root = tk.Tk()
        self.root.title("GRUD")
        self.root.geometry("650x300")
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Tourney name and number
        self.tabb_box = tk.Entry(self.root, width=5)
        self.tabb_box.grid(row=4, column=2, sticky="S")
        self.tabb_box.insert(0, self.tourney_name)

        self.hash_text = tk.Label(self.root, text="#", font=("Gotham", 12))
        self.hash_text.grid(row=4, column=3, sticky="S")

        self.tser_box = tk.Entry(self.root, width=5)
        self.tser_box.grid(row=4, column=4, padx=0, sticky="S")
        self.tser_box.insert(0, self.edition)

        # List of drives
        self.listbox = tk.Listbox(self.root, width=70, height=15)
        self.listbox.grid(row=1,column=1, rowspan=7, columnspan=1, padx= 20, pady=20)

        # Buttons
        self.refresh_button = tk.Button(self.root, text="REFRESH DRIVES", command=self.refresh_drives, padx=8, pady=0, font=("Gotham", 8))
        self.refresh_button.grid(row=5,column=2,sticky="S", rowspan=1, columnspan=3)
        self.open_drives_button = tk.Button(self.root, text="GO TO DRIVES", command=self.openThisPC, padx=10, pady=0, font=("Gotham", 8))
        self.open_drives_button.grid(row=7,column=2,sticky="N", rowspan=1, columnspan=3)
        self.download_button = tk.Button(self.root, text="DOWNLOAD", command=self.download_button, padx=20, pady=10, font=("Gotham", 8))
        self.download_button.grid(row=6,column=2, rowspan=1, columnspan=3)



    def download_button(self):
        download_path = filedialog.askdirectory(title="Select a Directory")

        if download_path:
            print(f"Selected directory path: {download_path}")
            message = f"{self.tabb_box.get()} {self.tser_box.get()}"
            self.download(download_path, message)

        self.refresh_drives()

        
    def download(self, download_path: str, message: str):
        asyncio.run(self.transferReplays(download_path))

        folders_to_zip = [folder for folder in os.listdir(download_path) if "Setup #" in folder]

        print("Zipping...")

        with ProcessPoolExecutor() as executor:

            tasks = [
                executor.submit(
                    compress.compress_folder,
                    f"{download_path}/{folder}", 
                    self.settings["FileSizeLimit"] * 1024 * 1024
                    )
                for folder in folders_to_zip
            ]

            # Wait for tasks to complete...
            for task in tasks:
                task.result()

        future = asyncio.run_coroutine_threadsafe(self.grudbot.send_message(message), self.grudbot.loop)
        future.result()

        folders_to_send = [f"{download_path}/{folder}.zip" for folder in folders_to_zip]
        for folder in folders_to_send:
            future = asyncio.run_coroutine_threadsafe(self.grudbot.send_file(folder), self.grudbot.loop)
            future.result()

        print("Done!")


    # Open a file dialog to select a folder
    def refresh_drives(self):
        if self.gui:
            self.listbox.delete(0, tk.END)

        folderStatus = ""

        for drive in self.drives:
            wiiNum = 0

            slpFolderFound = False
            workingDrive = False
            
            replayPath = f"{drive}Slippi"
            for content in os.listdir(drive):
                if content.isdigit():
                    wiiNum = content
                    continue

                if content == "Slippi":
                    slpFolderFound = True
                    continue
                    

            if wiiNum == 0:
                slpMsg = "Numbered folder missing!"
                wiiNum = "?"
            elif not slpFolderFound:
                slpMsg = '"Slippi" replay folder missing!'
            else:
                file_count = len(os.listdir(replayPath))
                if not file_count:
                    slpMsg = "Replay folder empty!"
                else:
                    slpMsg = f"{file_count}"
                    workingDrive = True


            if workingDrive:
                slippiFolders[wiiNum] = replayPath
                dirName = replayPath
            else:
                dirName = f"{drive}?????"

            if self.gui:
                self.listbox.insert(tk.ACTIVE, dirName + " Wii#" + wiiNum + " ----- " + slpMsg + folderStatus)

    

    def openThisPC(self):
        if os.name == "nt":
            subprocess.Popen("explorer.exe shell:MyComputerFolder")  


    def on_window_close(self):
        self.root.destroy()
        self.stop_grudbot();


    # :)
    def start_grudbot(self):
        self.grudbot = GRUDBot(self.settings["ReplayChannelID"])
        self.bot_thread = Thread(target=self.grudbot.run, args=((self.settings["GRUDBot_APIKEY"]), ))
        self.bot_thread.start()
        

    # :(
    def stop_grudbot(self):
        #TODO: ERRORS HAPPEN HERE, FIX THIS FIX THIS FIX THIS FIX THIS FIX THIS
        asyncio.run_coroutine_threadsafe(self.grudbot.close(), self.grudbot.loop)
        self.bot_thread.join()


    async def transferReplays(self, dest: str):
        if not os.path.exists(dest):
            print(f"Destination path '{dest}' does not exist")
            return

        if len(slippiFolders) == 0:
            print("No USB drives to download from!")
            return

        for wiiNum, slippiFolder in slippiFolders.items():
            setupPath = f"{dest}/Setup #{wiiNum}"
            os.makedirs(setupPath, exist_ok=True)
            for file in os.listdir(slippiFolder):
                src = f"{slippiFolder}/{file}"
                shutil.move(src, setupPath)
            print(f"Wii {wiiNum} complete")
            await asyncio.sleep(0)


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--naked", action="store_true", help="Run without any GUI")
    args = parser.parse_args()

    
    # Parse settings
    if os.path.isfile("settings.json"):
        with open("settings.json", "r") as file:
            settings = json.load(file)


        app = GRUDApp(
                gui=not args.naked, 
                settings=settings
            )
    else:
        print("Could not find settings.json")
        exit(1)

    if(not args.naked):
        app.root.mainloop()
    else:
        dest = os.path.dirname(os.path.abspath(__file__)) + "/Replays"
        os.makedirs(dest, exist_ok=True)
        app.download(dest, "TEST")


if __name__ == "__main__":
    main()


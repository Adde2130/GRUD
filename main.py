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

from concurrent.futures import ProcessPoolExecutor 

drives = []
drive_path = []
drive_number = []
slippiFolders = {}

class GRUDApp:
    def __init__(self, gui=True, tourney_name="", edition=""):
        self.drives = []
        self.drive_path = []
        self.listbox = None
        self.gui = gui 
        self.tourney_name = tourney_name
        self.edition = edition


        # Check for windows
        if os.name == "nt":
            self.drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            print("Only Windows is supported in this version of GRUD")
            exit(1)


        if gui:
            self.initGUI()

        self.getDrivesContent()

        
    def initGUI(self):
        self.root = tk.Tk()
        self.root.title("GRUD")
        self.root.geometry("650x300")

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
        self.refresh_button = tk.Button(self.root, text="REFRESH DRIVES", command=self.getDrivesContent, padx=8, pady=0, font=("Gotham", 8))
        self.refresh_button.grid(row=5,column=2,sticky="S", rowspan=1, columnspan=3)
        self.open_drives_button = tk.Button(self.root, text="GO TO DRIVES", command=self.openThisPC, padx=10, pady=0, font=("Gotham", 8))
        self.open_drives_button.grid(row=7,column=2,sticky="N", rowspan=1, columnspan=3)
        self.download_button = tk.Button(self.root, text="DOWNLOAD", command=self.download_button, padx=20, pady=10, font=("Gotham", 8))
        self.download_button.grid(row=6,column=2, rowspan=1, columnspan=3)


    def download_button(self):
        download_path = filedialog.askdirectory(title="Select a Directory")

        if download_path:
            print(f"Selected directory path: {download_path}")
            self.download(download_path)

        self.getDrivesContent()

        
    def download(self, download_path):
        asyncio.run(self.transferReplays(download_path))

        folders_to_zip = [folder for folder in os.listdir(download_path) if "Setup #" in folder]

        print("Zipping...")

        with ProcessPoolExecutor() as executor:

            tasks = [
                executor.submit(compressFolder, f"{download_path}/{folder}")
                for folder in folders_to_zip
            ]

            # Wait for tasks to complete...
            for task in tasks:
                task.result()

        print("Done!")


    # Open a file dialog to select a folder
    def getDrivesContent(self):
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


def compressFolder(path):
    with zipfile.ZipFile(f"{path}.zip", "w", zipfile.ZIP_LZMA, compresslevel=9) as zipf:
        for file in os.listdir(path):
            zipf.write(f"{path}/{file}", arcname=file)

        shutil.rmtree(path)

    print(f"{path} zipped")


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
                tourney_name=settings["TourneyName"],
                edition=settings["Edition"]
            )
    else:
        app = GRUDApp(gui=not args.naked)

    if(not args.naked):
        app.root.mainloop()
    else:
        dest = os.path.dirname(os.path.abspath(__file__)) + "/Replays"
        os.makedirs(dest, exist_ok=True)
        app.download(dest)


if __name__ == "__main__":
    main()


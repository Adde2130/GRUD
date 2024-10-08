import tkinter as tk
from tkinter import filedialog

import os
import string
import subprocess
import argparse
import json

from pathlib import Path

drives = []
drive_path = []
drive_number = []

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
            self.getDrives()

        

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
        self.refresh_button = tk.Button(self.root, text="REFRESH DRIVES", command=self.getDrives, padx=8, pady=0, font=("Gotham", 8))
        self.refresh_button.grid(row=5,column=2,sticky="S", rowspan=1, columnspan=3)
        self.open_drives_button = tk.Button(self.root, text="GO TO DRIVES", command=self.openThisPC, padx=10, pady=0, font=("Gotham", 8))
        self.open_drives_button.grid(row=7,column=2,sticky="N", rowspan=1, columnspan=3)
        self.download_button = tk.Button(self.root, text="DOWNLOAD", command=self.download, padx=20, pady=10, font=("Gotham", 8))
        self.download_button.grid(row=6,column=2, rowspan=1, columnspan=3)


    def hasReplayFolder(self, folderName):
        if folderName != "Slippi":
            return "No folder named Slippi!"
        else:
            return ""


    def download(self):
        download_path = filedialog.askdirectory(
            title="Select a Directory"
        )

        if download_path:
            print(f"Selected directory path: {download_path}")
        return download_path


    # Open a file dialog to select a folder
    def getDrives(self):
        self.listbox.delete(0, tk.END)
        msg = "start"
        folderStatus = ""
            # List all files and directories in the selected path with full paths
        for item in self.drives:
            print(msg)
            numFolderFound = False
            slpFolderFound = False
            for content in os.listdir(item):
                
                if content.isdigit():
                    wiiNum = content
                    numFolderFound = True

                if content == "Slippi":
                    slpFolderFound = True
                        
                    
                        #print(finalItem)
                        #print(os.path.join(item,content), wiiNum, slpMsg)
                if numFolderFound == True and slpFolderFound == True:
                    numOfFiles= sum(1 for d in Path(os.path.join(item, content)).iterdir() if Path(os.path.join(item, content)).is_file())
                    print(os.path.join(item, content))
                    slpMsg = f"{numOfFiles} files"
                    if slpMsg == "0 files":
                        slpMsg = "Replay folder empty!"
                    break
               
            
            if numFolderFound == False or slpFolderFound == False:
                if numFolderFound == True:
                    slpMsg = '"Slippi" replay folder missing!'
                else:
                    slpMsg = "Numbered folder missing!"
                    wiiNum = "?"
            if content == "Slippi":
                dirName = "Slippi"
            else:
                dirName = "??????"
            self.listbox.insert(tk.ACTIVE,os.path.join(item, dirName) + " Wii#" + wiiNum + " ----- " + slpMsg + folderStatus)

    def openThisPC(self):
        if os.name == "nt":
            subprocess.Popen("explorer.exe shell:MyComputerFolder")  
            

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
                tourney_name = settings["TourneyName"],
                edition = settings["Edition"]
            )
    else:
        app = GRUDApp(gui=not args.naked)

    if(not args.naked):
        app.root.mainloop()


if __name__ == "__main__":
    main()


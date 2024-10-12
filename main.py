import tkinter as tk
from tkinter import filedialog
import os
import customtkinter
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

COLORS = {"GRAY" : "#414151", "LIGHT_GREEN" : "#74e893", "YELLOW" : "#faf48c",
          "MAGENTA" : "#d953e6", "RED" : "#f54251", "BLUE" : "#8ab2f2"}

drives = []
drive_path = []
drive_number = []
slippi_folders = {}

#TODO: Make downloads non-blocking
class GRUDApp:
    def __init__(self, settings, gui=True):
        self.drives = []
        self.drive_path = []
        self.listbox = None
        self.gui = gui 

        self.settings = settings

        # Fix download path
        self.download_path = settings["DefaultDownloadPath"].replace("\\", "/")
        if not self.download_path or not os.path.isdir(self.download_path):
            self.download_path = ""


        # Check for windows
        if os.name == "nt":
            self.drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            print("Only Windows is supported in this version of GRUD")
            exit(1)

        self.start_grudbot()

        if gui:
            self.initGUI()

        self.refresh_drives()
        
    def initGUI(self):
        self.root = customtkinter.CTk()
        self.root.title("GRUD")
        self.root.geometry("800x400")
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["GRAY"])

        # Choose path
        self.checkbox = customtkinter.CTkCheckBox(self.root, width=10, height=1, corner_radius=0,
                                           text="Keep copy?", checkbox_width=30, font=("Cascadia Code", 16, "bold"))
        self.checkbox.grid(row=4, column=2, sticky="w", padx=20)
        self.path_button = tk.Button(self.root, text="Choose path...", command=self.select_path,
                                     font=("Cascadia Code", 16), state=tk.DISABLED, width=20, cursor="hand2")
        self.path_button.grid(row=4, column=2, sticky="w", padx=(240, 0), )

        if self.download_path:
            if len(self.download_path) > 18:
                path_text = f"...{self.download_path[-15:]}"
            else:
                path_text = self.download_path
            self.path_button.configure(text=path_text)
            self.checkbox.select()

        # Discord message box
        self.msg_box = tk.Text(self.root, width=40, height=2, font=("Arial", 16), fg="gray")
        self.msg_box.grid(row=5, column=2, sticky="S", rowspan=2)
        self.example_message = "Discord message here..."
        self.msg_box.insert("1.0", self.example_message)
        self.msg_box.bind("<FocusIn>", self.msg_focus_in)
        self.msg_box.bind("<FocusOut>", self.msg_focus_out)
        
        # List of drives
        self.listbox = tk.Listbox(self.root, width=50, height=15, font=("Cascadia Code", 12))
        self.listbox.grid(row=1,column=1, rowspan=7, columnspan=1, padx= 20, pady=20)

        # Bot status
        self.bot_label = customtkinter.CTkLabel(self.root, text="GRUDBot Status", font=("Cascadia Code", 24, "bold"), text_color=COLORS["MAGENTA"])
        self.bot_label.grid(row=1, column=2,  padx=30, sticky="s")
        self.bot_status = customtkinter.CTkLabel(self.root, text="Connecting...", font=("Cascadia Code", 24), text_color=COLORS["YELLOW"], anchor="w")
        self.bot_status.grid(row=2, column=2, padx=(110,0), sticky="w")

        # Buttons
        self.refresh_button = tk.Button(self.root, text="REFRESH DRIVES", command=self.refresh_drives,
                                        padx=8, pady=0, font=("Cascadia Code", 16), bg=COLORS["LIGHT_GREEN"], cursor="hand2")
        self.refresh_button.grid(row=9,column=0,sticky="W", rowspan=1, columnspan=3, padx=20)
        self.open_drives_button = tk.Button(self.root, text="GO TO DRIVES", command=self.openThisPC,
                                            padx=10, pady=0, font=("Cascadia Code", 16), bg=COLORS["YELLOW"], cursor="hand2")
        self.open_drives_button.grid(row=9,column=1,sticky="W", rowspan=1, columnspan=3, padx=295)
        self.download_button = tk.Button(self.root, text="DOWNLOAD", command=self.download_action, padx=20,
                                         pady=10, font=("Cascadia Code", 16), state=tk.DISABLED, cursor="hand2")
        self.download_button.grid(row=9,column=2, rowspan=1, columnspan=3)

        # Animation
        self.anim_counter = 0
        self.update_bot_status()
        self.update_misc()

    def msg_focus_in(self, event):
        if self.msg_box.get("1.0", tk.END).strip() == self.example_message:
            self.msg_box.delete("1.0", tk.END)
            self.msg_box.config(fg="black")


    def msg_focus_out(self, event):
        if self.msg_box.get("1.0", tk.END).strip() == "":
            self.msg_box.insert("1.0", self.example_message)
            self.msg_box.config(fg="gray")


    def update_bot_status(self):
        self.anim_counter += 1
        if not self.grudbot.connected:
            if self.grudbot.error == "LoginFailure":
                self.bot_status.grid_forget()
                self.bot_status.configure(text="Invalid API key!", text_color=COLORS["RED"], anchor="n")
                self.bot_status.grid(row=2, column=2, padx=0)

            elif self.grudbot.error == "ChannelNotFound":
                self.bot_status.grid_forget()
                self.bot_status.configure(text="Channel not found!", text_color=COLORS["RED"], anchor="n")
                self.bot_status.grid(row=2, column=2, padx=0)


            elif not self.anim_counter % 13:
                text = self.bot_status.cget("text")
                if text.count('.') == 3:
                    text = "Connecting."
                else:
                    text += '.'
                self.bot_status.configure(text=text)
        else:
            self.bot_status.grid_forget()
            self.bot_status.configure(text="Connected!", text_color=COLORS["LIGHT_GREEN"], anchor="n")
            self.bot_status.grid(row=2, column=2, padx=0)
            self.root.after(30, self.update_replay_download_status)

        self.root.after(30, self.update_bot_status)

    def update_replay_download_status(self):
        # TODO: ADD STATUS MESSAGES FOR TRANSFER, ZIPPING AND SENDING
        pass


    def update_misc(self):
        if self.checkbox.get() == 1:
            self.path_button.config(state=tk.NORMAL)
        else:
            self.path_button.config(state=tk.DISABLED)

        # Download button
        if self.grudbot.connected is False:
            self.download_button.config(state=tk.DISABLED, bg="white")
        elif not slippi_folders:
            self.download_button.config(state=tk.DISABLED, bg="white")
        elif self.checkbox.get() == 1 and self.download_path == "":
            self.download_button.config(state=tk.DISABLED, bg="white")
        else:
            self.download_button.config(state=tk.NORMAL, bg=COLORS["BLUE"])

        self.root.after(30, self.update_misc)

    def download_action(self):
        message = self.msg_box.get("1.0", tk.END).strip()
        if message == self.example_message:
            message = ""

        download_path = self.download_path
        print(download_path)
        if not download_path or self.checkbox.get() == 0:
            download_path = os.path.dirname(os.path.realpath(__file__))
            self.download(download_path, message, delete_files=True)
        else:
            self.download(download_path, message)
        self.refresh_drives()


    def select_path(self):
        download_path = filedialog.askdirectory(title="Select a directory to download to")
        
        if download_path:
            self.download_path = download_path
            if len(download_path) > 18:
                path_text = f"...{download_path[-15:]}"
            else:
                path_text = download_path
            self.path_button.configure(text=path_text)

        
    def download(self, download_path: str, message: str, delete_files=False):
        print(download_path)
        asyncio.run(self.transferReplays(download_path))

        folders_to_zip = [folder for folder in os.listdir(download_path) if "Setup #" in folder]

        self.zipping=True
        print("Zipping...")

        folders_to_remove = []
        
        for folder in folders_to_zip:
            if ".zip" in folder:
                printerror(f"The zip file {folder} already exists at this location. TODO: HANDLE THIS")
                folders_to_remove.append(folder)
        
        print(folders_to_zip)
        for folder in folders_to_remove:
            # Remove BOTH the zip file and the folder from the list
            print(folder)
            folders_to_zip.remove(folder[:-4])
            folders_to_zip.remove(folder)


        if not folders_to_zip:
            printerror("No folders to zip. Exiting function")
            self.zipping=False
            return

        folders_to_send = []

        with ProcessPoolExecutor() as executor:

            tasks = [
                executor.submit(
                    compress.compress_folder,
                    f"{download_path}/{folder}", 
                    self.settings["FileSizeLimit"] * 1024 * 1024
                    )
                for folder in folders_to_zip
            ]


            for i, task in enumerate(tasks):
                # Wait for tasks to complete...
                result = task.result()
                if result > 1: # We created multiple parts
                    for _ in range(0, result):
                        folders_to_send.append(f"{download_path}/{folders_to_zip[i]} part {i + 1}.zip")
                else:
                    folders_to_send.append(f"{download_path}/{folders_to_zip[i]}.zip")


        self.zipping=False
        self.sending=True
        
        future = asyncio.run_coroutine_threadsafe(self.grudbot.send_message(message), self.grudbot.loop)
        future.result()

        for folder in folders_to_send:
            future = asyncio.run_coroutine_threadsafe(self.grudbot.send_file(folder), self.grudbot.loop)
            future.result()
            if delete_files:
                os.remove(folder)

        print("Done!")
        self.sending=False
        self.done=True

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
                slippi_folders[wiiNum] = replayPath
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

        if len(slippi_folders) == 0:
            print("No USB drives to download from!")
            return

        for wiiNum, slippiFolder in slippi_folders.items():
            setupPath = f"{dest}/Setup #{wiiNum}"
            os.makedirs(setupPath, exist_ok=True)
            for file in os.listdir(slippiFolder):
                src = f"{slippiFolder}/{file}"
                shutil.move(src, setupPath)
            print(f"Wii {wiiNum} complete")
            await asyncio.sleep(0)


def printerror(text: str):
    print(f"\033[91m{text}\033[0m")

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
        printerror("Could not find settings.json")
        print("Creating settings.json")
        settings_json = {
            "GRUDBot_APIKEY" : "",
            "ReplayChannelID" : 0,
            "DefaultDownloadPath" : "",
            "FileSizeLimit" : 25
        }

        settings_object = json.dumps(settings_json, indent=4)
        with open("settings.json", "w") as file:
            file.write(settings_object)

        exit(1)

    if(not args.naked):
        app.root.mainloop()
    else:
        dest = os.path.dirname(os.path.abspath(__file__)) + "/Replays"
        os.makedirs(dest, exist_ok=True)
        app.download(dest, "TEST")


if __name__ == "__main__":
    main()


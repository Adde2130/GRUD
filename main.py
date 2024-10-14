import tkinter as tk
from tkinter import filedialog, font

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
import tempfile

from concurrent.futures import ProcessPoolExecutor 
from threading import Thread

from grudbot import GRUDBot 

COLORS = {"GRAY" : "#414151", "LIGHT_GREEN" : "#74e893", "YELLOW" : "#faf48c",
          "MAGENTA" : "#d953e6", "RED" : "#f54251", "BLUE" : "#8ab2f2", "ORANGE" : "#f7c54f",
          "PINK": "#ffb6c1"}

drives = []
drive_path = []
drive_number = []

FONT_PATH = os.path.join(os.path.dirname(__file__), "res", "CascadiaCode.ttf")
FONT_BOLD_PATH = os.path.join(os.path.dirname(__file__), "res", "CascadiaCode-Bold.ttf")

class GRUDApp:
    def __init__(self, settings, gui=True):
        self.drives = []
        self.drive_path = []
        self.listbox = None
        self.gui = gui 

        self.settings = settings
        self.download_thread = None

        self.temp_dir = tempfile.mkdtemp()

        self.plugged_in_folders = {}
        self.transfered_folders = {}

        if self.settings is None:
            self.settings = {
                "GRUDBot_APIKEY" : "",
                "ReplayChannelID" : 0,
                "DefaultDownloadPath" : ""
            }

            self.state = "invalid_settings"
        else:
            self.state = "connecting"


        # Fix download path
        self.download_path = self.settings["DefaultDownloadPath"].replace("\\", "/")
        if not self.download_path or not os.path.isdir(self.download_path):
            self.download_path = ""

        
        # Check for windows
        if os.name != "nt":
            printerror("Only Windows is supported in this version of GRUD")
            exit(1)

        if self.state == "connecting":
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
        self.keep_copy_box = customtkinter.CTkCheckBox(self.root, width=10, height=1, corner_radius=0,
                                           text="Keep copy?", checkbox_width=30, font=("Cascadia Code", 16, "bold"))
        self.keep_copy_box.grid(row=4, column=2, sticky="w", padx=20)
        self.path_button = tk.Button(self.root, text="Choose path...", command=self.select_path,
                                     font=("Cascadia Code", 16), state=tk.DISABLED, width=20, cursor="hand2")
        self.path_button.grid(row=4, column=2, sticky="w", padx=(240, 0), )

        if self.download_path:
            if len(self.download_path) > 18:
                path_text = f"...{self.download_path[-15:]}"
            else:
                path_text = self.download_path
            self.path_button.configure(text=path_text)
            self.keep_copy_box.select()

        # Discord message box
        self.example_message = "Discord message here..."

        self.send_message_box = customtkinter.CTkCheckBox(self.root, width=10, height=1, corner_radius=0,
                                           text="Send message?", checkbox_width=30, font=("Cascadia Code", 16, "bold"))
        self.send_message_box.grid(row=5, column=2, sticky="w", padx=20)
        self.send_message_box.select()

        self.msg_box = tk.Text(self.root, width=40, height=2, font=("Cascadia Code", 16), fg="gray")
        self.msg_box.grid(row=6, column=2, sticky="S", rowspan=2)
        self.msg_box.insert("1.0", self.example_message)
        self.msg_box.bind("<FocusIn>", self.msg_focus_in)
        self.msg_box.bind("<FocusOut>", self.msg_focus_out)
        
        # List of drives
        self.listbox = tk.Listbox(self.root, width=50, height=15, font=("Cascadia Code", 12))
        self.listbox.grid(row=1,column=1, rowspan=8, columnspan=1, padx= 20, pady=20)

        # Bot status
        self.bot_label = customtkinter.CTkLabel(self.root, text="GRUDBot Status", font=("Cascadia Code", 24, "bold"), text_color=COLORS["MAGENTA"])
        self.bot_label.grid(row=1, column=2,  padx=30, sticky="s")
        self.bot_status = customtkinter.CTkLabel(self.root, text="Connecting...", font=("Cascadia Code", 24, "bold"), text_color=COLORS["YELLOW"], anchor="w")
        self.bot_status.grid(row=2, column=2, padx=(110,0), sticky="w")

        # Buttons
        self.transfer_button = tk.Button(self.root, text="Transfer Drives", command=self.transfer_replays_action,
                                        padx=8, pady=0, font=("Cascadia Code", 16, "bold"), bg=COLORS["LIGHT_GREEN"], cursor="hand2")
        self.transfer_button.grid(row=9,column=0,sticky="W", rowspan=1, columnspan=3, padx=20)
        self.open_drives_button = tk.Button(self.root, text="Open Drives", command=self.open_drives,
                                            padx=16, pady=0, font=("Cascadia Code", 16, "bold"), bg=COLORS["YELLOW"], cursor="hand2")
        self.open_drives_button.grid(row=9,column=1,sticky="W", rowspan=1, columnspan=3, padx=295)
        self.download_button = tk.Button(self.root, text="Download", command=self.download_action, padx=20,
                                         pady=10, font=("Cascadia Code", 16, "bold"), state=tk.DISABLED, cursor="hand2")
        self.download_button.grid(row=9,column=2, rowspan=1, columnspan=3)

        # Animation
        self.anim_counter = 0
        self.update_status()

    def msg_focus_in(self, event):
        if self.msg_box.get("1.0", tk.END).strip() == self.example_message and self.msg_box.cget("state") == tk.NORMAL:
            self.msg_box.delete("1.0", tk.END)
            self.msg_box.config(fg="black")


    def msg_focus_out(self, event):
        if self.msg_box.get("1.0", tk.END).strip() == "":
            last_state = self.msg_box.cget("state")
            self.msg_box.config(state=tk.NORMAL)
            self.msg_box.insert("1.0", self.example_message)
            self.msg_box.config(fg="gray", state=last_state)


    def update_status(self):
        self.anim_counter += 1
        
        match self.state:
            case "connecting":

                self.status_message = "Connecting"

                self.disable_widget(self.download_button)

                if self.keep_copy_box.get() == 1:
                    self.enable_widget(self.path_button)
                else:
                    self.disable_widget(self.path_button)

                if self.send_message_box.get() == 1:
                    self.enable_widget(self.msg_box)
                else:
                    self.disable_widget(self.msg_box)


                if self.grudbot.error == "LoginFailure":
                    self.bot_status.grid_forget()
                    self.bot_status.configure(text="Invalid API key!", text_color=COLORS["RED"], anchor="n")
                    self.bot_status.grid(row=2, column=2, padx=0)
                    self.state = "zip_only_mode"
                    self.root.after(1500, self.update_status)
                    return

                elif self.grudbot.error == "ChannelNotFound":
                    self.bot_status.grid_forget()
                    self.bot_status.configure(text="Channel not found!", text_color=COLORS["RED"], anchor="n")
                    self.bot_status.grid(row=2, column=2, padx=0)
                    self.state = "zip_only_mode"
                    self.root.after(1500, self.update_status)
                    return
                
                elif self.grudbot.connected:
                    self.state = "ready"
                    self.status_message = "Ready"
                    
                    self.bot_status.grid_forget()
                    self.bot_status.configure(text=self.status_message, text_color=COLORS["LIGHT_GREEN"], anchor="n")
                    self.bot_status.grid(row=2, column=2, padx=0)
                else:
                    text = dotdotdot(self.status_message, self.anim_counter / 13 % 3 + 1)
                    self.bot_status.configure(text=text)

            case "zip_only_mode":

                if self.send_message_box.get() == 1:
                    self.send_message_box.deselect()

                if self.keep_copy_box.get() == 0:
                    self.keep_copy_box.select()

                if (self.transfered_folders or  self.plugged_in_folders) and self.download_path != "":
                    self.enable_widget(self.download_button)
                else:
                    self.disable_widget(self.download_button)


                self.disable_widget(self.send_message_box)
                self.disable_widget(self.keep_copy_box)
                self.disable_widget(self.msg_box)

                self.enable_widget(self.open_drives_button)
                self.enable_widget(self.transfer_button)
                self.enable_widget(self.path_button)

                self.status_message = "Zip-only mode"

                self.bot_status.grid_forget()
                self.bot_status.configure(text=self.status_message, text_color=COLORS["ORANGE"])
                self.bot_status.grid(row=2, column=2, padx=30)

            case "invalid_settings":

                self.disable_widget(self.download_button)
                self.status_message = "Invalid settings.json!\nCheck your syntax"
                self.bot_status.grid_forget()
                self.bot_status.configure(text=self.status_message, text_color=COLORS["RED"])
                self.bot_status.grid(row=2, column=2, padx=30)

            case "ready":

                self.bot_status.configure(text="Ready", text_color=COLORS["LIGHT_GREEN"])

                both_boxes_unchecked = self.keep_copy_box.get() == 0 and self.send_message_box.get() == 0

                if (not self.transfered_folders and not self.plugged_in_folders) \
                        or both_boxes_unchecked:
                    self.disable_widget(self.download_button)
                else:
                    self.enable_widget(self.download_button)
                self.enable_widget(self.open_drives_button)
                self.enable_widget(self.transfer_button)
                self.enable_widget(self.keep_copy_box)
                self.enable_widget(self.send_message_box)

                if self.keep_copy_box.get() == 1:
                    self.enable_widget(self.path_button)
                    if self.download_path == "":
                        self.disable_widget(self.download_button)
                else:
                    self.disable_widget(self.path_button)

                if self.send_message_box.get() == 1:
                    self.enable_widget(self.msg_box)
                else:
                    self.disable_widget(self.msg_box)

            case "transfering" | "zipping" | "sending":

                self.disable_widget(self.download_button) 
                self.disable_widget(self.transfer_button) 
                self.disable_widget(self.open_drives_button) 
                self.disable_widget(self.keep_copy_box) 
                self.disable_widget(self.path_button) 
                self.disable_widget(self.msg_box)
                self.disable_widget(self.send_message_box)

                text = dotdotdot(self.status_message, self.anim_counter / 13 % 3 + 1)
                self.bot_status.configure(text=text, text_color=COLORS["YELLOW"])
            case _:
                printerror(f"Unknown state {self.state}")

        self.refresh_drives()
        self.root.after(30, self.update_status)


    def download_action(self):
        message = self.msg_box.get("1.0", tk.END).strip()
        if message == self.example_message:
            message = ""

        download_path = self.download_path
        temp_files = False
        if not download_path or self.keep_copy_box.get() == 0:
            download_path = self.temp_dir
            temp_files = True

        send_message = self.send_message_box.get() == 1

        self.download_thread = Thread(
                target=self.download,
                args=(download_path, message),
                kwargs={"delete_files" : temp_files, "send_message" : send_message})
        self.download_thread.start()

        # self.download_button.config(state=tk.DISABLED)
        # self.open_drives_button.config(state=tk.DISABLED)
        # self.transfer_button.config(state=tk.DISABLED)
        # self.keep_copy_box.configure(state=tk.DISABLED)
        # self.path_button.configure(state=tk.DISABLED)
        #

    def select_path(self):
        download_path = filedialog.askdirectory(title="Select a directory to download to")
        
        if download_path:
            self.download_path = download_path
            if len(download_path) > 18:
                path_text = f"...{download_path[-15:]}"
            else:
                path_text = download_path
            self.path_button.configure(text=path_text)

        
    def download(self, download_path: str, message: str, delete_files=False, send_message=True):
        self.state="transfering"
        if self.gui:
            self.status_message="Transfering"
            self.bot_status.configure(text=self.status_message)

        asyncio.run(self.transfer_replays(self.temp_dir))

        folders_to_zip = [folder for folder in os.listdir(self.temp_dir) if "Setup #" in folder]

        self.state="zipping"
        
        if self.gui:
            self.status_message="Zipping"
            self.bot_status.configure(text=self.status_message)
        print("Zipping...")

        folders_to_remove = []
        
        for folder in folders_to_zip:
            if ".zip" in folder:
                printerror(f"The zip file {folder} already exists at this location. TODO: HANDLE THIS")
                folders_to_remove.append(folder)
        
        for folder in folders_to_remove:
            # Remove BOTH the zip file and the folder from the list
            folders_to_zip.remove(folder[:-4])
            folders_to_zip.remove(folder)


        if not folders_to_zip:
            printerror("No folders to zip. Exiting function")
            return

        folders_to_send = []

        if send_message:
            size_limit = self.grudbot.replay_channel.guild.filesize_limit # :D
        else:
            size_limit = 0

        with ProcessPoolExecutor() as executor:

            tasks = [
                executor.submit(
                    compress.compress_folder,
                    f"{self.temp_dir}/{folder}", 
                    size_limit
                    )
                for folder in folders_to_zip
            ]


            for i, task in enumerate(tasks):
                # Wait for tasks to complete...
                result = task.result()
                if result > 1: # We created multiple parts
                    for _ in range(0, result):
                        filename = f"{self.temp_dir}/{folders_to_zip[i]} part {i + 1}.zip"
                        folders_to_send.append(filename)
                        if not delete_files:
                            shutil.copy(filename, download_path)
                else:
                    filename = f"{self.temp_dir}/{folders_to_zip[i]}.zip"
                    folders_to_send.append(filename)
                    if not delete_files:
                        shutil.copy(filename, download_path)


        if send_message: 
            self.state = "sending"
            if self.gui:
                self.status_message="Sending"
                self.bot_status.configure(text=self.status_message)
            
            future = asyncio.run_coroutine_threadsafe(self.grudbot.send_message(message), self.grudbot.loop)
            future.result()

            for folder in folders_to_send:
                future = asyncio.run_coroutine_threadsafe(self.grudbot.send_file(folder), self.grudbot.loop)
                future.result()
                if delete_files:
                    os.remove(folder)

        self.transfered_folders = {}

        print("Done!")
        self.state = "ready"
        if self.gui:
            self.status_message = "Ready"

    # Open a file dialog to select a folder
    def refresh_drives(self):
        if self.gui:
            self.listbox.delete(0, tk.END)

        if os.name == "nt":
            self.drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]

        folderStatus = ""

        wii_nums_plugged_in = [] # Yes, I am duct taping this code together instead of rewriting it.
        folders_plugged_in = {}

        for drive in self.drives:
            wii_num = 0

            slpFolderFound = False
            workingDrive = False

            
            replayPath = f"{drive}Slippi"
            for content in os.listdir(drive):
                if content.isdigit():
                    wii_num = content
                    continue

                if content == "Slippi":
                    slpFolderFound = True
                    continue
                    

            if wii_num == 0:
                slpMsg = "Numbered folder missing!"
                wii_num = "?"
            else:
                wii_nums_plugged_in.append(wii_num)
                wii_nums_plugged_in.sort()
                if not slpFolderFound:
                    slpMsg = '"Slippi" replay folder missing!'
                else:
                    file_count = len(os.listdir(replayPath))
                    if not file_count:
                        slpMsg = "Replay folder empty!"
                    else:
                        slpMsg = f"{file_count}"
                        workingDrive = True


            if workingDrive:
                folders_plugged_in[wii_num] = replayPath
                folders_plugged_in = dict(sorted(folders_plugged_in.items()))
                dirName = replayPath
            else:
                dirName = f"{drive}??????"

            if self.gui:
                if wii_num in self.transfered_folders:
                    self.listbox.insert(tk.END, self.transfered_folders[wii_num] + " Wii#" + wii_num + " ----- Transfered" )
                    self.listbox.itemconfig(tk.END, foreground="green")
                else:
                    self.listbox.insert(tk.END, dirName + " Wii#" + wii_num + " ----- " + slpMsg + folderStatus)

        self.plugged_in_folders = folders_plugged_in

        if self.gui:
            for wii_num in self.transfered_folders:
                if wii_num not in wii_nums_plugged_in:
                    self.listbox.insert(tk.END,  "????????? Wii#" + wii_num + " ----- Transfered")
                    self.listbox.itemconfig(tk.END, foreground="green")



    def open_drives(self):
        if os.name == "nt":
            subprocess.Popen("explorer.exe shell:MyComputerFolder")  


    def on_window_close(self):
        if self.state == "zipping" or self.state == "sending": # TODO: Handle file cleanup instead of just refusing
            return

        if len(os.listdir(self.temp_dir)) > 0:
            # We probably transfered some files but forgot to send them
            # TODO: Add these files to the list when the program is restarted
            if os.name == "nt":
                appdata = os.path.join(os.environ["APPDATA"], "GRUD")
            
            shutil.copytree(self.temp_dir, appdata)

        shutil.rmtree(self.temp_dir)

        self.root.destroy()
        if self.grudbot.connected:
            self.stop_grudbot();


    # :)
    def start_grudbot(self):
        self.grudbot = GRUDBot(self.settings["ReplayChannelID"])
        self.bot_thread = Thread(target=self.grudbot.run, args=((self.settings["GRUDBot_APIKEY"]), ))
        self.bot_thread.start()
        

    # :(
    def stop_grudbot(self):
        asyncio.run_coroutine_threadsafe(self.grudbot.close(), self.grudbot.loop)
        self.bot_thread.join()

    async def transfer_folder(self, wii_num, slippi_folder, dest):
        setup_path = f"{dest}/Setup #{wii_num}"
        os.makedirs(setup_path, exist_ok=True)
        for file in os.listdir(slippi_folder):
            src = f"{slippi_folder}/{file}"
            shutil.move(src, setup_path)
        self.transfered_folders[wii_num] = slippi_folder
        print(f"Wii {wii_num} complete")

    async def transfer_replays(self, dest: str):
        if not os.path.exists(dest):
            printerror(f"Destination path '{dest}' does not exist")
            return

        if len(self.plugged_in_folders) == 0:
            printerror("No USB drives to download from!")
            return

        tasks = [
            self.transfer_folder(wii_num, slippi_folder, dest)
            for wii_num, slippi_folder, in self.plugged_in_folders.items()
            if wii_num not in self.transfered_folders
        ]

        await asyncio.gather(*tasks)


    def transfer_replays_action(self): # :/
        asyncio.run(self.transfer_replays(self.temp_dir))

    # TODO: Just store the correct function within the widget itself to avoid this mess...
    def enable_widget(self, widget): 
        if widget.cget("state") != tk.NORMAL:
            if widget is self.download_button:
                widget.config(state=tk.NORMAL, bg=COLORS["BLUE"])
            elif widget is self.transfer_button:
                widget.config(state=tk.NORMAL, bg=COLORS["LIGHT_GREEN"])
            elif widget is self.open_drives_button:
                widget.config(state=tk.NORMAL, bg=COLORS["YELLOW"])
            elif widget is self.path_button:
                widget.config(state=tk.NORMAL, bg=COLORS["PINK"])
            elif widget is self.msg_box:
                self.root.focus()
                if self.msg_box.get("1.0", tk.END).strip() == self.example_message:
                    widget.config(state=tk.NORMAL, fg="gray")
                else:
                    widget.config(state=tk.NORMAL, fg="black")
            elif widget is self.keep_copy_box or widget is self.send_message_box:
                widget.configure(state=tk.NORMAL)
            else:
                widget.config(state=tk.NORMAL)

    # TODO: same as enable_widget
    def disable_widget(self, widget):
        if widget.cget("state") != tk.DISABLED:
            if widget is self.download_button or \
               widget is self.transfer_button or \
               widget is self.open_drives_button or \
               widget is self.path_button:
                widget.config(state=tk.DISABLED, bg="white")
            elif widget is self.msg_box:
                self.root.focus()
                widget.config(state=tk.DISABLED, fg="gray")
            elif widget is self.keep_copy_box or widget is self.send_message_box:
                widget.configure(state=tk.DISABLED)
            else:
                widget.config(state=tk.DISABLED)


def printerror(text: str):
    print(f"\033[91m{text}\033[0m")

def dotdotdot(text: str, dots: int) -> str:
    text += '.' * int(dots)
    return text

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--naked", action="store_true", help="Run without any GUI")
    args = parser.parse_args()

    
    # Parse settings
    if os.path.isfile("settings.json"):
        with open("settings.json", "r") as file:
            try:
                settings = json.load(file)
            except json.decoder.JSONDecodeError as e:
                settings = None
                printerror(e)

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
            "DefaultDownloadPath" : ""
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


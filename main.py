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
import psutil

from enum import Enum
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from threading import Thread
from dataclasses import dataclass
from itertools import zip_longest
from pathvalidate import sanitize_filename
from tkinter import ttk

if os.name == "nt":
    from ctypes import windll
    from win32com import client
    import win32api

# This repo 
import compress
import slp_parser
from grudbot import GRUDBot 


COLORS = {"GRAY" : "#414151", "LIGHT_GREEN" : "#74e893", "YELLOW" : "#faf48c",
          "MAGENTA" : "#d953e6", "RED" : "#f54251", "BLUE" : "#8ab2f2", "ORANGE" : "#f7c54f",
          "PINK": "#ffb6c1"}


class ReplayState(Enum):
    IN_DRIVE = 1
    TRANSFERED = 2
    RECOVERED = 3

    def __lt__(self, other):
        if not isinstance(other, ReplayState):
            raise TypeError(f"Comparison between ReplayState and '{type(other).__name__}' not supported")
        return self.value < other.value


@dataclass(init=False, order=True, slots=True)
class ReplayFolder:
    state: ReplayState
    source: str 
    name: str
    filecount: int 
    path: str
    plugged_in: bool
    uuid: int

    def __init__(self, state: ReplayState, source: str, uuid: int, plugged_in=False):
        self.state = state
        self.source = source
        self.plugged_in = plugged_in
        self.uuid = uuid 
        self.path = source

        if state is ReplayState.RECOVERED:
            if os.name == "nt":
                index = self.source.rfind("\\")
            else:
                index = self.source.rfind("/")
            self.name = self.source[index + 1:]

        elif os.path.exists(os.path.join(self.source, "GRUD.json")):
            with open(os.path.join(self.source, "GRUD.json")) as f:
                settings = json.load(f)
                self.name = settings["name"]
        else:
            self.name = ""

        self.refresh_filecount()
    

    @property
    def can_transfer(self):
        return self.state in (ReplayState.IN_DRIVE, ReplayState.RECOVERED) and self.filecount > 0 and self.name

    @property
    def can_zip(self):
        return self.state is ReplayState.TRANSFERED and self.name


    def refresh_filecount(self):
        file_path = self.path
        if self.state is ReplayState.IN_DRIVE:
            file_path = os.path.join(self.source, "Slippi")

        if os.path.exists(file_path):
            self.filecount = len([
                file for file in os.listdir(file_path)
                if file.endswith(".slp")
            ])
        else:
            self.filecount = -1



#TODO: Separate GUI and GRUD
#      Fix recovery of folders that were successfully archived but not sent
#      Migrate to pyusb OR psutil for drives
#      Add scaling factor for app upscaling 
#      Window resizing (MASSIVE TASK)
#      AI Messages????
class GRUDApp:
    __slots__ = (
            # INTERNAL
            "gui", "should_refresh_gui", "settings",
            "settings", "editing_drive_name", "replay_folders",
            "state", "download_path", "appdata", "temp_dir",
            "grudbot", "bot_thread", "recovered", "files_to_compress",
            "files_compressed", "can_refresh",

            # GUI 
            "root", "keep_copy_box", "path_button", "listbox", "entry",
            "example_message", "msg_box", "send_message_box", "listbox_font",
            "input_field", "entry", "bot_label", "bot_status", "selected_item_index",
            "transfer_button", "open_drives_button", "download_button", "anim_counter",
            "scale_x", "scale_y", "progress_bar"
    )

    def __init__(self, settings, dev_state="", gui=True):
        self.gui = gui 
        self.should_refresh_gui = True
        self.can_refresh = True

        self.settings = settings
        self.editing_drive_name = False

        self.replay_folders = []
        self.files_to_compress = []
        self.files_compressed = None 


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
        if os.name == "nt":
            self.appdata = os.path.join(os.environ["APPDATA"], "GRUD")
            if not os.path.isdir(self.appdata):
                os.mkdir(self.appdata)

            windll.shcore.SetProcessDpiAwareness(1) # Laptop/upscaling fix
        else:
            printerror("Only Windows is supported in this version of GRUD")
            exit(1)

        self.temp_dir = os.path.join(self.appdata, ".temp")
        if not os.path.isdir(self.temp_dir):
            os.mkdir(self.temp_dir)
            if os.name == "nt":
                windll.kernel32.SetFileAttributesW(self.temp_dir, 0x2) # 0x2 == FILE_ATTRIBUTE_HIDDEN


        self.recovered = os.path.join(self.appdata, "recovered")
        if not os.path.isdir(self.recovered):
            os.mkdir(self.recovered)


        if dev_state:
            self.state = dev_state

        if self.state == "connecting":
            self.start_grudbot()
        else:
            self.grudbot = None

        if gui:
            self.initGUI()


        self.refresh_drives()

        
    def initGUI(self):
        self.root = customtkinter.CTk()
        self.root.title("GRUD")
        self.root.geometry("1000x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["GRAY"])

        if os.name == "nt":
            myappid = "Game.Replay.Uploader.for.Discord"
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
            self.root.iconbitmap(fr"res/grudbot.ico")

        # Get upscaling from high-DPI monitors
        scale = self.root.tk.call("tk", "scaling")

        self.scale_x = scale
        self.scale_y = scale

        # Choose path
        self.keep_copy_box = customtkinter.CTkCheckBox(self.root, width=10, height=1, corner_radius=0,
                                           text="Keep copies?", checkbox_width=30, font=("Cascadia Code", 16, "bold"))
        self.keep_copy_box.grid(row=4, column=2, sticky="w", padx=20)

        self.path_button = tk.Button(self.root, text="Choose path...", command=self.path_button_callback,
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
                                           text="Send discord message?", checkbox_width=30, font=("Cascadia Code", 16, "bold"))
        self.send_message_box.grid(row=5, column=2, sticky="w", padx=20)
        self.send_message_box.select()

        self.msg_box = tk.Text(self.root, width=40, height=2, font=("Cascadia Code", 16), fg="gray")
        self.msg_box.grid(row=6, column=2, sticky="S", rowspan=2)
        self.msg_box.insert("1.0", self.example_message)
        self.msg_box.bind("<FocusIn>", self.msg_focus_in)
        self.msg_box.bind("<FocusOut>", self.msg_focus_out)
        
        # List of drives
        self.listbox_font = font.Font(family="Cascadia Code", size=12)

        # For some fucking reason you can scroll this listbox by holding the mouse and draging 
        # left or right, despite xscrollcommand explicitly being None. The docs doesn't mention
        # this at all, I have no idea why it would even happen.
        self.listbox = tk.Listbox(self.root, width=50, height=15, selectmode=tk.SINGLE, font=self.listbox_font, activestyle="none", highlightthickness=0, xscrollcommnad=None) 
        self.listbox.bind("<<ListboxSelect>>", self.listbox_on_click)
        self.listbox.grid(row=1,column=1, rowspan=8, columnspan=1, padx= 20, pady=20)

        self.input_field = tk.StringVar()
        self.entry = tk.Entry(self.root, textvariable=self.input_field, font=self.listbox_font)
        self.entry.bind("<Return>", self.entry_on_return)

        # Bot status (rename this?)
        self.bot_label = customtkinter.CTkLabel(self.root, text="GRUDBot Status", font=("Cascadia Code", 24, "bold"), text_color=COLORS["MAGENTA"])
        self.bot_label.grid(row=1, column=2,  padx=30, sticky="s")
        self.bot_status = customtkinter.CTkLabel(self.root, text="Connecting...", font=("Cascadia Code", 24, "bold"), text_color=COLORS["YELLOW"], anchor="w")
        self.bot_status.grid(row=2, column=2, padx=(155,0), sticky="w")

        # Buttons
        self.transfer_button = tk.Button(self.root, text="Store locally", command=self.transfer_replays_button_callback,
                                        padx=8, pady=0, font=("Cascadia Code", 16, "bold"), bg=COLORS["LIGHT_GREEN"], cursor="hand2")
        self.transfer_button.grid(row=9,column=0,sticky="W", rowspan=1, columnspan=3, padx=20)

        self.open_drives_button = tk.Button(self.root, text="Open drives", command=self.open_drives,
                                            padx=16, pady=0, font=("Cascadia Code", 16, "bold"), bg=COLORS["YELLOW"], cursor="hand2")
        self.open_drives_button.grid(row=9,column=1,sticky="W", rowspan=1, columnspan=3, padx=293)

        self.download_button = tk.Button(self.root, text="Zip and send", command=self.download_button_callback, 
                                         width=12, padx=20, pady=10, font=("Cascadia Code", 16, "bold"), state=tk.DISABLED, cursor="hand2")
        self.download_button.grid(row=9,column=2, rowspan=1, columnspan=3)


        self.progress_bar = ttk.Progressbar(length=200 * self.scale_x, maximum=1)

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

                elif self.grudbot.error == "NoInternet":
                    self.bot_status.grid_forget()
                    self.bot_status.configure(text="No internet!", text_color=COLORS["RED"], anchor="n")
                    self.bot_status.grid(row=2, column=2, padx=0)
                    self.state = "zip_only_mode"
                    self.root.after(1500, self.update_status)
                    return
                
                elif self.grudbot.connected:
                    self.state = "ready"
                    
                    self.bot_status.grid_forget()
                    self.bot_status.configure(text="Ready", text_color=COLORS["LIGHT_GREEN"], anchor="n")
                    self.bot_status.grid(row=2, column=2, padx=0)
                else:
                    text = dotdotdot("Connecting", self.anim_counter / 13 % 3 + 1)
                    self.bot_status.configure(text=text)

            case "zip_only_mode":

                if self.send_message_box.get() == 1:
                    self.send_message_box.deselect()

                if self.keep_copy_box.get() == 0:
                    self.keep_copy_box.select()

                if self.download_path and any(folder.can_transfer or folder.can_zip for folder in self.replay_folders):
                    self.enable_widget(self.download_button)
                else:
                    self.disable_widget(self.download_button)

                self.disable_widget(self.send_message_box)
                self.disable_widget(self.keep_copy_box)
                self.disable_widget(self.msg_box)

                self.enable_widget(self.open_drives_button)
                self.enable_widget(self.transfer_button)
                self.enable_widget(self.path_button)

                self.download_button.config(text="Zip")

                self.bot_status.grid_forget()
                self.bot_status.configure(text="Zip-only mode", text_color=COLORS["ORANGE"])
                self.bot_status.grid(row=2, column=2, padx=30)

            case "invalid_settings":

                self.disable_widget(self.download_button)
                message = "Invalid settings.json!\nCheck your syntax"
                self.bot_status.grid_forget()
                self.bot_status.configure(text=message, text_color=COLORS["RED"])
                self.bot_status.grid(row=2, column=2, padx=30)

                self.state = "zip_only_mode"
                self.root.after(2500, self.update_status)
                return

            case "ready":
                self.bot_status.configure(text="Ready", text_color=COLORS["LIGHT_GREEN"])

                both_boxes_unchecked = self.keep_copy_box.get() == 0 and self.send_message_box.get() == 0

                if all(not folder.can_transfer and not folder.can_zip for folder in self.replay_folders) \
                        or both_boxes_unchecked:
                    self.disable_widget(self.download_button)
                else:
                    self.enable_widget(self.download_button)
                self.enable_widget(self.open_drives_button)
                self.enable_widget(self.transfer_button)
                self.enable_widget(self.keep_copy_box)
                self.enable_widget(self.send_message_box)
                self.progress_bar.grid_forget()

                if self.keep_copy_box.get() == 1:
                    self.enable_widget(self.path_button)
                    if self.download_path == "":
                        self.disable_widget(self.download_button)
                else:
                    self.disable_widget(self.path_button)

                if self.send_message_box.get() == 1:
                    self.enable_widget(self.msg_box)
                    self.download_button.config(text="Zip and send")
                else:
                    self.disable_widget(self.msg_box)
                    self.download_button.config(text="Zip")

            case "transfering" | "zipping" | "sending":

                self.disable_widget(self.download_button) 
                self.disable_widget(self.transfer_button) 
                self.disable_widget(self.open_drives_button) 
                self.disable_widget(self.keep_copy_box) 
                self.disable_widget(self.path_button) 
                self.disable_widget(self.msg_box)
                self.disable_widget(self.send_message_box)

                if self.state == "zipping":
                    self.progress_bar.grid(row=2, column=2, pady=(65 * self.scale_y,0))
                    if self.files_compressed is not None:
                        self.progress_bar["value"] = len(self.files_compressed) / (len(self.files_to_compress)) # 1 for testing purposes
                else:
                    self.progress_bar.grid_forget()

                text = dotdotdot(self.state.capitalize(), self.anim_counter / 13 % 3 + 1)
                self.bot_status.configure(text=text, text_color=COLORS["YELLOW"])

            case _:
                printerror(f"Unknown state {self.state}")

        self.refresh_drives()
        
        if self.editing_drive_name:
            self.listbox_update()
            self.entry_update()

        self.root.after(30, self.update_status)


    def download_button_callback(self):
        message = self.msg_box.get("1.0", tk.END).strip()
        if message == self.example_message:
            message = ""

        download_path = self.download_path
        if not download_path or self.keep_copy_box.get() == 0:
            download_path = self.temp_dir

        send_message = self.send_message_box.get() == 1

        download_thread = Thread(
                target=self.download,
                args=(download_path, message),
                kwargs={"send_message" : send_message})
        download_thread.start()


    def path_button_callback(self):
        download_path = filedialog.askdirectory(title="Select a directory to download to")
        
        if download_path:
            self.download_path = download_path
            if len(download_path) > 18:
                path_text = f"...{download_path[-15:]}"
            else:
                path_text = download_path
            self.path_button.configure(text=path_text)

        
    def download(self, download_path: str, message: str, send_message=True):
        delete_files = download_path == self.temp_dir

        self.state="transfering"

        asyncio.run(self.transfer_replays(self.temp_dir))

        folders_to_zip = []
        for replay_folder in self.replay_folders:
            if replay_folder.state is ReplayState.TRANSFERED:
                folders_to_zip.append(replay_folder.path)

        self.state="zipping"
        
        print("Zipping...")

        folders_to_remove = []
        
        # redundant now?
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


        # Rename SLP files
        for folder in folders_to_zip:
            slp_parser.adjust_names(folder)


        archives_to_send = []

        if send_message:
            size_limit = self.grudbot.replay_channel.guild.filesize_limit # :D
        else:
            size_limit = 0

        self.files_to_compress = []
        for folder in folders_to_zip:
            self.files_to_compress += [file for file in os.listdir(folder) if file.endswith(".slp")]


        print(folders_to_zip)


        with Manager() as manager:
            self.files_compressed = manager.list()

            with ProcessPoolExecutor() as executor:

                tasks = [
                    executor.submit(
                        compress.compress_folder,
                        folder, 
                        size_limit,
                        compressed_files=self.files_compressed
                    )
                    for folder in folders_to_zip
                ]


                for i, task in enumerate(tasks):
                    # Wait for tasks to complete...
                    result = task.result()
                    if result > 1: # We created multiple parts
                        for part in range(0, result):
                            filename = f"{folders_to_zip[i]} part {part + 1}.zip"
                            archives_to_send.append(filename)
                            if not delete_files:
                                shutil.copy(filename, download_path)
                    else:
                        filename = f"{folders_to_zip[i]}.zip"
                        archives_to_send.append(filename)
                        if not delete_files:
                            shutil.copy(filename, download_path)

            self.files_compressed = None


        # Remove zipped folders from the list
        self.replay_folders = [
            folder
            for folder in self.replay_folders
            if folder.path not in folders_to_zip
        ]

        print(self.replay_folders)

        self.should_refresh_gui = True

        if send_message and message[0:6] != "~TEST~": 
            self.state = "sending"
            
            future = asyncio.run_coroutine_threadsafe(self.grudbot.send_message(message), self.grudbot.loop)
            future.result()

            for archive in archives_to_send:
                future = asyncio.run_coroutine_threadsafe(self.grudbot.send_file(archive), self.grudbot.loop)
                future.result()


        for archive in archives_to_send:
            os.remove(archive)


        print("Done!")
        self.state = "ready"

            
    def refresh_drives(self):
        if not self.can_refresh:
            return

        if os.name == "nt":
            drives = [f"{d}:/" for d in string.ascii_uppercase if os.path.exists(f"{d}:/")]
            get_uuid = lambda drive: win32api.GetVolumeInformation(drive)[1]


        replay_folders = [
                folder
                for folder in self.replay_folders
                if folder.state is not ReplayState.IN_DRIVE
        ]


        # Unplugged transfered drives
        for i, folder in enumerate(replay_folders):
            if folder.state is ReplayState.TRANSFERED and folder.source not in drives:
                folder.plugged_in = False
                self.should_refresh_gui = True


        # Add folders currently in drives
        for drive in drives:
            uuid = get_uuid(drive)
            folder = ReplayFolder(ReplayState.IN_DRIVE, drive, uuid, plugged_in=True)

            index = -1
            for i, replay_folder in enumerate(replay_folders):
                if replay_folder.uuid == folder.uuid and replay_folder.state is ReplayState.TRANSFERED:
                    index = i 
                    break
            
            if index != -1:
                replay_folders[index].source = folder.source
                replay_folders[index].plugged_in = True
                self.should_refresh_gui = True
            else:
                replay_folders.append(folder)
                

        # Add recovered folders
        # TODO: Handle name collision for recovered folders and folders in drives
        for folder in os.listdir(self.recovered):
            full_path = os.path.join(self.recovered, folder)
            if not os.path.isdir(full_path):
                continue

            
            folder_object = ReplayFolder(ReplayState.RECOVERED, full_path, 0, plugged_in=False)
            if not any(
                    replay_folder.name == folder_object.name
                    for replay_folder in replay_folders
                    if replay_folder.state is not ReplayState.IN_DRIVE
                ):
                replay_folders.append(folder_object)


        replay_folders.sort()


        # if replay_folders != self.replay_folders or self.should_refresh_gui:
        self.replay_folders = replay_folders
        self.should_refresh_gui = False
        if self.gui:
            self.listbox_update()           


    def listbox_update(self):
        self.listbox.delete(0, tk.END)

        longest_name = max(len(folder.name) for folder in self.replay_folders)
        longest_name = max(len(self.input_field.get()), longest_name)

        for folder in self.replay_folders:
            state = folder.state 
            if folder.name:
                name_str = f"{folder.name} "
            else:
                name_str = f"?? "


            name_str += "-" * (longest_name - len(name_str) + 1) # Fill rest out with dashes

            if state is ReplayState.IN_DRIVE:
                if folder.filecount == -1:
                    self.listbox.insert(tk.END, f"{folder.source}?????? -- {name_str}-- No 'Slippi' folder found!")
                    self.listbox.itemconfig(tk.END, foreground="red")
                elif not folder.name:
                    self.listbox.insert(tk.END, f"{folder.source}Slippi -- {name_str}-- No name found!")
                    self.listbox.itemconfig(tk.END, foreground="red")
                else:
                    self.listbox.insert(tk.END, f"{folder.source}Slippi -- {name_str}-- Files: {folder.filecount}")
            elif state is ReplayState.TRANSFERED:
                if folder.plugged_in:
                    self.listbox.insert(tk.END, f"{folder.source}Slippi -- {name_str}-- Transfered ({folder.filecount} files)")
                else:
                    self.listbox.insert(tk.END, f"------------ {name_str}-- Transfered ({folder.filecount} files)")
                self.listbox.itemconfig(tk.END, foreground="green")
            elif state is ReplayState.RECOVERED:
                self.listbox.insert(tk.END, f"Recovered -- {name_str}-- In AppData ({folder.filecount} files)")
                self.listbox.itemconfig(tk.END, foreground="red")


    def listbox_on_click(self, event):
        if self.state not in ("ready", "connecting"):
            return

        selection = self.listbox.curselection()
        
        if not selection:
            return


        index = selection[0]
        folder = self.replay_folders[index]
        if folder.state is not ReplayState.IN_DRIVE:
            self.entry.place_forget()
            return

        self.selected_item_index = index

        x, y, width, height = self.listbox.bbox(index)

        padx = 20
        pady = 20

        x += padx + 115
        y += pady - 2

        if folder.name:
            self.input_field.set(folder.name)
        else:
            self.input_field.set("??")

        current_text = self.input_field.get()
        text_width = self.listbox_font.measure(current_text)

        self.editing_drive_name = True
        self.entry.place(x=x, y=y, width=max(10, text_width) + 5)
        
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx() 

        if not x < mouse_x < x + text_width + 5:
            self.entry.place_forget()
            self.editing_drive_name = False
            self.listbox.select_clear(0, tk.END)
            self.root.after(5, lambda: self.root.focus_set())
            self.listbox_update()
            return
        
        self.entry.selection_range(0, tk.END)
        self.root.after(5, lambda: self.entry.focus_set()) # Focus is handled async, so we chill 

    def entry_update(self):
        if self.root.focus_get() is not self.entry:
            if self.root.focus_get() is self.listbox:
                return
            else:
                self.entry.place_forget()
                self.editing_drive_name = False
                return

        current_text = self.input_field.get()

        text_width = self.listbox_font.measure(current_text)

        self.entry.place(width=max(10, text_width) + 5)

        longest_name = max(len(folder.name) for folder in self.replay_folders)
        longest_name = max(len(self.input_field.get()), longest_name)

        folder_name = self.input_field.get()
        folder_name += " " + "-" * (longest_name - len(folder_name) + 2) # Fill rest out with dashes

        text = self.listbox.get(self.selected_item_index)
        start_index = text.find(" ")
        end_index = text.rfind("- ")

        new_text = f"{text[:start_index]} -- {folder_name}{text[end_index + 1:]}"
        self.listbox.delete(self.selected_item_index)
        self.listbox.insert(self.selected_item_index, new_text)


    def entry_on_return(self, event):
        filename = sanitize_filename(self.input_field.get())
        folder = self.replay_folders[self.selected_item_index]
        folder.name = filename

        name = {"name" : folder.name}
        with open(f"{folder.source}/GRUD.json", "w") as file:
            json.dump(name, file, indent=4)

        self.entry.place_forget()
        self.editing_drive_name = False
        self.should_refresh_gui = True
        self.root.focus()


    def open_drives(self):
        if os.name == "nt":
            subprocess.Popen("explorer.exe shell:MyComputerFolder")  


    def on_window_close(self):
        for file in os.listdir(self.temp_dir):
            src = os.path.join(self.temp_dir, file)
            dst = os.path.join(self.recovered, file)

            # TODO: For some reason, this nests the folder if it already exists. Handle that.
            shutil.move(src, dst)

        os.rmdir(self.temp_dir)

        self.root.destroy()
        if self.grudbot:
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


    async def transfer_folder(self, replay_folder, dest):
        setup_path = f"{dest}/{replay_folder.name}"
        print(replay_folder)

        if replay_folder.state is ReplayState.RECOVERED:
            slippi_folder = replay_folder.source
        else:
            slippi_folder = f"{replay_folder.source}/Slippi" 

        if os.path.exists(setup_path) and replay_folder.state is not ReplayState.RECOVERED:
            printerror("We got folder source destination collision, yet it wasn't from a recovered folder.")
            printerror(f"IF YOU SEE THIS, SEND THIS TO ADDE!!!\nSource: {replay_folder.source}\nDestination: {setup_path}\nName: {replay_folder.name}")
            return

        os.makedirs(setup_path, exist_ok=True)

        slp_files = [
            file
            for file in os.listdir(slippi_folder)
            if file.endswith(".slp")
        ]

        
        # shutil.move is always blocking due to the OS API calls being blocking,
        # so we need to do this to avoid asynchio being blocking
        # NOTE: NAME COLLISION CAUSES OVERWRITES - SHOULDN'T BE A PROBLEM EXCEPT DURING TESTS
        loop = asyncio.get_running_loop()
        move_tasks = [
            loop.run_in_executor(None, shutil.move, f"{slippi_folder}/{file}", f"{setup_path}/{file}")
            for file in slp_files
        ]

        await asyncio.gather(*move_tasks)

        folder = next((folder for folder in self.replay_folders if folder.name == replay_folder.name), None)
        if not folder:
            printerror("I don't have the slightest idea why this has happened, but the folder magically disappeared from the list after the transfer")
            return


        if replay_folder.state is ReplayState.RECOVERED:
            self.replay_folders.remove(replay_folder)
            shutil.rmtree(replay_folder.source)


        folder.state = ReplayState.TRANSFERED
        folder.path = setup_path
        folder.refresh_filecount()
        self.should_refresh_gui = True 


        print(f"{replay_folder.name} transfered")

    async def transfer_replays(self, dest: str):
        self.can_refresh = False

        if not os.path.exists(dest):
            printerror(f"Destination path '{dest}' does not exist")
            return

        
        folders = [
            folder for folder in self.replay_folders
            if folder.can_transfer
        ]


        if len(folders) == 0:
            printerror("No USB drives to download from!")
            return


        tasks = [
            self.transfer_folder(folder, dest)
            for folder in folders
        ]

        await asyncio.gather(*tasks)
        self.can_refresh = True


    def transfer_replays_button_callback(self):
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
            elif widget is self.progress_bar:
                widget.grid_forget()
                widget.configure(state=tk.DISABLED)
            else:
                widget.config(state=tk.DISABLED)


def printerror(message: str):
    print(f"\033[91m{message}\033[0m")


def dotdotdot(text: str, dots: int) -> str:
    text += '.' * int(dots)
    return text


def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--naked", action="store_true", help="Run without any GUI")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-zo", action="store_true", help="run the program in Zip-only mode")
    group.add_argument("-i", action="store_true", help="run the program with invalid settings")
    group.add_argument("-t", action="store_true", help="run the program in the transfering state")
    group.add_argument("-z", action="store_true", help="run the program in the zipping state")
    group.add_argument("-s", action="store_true", help="run the program in the sending state")
    group.add_argument("-ws", action="store_true", help="create a windows shortcut to GRUD")

    args = parser.parse_args()

    dev_state = ""
    if args.zo:
        dev_state = "zip_only_mode"
    elif args.i:
        dev_state = "invalid_settings"
    elif args.t:
        dev_state = "transfering"
    elif args.z:
        dev_state = "zipping"
    elif args.s:
        dev_state = "sending"

    # Create shortcut (Windows only)
    if args.ws and os.name == "nt":
        shell = client.Dispatch("WScript.Shell")
        dir = os.path.dirname(os.path.realpath(__file__))
        shortcut = shell.CreateShortcut(f"{dir}/GRUD.lnk")
        shortcut.TargetPath = f"{dir}\\grud.vbs"
        shortcut.IconLocation = f"{dir}\\res\\grudbot.ico"
        shortcut.save()
        exit(1)


    # Parse settings
    if os.path.isfile("settings.json"):
        with open("settings.json", "r") as file:
            try:
                settings = json.load(file)
            except json.decoder.JSONDecodeError as e:
                settings = None
                printerror(e)

        app = GRUDApp(
                settings,
                dev_state=dev_state,
                gui=not args.naked
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

import tkinter as tk
from tkinter import filedialog
from asyncore import write
from concurrent.futures import thread
from operator import index
import os
from select import select
clear = lambda: os.system('cls')
import requests
import shutil
import zipfile
import string
import time
from tkinter import *
from tkinter import scrolledtext
import threading
import datetime
import json
import subprocess
from pathlib import Path

drive_path = []
drive_number = []

def init_gui():
    root = tk.Tk()
    root.title("GRUD")
    root.geometry("650x300")


    tabb_box = tk.Entry(root, width=5)
    tabb_box.grid(row=4, column=2, sticky="S")
    hash_text = tk.Label(root, text="#", font=("Gotham", 12))
    hash_text.grid(row=4, column=3, sticky="S")
    tser_box = tk.Entry(root, width=5)
    tser_box.grid(row=4, column=4, padx=0, sticky="S")

    listbox = tk.Listbox(root, width=70, height=15)
    listbox.grid(row=1,column=1, rowspan=7, columnspan=1, padx= 20, pady=20)
    # listbox.pack(padx=10, pady=10, anchor=tk.W)

    frame = tk.Frame(root, borderwidth=2, relief="sunken", padx=20, pady=20)
    # frame.pack(padx=10,pady=10)

    refresh_button = tk.Button(root, text="REFRESH DRIVES", command=getDrives, padx=8, pady=0, font=("Gotham", 8))
    refresh_button.grid(row=5,column=2,sticky="S", rowspan=1, columnspan=3)
    refresh_button = tk.Button(root, text="GO TO DRIVES", command=openThisPC, padx=10, pady=0, font=("Gotham", 8))
    refresh_button.grid(row=7,column=2,sticky="N", rowspan=1, columnspan=3)
    download_button = tk.Button(root, text="DOWNLOAD", command=download, padx=20, pady=10, font=("Gotham", 8))
    download_button.grid(row=6,column=2, rowspan=1, columnspan=3)
    # browse_button.pack(pady=10, anchor=tk.E)



def hasReplayFolder(folderName):
    if folderName != "Slippi":
        return "No folder named Slippi!"
    else:
        return ""


def download():
    download_path = filedialog.askdirectory(
        title="Select a Directory"
    )
    if download_path:
        print(f"Selected directory path: {download_path}")
    return download_path


# Open a file dialog to select a folder
def getDrives():
    listbox.delete(0, tk.END)
    msg = "start"
    folderStatus = ""
        # List all files and directories in the selected path with full paths
    for item in drives:
        print(msg)
        numFolderFound = False
        slpFolderFound = False
        for content in os.listdir(item):
            
                
                #print(content)
                
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
        listbox.insert(tk.ACTIVE,os.path.join(item, dirName) + " Wii#" + wiiNum + " ----- " + slpMsg + folderStatus)

def openThisPC():
    subprocess.Popen("explorer.exe shell:MyComputerFolder")  

            


       
        # Check if it is a directory and its name contains only digits
         



def main():
    # Check for windows
    if os.name == "nt":
        drive_list = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
    else:
        print("Only Windows is supported in this version of GRUD")
        exit(1)

    print(drive_list)

    getDrives()
    root.mainloop()

if __name__ == "__main__":
    main()





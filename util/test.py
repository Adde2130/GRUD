# TODO:
#       Add args for files (drives to include/exclude etc)
#       Automatic detection of how many files needed to create multiple parts
#       Autamatic mounting of virtual drives

import shutil
import string
import os

from ctypes import windll
import win32file

script_path = os.path.dirname(os.path.realpath(__file__))
example_file = os.path.join(script_path, "example.slp")

FILECOUNT = 55 # Adjust as needed (See TODO for automatic setting of this const)

if not os.path.exists(example_file):
    print(f"\033[91mCould not find the example file!\033[0m")
    exit(1)

if os.name == "nt":
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1 and os.path.exists(os.path.join(f"{letter}:", "GRUD.json")) and os.path.exists(os.path.join(f"{letter}:", "Slippi")): 
            drives.append(f"{letter}:")
        bitmask >>= 1


for drive in drives:
    for i in range(FILECOUNT):
        shutil.copyfile(example_file, os.path.join(drive, "Slippi", f"example {i}.slp"))


for i, file in enumerate(os.listdir(os.path.join(drives[-1], "Slippi"))):
    if i == 20:
        break

    os.remove(os.path.join(drives[-1], "Slippi", file))

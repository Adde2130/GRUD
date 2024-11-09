# TODO:
#       Add args for files (drives to include/exclude etc)
#       Automatic detection of how many files needed to create multiple parts
#       Autamatic mounting of virtual drives

import shutil
import os

script_path = os.path.dirname(os.path.realpath(__file__))
example_file = os.path.join(script_path, "example.slp")

FILECOUNT = 55 # Adjust as needed (See TODO for automatic setting of this const)

if not os.path.exists(example_file):
    print(f"\033[91mCould not find the example file!\033[0m")

drives = ["D:" , "E:", "F:", "G:"]

for drive in drives:
    for i in range(FILECOUNT):
        shutil.copyfile(example_file, os.path.join(drive, "Slippi", f"example {i}.slp"))

x = 0
for file in os.listdir("G:\\Slippi"):
    path = f"G:\\Slippi\\{file}"
    os.remove(path)
    x+=1
    if x >= 20:
        break

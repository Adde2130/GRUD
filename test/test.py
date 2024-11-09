# TODO:
#       Add args for files (drives to include/exclude etc)
#       Automatic detection of how many files needed to create multiple parts
#       Autamatic mounting of virtual drives

import shutil
import os

script_path = os.path.dirname(os.path.realpath(__file__))
source_dir = os.path.join(script_path, "test_files")


if not os.path.exists(source_dir):
    os.mkdir(source_dir)
    print(f"\033[91mYou need to add test files for this to work!\033[0m")

drives = ["D" , "E", "F", "G"]

for drive in drives:
    shutil.copytree(source_dir, f"{drive}:\\Slippi", dirs_exist_ok=True)

x = 0
for file in os.listdir("G:\\Slippi"):
    path = f"G:\\Slippi\\{file}"
    os.remove(path)
    x+=1
    if x >= 20:
        break

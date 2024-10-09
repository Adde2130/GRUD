# GRUD

**G**ame **R**eplay **U**ploader for **D**iscord

Script created by Hixon in order to download replays from USB drives en masse and upload them.

## How to use

1. Run grub, either by launching `grub.bat` or by running `main.py` with python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI.  

2. Check the list of drives to see if all Slippi replay folders are detected. If a directory or drive is missing, press 
**REFRESH DRIVES** to refresh the drives.

3. Choose a name for the tournament and the edition number. By default, these will be set to whatever the ***"TourneyEdition"***
and ***"Edition"*** are set to in `settings.json`.

4. Click **DOWNLOAD** to and choose a directory to download the replays to. You will find Zip archives of each setup, called
Setup #NUM, where NUM is the number of the setup.

**TODO:** Make this upload the replays to discord using a bot

## Installing

It is recommended to first create a virtual environment in python like so:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Then, just install the required dependancies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

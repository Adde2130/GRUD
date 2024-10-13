# GRUD

**G**ame **R**eplay **U**ploader for **D**iscord

Script created in order to download replays from USB drives en masse and upload them.
(Shoutout to Hixon for the name and idea)

**NOTE:** As of right now, grud from the terminal is broken and should not be used

## How to use
0. Configure your settings first. The `GRUDBot_APIKEY` and `ReplayChannelID` values are required for
the bot to send the message to your channel. You also need to add the GRUDBot. ***Right now, you will
have to host your OWN GRUDBot for this to work.*** Don't forget to also set the `FileSizeLimit` allowed per
message if your channel doesn't have any discord channel boosts.

1. Run grud, either by launching `grud.bat` or by running `main.py` with python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI.  

2. Check the list of drives to see if all Slippi replay folders are detected. If a directory or drive is missing, press 
**REFRESH DRIVES** to refresh the drives.

3. Choose a name for the tournament and the edition number. By default, these will be set to whatever the ***"TourneyEdition"***
and ***"Edition"*** are set to in `settings.json`.

4. Click **DOWNLOAD** to and choose a directory to download the replays to. You will find Zip archives of each setup, called
Setup #NUM, where NUM is the number of the setup. The discord bot will send a message to the channel ID given.

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

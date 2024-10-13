# GRUD

**G**ame **R**eplay **U**ploader for **D**iscord

Script created in order to download replays from USB drives en masse and upload them.
(Shoutout to Hixon for the name and idea)


## How to use
0. Configure your settings first. The `GRUDBot_APIKEY` and `ReplayChannelID` values are required for
the bot to send the message to your channel. You also need to add the GRUDBot. ***Right now, you will
have to host your OWN GRUDBot for this to work.*** For the optimal experience, please make sure you have
the *Cascadia Code* font installed, or text may be misaligned. (TODO: Have font included in project)

1. Run grud, either by launching `grud.bat` or by running `main.py` with python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI. **NOTE:** As of right now, GRUD from the terminal is broken and should not be used

2. Check the list of drives to see if all Slippi replay folders are detected. You will see a number
which represents the amount of replay files found within a drive. If you want to save copies of the
replays locally, check the "**Keep copy?**" box and choose a directory for the files to be stored to.

3. Click **DOWNLOAD** to transfer the replays, zip them and then send them to the channel with the `ReplayChannelID`. 
If keeping local copies, you will find Zip archives of each setup, called `Setup #NUM`, where `NUM` is the number of the setup. 

## Installing

It is recommended to first create a virtual environment in python like so:

```bash
python -m venv .venv
.venv\Scripts\activate
```
If you create a virtual environment, then you may want to modify `grud.bat` to activate
your environment before trying to launch GRUD.

Then, install the required dependancies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```
You should also install the fonts *Cascadia Code* and *Cascadia Code Bold* if you want the
text to be properly aligned, as they're the fonts intended for the GUI. 

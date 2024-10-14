# GRUD

**G**ame **R**eplay **U**ploader for **D**iscord

Script created in order to download replays from USB drives en masse and upload them.
(Shoutout to Hixon for the name and idea)


## How to use
0. Configure your settings first. If you don't have a settings.json file, run `grud.bat` and it will
generate a settings file for you. Set the `GRUDBot_APIKEY` and `ReplayChannelID` values required for
the bot to send the message to your channel. If `GRUDBot_APIKEY` or `ReplayChannelID` is not set, the program will run in `Zip-only mode`.

   You also need to add the GRUDBot if you want to send a Discord message with the files attached. ***Right now, you
   will have to host your OWN GRUDBot for this to work.*** For the optimal experience, please make sure you have the
   *Cascadia Code* font installed, or text may be misaligned. (TODO: Have font included in project)

1. Run grud, either by launching `grud.bat` or by running `main.py` with Python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI. **NOTE:** As of right now, GRUD from the terminal is broken and should not be used

2. Check the list of drives to see if all Slippi replay folders are detected. You will see a number
which represents the amount of replay files found within a drive. 

   If you can't fit all of the USBs into your PC at once, please press **Transfer Folders** to transfer
   from all of the drives currently plugged in.

   If you want to save copies of the replays locally, check the "**Keep copy?**" box and    choose a directory
   for the files to be stored to.

   If you **don't** want to send a Discord message and just store the replays locally, uncheck the "**Send message?**" box.
   Note that you can't have both **Keep copy?** and **Send message?** unchecked, as the **Download** button would just
   empty the drives then.

3. Click **DOWNLOAD** to transfer the replays, zip them and then send them to the channel with the `ReplayChannelID`. 
If keeping local copies, you will find Zip archives of each setup, called `Setup #NUM`, where `NUM` is the number of the setup. 

## Installing

It is recommended to first create a virtual environment in Python like so:

```bash
python -m venv .venv
.venv\Scripts\activate
```
If you create a virtual environment, then you may want to modify `grud.bat` to activate
your environment before trying to launch GRUD.

Then, install the required dependencies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```
You should also install the fonts *Cascadia Code* and *Cascadia Code Bold* if you want the
text to be properly aligned, as they're the fonts intended for the GUI. 


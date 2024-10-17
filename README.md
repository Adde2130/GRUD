# GRUD

**G**ame **R**eplay **U**ploader for **D**iscord

Script created in order to download replays from USB drives en masse and upload them.
(Shoutout to Hixon for the name and idea)


## How to use
0. Configure your settings first. If you don't have a settings.json file, run `grud.bat` to generate one. Set the `GRUDBot_APIKEY`
and `ReplayChannelID` values for the GRUDBot to send the message to your channel. If `GRUDBot_APIKEY` or `ReplayChannelID`
is not set, the program will run in **Zip-only mode**.

   You also need to add the GRUDBot to your server if you want to send a Discord message with the files attached. ***Right now, you
   will have to host your OWN GRUDBot for this to work.*** For the optimal experience, ensure you have the
   *Cascadia Code* font installed, or text may be misaligned. (TODO: Have font included in project)

1. Run GRUD, either by launching `grud.bat` or by running `main.py` with Python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI. **NOTE:** GRUD in terminal mode is currently broken and should not be used.

2. Check the list of drives to see if all Slippi replay folders are detected. You will see a number
representing the amount of replay files found within each drive. 

   If a name is missing from any of the drives, click it to rename it. This will add a `GRUD.json` file to
   the root of the drive which will contain the name of the setup (and more useful info in the future).

   If you can't fit all of the USBs into your PC at once, press **Transfer Folders** to transfer
   over all Slippi files form the drives currently plugged in. They will be stored locally until
   they are sent or zipped.

3. Click **DOWNLOAD** to transfer the replays, zip them and then send them to the channel with the `ReplayChannelID`. 

   If you want to save copies of the replays locally, check the "**Keep copy?**" box and choose a directory
   for storing the files. GRUD will save Zip archives of each setup, which may be split into parts if the
   folder size is too big to be sent as one Zip in your Discord channel (Does not apply if **Send message?** is unchecked).

   If you **don't** want to send a Discord message and just store the replays locally, uncheck the "**Send message?**" box.
   This can't be unchecked if **Keep copy?** is also unchecked.


## Installing

It is recommended to first create a virtual environment in Python like so:

```bash
python -m venv .venv
.venv\Scripts\activate
```
If you create a virtual environment, you want to modify `grud.bat` to activate
your environment before launching GRUD. Add the following:

```batch
@echo off
call .venv\Scripts\activate # <-- new line to add
python "%~dp0/main.py" %*
```

Then, install the required dependencies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

You should also install the fonts *Cascadia Code* and *Cascadia Code Bold* if you want the
text to be properly aligned, as they're the fonts intended for the GUI. You can download
them from [here](https://github.com/microsoft/cascadia-code).


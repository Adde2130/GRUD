<p align="center">
   <img src="https://i.imgur.com/Rtipuvi.png"><br>
   <h1 align="center">😱 Game Replay Uploader for Discord 😱</h1> <br>
   <img src="https://i.imgur.com/qfNmWQM.png">
   <p align="center">App created in order to download replays from USB drives en masse and upload them.
   (Shoutout to Hixon for the name and idea)
   <p align="center"></p> <br>
<p>


## How to use
0. Configure your settings first. If you don't have a settings.json file, run `grud.bat` to generate one. Set the `GRUDBot_APIKEY`
and `ReplayChannelID` values for the GRUDBot to send the message to your channel. If `GRUDBot_APIKEY` or `ReplayChannelID`
is not set, the program will run in **Zip-only mode**.

   You also need to add the GRUDBot to your server if you want to send a Discord message with the files attached. ***Right now, you
   will have to host your OWN GRUDBot for this to work.***

1. Run GRUD, either by launching `grud.bat` or by running `main.py` with Python. Run it with the flag `-n` or `--naked` to 
use the program without any GUI. **NOTE:** GRUD in terminal mode is currently broken and should not be used.

   You can also run it with the flag `-ws` in order to create a shortcut with the GRUD logo (Windows only).

2. Check the list of drives to see if all Slippi replay folders are detected. You will see a number
representing the amount of replay files found within each drive. 

   If a name is missing from any of the drives, click it to rename it. This will add a `GRUD.json` file to
   the root of the drive which will contain the name of the setup.

   <p><img src=https://i.imgur.com/ysPbes8.gif></p>

   If you can't fit all of the USBs into your PC at once, press **Store Locally** to transfer
   over all Slippi files form the drives currently plugged in. They will be stored locally on the
   computer until they are sent or zipped.

4. Click **Zip and Send** (Blue button) to transfer the replays, zip them and then send them to the channel with the `ReplayChannelID`. 

   If you want to save copies of the replays locally, check the "**Keep copy?**" box and choose a directory
   for storing the files. GRUD will save Zip archives of each setup, which may be split into parts if the
   folder size is too big to be sent as one Zip in your Discord channel (Does not apply if **Send message?** is unchecked).

   If you **don't** want to send a Discord message and just store the replays locally, uncheck the "**Send message?**" box.
   This can't be unchecked if **Keep copy?** is also unchecked.


## Installing

It is recommended to first create a virtual environment in Python like so:

```shell
python -m venv .venv
```
Then, on Windows run:
```shell
.venv\Scripts\activate
```

For Linux/MacOS, run:
```shell
source .venv/bin/activate
```

If you're on Linux, you may also have to install the tk package
```shell
pacman -S tk
```


Then, install the required dependencies using the `requirements.txt` file:
```shell
pip install -r requirements.txt
```

If you are on Linux or Mac, you should also install the fonts *Cascadia Code* and
*Cascadia Code Bold* if you want the text to be properly aligned, as they're the fonts
used for the GUI. You can download them from [here](https://github.com/microsoft/cascadia-code) or using a package manager.

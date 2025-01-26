# REFERENCE: https://github.com/project-slippi/slippi-wiki/blob/master/SPEC.md

# This would be 1000x nicer to parse in C but I don't want to
# include other languages than python unless I REALLY have to


# TAKE A LOOK AT THIS:
# https://github.com/project-slippi/project-slippi/blob/master/scripts/extractCombos.js
# This is extraction of combos in JavaScript. 

# https://github.com/project-slippi/slippi-js
# This is parsing the files but in JavaScript. 


from dataclasses import dataclass
import os
import random
import string

EVENT_PAYLOADS_OFFSET = 0xF


# OFFSETS FOR THE GAME INFO BLOCK
STATE_OFFSET = 0xE

CHARACTER_OFFSET = 0x60
CHARACTER_TYPE_OFFSET = 0x61 # Player, CPU, Demo, None


CHARACTERS = (
        "Captain Falcon", "Donkey Kong", "Fox", "Mr. Game & Watch",
        "Kirby", "Bowser", "Link", "Luigi", "Mario", "Marth", "Mewtwo",
        "Ness", "Peach", "Pikachu", "Ice Climbers", "Jigglypuff", "Samus",
        "Yoshi", "Zelda", "Sheik", "Falco", "Young Link", "Dr. Mario", 
        "Roy", "Pichu","Ganondorf", "Master Hand", "Wireframe Male",
        "Wireframe Female", "Giga Bowser", "Crazy Hand", "Sandbag", "Popo", "Event"
)

STAGES = (
        "Dummy", "TEST", "Fountain of Dreams", "Pokémon Stadium", 
        "Princess Peach's Castle", "Kongo Jungle", "Brinstar", "Corneria",
        "Yoshi's Story", "Onett", "Mute City", "Rainbow Cruise", "Jungle Japes", 
        "Great Bay", "Hyrule Temple", "Brinstar Depths", "Yoshi's Island",
        "Green Greens", "Fourside", "Mushroom Kingdom I", "Mushroom Kingdom II",
        "Akaneia", "Venom", "Poké Floats", "Big Blue", "Icicle Mountain", "Icetop",
        "Flat Zone", "Dream Land N64", "Yoshi's Island N64", "Kongo Jungle N64",
        "Battlefield", "Final Destination"
)

def parse_file(filename: str) -> tuple[str, str, str]:
    characters = []
    stage = ""

    with open(filename, "rb") as file:
        file.seek(EVENT_PAYLOADS_OFFSET + 1, 0) # Skip payload byte 0x35
        event_payload_size = int.from_bytes(file.read(1), "big")

        game_start_length = 0

        for i in range(event_payload_size // 3):
            event = int.from_bytes(file.read(1), "big")
            if event == 0x36:
                file.seek(1, 1)
                game_start_length = int.from_bytes(file.read(2), "big")
                break

            file.seek(2, 1) # Seek next event

        file.seek(event_payload_size + EVENT_PAYLOADS_OFFSET + 1)
        game_start_bytes = file.read(game_start_length)
        game_info_block = game_start_bytes[0x5:0x138]

        # HERE IS THE ISSUE
        if game_info_block[STATE_OFFSET + 1] >= len(STAGES):
            print(f"UNKNOWN/MODDED STAGE: \nFILE  - {filename}\nSTAGE - {game_info_block[STATE_OFFSET + 1]}")

        if game_info_block[STATE_OFFSET + 1] >= len(STAGES):
            stage = "unknown"
        else:
            stage = STAGES[game_info_block[STATE_OFFSET + 1]]
        
        # Get player characters
        for i in range(4):
            offset = 0x24
            if game_info_block[CHARACTER_TYPE_OFFSET + offset * i] != 3:
                characters.append(CHARACTERS[game_info_block[CHARACTER_OFFSET + offset * i]])

    return (stage, *characters)


def adjust_names(folder: str):
    charset = string.ascii_letters + string.digits
    seed = "".join(random.choices(charset, k=4)) # Avoid name collision

    files = [
        f"{folder}/{file}" 
        for file in os.listdir(folder)
        if file.endswith(".slp")
    ]

    files.sort(key=os.path.getctime, reverse=True)

    for i, file in enumerate(files): 
        stage, *characters = parse_file(file)
        os.rename(file, f"{folder}/{seed}_{i} - {characters[0]} VS. {characters[1]}, {stage}.slp")



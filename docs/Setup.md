# Setup

## Requirements

| Software | Notes |
|---|---|
| [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases/latest) | Install this first |
| [Bizhawk 2.11](https://github.com/TASEmulators/BizHawk/releases/tag/2.11) | **Bizhawk 2.11 required** — This currently runs on the 2.11 version of Bizhawk. Previous versions do not run this game correctly. |
| A LEGALLY DUMPED Wario Land 3 GBC ROM (EN/JP is intended, but should work with other regions) | |

---

## First-Time Setup

### 1. Install the apworld

Open the Archipelago Launcher and click on "Install APWorld", and select the wl3.apworld you downloaded.

### 2. Place your ROM

Click "Browse Files" at the bottom of the Archipelago launcher to open your Archipelago folder.

Place your LEGALLY DUMPED Wario Land 3 ROM exactly `warioland3.gbc` in this folder.

Currently, I have not been able to find any regional differences, so any Wario Land 3 cartridge should work. I have only been able to test with my copy (EN/JP). If you do have a non EN/JP copy, please let me know if there are any issues with it.

### 3. Generate Your Yaml

In the Archipelago launcher, click "Generate Template Options". This should generate a WarioLand3.yaml file. Open the WarioLand3.yaml file in any text editor to select your options! Save your options in your "Archipelago/players" folder! (Click "Browse Files" at the bottom of the Archipelago launcher to open your Archipelago folder)

This yaml is what you what you will roll your seed with, either by putting it in the "Archipelago/Players" folder or what you will provide your host with.

---

## Playing a Game

### Step 1 — Get your patch file

When playing on a hosted room, the room page will have a **Download Patch File** link for your slot. Download the `.apwl3` file from there. (For more information on hosting/generating a seed, please visit (https://archipelago.gg/tutorial/Archipelago/setup_en) and read under "generating a game").

### Step 2 — Patch your ROM

Double-click the `.apwl3` file. The first time setting this up, a prompt will come up asking for your EmuHawk Exectuable. Double-click on your EmuHawk.exe, located in your Bizhawk 2.11 folder (the Bizhawk 2.11 release is linked in the "Requirements" section above). Once you've done this, the patched seed in Bizhawk, the lua script and the Bizhawk Client should all open. After this initial setup, this will happen automatically after double clicking on the `.apwl3` patch.

### Step 3 — Connect in the BizHawk Client

In the BizHawk Client window that opened during patching, enter your connection details and connect:

- **Host:** your server address (e.g. `archipelago.gg:12345` for a hosted room)
- **Slot:** your player name from the YAML
- **Password:** room password if applicable

Once connected, you will be able to start sending/receiving items! Once connected, click New Game. Sending/receiving ability items can be a little buggy on the title screen, so it's suggested to select "New Game" before receiving items.

Have fun!! You will run into bugs, as this game is in a testing phase currently. Please let me know if you run into any bugs or logic issues and I will address them as necessary!

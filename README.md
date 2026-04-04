# Wario Land 3 Archipelago

> **PRE-ALPHA / TESTING ONLY**
> This apworld is in early testing and **should not be brought into public multiworlds**. There will be bugs. You will likely need to use `/send_location` at some point to work around logic issues — please report any you find so they can be fixed!

---

> **AI Disclaimer**
> A significant portion of this project was built with the assistance of [Claude Code](https://claude.ai/claude-code). I want to be fully transparent about this — as it was also a personal learning project for me. I have no issue with anyone choosing not to use this because of AI involvement, and I appreciate any and all feedback with this project!

---

>HUGE SHOUTOUTS to snackerfork for the awesome AP logo, lizzietwoshoes for separating chest/key logic (and logic help in general), and ivory for helping with logic too!

---

## What is this?

A randomizer for **Wario Land 3** built on the [Archipelago](https://archipelago.gg) multiworld framework. Currently, all 100 treasure chests across 25 levels are shuffled into the item pool. All locked levels start with a Red blinking node, and will turn white once they are available to play (when you find their level unlock).

**This project is completely unrelated to the current Wario Land 3 Randomizer. Please direct any questions/concerns to me with this project!**

## What's changed from the vanilla game?
- Progressive Overalls/Grab/Flippers. You SHOULD always receive the first tier of these items! Abilities are also immediately granted, so they should work even if you receive them while in-level.
- LOTS of cutscene skips. You can immediately start playing your game and not wait 5 minutes through intro cutscenes. Also, all cutscenes after treasures/abilities have been cut.
- The entire map has been opened to help a bit with logic. The levels will be locked (notated with a red blinking dot) until you get each levels unlock (i.e. Tablets for W1). This helps the game feel less linear.
- I've taken vanilla Gems out of the game (they were treasures that didn't have any affect on the game). They are now used to notate others items.
   - Red Gems are progression items.
   - Blue Gems are useful items.
   - Green Gems are filler items.
- The option to combine level unlocks to one item has been added (i.e. For W1, you only need "Tablets" instead of each of the two tablets). This helps with generation, seed variety, and keeps the massive amount of progression items down. This is the suggested option. All extra items have been changed to filler (Crests that act as coins). If you do want to play without combined-items, there will be a several pre-fill items placed in your game to help with seed generation.
- The game SHOULD sync all your items if you play offline then reconnect. This needs a bit more testing, but should be working.
- There's nothing that notates that you've received an item in-game. I could set this up as an option, though. You can receive items in-level or overworld, you will receive the item regardless. You'll need to refresh the overworld for the red dots to disappear, but even if they are on the level it's accessible if you have the item(s).
- You SHOULD be able to play this game solo offline completely (with the exception of start_inventory, in which you'll need to connect once). Offline play needs more testing, so please feel free to try this out!
- Rudy cutscene will show the Music Boxes you've collected instead of all 5 (not important but a neat feature!)
- Crests have also been taken out of the game, they now act as Coin items (this helps with the lack of filler items in this game).
- Quick key pickups (down to 1 second). I'm not against adding the vanilla option and instant pickup as QoL, let me know opinions on this!
- Quick treasure pickup. (Also not against adding vanilla pickups back in, just give me opinions on this!)
---

## Requirements

| Software | Notes |
|---|---|
| [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases/latest) | Install this first |
| [Bizhawk 2.11](https://github.com/TASEmulators/BizHawk/releases/tag/2.11) | **Bizhawk 2.11 required** — This currently runs on the 2.11 version of Bizhawk. Previous versions do not run this game correctly. |
| A LEGALLY DUMPED Wario Land 3 GBC ROM (EN/JP is intended, but should work with other regions) | 

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

---

## Options

| Option | Description |
|---|---|
| **Music Boxes Required** | How many of the 5 music boxes must be collected before the Temple opens (0–5) |
| **Music Box Shuffle** | Whether music boxes can only appear at boss chests or anywhere in the multiworld |
| **Start with Axe** | Grants the Axe at the start, opening 3 early locations in Out of the Woods. It's suggested to use this option to help more easily generate seeds. |
| **Combined Level Unlocks** | Combines multi-item level unlocks (e.g. Blue Tablet + Green Tablet → Tablets) into single items for more seed variety |
| **Golf Price** | Vanilla / Cheap / Free mini-game pricing |
| **Golf Building** | Whether the Golf Building requires all 7 crayons or is always open (always free to play) |
| **Start with Magnifying Glass** | Grants the Magnifying Glass at the start (reveals chest collection status on the overworld map) |
| **Music Shuffle** | Randomize level music: vanilla / split day-night / fully random |
| **Palette Shuffle** | Randomize enemy sprite palettes |

---

## Known Quirks

These are known visual or logic oddities. Please report anything else you notice.

**Ability Issues**
- Currently being worked on, but when you have specific abilities, enemies will assume you have Garlic (flying off the screen/destroying heavy enemies). I'm still working on getting this fixed, but I don't currently see any logic issues with it while I figure this out. If you do find some logic issues, PLEASE let me know!

- There are some audio bugs with overalls. This doesn't affect anything, but worth noting.

**Large Non-Cracked Blocks require Garlic + Tier 2 Overalls**
The Peaceful Village Blue Chest and The West Crater Red Chest both require Tier 2 Overalls AND Garlic. This is due to how large non-cracked blocks handle collision — it may be vanilla behavior, but it's not fully confirmed. If you find any other chests or blocks with this issue, please report them.

**N3 (The Vast Plain at Night) — Chemical background glitch**
If you have the blue or red chemical item, the stalks in this level will produce a glitched-looking background. This is a visual issue only and does not affect gameplay.

**W5 (Beneath the waves)— Octopi and the chemical pathway**
With the blue or red chemical, octopi will grow and appear to open the underwater pathway. However, the path remains physically blocked unless you also have the Sapling of Growth — it just looks open. You cannot swim through it.

**S3 (Tower of Revival) — Visual issues**
The Tower of Revival level has some graphical roughness, but all mechanics work correctly. Specifically:
- The Blue Snake Door will appear open but still requires the correct treasures to actually enter
- The wire will appear built but cannot be climbed without the Statue

**S5 (Cave of Flames) — Visual Issues**
Cave of Flames rust blocks show up as non-breakable blocks if you just have rust spray but not explosive plunger box, due to the graphic set per variant. This is only visual, you can break these blocks.

---

## Reporting Issues

This is pre-alpha software. When you encounter a bug or logic issue:

1. Use `/send_location` in the Archipelago text client as a workaround if you're stuck
2. Report the issue with as much detail as possible (level, chest color, items you had, what happened)

Future plans: [Trello](https://trello.com/b/hF0nKXow/wario-land-3-ap)

Thanks for testing!

# FAQ

## What is this?

A randomizer for **Wario Land 3** built on the [Archipelago](https://archipelago.gg) multiworld framework. All 100 chests are randomized, with the option to also randomize the keys and big (musical) coins with treasures and each other, as well as many other Quality of Life and Cosmetic options as well. All locked levels start with a Red blinking node, and will turn white once they are available to play (when you find their level unlock).

**This project is completely unrelated to the current Wario Land 3 Randomizer. Please direct any questions/concerns to me with this project!**

---

## What's changed from the vanilla game?

- Progressive Overalls/Grab/Flippers. You SHOULD always receive the first tier of these items! Abilities are also immediately granted, so they should work even if you receive them while in-level.
- LOTS of cutscene skips. You can immediately start playing your game and not wait 5 minutes through intro cutscenes. Also, all cutscenes after treasures/abilities have been cut.
- The entire map has been opened to help a bit with logic. The levels will be locked (notated with a red blinking dot) until you get each levels unlock (i.e. Tablets for W1). This helps the game feel less linear.
- I've taken vanilla Gems out of the game (they were treasures that didn't have any affect on the game). They are replaced by the Archipelago logo (made by snackerfork), to notate other world's items.
   - Purple AP logos are progression items.
   - Blue AP logos are useful items.
   - Grey AP logos are filler items.
- The option to combine level unlocks and in-level items to one item has been added (i.e. For W1, you only need "Tablets" instead of each of the two tablets). This helps with generation, seed variety, and keeps the massive amount of progression items down. This is the suggested option. All extra items have been changed to filler (Crests that act as coins).
- The game SHOULD sync all your items if you play offline then reconnect. This needs a bit more testing, but should be working.
- When you receive or send an item within a level, a message will show at the bottom of the screen. If you receive one in the overworld, it will show when you next enter a level. "/skip" can be used in the Bizhawk Client to cancel all messages in the queue (e.g. after a release or when re-opening the client).
- When you receive an item in the overworld, if it unlocks a new level, the red dots will not disappear until you refresh the map, but the level will still be accessible if you try to enter it.
- You SHOULD be able to play this game solo offline completely (with the exception of start_inventory, in which you'll need to connect once). Offline play needs more testing, so please feel free to try this out!
- Rudy cutscene will show the Music Boxes you've collected instead of all 5 (not important but a neat feature!)
- Crests have also been taken out of the game, they now act as Coin items (this helps with the lack of filler items in this game).
- Quick key pickups (down to 1 second). I'm not against adding the vanilla option and instant pickup as QoL, let me know opinions on this!
- Quick treasure pickup. (Also not against adding vanilla pickups back in, just give me opinions on this!)
- Keys are persistent - if you collect a key, and then leave the level, you will still have the key. This affects the logic for three chests compared to the vanilla game: N5 Bank of the Wild River Grey and Red Chests, and S3 Tower of Revival Green Chest.
- Musical coins locations disappear after pickup, so that you know what you've already collected!
- Choosing the "Action Help" option in the menu will take you instead to the "Collected Treasures" screen.

---

## How do I report a bug?

This is pre-alpha software. When you encounter a bug or logic issue:

1. Use `/send_location` in the Archipelago text client as a workaround if you're stuck
2. Report the issue with as much detail as possible (level, chest color, items you had, what happened)

Future plans: [Trello](https://trello.com/b/hF0nKXow/wario-land-3-ap)

Thanks for testing!

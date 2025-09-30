# ChromaRoll

A dice-rolling game built in Python, inspired by Balatro with a Yahtzee twist. Roll colorful dice, form hands like pairs or straights, equip charms for bonuses, battle boss effects, and progress through stakes to beat blinds!

## Features
- **Core Gameplay**: Draw 5 dice, hold/reroll/discards to form hands (e.g., Pair, Full House, Straight). Score to beat blind targets.
- **Charms & Pouches**: 30+ charms with effects like score boosts or reroll recyclers. Starting pouches add extra dice/slots.
- **Boss Effects**: 30+ challenging modifiers (e.g., Hold Ban, Face Shuffle) for Boss blinds.
- **Progression**: Stakes increase difficulty; unlocks for pouches/charms (WIP).
- **UI & Audio**: Resizable window, animations, SFX (roll, break, coin), mute toggle in pause menu.
- **Debug Mode**: Unlimited rerolls, forced dice colors for testing.

## Installation
1. **Prerequisites**: Python 3.8+ and Pygame (`pip install pygame`).
2. Clone the repo:git clone https://github.com/dmandork/ChromaRoll.git
cd ChromaRoll
3. Run the game:

For a standalone executable, use PyInstaller: `pyinstaller --onefile ChromaRoll.py` (add `--add-data "assets;assets"` for assets).

## Usage
- **Controls**:
- Mouse: Click dice to hold/discard, buttons to roll/score/shop.
- Escape: Pause menu (return, main menu, quit, mute).
- **Game Flow**: Choose pouch > Roll dice > Hold/reroll > Score hands to beat blinds > Shop for charms > Repeat with increasing stakes.
- **Debug**: Set `DEBUG = True` in constants.py for infinite coins/rerolls and forced dice colors.

## Project Structure
- `ChromaRoll.py`: Main game class and loop.
- `savegame.py`: Saving/loading game state.
- `constants.py`: Game constants (sizes, colors, themes).
- `data.py`: Charms, pouches, boss effects, hand types.
- `utils.py`: Helpers (resource paths, drawing, bag creation).
- `statemachine.py`: State machine for screens (splash, game, shop, pause).
- `screens.py`: Rendering functions for UI/screens.
- `assets/`: Images (icons, titlescreen), audio (sounds), fonts.

## Contributing
- Fork the repo and create a pull request for fixes/features.
- Report issues on GitHub (e.g., bugs, balance suggestions).
- Todo: Full tutorial, more unlocks, balancing.

## License


---

Screenshots/GIFs (add if available):
![Gameplay Screenshot](path/to/screenshot.png)

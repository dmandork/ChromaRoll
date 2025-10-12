# savegame.py
import json
import os
import copy
import data  # For restoring pouch by name
import constants
# At the top of savegame.py, ensure these imports are present (add any missing ones):
from states.splash import SplashState
from states.prompt import PromptState
from states.init import InitState
from states.shop import ShopState
from states.game import GameState
from states.blinds import BlindsState
from states.game_over import GameOverState
# If you have a pause state (commented in your code), add:
from states.pause import PauseMenuState

def save_game(game):
    """Saves the game state to JSON."""
    print("Saving to:", os.path.abspath('save.json'))
    current_state_name = type(game.state_machine.current_state).__name__ if hasattr(game, 'state_machine') and game.state_machine.current_state else None
    previous_state_name = type(game.previous_state).__name__ if game.previous_state and not isinstance(game.previous_state, str) else game.previous_state
    save_data = {
        'turn_initialized': game.turn_initialized,
        'version': 1,  # Add versioning for future-proofing (increment on breaking changes)
        'coins': game.coins,
        'extra_coins': game.extra_coins,
        'bag': copy.deepcopy(game.bag),  # Deep copy for dicts/lists
        'full_bag': copy.deepcopy(game.full_bag),
        'equipped_charms': copy.deepcopy(game.equipped_charms),
        'disabled_charms': game.disabled_charms[:],  # List copy
        'current_stake': game.current_stake,
        'current_blind': game.current_blind,
        'round_score': game.round_score,
        'pouch_type': game.current_pouch['name'] if hasattr(game, 'current_pouch') and game.current_pouch else None,
        'green_pouch_active': game.green_pouch_active if hasattr(game, 'green_pouch_active') else False,
        'hands_left': game.hands_left,
        'rerolls_left': game.rerolls_left,
        'discards_left': game.discards_left,
        'discard_used_this_round': game.discard_used_this_round,
        'hand': copy.deepcopy(game.hand),
        'rolls': copy.deepcopy(game.rolls),
        'held': game.held[:],
        'discard_selected': game.discard_selected[:],
        'is_discard_phase': game.is_discard_phase,
        'has_rolled': game.has_rolled,
        'broken_dice': game.broken_dice[:],
        'break_effect_start': game.break_effect_start,
        'temp_message': game.temp_message,
        'temp_message_start': game.temp_message_start,
        'upcoming_boss_effect': copy.deepcopy(game.upcoming_boss_effect) if game.upcoming_boss_effect else None,
        'current_boss_effect': copy.deepcopy(game.current_boss_effect) if game.current_boss_effect else None,
        'boss_rainbow_color': game.boss_rainbow_color,
        'boss_shuffled_faces': copy.deepcopy(game.boss_shuffled_faces),
        'boss_reroll_count': game.boss_reroll_count,
        'shop_charms': copy.deepcopy(game.shop_charms),
        'available_packs': game.available_packs[:],
        'shop_reroll_cost': game.shop_reroll_cost,
        'current_state': current_state_name,
        'previous_state': previous_state_name,  # New: Save previous for pause cases
        'mute': game.mute,  # Save mute state
        'rune_tray': copy.deepcopy(game.rune_tray),
        'confirmed_hands_this_round': game.confirmed_hands_this_round,
        'hands_played_this_round': getattr(game, 'hands_played_this_round', 0),  # Keep for compatibility
        # Dagger/Score Multipliers
        'score_mult': getattr(game, 'score_mult', 1.0),  # Safe default if not present
        'dagger_mult': getattr(game, 'dagger_mult', 0.0),
        
        # Pack/Shop Continuity
        'pack_choices': copy.deepcopy(game.pack_choices),  # Deepcopy for list of dicts/strings
        'confirm_sell_index': game.confirm_sell_index,
        
        # Turn and Popups
        'turn': game.turn,
        'show_popup': game.show_popup,
        'popup_message': game.popup_message if game.popup_message else "",  # Handle None
        
        # If you add instance-tracked modified constants (recommended for charm bonuses)
        'effective_interest_max': getattr(game, 'effective_interest_max', constants.INTEREST_MAX),

        # Tutorial Progress (new)
        'tutorial_step': game.tutorial_step,
        'tutorial_mode': game.tutorial_mode,
        'tutorial_completed': game.tutorial_completed,
        
        # Unlocks (new, deepcopy for dict)
        'unlocks': copy.deepcopy(game.unlocks),
        'hand_multipliers': copy.deepcopy(game.hand_multipliers)
    }
    try:
        with open('save.json', 'w') as f:
            json.dump(save_data, f, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else o)
    except IOError as e:
        print(f"Error saving game: {e}")  # Basic logging; could set game.temp_message instead

# Then, inside load_game (or just before it), add this dict:
STATE_MAP = {
    'SplashState': SplashState,
    'PromptState': PromptState,
    'InitState': InitState,
    'ShopState': ShopState,
    'GameState': GameState,
    'BlindsState': BlindsState,
    'GameOverState': GameOverState,
    'PauseMenuState': PauseMenuState,
}

def load_game(game):
    """Loads the game state from JSON."""
    try:
        with open('save.json', 'r') as f:
            save_data = json.load(f)
        
        # Check version (for future migrations)
        version = save_data.get('version', 0)  # Default 0 for old saves
        if version > 1:
            print("Warning: Save from newer version—may not load fully.")  # Or raise/return None
            # Future: Add migration logic here (e.g., if version==2, add new fields)
        elif version < 1:
            print("Old save detected—attempting load with defaults.")
        
        # All setters moved here (from the old if block)
        game.turn_initialized = save_data.get('turn_initialized', False)
        game.coins = save_data.get('coins', 0)
        game.extra_coins = save_data.get('extra_coins', 0)
        game.bag = copy.deepcopy(save_data.get('bag', []))
        game.full_bag = copy.deepcopy(save_data.get('full_bag', []))
        game.equipped_charms = copy.deepcopy(save_data.get('equipped_charms', []))
        game.disabled_charms = save_data.get('disabled_charms', [])
        game.current_stake = save_data.get('current_stake', 1)
        game.current_blind = save_data.get('current_blind', 'Small')
        game.round_score = save_data.get('round_score', 0)
        pouch_name = save_data.get('pouch_type')
        if pouch_name:
            game.current_pouch = next((p for p in data.POUCHES if p['name'] == pouch_name), None)
            if game.current_pouch:
                game.max_charms = 5 + game.current_pouch.get('bonus', {}).get('charm_slots', 0)
                game.green_pouch_active = 'Green' in game.current_pouch['name']
                # Add other static pouch effects here (e.g., if any flags beyond green)
            else:
                print(f"Warning: Pouch '{pouch_name}' not found in data.POUCHES—using defaults.")
        game.green_pouch_active = save_data.get('green_pouch_active', False)
        game.hands_left = save_data.get('hands_left', constants.MAX_HANDS)
        game.rerolls_left = save_data.get('rerolls_left', constants.MAX_REROLLS)
        game.discards_left = save_data.get('discards_left', constants.MAX_DISCARDS)
        game.discard_used_this_round = save_data.get('discard_used_this_round', False)
        game.hand = copy.deepcopy(save_data.get('hand', []))
        game.rolls = copy.deepcopy(save_data.get('rolls', []))
        game.held = save_data.get('held', [False] * constants.NUM_DICE_IN_HAND)
        game.discard_selected = save_data.get('discard_selected', [False] * constants.NUM_DICE_IN_HAND)
        game.is_discard_phase = save_data.get('is_discard_phase', False)
        game.has_rolled = save_data.get('has_rolled', False)
        game.broken_dice = save_data.get('broken_dice', [])
        game.break_effect_start = save_data.get('break_effect_start', 0)
        game.temp_message = save_data.get('temp_message', None)
        game.temp_message_start = save_data.get('temp_message_start', 0)
        game.upcoming_boss_effect = copy.deepcopy(save_data.get('upcoming_boss_effect', None))
        game.current_boss_effect = copy.deepcopy(save_data.get('current_boss_effect', None))
        game.boss_rainbow_color = save_data.get('boss_rainbow_color', None)
        game.boss_shuffled_faces = copy.deepcopy(save_data.get('boss_shuffled_faces', {}))
        game.boss_reroll_count = save_data.get('boss_reroll_count', 0)
        game.shop_charms = copy.deepcopy(save_data.get('shop_charms', []))
        game.available_packs = save_data.get('available_packs', [])
        game.shop_reroll_cost = save_data.get('shop_reroll_cost', 5)
        game.mute = save_data.get('mute', False)
        game.toggle_mute()  # Applies volumes immediately (ensures SFX are set correctly on load)
        game.hand_multipliers = copy.deepcopy(save_data.get('hand_multipliers', {}))
        game.confirmed_hands_this_round = save_data.get('confirmed_hands_this_round', 0)
        game.hands_played_this_round = save_data.get('hands_played_this_round', 0)  # Keep for compatibility
        game.rune_tray = copy.deepcopy(save_data.get('rune_tray', [None, None]))
        for ht in data.HAND_TYPES:
            if ht not in game.hand_multipliers:
                game.hand_multipliers[ht] = 1.0
        # Dagger/Score Multipliers
        game.score_mult = save_data.get('score_mult', 1.0)
        game.dagger_mult = save_data.get('dagger_mult', 0.0)  # Single set; removed duplicate below

        # Pack/Shop Continuity
        game.pack_choices = copy.deepcopy(save_data.get('pack_choices', []))
        game.confirm_sell_index = save_data.get('confirm_sell_index', -1)

        # Turn and Popups
        game.turn = save_data.get('turn', 0)
        game.show_popup = save_data.get('show_popup', False)
        game.popup_message = save_data.get('popup_message', "")

        # If adding modified constants
        game.effective_interest_max = save_data.get('effective_interest_max', constants.INTEREST_MAX)
        # Removed duplicate dagger_mult set here

        # Tutorial Progress (new)
        game.tutorial_step = save_data.get('tutorial_step', 0)
        game.tutorial_mode = save_data.get('tutorial_mode', False)
        game.tutorial_completed = save_data.get('tutorial_completed', False)

        # Unlocks (new)
        game.unlocks = copy.deepcopy(save_data.get('unlocks', {}))

        # In load_game, remove/replace the existing if-block with:
        game.apply_boss_face_shuffle()

        # Recompute hand/modifier texts based on loaded state
        game.update_hand_text()

        # Restore state (use previous if paused)
        saved_state = save_data.get('current_state')
        saved_previous = save_data.get('previous_state')
        resume_state = saved_previous if saved_state == 'PauseMenuState' else saved_state
        state_class = STATE_MAP.get(resume_state, BlindsState)  # Fallback to BlindsState

        # Set is_resuming if loading into GameState
        if resume_state == 'GameState':
            game.is_resuming = True

        game.state_machine.change_state(state_class(game))
        return save_data  # Return the dict for PromptState
    except FileNotFoundError:
        return None  # No save
    except json.JSONDecodeError as e:
        print(f"Corrupt save file: {e}. Deleting and starting fresh.")  # Or set game.temp_message = "Corrupt save—starting new."
        delete_save()
        return None  # Invalid file
    except Exception as e:  # Catch-all for unexpected (e.g., key errors in data)
        print(f"Unexpected load error: {e}")
        return None

def delete_save():
    """Deletes the save file."""
    if os.path.exists('save.json'):
        os.remove('save.json')
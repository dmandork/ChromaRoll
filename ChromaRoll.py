from cmath import rect
import math  # For ceil in bag rows
import random  # For rolling dice and drawing from bag
import pygame  # For graphics and input handling
import time  # For animation delays
import copy
import sys
sys.path.insert(0, '.')
import data
import screens
import savegame
import os
from constants import *
from utils import draw_rounded_element, resource_path, create_dice_bag, wrap_text, get_easing

from states.splash import SplashState
from states.prompt import PromptState
from states.init import InitState
from states.shop import ShopState
from states.base import StateMachine
from states.game_over import GameOverState



# Rarity base weights (0-1 scale)
RARITY_WEIGHTS = {
    'Common': 0.6,
    'Uncommon': 0.3,
    'Rare': 0.1,
    'Legendary': 0.0  # Starts at 0, ramps with stake
}

# Game class to manage state and visuals
class ChromaRollGame:
    def __init__(self):
        pygame.init()  # Initialize Pygame
        self.loaded_from_save = False
        self.turn_initialized = False
        self.hovered_die = None  # Index of die under mouse, or None
        self.hovered_hand_die = None
        self.hovered_bag_die = None
        self.hand_die_rects = []
        self.bag_die_rects = []

        # Dedup CHARMS_POOL by name (safeguard against old dups or mutations)
        unique_pool = {}
        for c in data.CHARMS_POOL:
            if c['name'] not in unique_pool:
                unique_pool[c['name']] = c
        data.CHARMS_POOL = list(unique_pool.values())
        #  print("DEBUG: Deduped CHARMS_POOL to", len(data.CHARMS_POOL), "unique charms")  # Optional: Confirm (remove after test)
        
        self.state_machine = StateMachine(self, SplashState(self))
        self.screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)  # Resizable window
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Chroma Roll")  # Set title
        # Use imported THEME (raw paths) + resource_path for loading
        self.font = pygame.font.Font(resource_path(THEME['font_main_path']), THEME['font_main_size'])  # Font for text
        self.small_font = pygame.font.Font(resource_path(THEME['font_small_path']), THEME['font_small_size'])  # Smaller font for hand/modifier info
        self.tiny_font = pygame.font.Font(resource_path(THEME['font_tiny_path']), THEME['font_tiny_size'])  # Even smaller for top texts

        # Show loading text during heavy loads
        self.screen.fill(THEME['background'])
        loading_text = self.font.render("Loading...", True, (THEME['text']))
        self.screen.blit(loading_text, (self.width // 2 - loading_text.get_width() // 2, self.height // 2 - loading_text.get_height() // 2))
        pygame.display.flip()

        # Pre-load splash image
        try:
            self.splash_image = pygame.image.load(resource_path('assets/images/titlescreen.png')).convert()
        except pygame.error as e:
            print(f"Error loading splash: {e}")
            self.splash_image = pygame.Surface((838, 1248))  # Fallback blank
            self.splash_image.fill((0, 0, 0))  # Black if missing

        # Pre-load other assets (icons, sounds, etc.) here as before
        # e.g., your charm pre-load loop, mixer.init(), Sound loads

        # In __init__, add the icon paths and cache
        self.charm_icon_paths = {
            'Zany Charm': resource_path('assets/icons/zany_charm.png'),
            'Mad Charm': resource_path('assets/icons/two_pair.png'),
            'Crazy Charm': resource_path('assets/icons/crazy_charm.png'),
            'Droll Charm': resource_path('assets/icons/droll_charm.png'),
            'Sly Charm': resource_path('assets/icons/sly_charm.png'),
            'Wily Charm': resource_path('assets/icons/wily.png'),
            'Clever Charm': resource_path('assets/icons/clever.png'),
            'Devious Charm': resource_path('assets/icons/devious_charm.png'),
            'Half Charm': resource_path('assets/icons/half.png'),
            'Stencil Charm': resource_path('assets/icons/stencil.png'),
            'Four Fingers Charm': resource_path('assets/icons/four_fingers.png'),
            'Mime Charm': resource_path('assets/icons/clown_mime.png'),
            'Debt Charm': resource_path('assets/icons/debt.png'),
            'Dagger Charm': resource_path('assets/icons/dagger_charm.png'),
            'Golden Touch Charm': resource_path('assets/icons/golden_touch.png'),
            'Silver Lining Charm': resource_path('assets/icons/silver_lining.png'),
            'Fragile Fortune Charm': resource_path('assets/icons/fragile_fortune.png'),
            'Even Stevens Charm': resource_path('assets/icons/even_stevens.png'),
            'Oddball Charm': resource_path('assets/icons/oddball.png'),
            'Rainbow Prism Charm': resource_path('assets/icons/rainbow_prism.png'),
            'Full House Party Charm': resource_path('assets/icons/full_house_party.png'),
            'Quadruple Threat Charm': resource_path('assets/icons/quadruple_threat.png'),
            'Reroll Recycler Charm': resource_path('assets/icons/reroll_recycler_charm.png'),
            'Interest Booster Charm': resource_path('assets/icons/interest_booster_charm.png'),
            # Add paths for your other charms here, e.g.:
            # 'Basic Charm': 'assets/icons/basic_charm.png',
            # 'Red Greed Charm': 'assets/icons/red_greed.png',
            # 'Blue Lust Charm': 'assets/icons/blue_lust.png',
            # 'Green Wrath Charm': 'assets/icons/green_wrath.png',
            # 'Purple Glutton Charm': 'assets/icons/purple_glutton.png',
            # 'Yellow Jolly Charm': 'assets/icons/yellow_jolly.png',
            # And so on for the remaining ~6 charms in your pool.
        }

        self.charm_icon_cache = {}

        # After charm_icon_cache loading
        self.pack_icon_paths = {
            0: resource_path('assets/icons/Basic_Prism.png'),  # pack_idx 0
            1: resource_path('assets/icons/Standard_Prism.png'),  # 1
            2: resource_path('assets/icons/Premium_Prism.png')   # 2
        }
        self.pack_icon_cache = {}
        for pack_idx, path in self.pack_icon_paths.items():
            try:
                original = pygame.image.load(path)
                scaled = pygame.transform.smoothscale(original, (40, 40))  # Fixed size for centering (adjust if too small)
                self.pack_icon_cache[pack_idx] = scaled
            except Exception as e:
                print(f"Failed to load pack icon {path}: {e}")

        self.button_paths = {
        'green': resource_path('assets/icons/button_green.png'),
        'red': resource_path('assets/icons/button_red.png'),
        }
        self.button_cache = {}
        for key, path in self.button_paths.items():
            try:
                original = pygame.image.load(path)
                scaled = pygame.transform.smoothscale(original, (BUTTON_WIDTH, BUTTON_HEIGHT))  # Fit 150x50
                self.button_cache[key] = scaled
            except Exception as e:
                print(f"Failed to load button {path}: {e}")

        # Pre-load all charm icons into cache (for efficiency—no reloads in loops)
        inner_size = int(CHARM_DIE_SIZE * INNER_ICON_SCALE)  # e.g., 80 for 0.8 scale
        for name, path in self.charm_icon_paths.items():
            try:
                image = pygame.image.load(resource_path(path)).convert_alpha()
                scaled = pygame.transform.smoothscale(image, (inner_size, inner_size))  # Scale to inner (80x80)
                self.charm_icon_cache[path] = scaled
            except pygame.error as e:
                print(f"Error pre-loading charm icon {path}: {e}")
        
        # Load break icon (fragile_fortune PNG)
        try:
            break_image = pygame.image.load(resource_path('assets/icons/fragile_fortune.png')).convert_alpha()
            self.break_icon = pygame.transform.smoothscale(break_image, (DIE_SIZE, DIE_SIZE))
        except pygame.error as e:
            print(f"Error loading break icon: {e}")
            self.break_icon = None

        # Audio setup
        pygame.mixer.init()  # Init mixer (keep your existing init)
        self.mute = False  # Default unmuted
        self.sfx_volume = 1.0  # Base multiplier for SFX volumes (we'll scale your per-sound volumes)

        # Load existing SFX (keep your loads and initial volumes)
        self.roll_sound = pygame.mixer.Sound(resource_path('assets/audio/roll.wav'))
        self.roll_sound.set_volume(0.5 * self.sfx_volume if not self.mute else 0.0)  # Apply mute scaling
        self.break_sound = pygame.mixer.Sound(resource_path('assets/audio/break.wav'))
        self.break_sound.set_volume(0.7 * self.sfx_volume if not self.mute else 0.0)
        self.coin_sound = pygame.mixer.Sound(resource_path('assets/audio/coin.wav'))
        self.coin_sound.set_volume(0.4 * self.sfx_volume if not self.mute else 0.0)

        # Optional BGM (add if you want background music; skip if not)
        self.background_music_path = resource_path('assets/audio/background_music.ogg')  # Example path
        if os.path.exists(self.background_music_path):
            pygame.mixer.music.load(self.background_music_path)
            pygame.mixer.music.play(-1)  # Loop
            pygame.mixer.music.set_volume(0.5 if not self.mute else 0.0)  # Example base volume

        # Channels for SFX (recommended for group control; optional but future-proof)
        self.sfx_channel = pygame.mixer.Channel(0)  # Use this for playing SFX later

        # Load icons for mute button (optional; fallback to text if files missing)
        try:
            self.speaker_on_icon = pygame.transform.scale(pygame.image.load(resource_path('assets/icons/speaker_on.png')), (40, 40))
            self.speaker_off_icon = pygame.transform.scale(pygame.image.load(resource_path('assets/icons/speaker_off.png')), (40, 40))
        except FileNotFoundError:
            self.speaker_on_icon = None  # Fallback to text button

        self.mute_button_rect = pygame.Rect(self.width - 50, 10, 40, 40)  # Top-right; adjust as needed

        self.current_boss_effect = None  # Current active boss effect dict, or None
        self.disabled_charms = []  # For effects like Charm Glitch/Eclipse: list of indices or names
        self.boss_reroll_count = 0  # Track rerolls used for effects like Break Surge
        self.boss_rainbow_color = None  # For Rainbow Restriction: fixed color for the round
        self.boss_shuffled_faces = {}  # Die ID to shuffled faces for Face Shuffle
        self.upcoming_boss_effect = None  # Preview of the Boss effect for the current round
        self.upcoming_boss_effect = random.choice(data.BOSS_EFFECTS)  # Initial preview for first round

        self.debug_boss_dropdown_open = False  # Flag for dropdown panel
        self.debug_boss_scroll_offset = 0  # For scrolling long list
        self.debug_boss_selected = None  # Temp for selection

        self.is_last_hand = False         # For Final Forge
        self.is_final_discard = False     # For Acrobat Amulet
        self.used_reroll_advantage = False  # For Fate's Favor
        self.rune_cast_used = False       # For Gambler's Grimoire

        self._init_defaults()  # Call after one-time setups

    def _init_defaults(self):
        self.bag = create_dice_bag()  # Create dice bag (mutable list for removal)
        self.hand = []  # Current hand of dice
        self.full_bag = [d.copy() for d in self.bag]  # Template of all owned dice
        self.rolls = []  # Current rolls: list of (die, value)
        self.held = [False] * NUM_DICE_IN_HAND  # Track held dice
        self.discard_selected = [False] * NUM_DICE_IN_HAND  # Track selected for discard
        self.rerolls_left = -1 if DEBUG and DEBUG_UNLIMITED_REROLLS else MAX_REROLLS  # Rerolls per turn (-1 for unlimited in debug)
        self.discards_left = MAX_DISCARDS  # Discards per round
        self.discard_used_this_round = False  # Track if discard was used in the current hand's discard phase
        self.hands_left = MAX_HANDS  # Hands (scores) per round
        self.coins = 0  # Chroma Coins for upgrades
        self.extra_coins = 0  # For tracking bonus coins from gold and silver dice
        if DEBUG and DEBUG_INFINITE_COINS:
            self.coins = 999999  # Infinite coins for debug (large value to simulate infinity without breaking int ops)
        self.round_score = 0  # Score for current blind/round
        self.current_stake = 1  # Current stake level
        self.current_blind = 'Small'  # Current blind: Small, Big, Boss
        self.game_state = 'splash'  # Start with splash instead of 'blinds'
        self.splash_start_time = 0  # Timestamp for anim start
        self.splash_phase = 'pan'  # Phases: 'pan', 'hold', 'zoom_out', 'done'
        self.previous_state = None  # Init to starting state
        self.pause_menu_selection = None  # For button handling (optional)
        self.show_popup = False  # Flag for beaten blind popup
        self.broken_dice = []  # List of indices (0-4) of breaking Glass dice
        self.break_effect_start = 0  # Timestamp when effect starts
        self.break_effect_duration = 1.0  # Seconds for fade-out
        self.popup_message = ""  # Message for beaten blind popup
        self.temp_message = None  # Text for temporary messages
        self.temp_message_start = 0  # Timestamp for fade start
        self.temp_message_duration = 3.0  # Seconds to show message
        self.turn = 0  # Current turn number
        self.current_hand_text = ""  # Text for current hand type and base points
        self.current_modifier_text = ""  # Text for color modifier
        self.is_discard_phase = True  # Start in discard phase before first roll
        self.has_rolled = False  # Track if initial roll happened
        self.max_charms = 5
        self.equipped_charms = []
        self.shop_charms = []
        self.dragging_charm_index = -1  # For drag and drop
        self.dragging_shop = False  # Flag if dragging in shop
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.score_mult = 1.0  # For Dagger charm
        self.hand_multipliers = {ht: 1.0 for ht in data.HAND_TYPES}  # Multipliers for hand types
        self.pack_choices = []  # Choices for pack selection
        self.confirm_sell_index = -1  # Index of charm to confirm sell
        self.shop_reroll_cost = 5  # Initial reroll cost for shop
        self.available_packs = random.sample([0, 1, 2, 3, 4], 2)  # Random 2 from 5 packs
        self.available_rune_packs = []
        self.multipliers_hover = False  # For showing multipliers panel
        self.current_pouch = None
        self.active_tags = []
        self.rune_tray = [None, None]  # Two rune slots
        # Dedup CHARMS_POOL by name (safeguard against old dups)
        seen_names = set()
        self.is_resuming = False  # Flag
        self.select_count = 1  # For multi-select in packs
        self.selected_runes = []  # Temp for rune selection
        self.current_rune = None  # For 
        self.current_rune_slot = -1
        self.selected_dice = []  # For die selection during apply

        # Set initial hand texts
        self.update_hand_text()
        self.tutorial_step = 0  # Current step in tutorial (0-5)
        self.tutorial_mode = False  # Flag if in tutorial
        self.tutorial_completed = False  # Track if finished (for future skips/unlocks)
        pouches = data.POUCHES
        if DEBUG:
            for pouch in pouches[4:]:  # Indices 4-7 for 5-8
                pouch['unlocked'] = True
        self.selected_pouch = None  # Track chosen pouch for bonuses
        self.green_pouch_active = False  # Flag for Green Pouch effect
        self.pouch_offset = 0  # For carousel scrolling
        self.unlocks = {}  # Future: Track unlocks, e.g., self.unlocks['Black Pouch'] = False; for now, use pouch['unlocked']
        self.current_boss_effect = None  # Current active boss effect dict, or None
        self.disabled_charms = []  # For effects like Charm Glitch/Eclipse: list of indices or names
        self.boss_reroll_count = 0  # Track rerolls used for effects like Break Surge
        self.boss_rainbow_color = None  # For Rainbow Restriction: fixed color for the round
        self.boss_shuffled_faces = {}  # Die ID to shuffled faces for Face Shuffle
        self.upcoming_boss_effect = None  # Preview of the Boss effect for the current round
        self.upcoming_boss_effect = random.choice(data.BOSS_EFFECTS)  # Initial preview for first round
        self.debug_boss_dropdown_open = False  # Flag for dropdown panel
        self.debug_boss_scroll_offset = 0  # For scrolling long list
        self.debug_boss_selected = None  # Temp for selection
        self.hands_played_this_round = 0  # (increment on score)
        self.avoid_streak = 0  # (reset on most_played use, +1 otherwise)
        self.most_played_hand = None  # (update post-score with max freq)
        self.lucky_triggers = 0  # (from rune logic)
        self.shop_rerolls = 0  # (increment on reroll_shop)
        self.stake_milestones = 0  # ( +1 on blind/boss win)
        self.die_score_bonus = 0  # (for Hiker permanent)
        self.permanent_score_bonus = 0  # (for Square scaling—add charm['value'] on condition met)
        self.discards_used_this_round = 0  # Track for Discard Drake/Acrobat Amulet
        self.rerolls_left_initial = 3
        self.hand_play_counts = {ht: 0 for ht in data.HAND_TYPES}  # Track counts per hand type

    


    def toggle_mute(self):
        self.mute = not self.mute
        # Apply to SFX (scale your original volumes)
        self.roll_sound.set_volume(0.5 * self.sfx_volume if not self.mute else 0.0)
        self.break_sound.set_volume(0.7 * self.sfx_volume if not self.mute else 0.0)
        self.coin_sound.set_volume(0.4 * self.sfx_volume if not self.mute else 0.0)
        # If adding BGM: pygame.mixer.music.set_volume(0.5 if not self.mute else 0.0)
        # If using channel for play: self.sfx_channel.set_volume(0.0 if self.mute else self.sfx_volume)

    def get_bag_color(self):
        """Returns the bag color based on selected pouch, fallback to default brown."""
        if self.current_pouch and 'color' in self.current_pouch:
            return COLORS.get(self.current_pouch['color'], BAG_COLOR)
        return BAG_COLOR  # Default brown if no pouch selected
    
    # Function to draw a hand of dice from the bag
    def draw_hand(self, num_dice=NUM_DICE_IN_HAND):
        """Randomly draws unique dice from the bag without replacement. Resets bag if too low."""
        
        if len(self.full_bag) == 0:  # All dice destroyed (breaks emptied everything)
            self.game_state = 'game_over'
            self.popup_message = "All dice shattered! Game Over."  # Optional: Custom message in game_over screen
            return  # Exit early, no draw
        
        if len(self.bag) < num_dice:
            full_refill = [copy.deepcopy(d) for d in self.full_bag]
            if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Bag Bottleneck':
                random.shuffle(full_refill)
                self.bag[:] = full_refill[:len(full_refill)//2]  # Half full
            else:
                self.bag[:] = full_refill
        
        if DEBUG and DEBUG_FORCE_BAG_COLORS:
            # Default to empty if not defined (e.g., commented out)
            debug_colors = globals().get('DEBUG_COLORS', [])  # Safely get global if commented
            if debug_colors:  # Only force if non-empty list
                # Debug mode: Force specific colors without removing from bag
                hand = []
                for color in debug_colors:
                    available = [d for d in self.bag if d['color'] == color]
                    if available:
                        selected = random.choice(available)
                        hand.append(copy.deepcopy(selected))  # Deepcopy to avoid mutating original bag dice
                    else:
                        # New: If no dice of this color (e.g., Glass for testing), create temp one
                        temp_id = f"Temp{color}{len(hand) + 1}"
                        temp_die = {'id': temp_id, 'color': color, 'faces': DICE_FACES[:], 'is_temp': True}  # Flag as temp (optional: skip in saves)
                        hand.append(temp_die)  # Add temp without modifying bag
                #  print(f"DEBUG: Forced hand colors: {[d['color'] for d in hand]}")  # Log for insight (remove if noisy)
                return hand[:num_dice]  # Ensure exactly num_dice (trim if extra)
            # If empty, fall through to normal draw (with other DEBUG perks active)
        else:
            # Normal bag creation (your existing code here)
            pass  # No additional logic needed here; continue to normal draw below
        
        # Normal draw (or DEBUG fallback)
        actual_num = min(num_dice, len(self.bag))
        hand = random.sample(self.bag, actual_num)
        for die in hand:
            self.bag.remove(die)  # Remove drawn dice from bag
        return hand
    
    def get_blind_target(self, blind_type=None):
        """Calculates the target score for the specified or current blind, scaled by stake and boss effects if applicable."""
        if blind_type is None:
            blind_type = self.current_blind
        base_target = BASE_TARGETS[blind_type]
        target = base_target * (1 + (self.current_stake - 1) * 0.5)
        # Apply boss effects only if this is the current blind and it's Boss (effects are per-round)
        if blind_type == self.current_blind and self.current_blind == 'Boss' and self.current_boss_effect:
            effect_name = self.current_boss_effect['name']
            if effect_name == 'Target Bump':
                target *= 1.20
            elif effect_name == 'Blind Boost':
                target *= 1.30
        return target
    
    # New helper method to calculate stencil mult (add to class)
    def get_stencil_mult(self):
        for charm in self.equipped_charms:
            if charm['type'] == 'empty_slot_mult':
                empty_slots = self.max_charms - len(self.equipped_charms)  # Exclude self (actual empties only)
                return 1.0 + (charm['value'] * empty_slots)  # e.g., +0.5 per empty
        return 1.0  # No stencil

    def advance_blind(self):
        """Advances to the next blind or stake and resets the dice bag."""
        blind_order = ['Small', 'Big', 'Boss']
        current_index = blind_order.index(self.current_blind)
        if current_index < len(blind_order) - 1:
            self.current_blind = blind_order[current_index + 1]
        else:
            self.current_stake += 1
            self.current_blind = 'Small'
            self.upcoming_boss_effect = None  # Reset preview for new round/stake

        self.confirmed_hands_this_round = 0

        # Reset boss states
        self.current_boss_effect = None
        self.disabled_charms = []
        self.boss_reroll_count = 0
        self.boss_rainbow_color = None
        self.boss_shuffled_faces = {}

        # Generate preview if starting Small
        if self.current_blind == 'Small':
            self.upcoming_boss_effect = random.choice(data.BOSS_EFFECTS)  # Pre-generate for preview

        if self.current_blind == 'Boss':
            self.current_boss_effect = self.upcoming_boss_effect or random.choice(data.BOSS_EFFECTS)  # Use preview if set
            if self.current_boss_effect['name'] == 'Charm Glitch' and self.equipped_charms:
                self.disabled_charms = [random.randint(0, len(self.equipped_charms) - 1)]  # Disable one
            elif self.current_boss_effect['name'] == 'Charm Eclipse':
                self.disabled_charms = list(range(len(self.equipped_charms)))  # Disable all
            elif self.current_boss_effect['name'] == 'Rainbow Restriction':
                self.boss_rainbow_color = random.choice(BASE_COLORS)
            elif self.current_boss_effect['name'] == 'Face Shuffle':
                for die in self.full_bag:
                    faces = DICE_FACES[:]
                    random.shuffle(faces)  # Simple shuffle; could add duplicates/missing for more chaos
                    self.boss_shuffled_faces[die['id']] = faces
            elif self.current_boss_effect['name'] == 'Charm Tax':
                tax = len(self.equipped_charms) // 2  # 0.5 per, rounded down
                self.hands_left = max(0, self.hands_left - tax)
            elif self.current_boss_effect['name'] == 'Hand Trim':
                self.hands_left = max(0, self.hands_left - 1)
            elif self.current_boss_effect['name'] == 'Reroll Ration':
                self.rerolls_left = max(0, self.rerolls_left - 1)  # Consider moving to new_turn if per-hand
            elif self.current_boss_effect['name'] == 'Discard Drought':
                self.discards_left = max(0, self.discards_left - 1)
            elif self.current_boss_effect['name'] == 'Blind Boost':
                self.discards_left += 1  # Compensation
            # Note: Other effects applied in specific methods below

        self.round_score = 0
        self.hands_left = MAX_HANDS
        self.discards_left = MAX_DISCARDS
        self.extra_coins = 0
        self.turn_initialized = False  # Reset for new round/turn
        self.bag[:] = [copy.deepcopy(d) for d in self.full_bag]  # Refill bag from owned template
        if self.current_boss_effect and self.current_boss_effect['name'] == 'Charm Eclipse':
            self.disabled_charms = list(range(len(self.equipped_charms)))  # Ensure all current charms disabled
        
        # Handle Dagger charm
        i = 0
        while i < len(self.equipped_charms) - 1:
            if self.equipped_charms[i]['type'] == 'sacrifice_mult':
                if self.score_mult >= MAX_DAGGER_MULT:
                    i += 1  # Skip if already at max (no gain, no consume)
                    continue
                # Calculate potential add (before consume)
                next_charm = self.equipped_charms[i + 1]
                add_mult = next_charm['cost'] * DAGGER_MULT_PER_COST
                if add_mult <= 0:
                    i += 1  # Skip if no gain (edge case)
                    continue
                # Consume and apply if gain possible
                sacrificed = self.equipped_charms.pop(i + 1)
                self.score_mult += add_mult
                self.score_mult = min(self.score_mult, MAX_DAGGER_MULT)  # Cap after add
            else:
                i += 1

    def new_turn(self):
        """Starts a new turn: draw hand, set to value 1, reset holds and rerolls."""
        #  print("DEBUG: Calling new_turn - pulling dice")  # Log to see when triggered
        self.hand = self.draw_hand()
        self.turn_initialized = True
        self.rolls = [(die, 1) for die in self.hand]  # Start with value 1 (single pip)
        self.held = [False] * NUM_DICE_IN_HAND
        self.discard_selected = [False] * NUM_DICE_IN_HAND
        self.rerolls_left = MAX_REROLLS if not DEBUG else -1  # Reset to unlimited in debug
        self.rerolls_left_initial = self.rerolls_left
        self.confirmed_hands_this_round = 0
        self.lucky_triggers = 0  # Reset to 0 each new turn/hand
        self.turn += 1
        self.discard_used_this_round = False  # Reset per hand
        self.is_discard_phase = True  # Reset to discard phase
        self.has_rolled = False  # No initial roll yet
        self.update_hand_text()  # Update initial hand text
        # In new_turn():
        if not game.turn_initialized:
            # ... (existing turn setup)
            game.apply_boss_face_shuffle()
            game.turn_initialized = True
        # Add after setting self.rerolls_left, etc.
        if self.current_blind == 'Boss' and self.current_boss_effect:
            effect_name = self.current_boss_effect['name']
            if effect_name == 'Reroll Ration':
                self.rerolls_left = max(0, self.rerolls_left - 1)
            if effect_name == 'Discard Delay':
                self.is_discard_phase = False  # Skip initial discard; enable after first reroll
            # Reset per-turn trackers if needed
            self.boss_reroll_count = 0

    def roll_hand(self):
        """Rolls each die in the hand, returning list of (die, value)."""
        return [(die, random.choice(die['faces'])) for die in self.hand]

    def reroll(self):
        """Rerolls non-held dice with animation if rerolls left, else scores and new turn."""
        if self.is_discard_phase:
            return  # Can't reroll during discard phase
        if self.rerolls_left > 0 or DEBUG:  # Always allow reroll in debug
            if self.current_blind == 'Boss' and self.current_boss_effect:
                effect_name = self.current_boss_effect['name']
                if effect_name == 'Reroll Penalty' and self.coins > 0:
                    self.coins -= 1
                elif effect_name == 'Reroll Rebound':
                    held_indices = [i for i in range(len(self.held)) if self.held[i]]
                    if held_indices:
                        unhold_i = random.choice(held_indices)
                        self.held[unhold_i] = False
                elif effect_name == 'Die Drain':
                    # Remove one random die and replace with a new draw if bag has dice
                    if len(self.rolls) > 1:  # Use self.rolls for check (active hand)
                        drain_i = random.randint(0, len(self.rolls) - 1)
                        drained_die = self.rolls[drain_i][0]  # Get die to return to bag
                        del self.rolls[drain_i]
                        del self.held[drain_i]
                        del self.discard_selected[drain_i]  # Sync discard

                        # Replace with new draw if bag not empty
                        if self.bag:
                            new_die = random.choice(self.bag)
                            self.bag.remove(new_die)
                            new_value = random.choice(new_die['faces'])
                            self.rolls.append((new_die, new_value))
                            self.held.append(False)  # New not held
                            self.discard_selected.append(False)  # Sync

                        # Return drained die to bag (optional for balance)
                        self.bag.append(drained_die)
                elif effect_name == 'Hold Ban':
                    if any(self.held):  # Check if any held
                        self.temp_message = "Hold Ban: Cannot hold for reroll - unhold all to proceed"
                        self.temp_message_start = time.time()
                        return  # Skip reroll, no auto-unhold/reroll
                elif effect_name == 'Hold Limit':
                    held_count = sum(self.held)
                    if held_count > 3:
                        self.temp_message = "Hold Limit: Max 3 holds for reroll - unhold some to proceed"
                        self.temp_message_start = time.time()
                        return  # Skip reroll, no auto-unhold
                elif effect_name == 'Hold Hazard':
                    for i in range(len(self.held)):
                        if self.held[i] and random.random() < 0.20:
                            self.held[i] = False  # Force reroll
                
            # Animate cycling for non-held dice
            # Play roll sound here (at start of reroll)
            self.sfx_channel.play(self.roll_sound)
            for frame in range(ANIMATION_FRAMES):
                for i in range(len(self.rolls)):
                    if not self.held[i]:
                        die_temp = self.rolls[i][0]  # Temp var for the die
                        faces = self.boss_shuffled_faces.get(die_temp['id'], die_temp['faces']) if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Face Shuffle' else die_temp['faces']
                        self.rolls[i] = (die_temp, random.choice(faces))
                self.screen.fill(THEME['background'])  # Clear screen
                screens.draw_game_screen(self)
                pygame.display.flip()  # Update screen during animation
                time.sleep(ANIMATION_DELAY)
            
            # Final actual roll (the last frame is the real one)
            for i in range(len(self.rolls)):
                if not self.held[i]:
                    die = self.rolls[i][0]
                    faces = self.boss_shuffled_faces.get(die['id'], die['faces']) if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Face Shuffle' else die['faces']
                    self.rolls[i] = (die, random.choice(faces))
            
            if not DEBUG:
                self.rerolls_left -= 1
            self.update_hand_text()  # Update after reroll
            self.boss_reroll_count += 1  # Track for Break Surge
        else:
            # Score and advance hand or end round
            score = self.calculate_score()
            self.round_score += score
            # Accumulate extra coins from Gold/Silver
            for i, (die, _) in enumerate(self.rolls):
                if die['color'] == 'Gold' and self.held[i]:
                    self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                    self.extra_coins += 1
                elif die['color'] == 'Silver' and not self.held[i]:
                    self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                    self.extra_coins += 1
            # Add extra coin bonuses from charms
            for charm in self.equipped_charms:
                if charm['type'] == 'extra_coin_bonus':
                    for j, (die, _) in enumerate(self.rolls):
                        if die['color'] == charm['color']:
                            if (charm['color'] == 'Gold' and self.held[j]) or (charm['color'] == 'Silver' and not self.held[j]):
                                self.extra_coins += charm['value']
            # Compute dynamic Glass break chance and penalty from charms
            # For Fragile Flip / Break Surge in glass break check (in reroll):
            glass_break_chance = 0.25
            if self.current_blind == 'Boss' and self.current_boss_effect:
                effect_name = self.current_boss_effect['name']
                if effect_name == 'Fragile Flip':
                    glass_break_chance = 0.50
                elif effect_name == 'Break Surge':
                    glass_break_chance += 0.10 * self.boss_reroll_count
                if effect_name == 'Special Silence':
                    glass_break_chance = 0  # No breaks if specials silenced
            glass_break_penalty = 0
            for charm in self.equipped_charms:
                if charm['type'] == 'glass_mod':
                    glass_break_chance = charm['break_chance']
                    glass_break_penalty = charm['break_penalty']

            # Check for Mime Charm (add here)
            has_mime = any(c['type'] == 'retrigger_held' for c in self.equipped_charms)

            # Handle Glass break chance (only for held Glass)
            for i, (die, _) in enumerate(self.rolls):
                if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                    # Break: Remove from full_bag and bag
                    self.break_sound = pygame.mixer.Sound(resource_path('assets/audio/break.wav'))
                    self.break_sound.set_volume(0.7)  # Louder for impact
                    self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                    self.bag = [d for d in self.bag if d['id'] != die['id']]
                    self.coins -= glass_break_penalty
                    self.broken_dice.append(i)  # Add index for animation
                    self.break_effect_start = time.time()  # Start timer
            
            # Retrigger if Mime (add here)
            if has_mime:
                # Retrigger coins for held special dice (Gold only; skip Silver)
                for i, (die, _) in enumerate(self.rolls):
                    if self.held[i]:  # Only retrigger held
                        if die['color'] == 'Gold':
                            self.extra_coins += 1
                # Retrigger Glass mult (re-apply x4 per held Glass to score)
                glass_count = sum(1 for i, (die, _) in enumerate(self.rolls) if die['color'] == 'Glass' and self.held[i])
                score *= (4 ** glass_count)  # Doubles the original mult

                # Retrigger Glass break for held
                for i, (die, _) in enumerate(self.rolls):
                    if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                        # Break again
                        self.break_sound = pygame.mixer.Sound(resource_path('assets/audio/break.wav'))
                        self.break_sound.set_volume(0.7)  # Louder for impact
                        self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                        self.bag = [d for d in self.bag if d['id'] != die['id']]
                        self.coins -= glass_break_penalty
                        self.broken_dice.append(i)  # Add index for animation
                        self.break_effect_start = time.time()  # Start timer

            self.hands_left -= 1
            if self.round_score >= self.get_blind_target():
                # Compute dynamic interest max from charms (existing)
                dynamic_interest_max = INTEREST_MAX
                for charm in self.equipped_charms:
                    if charm['type'] == 'interest_max_bonus':
                        dynamic_interest_max += charm['value']
                
                if self.green_pouch_active:
                    remains_coins = (self.hands_left * 2) + (self.discards_left * 1)
                    interest = 0  # No interest for Green Pouch, like Balatro
                    hands_dollars = '$$' * self.hands_left  # Visual for *2
                    discards_dollars = '$' * self.discards_left  # Visual for *1
                    interest_dollars = ''  # No interest
                else:
                    remains_coins = self.hands_left + self.discards_left if not DEBUG else 0
                    interest = min(self.coins, dynamic_interest_max) // INTEREST_RATE
                    hands_dollars = '$' * self.hands_left
                    discards_dollars = '$' * self.discards_left
                    interest_dollars = '$' * interest if interest >= 0 else str(interest)
                
                total_coins = remains_coins + interest + self.extra_coins
                extras_dollars = '$' * self.extra_coins if self.extra_coins > 0 else ''
                total_dollars = '$' * abs(total_coins) if total_coins >= 0 else str(total_coins)
                extras_line = f"Extras: {extras_dollars}\n" if self.extra_coins > 0 else ""
                self.popup_message = (f"{self.current_blind} Blind Beaten! Score: {self.round_score}/{int(self.get_blind_target())}\n"
                                    f"Hands left: {hands_dollars}\n"
                                    f"Discards Left: {discards_dollars}\n"
                                    f"Interest: {interest_dollars}\n"
                                    f"{extras_line}"
                                    f"Coins gained: {total_dollars}")
                self.coins += total_coins
                self.show_popup = True
            elif self.hands_left > 0:
                self.new_turn()  # Next hand in round
            else:
                # Game over
                self.game_state = 'game_over'

    def discard(self):
        """Discards selected dice and draws new ones from bag, replacing in same positions with value 1."""
        if self.discards_left <= 0 or not self.is_discard_phase:
            return
        selected_indices = [i for i in range(NUM_DICE_IN_HAND) if self.discard_selected[i]]
        selected_count = len(selected_indices)
        if selected_count >= 1:
            # In discard():
            if self.current_blind == 'Boss' and self.current_boss_effect:
                effect_name = self.current_boss_effect['name']
                if effect_name == 'Discard Cap':
                    selected_count = sum(self.discard_selected)
                    if selected_count > 2:
                        self.temp_message = "Discard Cap: Max 2 dice per discard - deselect some to proceed"
                        self.temp_message_start = time.time()
                        return  # Skip discard
            # Then normal
            # Draw new dice
            new_dice = self.draw_hand(selected_count)
            # Replace at the selected positions with value 1 (single pip)
            for idx, new_die in zip(selected_indices, new_dice):
                self.hand[idx] = new_die
                self.rolls[idx] = (new_die, 1)  # Set to 1 for single pip
            self.held = [False] * NUM_DICE_IN_HAND
            self.discard_selected = [False] * NUM_DICE_IN_HAND
            self.discards_left -= 1
            self.discard_used_this_round = True
            # New: Grant extra reroll if Recycler equipped and discard used
            recycler_count = sum(1 for c in self.equipped_charms if c['type'] == 'reroll_recycler')
            if recycler_count > 0:
                self.rerolls_left += recycler_count  # +1 per charm
            self.update_hand_text()

    def toggle_discard(self, index):
        """Toggles discard selection for a die, only in discard phase."""
        if self.is_discard_phase:
            self.discard_selected[index] = not self.discard_selected[index]

    def start_roll_phase(self):
        """Exits discard phase, rolls the hand with animation, and enters roll phase."""
        if self.show_popup:
            return  # Block actions during popup
        self.is_discard_phase = False
        self.has_rolled = True
        # In start_roll_phase():
        if self.current_blind == 'Boss' and self.current_boss_effect['name'] == 'Discard Delay':
            self.is_discard_phase = True  # Enable after first roll? Wait, start_roll exits discard, so for delay, perhaps flag to skip initial but allow post-first.
        # Note: For Discard Delay, in new_turn set is_discard_phase=False, then here after first roll (has_rolled=True), set to True if not used yet? Needs tweak.
        # Play sound at animation start
        self.sfx_channel.play(self.roll_sound)
        # Animate rolling for all dice
        for frame in range(ANIMATION_FRAMES):
            self.rolls = [(die, random.choice(die['faces'])) for die in self.hand]
            self.screen.fill(THEME['background'])  # Clear screen
            screens.draw_game_screen(self)
            pygame.display.flip()  # Update screen during animation
            time.sleep(ANIMATION_DELAY)
        # Final roll
        self.apply_boss_face_shuffle()  # Ensure shuffle before rolling
        self.rolls = self.roll_hand()
        self.discard_selected = [False] * NUM_DICE_IN_HAND  # Clear selections
        self.update_hand_text()

    def score_and_new_turn(self):
        """Manually scores and starts a new turn."""
        hand_type, base_score, modifier_desc, final_score, charm_chips, charm_mono_add = self.get_hand_type_and_score(is_preview=False)
        if self.show_popup:
            return  # Block actions during popup
        
        # Apply Hiker Hex per-die bonus if equipped and not disabled
        held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
        for idx, charm in enumerate(self.equipped_charms):
            if charm['type'] == 'die_bonus_perm' and idx not in self.disabled_charms:
                print("Hiker Hex: Applying +4 to", len(held_rolls), "dice")
                for die, _ in held_rolls:
                    die_id = die.get('id')
                    if die_id is None:
                        print("Warning: Die missing 'id'")  # If no 'id', add unique IDs to all dice in init
                    for bag_die in self.full_bag:
                        if bag_die.get('id') == die_id:
                            current_bonus = bag_die.get('score_bonus', 0)
                            bag_die['score_bonus'] = current_bonus + charm['value']
                            print(f"Updated bag die {die_id}: now {bag_die['score_bonus']}")
                            break  # No need to loop further
                break

        # score = self.calculate_score() # Old: Calculate score again
        score = final_score  # Use pre-calculated final score
        print("Computed score:", score, "(base:", base_score, "chips:", charm_chips, "modifier:", 1 + charm_mono_add)  # Add this debug to see components
        self.round_score += score

        # Apply Square Sphere permanent bonus on charm if equipped, not disabled, and exactly 4 dice scored
        for idx, charm in enumerate(self.equipped_charms):
            if charm['name'] == 'Square Sphere' and idx not in self.disabled_charms:
                if len(held_rolls) == 4:
                    charm['permanent_bonus'] = charm.get('permanent_bonus', 0) + charm['value']
                    print("Square Sphere charm bonus applied (4 dice): now", charm['permanent_bonus'])  # Debug
                break

        for idx, charm in enumerate(self.equipped_charms):
            if charm['type'] == 'score_conditional' and idx not in self.disabled_charms:
                self.permanent_score_bonus = getattr(self, 'permanent_score_bonus', 0) + charm['value']
                print("Square Sphere permanent bonus applied: now", self.permanent_score_bonus)  # Debug, remove later
                break

        # Apply Lucky Labyrinth permanent bonus on charm if equipped and triggers >0
        for idx, charm in enumerate(self.equipped_charms):
            if charm['name'] == 'Lucky Labyrinth' and idx not in self.disabled_charms:
                triggers = self.lucky_triggers
                if triggers > 0:
                    charm['permanent_bonus'] = charm.get('permanent_bonus', 0.0) + (charm['value'] * triggers)
                    print("Lucky Labyrinth permanent bonus applied:", charm['permanent_bonus'])  # Debug, remove later
                break

        for _ in range(self.lucky_triggers):
            self.sfx_channel.play(self.coin_sound)  # Play per coin

        # Track hand play counts and streak
        if hand_type != "Nothing":
            previous_most_played = self.most_played_hand  # ADDED: Track previous to avoid immediate reset on change
            self.hand_play_counts[hand_type] += 1
            self.most_played_hand = max(self.hand_play_counts, key=self.hand_play_counts.get) if any(self.hand_play_counts.values()) else None
            if previous_most_played and hand_type != previous_most_played:
                self.avoid_streak += 1
            else:
                self.avoid_streak = 0

        # Accumulate extra coins from Gold/Silver
        for i, (die, _) in enumerate(self.rolls):
            if die['color'] == 'Gold' and self.held[i]:
                self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                self.extra_coins += 1
            elif die['color'] == 'Silver' and not self.held[i]:
                self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                self.extra_coins += 1
        # Add extra coin bonuses from charms
        for charm in self.equipped_charms:
            if charm['type'] == 'extra_coin_bonus':
                for j, (die, _) in enumerate(self.rolls):
                    if die['color'] == charm['color']:
                        if (charm['color'] == 'Gold' and self.held[j]) or (charm['color'] == 'Silver' and not self.held[j]):
                            self.extra_coins += charm['value']

        # Compute dynamic Glass break chance and penalty from charms
        glass_break_chance = 0.25
        glass_break_penalty = 0
        for charm in self.equipped_charms:
            if charm['type'] == 'glass_mod':
                glass_break_chance = charm['break_chance']
                glass_break_penalty = charm['break_penalty']

        # Handle Glass break chance (only for held Glass)
        for i, (die, _) in enumerate(self.rolls):
            if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                self.sfx_channel.play(self.break_sound)
                self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                self.bag = [d for d in self.bag if d['id'] != die['id']]
                self.coins -= glass_break_penalty
                self.broken_dice.append(i)
                self.break_effect_start = time.time()

        # Add Mime here
        has_mime = any(c['type'] == 'retrigger_held' for c in self.equipped_charms)

        if has_mime:
            for i, (die, _) in enumerate(self.rolls):
                if self.held[i]:
                    if die['color'] == 'Gold':
                        self.extra_coins += 1

            glass_count = sum(1 for i, (die, _) in enumerate(self.rolls) if die['color'] == 'Glass' and self.held[i])
            score *= (4 ** glass_count)

            for i, (die, _) in enumerate(self.rolls):
                if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                    self.sfx_channel.play(self.break_sound)
                    self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                    self.bag = [d for d in self.bag if d['id'] != die['id']]
                    self.coins -= glass_break_penalty
                    self.broken_dice.append(i)
                    self.break_effect_start = time.time()

        if self.round_score >= self.get_blind_target():
            self.stake_milestones = getattr(self, 'stake_milestones', 0) + 1  # Increment on blind win

        self.hands_left -= 1
        self.hands_left = max(0, self.hands_left)  # Clamp to prevent negative
        if self.round_score >= self.get_blind_target():
            # Compute dynamic interest max from charms
            dynamic_interest_max = INTEREST_MAX
            for charm in self.equipped_charms:
                if charm['type'] == 'interest_max_bonus':
                    dynamic_interest_max += charm['value']
            
            if self.green_pouch_active:
                remains_coins = (self.hands_left * 2) + (self.discards_left * 1)
                interest = 0
                hands_dollars = '$$' * self.hands_left
                discards_dollars = '$' * self.discards_left
                interest_dollars = ''
            else:
                remains_coins = self.hands_left + self.discards_left
                interest = min(self.coins, dynamic_interest_max) // INTEREST_RATE
                hands_dollars = '$' * self.hands_left
                discards_dollars = '$' * self.discards_left
                interest_dollars = '$' * interest if interest >= 0 else str(interest)
            
            # Track Luck's Locket coins explicitly from this hand
            luck_locket_coins = 0
            for charm in self.equipped_charms:
                if charm['name'] == "Luck's Locket" and self.lucky_triggers > 0:
                    luck_locket_coins += charm['value'] * self.lucky_triggers
            
            # Track base lucky coins ( +1 per trigger, already added in get_hand_type_and_score)
            base_lucky_coins = self.lucky_triggers * 1  # Base +1 per
            
            # Total coins including Luck's Locket effect
            total_coins = remains_coins + interest + self.extra_coins + luck_locket_coins + base_lucky_coins
            
            # Visual representations
            luck_locket_dollars = '$$' * luck_locket_coins if luck_locket_coins > 0 else ''
            luck_locket_line = f"Luck Bonus: {luck_locket_dollars}\n" if luck_locket_coins > 0 else ""
            
            base_lucky_dollars = '$' * base_lucky_coins if base_lucky_coins > 0 else ''
            base_lucky_line = f"Lucky Coins: {base_lucky_dollars}\n" if base_lucky_coins > 0 else ""
            
            extras_dollars = '$' * self.extra_coins if self.extra_coins > 0 else ''
            extras_line = f"Extras: {extras_dollars}\n" if self.extra_coins > 0 else ""
            total_dollars = '$' * abs(total_coins) if total_coins >= 0 else str(total_coins)
            
            self.popup_message = (f"{self.current_blind} Blind Beaten! Score: {self.round_score}/{int(self.get_blind_target())}\n"
                                f"Hands left: {hands_dollars}\n"
                                f"Discards Left: {discards_dollars}\n"
                                f"Interest: {interest_dollars}\n"
                                f"{extras_line}"
                                f"{luck_locket_line}"  # Luck's Locket
                                f"{base_lucky_line}"  # Base 'Lucky'
                                f"Coins gained: {total_dollars}")
            
            self.coins += total_coins
            self.coins = max(0, self.coins)  # Clamp to prevent negative coins from penalties
            self.show_popup = True
        elif self.hands_left > 0:
            self.new_turn()  # Next hand in round
        else:
            # Game over - transition to state
            self.state_machine.change_state(GameOverState(self))

    def toggle_hold(self, index):
        """Toggles hold state for a die."""
        # In toggle_hold(index):
        if self.current_blind == 'Boss' and self.current_boss_effect:
            effect_name = self.current_boss_effect['name']
            if effect_name == 'Glass Guard':
                die = self.hand[index]
                if die['color'] == 'Glass':
                    return  # Cannot hold Glass
        # Then normal toggle
        if self.show_popup:
            return  # Block actions during popup
        self.held[index] = not self.held[index]
        self.update_hand_text()

    def get_hand_type_and_score(self, is_preview=True):
        """Determines the hand type, base score, modifier, and final score.
        is_preview: If True, compute without side effects (for UI previews).
        """
        
        held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
        if not held_rolls:
            return "Nothing", 0, "None", 0, 0, 0.0
        values = [value for die, value in held_rolls]
        colors_list = [die['color'] for die, value in held_rolls]
        sorted_values = sorted(values)
        counts = {i: values.count(i) for i in set(values)}
        max_count = max(counts.values()) if counts else 0
        pair_count = list(counts.values()).count(2)

        # Group dice by value for color checks: {value: [colors]}
        groups = {}
        for (die, val) in held_rolls:
            if val not in groups:
                groups[val] = []
            groups[val].append(die['color'])

        hand_type = "Nothing"
        base_score = 0
        base_modifier = 0.0
        modifier_desc = []  # List to collect descriptions, join later

        straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
        short_straights_small = [[1,2,3], [2,3,4], [3,4,5], [4,5,6]]
        short_straights_large = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]

        has_four_fingers = any(c['type'] == 'short_straight' for c in self.equipped_charms if self.equipped_charms.index(c) not in self.disabled_charms)

        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Value Vault':
            values = [7 - v for v in values]
            sorted_values = sorted(values)

        # Collect wild faces with safety check
        wild_faces = set()
        for charm in self.equipped_charms:
            if charm['type'] in ('face_wild', 'kind_wild') and 'face' in charm:
                wild_faces.add(charm['face'])
            elif charm['type'] in ('face_wild', 'kind_wild'):
                pass  # No print to avoid spam

        # Adjust counts/max_count for wilds
        wild_count = sum(1 for v in values if v in wild_faces)
        wild_colors = [colors_list[i] for i, v in enumerate(values) if v in wild_faces]  # Ensure flat list of strings
        if wild_count > 0:
            non_wild_counts = {k: v for k, v in counts.items() if k not in wild_faces}
            if non_wild_counts:
                max_non_wild_key = max(non_wild_counts, key=lambda k: (non_wild_counts[k], k))
                counts[max_non_wild_key] += wild_count
                max_count = max(counts.values())
                # Update groups to reflect wilds for color checks
                groups[max_non_wild_key] = groups.get(max_non_wild_key, []) + wild_colors[:wild_count]
                for wild_face in wild_faces:
                    if wild_face in groups and wild_face != max_non_wild_key:
                        groups[wild_face] = [c for c in groups[wild_face] if c not in wild_colors[:wild_count]]
                        if not groups[wild_face]:
                            del groups[wild_face]
            pair_count = list(counts.values()).count(2)

        if max_count == 5:
            hand_type = "5 of a Kind"
            base_score = 250
            actual_colors = [c for c in colors_list if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier += 3.0
                modifier_desc.append("Monochrome +3")
            elif len(actual_colors) == len(actual_set):
                base_modifier += 2.0
                modifier_desc.append("Rainbow +2")
        elif max_count == 4:
            hand_type = "4 of a Kind"
            base_score = 160
            for val, group_colors in groups.items():
                if counts.get(val, 0) == 4:
                    actual_colors = [c for c in group_colors if c != 'Rainbow']
                    actual_set = set(actual_colors)
                    if len(actual_set) <= 1:
                        base_modifier += 2.0
                        modifier_desc.append("Monochrome +2")
                    elif len(actual_colors) == len(actual_set):
                        base_modifier += 1.0
                        modifier_desc.append("Rainbow +1")
                    break
        elif max_count == 3 and 2 in counts.values():
            hand_type = "Full House"
            base_score = 160
            three_val = next((val for val, count in counts.items() if count == 3), None)
            pair_val = next((val for val, count in counts.items() if count == 2), None)
            three_group = groups.get(three_val, [])
            pair_group = groups.get(pair_val, [])
            actual_colors = [c for c in colors_list if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier += 3.0
                modifier_desc.append("Full Mono +3")
            elif len(actual_colors) == len(actual_set):
                base_modifier += 2.0
                modifier_desc.append("Rainbow +2")
            else:
                mono_three = len(set(c for c in three_group if c != 'Rainbow')) <= 1 if three_group else False
                mono_pair = len(set(c for c in pair_group if c != 'Rainbow')) <= 1 if pair_group else False
                if mono_three and mono_pair:
                    base_modifier += 1.0
                    modifier_desc.append("Both Mono +1")
                elif mono_three or mono_pair:
                    base_modifier += 0.5
                    modifier_desc.append("One Mono +0.5")
        elif sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large)):
            hand_type = "Large Straight"
            base_score = 160
            straight_len = 5
            straight_colors = colors_list
            straight_values = sorted_values if not has_four_fingers else next(s for s in short_straights_large if all(x in values for x in s)) or sorted_values
            straight_len = len(straight_values)
            straight_colors = []
            for v in straight_values:
                straight_colors += groups.get(v, [])
            actual_colors = [c for c in straight_colors if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier += 1.0
                modifier_desc.append("Monochrome +1")
            elif len(actual_colors) == len(actual_set):
                base_modifier += 1.0
                modifier_desc.append("Rainbow +1")
        elif any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small)):
            hand_type = "Small Straight"
            base_score = 90
            straight_len = 4
            straight_colors = colors_list
            straight_values = next(s for s in straights if all(x in values for x in s)) if not has_four_fingers else next(s for s in short_straights_small if all(x in values for x in s)) or sorted_values
            straight_len = len(straight_values)
            straight_colors = []
            for v in straight_values:
                straight_colors += groups.get(v, [])
            actual_colors = [c for c in straight_colors if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier += 1.0
                modifier_desc.append("Monochrome +1")
            elif len(actual_colors) == len(actual_set):
                base_modifier += 1.0
                modifier_desc.append("Rainbow +1")
        elif max_count == 3:
            hand_type = "3 of a Kind"
            base_score = 80
            for val, group_colors in groups.items():
                if counts.get(val, 0) == 3:
                    actual_colors = [c for c in group_colors if c != 'Rainbow']
                    actual_set = set(actual_colors)
                    if len(actual_set) <= 1:
                        base_modifier += 1.0
                        modifier_desc.append("Monochrome +1")
                    elif len(actual_colors) == len(actual_set):
                        base_modifier += 0.5
                        modifier_desc.append("Rainbow +0.5")
                    break
        elif pair_count == 2:
            hand_type = "2 Pair"
            base_score = 60
            mono_pairs = 0
            for group_colors in groups.values():
                if len(group_colors) == 2:
                    actual_set = set(c for c in group_colors if c != 'Rainbow')
                    if len(actual_set) <= 1:
                        mono_pairs += 1
            if mono_pairs == 1:
                base_modifier += 0.5
                modifier_desc.append("One Mono Pair +0.5")
            elif mono_pairs == 2:
                base_modifier += 1.0
                modifier_desc.append("Two Mono Pairs +1")
        elif pair_count == 1:
            hand_type = "Pair"
            base_score = 20
            for val, group_colors in groups.items():
                if counts.get(val, 0) == 2:
                    actual_colors = [c for c in group_colors if c != 'Rainbow']
                    actual_set = set(actual_colors)
                    if len(actual_set) <= 1:
                        base_modifier += 0.5
                        modifier_desc.append("Monochrome +0.5")
                    break

        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Rainbow Restriction':
            colors_list = [self.boss_rainbow_color if c == 'Rainbow' else c for c in colors_list]
            unique_colors = set(colors_list)

        if self.current_blind == 'Boss' and self.current_boss_effect:
            effect_name = self.current_boss_effect['name']
            if effect_name == 'Score Dip':
                base_score = int(base_score * 0.9)
            if effect_name == 'Color Fade':
                base_modifier = 0.0
                modifier_desc = ["None"]
            if effect_name == 'Mono Mixup' and len(set(colors_list)) > 1:
                base_modifier -= 0.5

        rune_chips = 0
        rune_mult_add = 0.0
        rune_break_dies = []
        self.lucky_triggers = 0
        for die, value in held_rolls:
            enh = die.get('enhancements', [])
            if 'Bonus' in enh:
                rune_chips += 10
            if 'Mult' in enh:
                rune_mult_add += 0.5
            if 'Lucky' in enh and not is_preview and random.random() < 0.33:
                self.lucky_triggers += 1
                self.coins += 1  # +1 coin
            if 'Steel' in enh:
                rune_mult_add += 0.5
            if 'Fragile' in enh:
                rune_mult_add += 1.0
                if not is_preview and random.random() < 0.25:
                    rune_break_dies.append(die)
            if 'Stone' in enh:
                rune_chips += 50

        for die in rune_break_dies:
            self.broken_dice.append(held_rolls.index((die, value)))

        charm_chips = 0
        charm_color_mult_add = 0.0
        charm_mult_add = 0.0
        is_mono = any("Mono" in d for d in modifier_desc)
        is_rainbow = any("Rainbow" in d for d in modifier_desc)
        num_dice_used = len(held_rolls)
        is_small_straight = any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small))
        is_large_straight = sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large))
        self.confirmed_hands_this_round = getattr(self, 'confirmed_hands_this_round', 0)  # Ensure initialized
        for idx, charm in enumerate(self.equipped_charms):
            if idx in self.disabled_charms:
                continue
            if charm['type'] == 'flat_bonus':
                charm_chips += charm['value']
            elif charm['type'] == 'per_color_bonus':
                charm_chips += colors_list.count(charm['color']) * charm['value']
            elif charm['type'] == 'hand_bonus':
                for h in charm['hands']:
                    if h == 'Pair' and max_count >= 2:
                        charm_chips += charm['value']
                    elif h == '2 Pair' and pair_count >= 2:
                        charm_chips += charm['value']
                    elif h == '3 of a Kind' and max_count >= 3:
                        charm_chips += charm['value']
                    elif h == '4 of a Kind' and max_count >= 4:
                        charm_chips += charm['value']
                    elif h == '5 of a Kind' and max_count == 5:
                        charm_chips += charm['value']
                    elif h == 'Full House' and max_count == 3 and 2 in counts.values():
                        charm_chips += charm['value']
                    elif h == 'Small Straight' and is_small_straight:
                        charm_chips += charm['value']
                    elif h == 'Large Straight' and is_large_straight:
                        charm_chips += charm['value']
            elif charm['type'] == 'mono_mult_bonus':
                if is_mono:
                    charm_color_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']}")
            elif charm['type'] == 'few_dice_bonus':
                if num_dice_used <= charm['max_dice']:
                    charm_chips += charm['value']
            elif charm['type'] == 'empty_slot_mult':
                empty_slots = self.max_charms - len(self.equipped_charms)
                mult_add = charm['value'] * empty_slots
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add}")
            elif charm['type'] == 'per_value_bonus':
                count = 0
                for _, value in held_rolls:
                    if (charm['parity'] == 'even' and value % 2 == 0) or (charm['parity'] == 'odd' and value % 2 != 0):
                        count += 1
                    charm_chips += count * charm['value']
            elif charm['type'] == 'rainbow_mult_bonus':
                if is_rainbow:
                    charm_color_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']}")
            elif charm['type'] == 'sacrifice_mult':
                mult_add = self.score_mult
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add}")
            elif charm['type'] == 'mult_bonus':
                if 'hands' in charm:
                    if hand_type in charm['hands']:
                        mult_add = charm['value'] - 1
                        charm_mult_add += mult_add
                        modifier_desc.append(f"{charm['name']} +{mult_add}")
                else:
                    mult_add = charm['value'] - 1
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add}")
            elif charm['type'] == 'color_mult':
                count = sum(1 for die, _ in held_rolls if die['color'] == charm['color'])
                mult_add = count * charm['value']
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({count} {charm['color']})")
            elif charm['type'] == 'color_mult_conditional':
                if not hasattr(self, 'rerolls_left_initial') or self.rerolls_left != self.rerolls_left_initial:
                    continue
                count = sum(1 for die, _ in held_rolls if die['color'] == charm['color'])
                mult_add = count * charm['value']
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({count} {charm['color']})")
            elif charm['type'] == 'mult_conditional':
                if charm.get('mono', False):
                    if len(set(colors_list)) == 1:
                        mult_add = charm['value'] - 1
                        charm_mult_add += mult_add
                        modifier_desc.append(f"{charm['name']} +{mult_add}")
                if charm.get('glass', False):
                    glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass' or 'Glass' in die.get('enhancements', []))
                    if glass_count > 0:
                        mult_add = charm['value'] - 1
                        charm_mult_add += mult_add
                        modifier_desc.append(f"{charm['name']} +{mult_add}")
            elif charm['type'] == 'mult_per_face':
                count = sum(1 for _, v in held_rolls if v in charm['faces'])
                mult_add = charm['value'] * count
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({count} faces)")
            elif charm['type'] == 'bonus_per_charm':
                count = len([c for idx, c in enumerate(self.equipped_charms) if idx not in self.disabled_charms])
                mult_add = charm['mult'] * count
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({count} charms)")
                charm_chips += charm['score'] * count
            elif charm['type'] == 'mult_per_streak':
                mult_add = round(charm['value'] * self.avoid_streak, 1)
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({self.avoid_streak} streak)")
            elif charm['type'] == 'mult_per_low_bag':
                low_count = max(0, 25 - len(self.full_bag))
                mult_add = charm['value'] * low_count
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({low_count} below 25)")
            elif charm['type'] == 'mult_per_lucky':
                mult_add = charm.get('permanent_bonus', 0.0)  # EDIT: Only add permanent_bonus; no current lucky_triggers mult for this hand
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} (permanent)")  # EDIT: Always show as permanent
            elif charm['type'] == 'mult_per_milestone':
                mult_add = charm['value'] * getattr(self, 'stake_milestones', 0)
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({self.stake_milestones} milestones)")
            elif charm['type'] == 'advantage_choice':
            # Stub: Requires roll logic outside scoring (e.g., in roll phase)
            # For now, no in-score effect; handle in roll method
                pass
            elif charm['type'] == 'reroll_advantage':
                # Stub: Once per blind, allow advantage reroll; track in game state
                if not is_preview and not getattr(self, 'used_reroll_advantage', False):
                    # Logic would go in reroll method; here, no score effect
                    pass
            elif charm['type'] == 'rune_cast':
                # Stub: Cast random rune once per shop; needs state (e.g., self.rune_cast_used)
                if not is_preview and not getattr(self, 'rune_cast_used', False):
                    # Apply random rune effect (to be defined in rune system)
                    pass
            elif charm['type'] == 'coin_per_lucky':
                if not is_preview and self.lucky_triggers > 0:
                    coins_added = charm['value'] * self.lucky_triggers
                    self.coins += coins_added  # Add directly to coins
                    modifier_desc.append(f"{charm['name']} +{coins_added} coins ({self.lucky_triggers} lucky)")
            elif charm['type'] == 'random_rune':
                # Stub: Add random rune at blind start; no per-hand effect
                pass
            elif charm['type'] == 'interest_bonus':
                # Stub: Adds 1 coin per 10 coins at round end; handle in score_and_new_turn
                pass
            elif charm['type'] == 'retrigger_special':
                # Stub: Retrigger enhancements on special colors; needs color check
                if not is_preview:
                    special_colors = ['Gold', 'Silver', 'Glass', 'Rainbow']  # Define as needed
                    special_count = sum(1 for die, _ in held_rolls if die['color'] in special_colors)
                    if special_count > 0:
                        # Retrigger logic (e.g., double coin effects) to be defined
                        pass
            elif charm['type'] == 'mult_per_enhance':
                enhance_count = sum(1 for die, _ in held_rolls if die.get('enhancements'))
                mult_add = charm['value'] * enhance_count
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({enhance_count} enhancements)")
            elif charm['type'] == 'discard_mult':
                mult_add = charm['value'] * getattr(self, 'discards_used_this_round', 0)
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({self.discards_used_this_round} discards)")
            elif charm['type'] == 'coin_per_wild':
                wild_count = sum(1 for die, _ in held_rolls if die['color'] == 'Rainbow' and len(set([d['color'] for d, _ in held_rolls if d['color'] != 'Rainbow'])) <= 1)
                if not is_preview and wild_count > 0:
                    charm_chips += charm['value'] * wild_count
                    modifier_desc.append(f"{charm['name']} +{charm['value'] * wild_count} coins ({wild_count} wilds)")
            elif charm['type'] == 'final_mult_conditional':
                # Stub: +3 mult on last hand with enhancement; needs hand count check
                if not is_preview and getattr(self, 'is_last_hand', False) and any(die.get('enhancements') for die, _ in held_rolls):
                    charm_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']} (final)")
            elif charm['type'] == 'face_buy_high':
                # Stub: Pay 3 coins for +2 to a face; handle in event/turn logic
                pass
            elif charm['type'] == 'coin_per_discard':
                discards_left = getattr(self, 'discards_left', 0)
                if not is_preview and discards_left > 0:
                    charm_chips += charm['value'] * discards_left
                    modifier_desc.append(f"{charm['name']} +{charm['value'] * discards_left} coins ({discards_left} discards)")
            elif charm['type'] == 'risk_mult':
                # Stub: -1 to one die, +0.5 mult; handle die mod in roll phase
                if not is_preview:
                    charm_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']} (risk)")
            elif charm['type'] == 'loss_prevent':
                # Stub: Prevent loss once per game; handle in game over logic
                pass
            elif charm['type'] == 'rune_scribe':
                # Stub: Scribe rune on magic 3; handle in scoring or turn start
                if not is_preview and any(value == 3 for _, value in held_rolls):
                    # Logic to add to rune tray
                    pass
            elif charm['type'] == 'revive_die':
                # Stub: 50% chance to revive a die; handle in break or turn end
                pass
            elif charm['type'] == 'discard_destroy_coin':
                # Stub: Destroy 1 die for 3 coins on first discard; handle in discard phase
                pass
            elif charm['type'] == 'score_per_discard_color':
                # Stub: +3 per discarded color die; needs discard tracking
                pass
            elif charm['type'] == 'mult_final_discard':
                # Stub: +2 mult on final discard; needs discard count
                if not is_preview and getattr(self, 'is_final_discard', False):
                    charm_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']} (final discard)")
            elif charm['type'] == 'score_per_coin':
                charm_chips += charm['value'] * self.coins
            elif charm['type'] == 'score_bonus' and charm['value'] == 'stat_sum':
                # Sum the face values of all held dice
                face_sum = sum(value for _, value in held_rolls)
                charm_chips += face_sum  # Add to chips (base score additive)
                modifier_desc.append(f"{charm['name']} +{face_sum} (Sum of faces)")
            elif charm['type'] == 'score_decay':
                # Initialize hands_played on the charm if not present (per-charm counter)
                if 'hands_played' not in charm:
                    charm['hands_played'] = 0
                decay_bonus = max(0, charm['start'] - (charm['decay'] * charm['hands_played']))
                charm_chips += decay_bonus
            elif charm['type'] == 'score_conditional':
                if len(held_rolls) == charm['dice']:
                    charm_chips += charm['value']
                    charm_chips += charm.get('permanent_bonus', 0)
            elif charm['type'] == 'die_bonus_perm':
                # No calculation here; increment moved to score_and_new_turn to avoid previews
                pass

        # Sum per-die bonuses for scored dice
        for die, _ in held_rolls:
            bonus = die.get('score_bonus', 0)
            #  print(f"Die ID {die.get('id', 'no_id')} bonus: {bonus}")  # Debug: shows if/why 0
            charm_chips += die.get('score_bonus', 0)

        total_modifier = base_modifier + charm_color_mult_add + rune_mult_add + charm_mult_add

        if hand_type in self.hand_multipliers:
            mult_add = self.hand_multipliers[hand_type] - 1
            total_modifier += mult_add
            if mult_add > 0:
                modifier_desc.append(f"Prism Pack +{mult_add}")

        silence_glass = False
        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Special Silence':
            silence_glass = True

        glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass')
        glass_mult = (3 + glass_count) if glass_count > 0 and not silence_glass else 0
        if glass_mult > 0:
            total_modifier += glass_mult
            modifier_desc.append(f"Glass +{glass_mult}")

        has_mime = any(c['type'] == 'retrigger_held' for idx, c in enumerate(self.equipped_charms) if idx not in self.disabled_charms)
        if has_mime and not silence_glass and glass_count > 0:
            total_modifier += glass_mult
            modifier_desc.append(f"Mime (Glass) +{glass_mult}")

        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Multiplier Mute':
            total_modifier = min(total_modifier, 2.5)
            if total_modifier >= 2.5:
                modifier_desc.append("Multiplier Mute capped at +2.5")

        modifier_desc = ", ".join(modifier_desc) if modifier_desc else "None"

        final_score = int((base_score + charm_chips + rune_chips) * (1 + total_modifier))
        return hand_type, base_score, modifier_desc, final_score, charm_chips, charm_color_mult_add
    
    def calculate_score(self):
        """Calculates and returns the final score."""
        _, _, _, final_score, _, _ = self.get_hand_type_and_score()
        return final_score
    
    def update_hand_text(self):
        """Updates the texts showing current hand and modifier."""
        if self.is_discard_phase:
            # New: Show placeholders during discard phase
            self.current_hand_text = "Current Hand: Nothing (0 base) = 0 total"
            self.current_modifier_text = "Modifiers: None"
        else:
            held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
            if not held_rolls:
                # New: Explicit placeholders if no held
                self.current_hand_text = "Current Hand: Nothing (0 base) = 0 total"
                self.current_modifier_text = "Modifiers: None"
            else:
                hand_type, base_score, modifier_desc, final_score, charm_chips, charm_mono_add = self.get_hand_type_and_score()
                self.current_hand_text = f"Current Hand: {hand_type} ({base_score} base + {charm_chips} charms) = {final_score} total"

                # Build modifier parts  <-- Now indented under else
                modifier_parts = []
                if modifier_desc:
                    modifier_parts.append(modifier_desc)
                if charm_mono_add > 0:
                    modifier_parts.append(f"{charm_mono_add:.1f}x charms")
                stencil_mult = self.get_stencil_mult()
                if stencil_mult > 1.0:
                    modifier_parts.append(f"Stencil x{stencil_mult}")

                # Check if dagger charm is equipped and not disabled
                has_active_dagger = any(charm['type'] == 'sacrifice_mult' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))
                dagger_text = f"Dagger x{self.score_mult:.1f}"
                if self.score_mult > 1.0:
                    if has_active_dagger:
                        modifier_parts.append(dagger_text)
                    else:
                        modifier_parts.append(dagger_text + " (disabled)")

                

                # Call get_hand_type_and_score to get the updated hand info, including modifiers
                hand_type, base_score, modifier_desc, final_score, charm_chips, charm_mono_add = self.get_hand_type_and_score()

                # Update the hand text using the returned values
                self.current_hand_text = f"{hand_type} ({base_score} base + {charm_chips} charms) = {final_score} total"
                self.modifiers_text = f"Modifiers: {modifier_desc}"  # Assuming you have a separate text for modifiers

                # Add pack boost if >1.0
                hand_boost = self.hand_multipliers.get(hand_type, 1.0)
                if hand_boost > 1.0:
                    modifier_parts.append(f"{hand_type} {hand_boost:.1f}x")

                # Set modifier text with "Modifiers: " prefix and " + " joins
                if modifier_parts:
                    self.current_modifier_text = "Modifiers: " + " + ".join(modifier_parts)
                else:
                    self.current_modifier_text = ""
    
    def get_pause_button_rects(self):
        """Calculates and returns button rects for pause menu (no drawing)."""
        popup_x = (self.width - POPUP_WIDTH) // 2
        popup_y = (self.height - POPUP_HEIGHT) // 2
        button_spacing = 20
        button_y = popup_y + 80
        button_rects = []
        options = ["Return to Game", "Main Menu", "Quit"]
        for opt in options:
            button_rect = pygame.Rect(popup_x + (POPUP_WIDTH - BUTTON_WIDTH) // 2, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            button_rects.append((button_rect, opt))
            button_y += BUTTON_HEIGHT + button_spacing
        return button_rects

    def draw_dagger_icon(self, rect):
        """Draws a simple dagger icon inside the given rect."""
        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        blade_length = rect.height // 3
        handle_length = rect.height // 5
        width = rect.width // 6
        # Blade
        pygame.draw.polygon(self.screen, (192, 192, 192), [
            (center_x, center_y - blade_length),
            (center_x - width // 2, center_y),
            (center_x + width // 2, center_y)
        ])
        # Handle
        pygame.draw.rect(self.screen, (139, 69, 19), pygame.Rect(center_x - width // 4, center_y, width // 2, handle_length))
        # Crossguard
        pygame.draw.line(self.screen, (169, 169, 169), (center_x - width // 2, center_y), (center_x + width // 2, center_y), 2)

    def draw_charms(self):
        """Draws equipped charms at the top with hover tooltips."""
        # Inside draw_game_screen, after self.draw_bag_visual()
        mouse_pos = pygame.mouse.get_pos()
        # Add equipped charms drawing loop here (with grayscale for disabled)
        for i, charm in enumerate(self.equipped_charms):
            x = 50 + i * (CHARM_SIZE + 10)
            y = 10
            rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
            self.draw_charm_die(rect, charm, index=i)  # Pass index, no is_shop
            
            if rect.collidepoint(mouse_pos):
                tooltip_text = charm['name'] + ": " + charm['desc']
                if charm['type'] == 'sacrifice_mult':
                    tooltip_text += f" (Current mult: x{self.score_mult})"
                    if self.score_mult < 10.0:
                        tooltip_text += " (max x10)"
                elif charm['type'] == 'empty_slot_mult':
                    current_mult = self.get_stencil_mult()
                    tooltip_text += f" (Current: x{current_mult})"
                if i in self.disabled_charms:
                    tooltip_text += " (Disabled this round by Boss Effect)"
                screens.draw_tooltip(x, y + CHARM_SIZE + TOOLTIP_PADDING, tooltip_text)
        # Draw dragged charm
        if self.dragging_charm_index != -1 and not self.dragging_shop:
            charm = self.equipped_charms[self.dragging_charm_index]
            x = mouse_pos[0] - self.drag_offset_x
            y = mouse_pos[1] - self.drag_offset_y
            rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)  # Use CHARM_SIZE (100x100)
            self.draw_charm_die(rect, charm)

    def get_charm_surface(self, charm, index):
        """Returns the charm icon surface, grayscaled if disabled."""
        # Load from cache (adjust path key if needed)
        path = self.charm_icon_paths.get(charm['name'])
        if path and path in self.charm_icon_cache:
            surf = self.charm_icon_cache[path].copy()  # Copy to avoid modifying cache
            
            # Check if disabled
            if index in self.disabled_charms:
                surf = self.grayscale_surface(surf)  # Apply grayscale
            
            return surf
        else:
            # Fallback surface if no icon
            surf = pygame.Surface((CHARM_SIZE, CHARM_SIZE))
            surf.fill((200, 200, 200))  # Gray placeholder
            text = self.tiny_font.render(charm['name'][:5], True, (0, 0, 0))
            surf.blit(text, (10, 10))
            return surf

    def draw_hand_type_icon(self, rect, hand_type):
        """Draws icon for hand type with white dice showing the combo."""
        pygame.draw.rect(self.screen, (100, 100, 100), rect)
        hand_values = {
            'Pair': [1, 1],
            '2 Pair': [6, 6, 5, 5],
            '3 of a Kind': [3, 3, 3],
            '4 of a Kind': [4, 4, 4, 4],
            '5 of a Kind': [5, 5, 5, 5, 5],
            'Full House': [6, 6, 6, 5, 5],
            'Small Straight': [1, 2, 3, 4],
            'Large Straight': [2, 3, 4, 5, 6]
        }
        if hand_type in hand_values:
            values = hand_values[hand_type]
        else:
            values = [1, 2, 3, 4, 5]  # Fallback
        num_dice = len(values)
        die_size = SMALL_ICON_DIE_SIZE  # 15 from constants
        spacing = 5  # Pixels between dice
        total_width = num_dice * die_size + (num_dice - 1) * spacing
        start_x = (rect.width - total_width) // 2
        start_y = (rect.height - die_size) // 2
        dice_positions = []
        for i in range(num_dice):
            x = start_x + i * (die_size + spacing)
            y = start_y
            dice_positions.append((x, y))
        for i, pos in enumerate(dice_positions):
            die_rect = pygame.Rect(rect.x + pos[0], rect.y + pos[1], die_size, die_size)
            pygame.draw.rect(self.screen, (255, 255, 255), die_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), die_rect, 1)
            value = values[i]  # No modulo needed
            for dot_pos in data.DOT_POSITIONS.get(value, []):
                dot_x = die_rect.x + dot_pos[0] * die_size
                dot_y = die_rect.y + dot_pos[1] * die_size
                pygame.draw.circle(self.screen, (0, 0, 0), (int(dot_x), int(dot_y)), 2)

    def reset_game(self):
        # Existing resets (e.g., coins=0, stake=1, blind='Small', etc.)
        self.coins = 999999 if DEBUG else 0
        self.turn_initialized = False  # Reset for new round/turn
        self.current_stake = 1
        self.current_blind = 'Small'
        self.round_score = 0
        self.hands_left = MAX_HANDS
        self.rerolls_left = MAX_REROLLS if not DEBUG else -1
        self.discards_left = MAX_DISCARDS
        self.hand = []
        self.rolls = []
        self.held = [False] * NUM_DICE_IN_HAND
        self.discard_selected = [False] * NUM_DICE_IN_HAND
        self.is_discard_phase = False
        self.has_rolled = False
        self.bag = create_dice_bag()  # Fresh 25 dice
        self.full_bag = [d.copy() for d in self.bag]  # Copy fresh
        self.equipped_charms = []
        self.disabled_charms = []
        self.shop_charms = []
        self.available_packs = []
        self.shop_reroll_cost = 5
        self.upcoming_boss_effect = None
        self.current_boss_effect = None
        self.boss_rainbow_color = None
        self.boss_shuffled_faces = {}
        self.boss_reroll_count = 0
        self.hand_multipliers = {}  # Reset prism boosts
        self.dagger_mult = 0 if hasattr(self, 'dagger_mult') else 0
        self.green_pouch_active = False
        self.current_pouch = None
        self.extra_coins = 0
        self.broken_dice = []
        self.break_effect_start = 0
        self.temp_message = None
        self.temp_message_start = 0
        self.show_popup = False
        self.popup_message = None
        self.dragging_charm_index = -1
        self.dragging_shop = False
        # Set initial hand texts
        self.update_hand_text()
        self.hand_multipliers = {ht: 1.0 for ht in data.HAND_TYPES}  # Reset to base 1.0 for all types
        # Add any other vars to reset (e.g., multipliers_hover=False)
        self.tutorial_step = 0; self.tutorial_mode = False; self.tutorial_completed = False; self.unlocks = {}

    def apply_pouch(self, pouch):
        """Applies the selected pouch's bonuses to the game state."""
        self.current_pouch = pouch
        # Reset bag to base
        self.bag = create_dice_bag()
        self.full_bag = [d.copy() for d in self.bag]
        
        # Add extra dice
        extras = pouch.get('bonus', {}).get('extra_dice', {})
        for color, count in extras.items():
            for i in range(count):
                new_id = f"{color}{len([d for d in self.bag if d['color'] == color]) + 1}"
                new_die = {'id': new_id, 'color': color, 'faces': DICE_FACES[:]}
                self.bag.append(new_die)
                self.full_bag.append(copy.deepcopy(new_die))
        
        # Apply action/coin bonuses
        self.discards_left += pouch.get('bonus', {}).get('discards', 0)
        self.hands_left += pouch.get('bonus', {}).get('hands', 0)
        self.coins += pouch.get('bonus', {}).get('coins', 0)
        
        # Special flags (e.g., for Green)
        self.green_pouch_active = 'Green' in pouch['name']  # Simple check; refine if adding more

        # New bonuses
        self.max_charms += pouch.get('bonus', {}).get('charm_slots', 0)  # e.g., Black
        self.hands_left += pouch.get('bonus', {}).get('hands', 0)  # Negative for Black
        if 'random_special' in pouch.get('bonus', {}).get('extra_dice', {}):
            special_color = random.choice(SPECIAL_COLORS)
            # Add die logic like extras
            new_id = f"{special_color}{len([d for d in self.bag if d['color'] == special_color]) + 1}"
            new_die = {'id': new_id, 'color': special_color, 'faces': DICE_FACES[:]}
            self.bag.append(new_die)
            self.full_bag.append(copy.deepcopy(new_die))
        if pouch.get('bonus', {}).get('randomize_bag', False):
            for die in self.bag:
                die['color'] = random.choice(list(COLORS.keys()))  # Random color; add face randomize if wanted
        # For Plasma/Ghost: Add flags like self.balance_score = True, use in calculate_score/shop generation

    def generate_shop(self):
        self.shop_reroll_cost = 5
        all_packs = [0,1,2,3,4,5] + [6,7,8]  # Assume 0-5 existing, 6-8 for rune packs
        weights = [1]*6 + [1, 0.8, 0.3]  # Lower for Super
        self.available_packs = random.choices(all_packs, weights=weights, k=2 + any(tag['name'] == 'Voucher Tag' for tag in self.active_tags))  # Extra if Voucher Tag
        # Map indices to packs, e.g., if pack_id in [6,7,8]: self.pack_choices = random.sample(data.MYSTIC_RUNES, pack['choices'])
        
        # Filter pool to exclude owned (as before)
        available_pool = [c for c in data.CHARMS_POOL if c['name'] not in [e['name'] for e in self.equipped_charms]]
        
        # Compute weights per charm: base rarity * stake modifier
        charm_weights = []
        for charm in available_pool:
            rarity = charm.get('rarity', 'Common')  # Default Common
            base_weight = RARITY_WEIGHTS.get(rarity, 0.0)
            if rarity == 'Legendary':
                # Ramp: 0% early, +5% per stake beyond 1 (e.g., 10% at Stake 3)
                base_weight += 0.05 * max(0, self.current_stake - 1)
                base_weight = min(base_weight, 0.2)  # Cap at 20% to avoid flooding
            charm_weights.append(base_weight)
        
        # Sample with weights, but ensure no duplicates (use sample fallback or custom unique weighted)
        num_shop = min(3, len(available_pool))
        if sum(charm_weights) > 0:
            # Weighted but unique: Use choices, then dedup and resample if needed
            candidates = random.choices(available_pool, weights=charm_weights, k=num_shop * 2)  # Oversample to ensure uniques
            unique_candidates = []
            seen_names = set()
            for c in candidates:
                if c['name'] not in seen_names:
                    seen_names.add(c['name'])
                    unique_candidates.append(c)
                if len(unique_candidates) == num_shop:
                    break
            self.shop_charms = unique_candidates[:num_shop]
            if len(self.shop_charms) < num_shop:  # Fallback if too few uniques
                self.shop_charms += random.sample([c for c in available_pool if c['name'] not in seen_names], num_shop - len(self.shop_charms))
        else:
            self.shop_charms = random.sample(available_pool, num_shop) if available_pool else []
        
        self.available_rune_packs = random.sample(data.RUNE_PACKS, min(2, len(data.RUNE_PACKS)))  # Random 1-2 rune packs

        #  print("DEBUG: Generated shop charms:", [c['name'] for c in self.shop_charms])  # Optional: Confirm no dups (remove after test)

    def add_to_rune_tray(self, rune):
        for k in range(len(self.rune_tray)):
            if self.rune_tray[k] is None:
                self.rune_tray[k] = copy.deepcopy(rune)
                return True
        self.temp_message = "Rune tray full - discard a rune first."
        return False

    def reroll_shop(self):
        if self.coins >= self.shop_reroll_cost:
            self.coins -= self.shop_reroll_cost
            self.shop_reroll_cost += 3
            self.generate_shop()

    def apply_boss_face_shuffle(self):
        """Applies shuffled faces from the current boss effect to all relevant dice if active."""
        if self.current_boss_effect and self.current_boss_effect.get('name') == 'Face Shuffle' and self.boss_shuffled_faces:
            all_dice = self.full_bag + self.bag + self.hand + [r[0] for r in self.rolls] + self.broken_dice
            for die in all_dice:
                if die['id'] in self.boss_shuffled_faces:
                    die['faces'] = copy.deepcopy(self.boss_shuffled_faces[die['id']])
            # Optional: Log for debug
            if DEBUG:
                print("Applied boss face shuffle to", len(all_dice), "dice")

    def apply_rune_effect(self, rune, die_list=None):
        if die_list is None:
            die_list = []
        name = rune['name']
        max_dice = rune.get('max_dice', 0)
        if max_dice > 0 and len(die_list) == 0:
            self.temp_message = f"Select at least 1 die for {name}!"
            return
        if len(die_list) > max_dice:
            self.temp_message = "Too many dice selected!"
            return

        if name == 'Mystic Fool Rune':
            if hasattr(self, 'last_rune') and self.last_rune and self.add_to_rune_tray(self.last_rune):
                self.temp_message = "Copied last rune!"
            else:
                self.temp_message = "No last rune or tray full."

        elif name == 'Mystic Luck Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['enhancements'].append('Lucky')

        elif name == 'Mystic Oracle Rune':
            # Assume UPGRADE_RUNES exists or stub: add 2 random hand boosts
            for _ in range(2):
                ht = random.choice(data.HAND_TYPES)
                self.hand_multipliers[ht] += 0.5  # Or add to rune tray if upgrades are runes

        elif name == 'Mystic Mult Rune':
            # Up to 2, but allow fewer
            for die in die_list:
                die['enhancements'].append('Mult')

        elif name == 'Mystic Emperor Rune':
            for _ in range(2):
                new_rune = random.choice(data.MYSTIC_RUNES)
                self.add_to_rune_tray(new_rune)

        elif name == 'Mystic Bonus Rune':
            # Up to 2
            for die in die_list:
                die['enhancements'].append('Bonus')

        elif name == 'Mystic Wild Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['color'] = 'Rainbow'
                die['enhancements'].append('Wild')

        elif name == 'Mystic Steel Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['enhancements'].append('Steel')

        elif name == 'Mystic Fragile Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['enhancements'].append('Fragile')

        elif name == 'Mystic Wealth Rune':
            gain = min(self.coins, 20)
            self.coins += gain
            self.temp_message = f"Gained {gain} coins!"

        elif name == 'Mystic Fate Rune':
            if random.random() < 0.25 and self.bag:
                die = random.choice(self.bag)
                edition = random.choice(['Foil', 'Holo', 'Poly'])
                die['enhancements'].append(edition)
                die['enhancements'].append('Fate')

        elif name == 'Mystic Strength Rune':
            # Up to 2
            for die in die_list:
                faces = sorted(die['faces'])
                die['faces'] = faces[2:] + random.choices(faces[3:], k=2)  # Mid-high dups
                die['faces'] = die['faces'][:6]
                die['enhancements'].append('Strength')

        elif name == 'Mystic Sacrifice Rune':
            # Up to 2
            for die in die_list:
                value = 10 if die['color'] in SPECIAL_COLORS else 5
                self.coins += value
                self.bag.remove(die)
                if die in self.full_bag:
                    self.full_bag.remove(die)

        elif name == 'Mystic Transmute Rune':
            if len(die_list) != 2:
                self.temp_message = "Select exactly 2 dice!"
                return
            target, source = die_list  # First selected = target (#1), second = source (#2)
            target['color'] = source['color']
            target['faces'] = source['faces'][:]
            target['enhancements'].append('Transmute')

        elif name == 'Mystic Balance Rune':
            total = sum(c.get('cost', 0) for c in self.equipped_charms)
            self.coins += min(total, 50)

        elif name == 'Mystic Gold Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['color'] = 'Gold'
                die['enhancements'].append('Gold')

        elif name == 'Mystic Stone Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['enhancements'].append('Stone')
                die['faces'] = [random.randint(3,6)] * 6  # Fixed high-ish

        elif name in ['Mystic Red Rune', 'Mystic Blue Rune', 'Mystic Green Rune', 'Mystic Purple Rune', 'Mystic Yellow Rune']:
            # Up to 3
            color = name.split()[1].capitalize()  # Red, etc.
            for die in die_list:
                die['color'] = color
                die['enhancements'].append(color)

        elif name == 'Mystic Judgement Rune':
            charm = random.choice([c for c in data.CHARMS_POOL if c['rarity'] == 'Common'])
            if len(self.equipped_charms) < self.max_charms:
                self.equipped_charms.append(charm)
                self.temp_message = f"Added {charm['name']}!"
            else:
                self.temp_message = "Charm slots full!"

        elif name == 'Mystic Silver Rune':
            if len(die_list) != 1:
                self.temp_message = "Select exactly 1 die!"
                return
            for die in die_list:
                die['color'] = 'Silver'
                die['enhancements'].append('Silver')

        self.last_rune = rune  # Track for Fool
        self.refresh_bag()  # Update visuals
        self.temp_message = f"Applied {name}!" if not self.temp_message else self.temp_message

    def refresh_bag(self):
        """Force update bag visuals after rune apply."""
        # Update full_bag to match bag (if needed for persistence)
        self.full_bag = [d for d in self.full_bag if d in self.bag] + [d for d in self.bag if d not in self.full_bag]  # Sync
        # If in shop/game, force redraw (state will handle in next draw call)
        #  print("Bag refreshed")  # Debug; remove later

    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    savegame.save_game(self)  # Save on close
                    running = False
                self.state_machine.handle_event(event)

            self.state_machine.update(dt)
            self.state_machine.draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = ChromaRollGame()
    game.run()
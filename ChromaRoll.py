from cmath import rect
import math  # For ceil in bag rows
import random  # For rolling dice and drawing from bag
import pygame  # For graphics and input handling
import sys  # For exiting the game
import time  # For animation delays
import copy
import sys
import data
import screens
import savegame
import os
from constants import *
from utils import draw_rounded_element, resource_path, create_dice_bag, wrap_text, get_easing
from statemachine import StateMachine, SplashState, GameOverState

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

        # Dedup CHARMS_POOL by name (safeguard against old dups or mutations)
        unique_pool = {}
        for c in data.CHARMS_POOL:
            if c['name'] not in unique_pool:
                unique_pool[c['name']] = c
        data.CHARMS_POOL = list(unique_pool.values())
        print("DEBUG: Deduped CHARMS_POOL to", len(data.CHARMS_POOL), "unique charms")  # Optional: Confirm (remove after test)
        
        self.state_machine = StateMachine(self, SplashState(self))
        self.screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)  # Resizable window
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Chroma Roll")  # Set title
        # Use imported THEME (raw paths) + resource_path for loading
        self.font = pygame.font.Font(resource_path(THEME['font_main_path']), THEME['font_main_size'])  # Font for text
        self.small_font = pygame.font.Font(resource_path(THEME['font_small_path']), THEME['font_small_size'])  # Smaller font for hand/modifier info
        self.tiny_font = pygame.font.Font(resource_path(THEME['font_tiny_path']), THEME['font_tiny_size'])  # Even smaller for top texts
        self.bag = create_dice_bag()  # Create dice bag (mutable list for removal)
        self.hand = []  # Current hand of dice
        self.full_bag = [d.copy() for d in self.bag]  # Template of all owned dice
        self.rolls = []  # Current rolls: list of (die, value)
        self.held = [False] * NUM_DICE_IN_HAND  # Track held dice
        self.discard_selected = [False] * NUM_DICE_IN_HAND  # Track selected for discard
        self.rerolls_left = MAX_REROLLS if not DEBUG else -1  # -1 for unlimited in debug
        self.discards_left = MAX_DISCARDS  # Discards per round
        self.discard_used_this_round = False  # Track if discard was used in the current hand's discard phase
        self.hands_left = MAX_HANDS  # Hands (scores) per round
        self.coins = 0  # Chroma Coins for upgrades
        self.extra_coins = 0  # For tracking bonus coins from gold and silver dice
        if DEBUG:
            self.coins = 999999  # Infinite coins for debug (large value to simulate infinity without breaking int ops)
        self.round_score = 0  # Score for current blind/round
        self.current_stake = 1  # Current stake level
        self.current_blind = 'Small'  # Current blind: Small, Big, Boss
        self.game_state = 'splash'  # Start with splash instead of 'blinds'
        self.splash_start_time = 0  # Timestamp for anim start
        self.splash_image = None  # Loaded image
        self.splash_phase = 'pan'  # Phases: 'pan', 'hold', 'zoom_out', 'done'
        self.previous_state = None  # Init to starting state
        self.pause_menu_selection = None  # For button handling (optional)
        self.show_popup = False  # Flag for beaten blind popup
        self.broken_dice = []  # List of indices (0-4) of breaking Glass dice
        self.break_effect_start = 0  # Timestamp when effect starts
        self.break_effect_duration = 1.0  # Seconds for fade-out
        self.break_icon = None  # Cached scaled PNG
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
        self.multipliers_hover = False  # For showing multipliers panel
        self.current_pouch = None
        self.active_tags = []
        self.rune_tray = [None, None]  # Two rune slots
        # Dedup CHARMS_POOL by name (safeguard against old dups)
        seen_names = set()
        self.is_resuming = False  # Flag

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

        # In ChromaRollGame __init__, add:
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

        self.selected_pouch = None  # Track chosen pouch for bonuses
        self.green_pouch_active = False  # Flag for Green Pouch effect
        self.pouch_offset = 0  # For carousel scrolling
        self.unlocks = {}  # Future: Track unlocks, e.g., self.unlocks['Black Pouch'] = False; for now, use pouch['unlocked']
        # Set initial hand texts
        self.update_hand_text()
        self.tutorial_step = 0  # Current step in tutorial (0-5)
        self.tutorial_mode = False  # Flag if in tutorial
        self.tutorial_completed = False  # Track if finished (for future skips/unlocks)
        pouches = data.POUCHES
        if DEBUG:
            for pouch in pouches[4:]:  # Indices 4-7 for 5-8
                pouch['unlocked'] = True

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
        
        if DEBUG:
            # Default to empty if not defined (e.g., commented out)
            debug_colors = globals().get('DEBUG_COLORS', [])  # Safely get global if commented
            if debug_colors:  # Only force if non-empty list
                # Debug mode: Force specific colors without removing from bag
                hand = []
                for color in debug_colors:
                    available = [d for d in self.bag if d['color'] == color]
                    if available:
                        selected = random.choice(available)
                        hand.append(selected)
                    else:
                        # New: If no dice of this color (e.g., Glass for testing), create temp one
                        temp_id = f"Temp{color}{len(hand) + 1}"
                        temp_die = {'id': temp_id, 'color': color, 'faces': DICE_FACES[:]}
                        hand.append(temp_die)  # Add temp without modifying bag
                return hand[:num_dice]  # Ensure exactly num_dice
            # If empty, fall through to normal draw (with other DEBUG perks active)
        
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
        self.hand = self.draw_hand()
        self.rolls = [(die, 1) for die in self.hand]  # Start with value 1 (single pip)
        self.held = [False] * NUM_DICE_IN_HAND
        self.discard_selected = [False] * NUM_DICE_IN_HAND
        self.rerolls_left = MAX_REROLLS if not DEBUG else -1  # Reset to unlimited in debug
        self.turn += 1
        self.discard_used_this_round = False  # Reset per hand
        self.is_discard_phase = True  # Reset to discard phase
        self.has_rolled = False  # No initial roll yet
        self.update_hand_text()  # Update initial hand text
        # In new_turn():
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
        self.rolls = self.roll_hand()
        self.discard_selected = [False] * NUM_DICE_IN_HAND  # Clear selections
        self.update_hand_text()

    def score_and_new_turn(self):
        """Manually scores and starts a new turn."""
        if self.show_popup:
            return  # Block actions during popup
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
        glass_break_chance = 0.25
        glass_break_penalty = 0
        for charm in self.equipped_charms:
            if charm['type'] == 'glass_mod':
                glass_break_chance = charm['break_chance']
                glass_break_penalty = charm['break_penalty']

        # Handle Glass break chance (only for held Glass)
        for i, (die, _) in enumerate(self.rolls):
            if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                # Play break sound here again (on retrigger break)
                self.sfx_channel.play(self.glass_break_sound)
                # Break: Remove from full_bag and bag
                self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                self.bag = [d for d in self.bag if d['id'] != die['id']]
                self.coins -= glass_break_penalty
                self.broken_dice.append(i)  # Add index for animation
                self.break_effect_start = time.time()  # Start timer

        # Add Mime here (same as above)
        has_mime = any(c['type'] == 'retrigger_held' for c in self.equipped_charms)

        # Retrigger if Mime (same as above)
        if has_mime:
            for i, (die, _) in enumerate(self.rolls):
                if self.held[i]:
                    if die['color'] == 'Gold':
                        self.extra_coins += 1

            glass_count = sum(1 for i, (die, _) in enumerate(self.rolls) if die['color'] == 'Glass' and self.held[i])
            score *= (4 ** glass_count)

            for i, (die, _) in enumerate(self.rolls):
                if die['color'] == 'Glass' and self.held[i] and random.random() < glass_break_chance:
                    # Play break sound here again (on retrigger break)
                    self.sfx_channel.play(self.glass_break_sound)
                    self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                    self.bag = [d for d in self.bag if d['id'] != die['id']]
                    self.coins -= glass_break_penalty
                    self.broken_dice.append(i)  # Add index for animation
                    self.break_effect_start = time.time()  # Start timer

        self.hands_left -= 1
        self.hands_left = max(0, self.hands_left)  # Clamp to prevent negative
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
                remains_coins = self.hands_left + self.discards_left  # Remove 'if not DEBUG else 0' to always gain from hands/discards
                # If you want to keep debug override (e.g., for testing no remains), uncomment and adjust:
                # remains_coins = self.hands_left + self.discards_left if not DEBUG else 0
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

    def get_hand_type_and_score(self):
        """Determines the hand type, base score, modifier, and final score."""
        held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
        if not held_rolls:
            return "Nothing", 0, "None", 0, 0, 0.0
        values = [value for die, value in held_rolls]
        colors_list = [die['color'] for die, value in held_rolls]  # List of colors
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
        base_modifier = 1.0
        modifier_desc = "None"

        straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
        short_straights_small = [[1,2,3], [2,3,4], [3,4,5], [4,5,6]]
        short_straights_large = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]

        has_four_fingers = any(c['type'] == 'short_straight' for c in self.equipped_charms if self.equipped_charms.index(c) not in self.disabled_charms)

        # Apply Value Vault early if active (inverts before hand detection)
        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Value Vault':
            values = [7 - v for v in values]  # Invert: 1->6, 2->5, etc.
            sorted_values = sorted(values)

        if max_count == 5:
            hand_type = "5 of a Kind"
            base_score = 250
            # Handle wild for mono/rainbow
            actual_colors = [c for c in colors_list if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier *= 4.0
                modifier_desc = "Monochrome x4"
            elif len(actual_colors) == len(actual_set):  # No dups in actual, can make rainbow
                base_modifier *= 3.0
                modifier_desc = f"{modifier_desc + ' + ' if modifier_desc != 'None' else ''}Rainbow x3"
        elif max_count == 4:
            hand_type = "4 of a Kind"
            base_score = 160
            for val, group_colors in groups.items():
                if len(group_colors) == 4:
                    actual_colors = [c for c in group_colors if c != 'Rainbow']
                    actual_set = set(actual_colors)
                    if len(actual_set) <= 1:
                        base_modifier *= 3.0
                        modifier_desc = "Monochrome x3"
                    elif len(actual_colors) == len(actual_set):  # Prioritize mono, else rainbow if possible
                        base_modifier *= 2.0
                        modifier_desc = f"{modifier_desc + ' + ' if modifier_desc != 'None' else ''}Rainbow x2"
                    break
        elif max_count == 3 and 2 in counts.values():
            hand_type = "Full House"
            base_score = 160
            # Find the 3ok and pair groups
            three_group = next(g for g in groups.values() if len(g) == 3)
            pair_group = next(g for g in groups.values() if len(g) == 2)
            # Mono checks with wild
            mono_three = len(set(c for c in three_group if c != 'Rainbow')) <= 1
            mono_pair = len(set(c for c in pair_group if c != 'Rainbow')) <= 1
            if mono_three and mono_pair:
                base_modifier *= 2.0
                modifier_desc = "Both Mono x2"
            elif mono_three or mono_pair:
                base_modifier *= 1.5
                modifier_desc = "One Mono x1.5"
            # Full mono/rainbow with priority to mono
            actual_colors = [c for c in colors_list if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier *= 4.0
                modifier_desc = "Full Mono x4"
            elif len(actual_colors) == len(actual_set):
                base_modifier *= 3.0
                modifier_desc = f"{modifier_desc + ' + ' if modifier_desc != 'None' else ''}Rainbow x3"
        elif sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large)):
            hand_type = "Large Straight"
            base_score = 160
            straight_len = 5
            straight_colors = colors_list  # Default full hand
            straight_values = sorted_values if not has_four_fingers else next(s for s in short_straights_large if all(x in values for x in s)) or sorted_values
            straight_len = len(straight_values)
            straight_colors = []
            for v in straight_values:
                straight_colors += groups.get(v, [])
            actual_colors = [c for c in straight_colors if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier *= 2.0
                modifier_desc = "Monochrome x2"
            elif len(actual_colors) == len(actual_set):
                base_modifier *= 2.0
                modifier_desc = f"{modifier_desc + ' + ' if 'Mono' in modifier_desc else ''}Rainbow x2"
        elif any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small)):
            hand_type = "Small Straight"
            base_score = 90
            straight_len = 4
            straight_colors = colors_list  # Default full hand
            straight_values = next(s for s in straights if all(x in values for x in s)) if not has_four_fingers else next(s for s in short_straights_small if all(x in values for x in s)) or sorted_values
            straight_len = len(straight_values)
            straight_colors = []
            for v in straight_values:
                straight_colors += groups.get(v, [])
            actual_colors = [c for c in straight_colors if c != 'Rainbow']
            actual_set = set(actual_colors)
            if len(actual_set) <= 1:
                base_modifier *= 2.0
                modifier_desc = "Monochrome x2"
            elif len(actual_colors) == len(actual_set):
                base_modifier *= 2.0
                modifier_desc = f"{modifier_desc + ' + ' if 'Mono' in modifier_desc else ''}Rainbow x2"
        elif max_count == 3:
            hand_type = "3 of a Kind"
            base_score = 80
            for val, group_colors in groups.items():
                if len(group_colors) == 3:
                    actual_colors = [c for c in group_colors if c != 'Rainbow']
                    actual_set = set(actual_colors)
                    if len(actual_set) <= 1:
                        base_modifier *= 2.0
                        modifier_desc = "Monochrome x2"
                    elif len(actual_colors) == len(actual_set):
                        base_modifier *= 1.5
                        modifier_desc = f"{modifier_desc + ' + ' if modifier_desc != 'None' else ''}Rainbow x1.5"
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
                base_modifier *= 1.5
                modifier_desc = "One Mono Pair x1.5"
            elif mono_pairs == 2:
                base_modifier *= 2.0
                modifier_desc = "Two Mono Pairs x2"
        elif pair_count == 1:
            hand_type = "Pair"
            base_score = 20
            for group_colors in groups.values():
                if len(group_colors) == 2:
                    actual_set = set(c for c in group_colors if c != 'Rainbow')
                    if len(actual_set) <= 1:
                        base_modifier *= 1.5
                        modifier_desc = "Monochrome x1.5"
                    break
        # Nothing remains 0, no modifier

        # Apply Rainbow Restriction if active (before color checks)
        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Rainbow Restriction':
            colors_list = [self.boss_rainbow_color if c == 'Rainbow' else c for c in colors_list]
            # Recompute unique_colors if needed for later checks
            unique_colors = set(colors_list)

        # Apply boss effects to base elements (after hand detection, before charms)
        if self.current_blind == 'Boss' and self.current_boss_effect:
            effect_name = self.current_boss_effect['name']
            if effect_name == 'Score Dip':
                base_score = int(base_score * 0.9)
            if effect_name == 'Color Fade':
                base_modifier = 1.0
                modifier_desc = "None"
            if effect_name == 'Mono Mixup' and len(set(colors_list)) > 1:  # Use updated colors_list
                base_modifier /= 2

        # Apply charms (skip disabled)
        charm_chips = 0
        charm_color_mult_add = 0.0  # Renamed from charm_mono_add
        charm_mult_add = 1.0
        is_mono = 'Mono' in modifier_desc
        is_rainbow = 'Rainbow' in modifier_desc
        num_dice_used = len(held_rolls)  # Approximate "uses" as unique values? Wait, it's len(held_rolls)
        is_small_straight = any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small))
        is_large_straight = sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large))
        for idx, charm in enumerate(self.equipped_charms):
            if idx in self.disabled_charms:
                continue  # Skip disabled charms
            if charm['type'] == 'flat_bonus':
                charm_chips += charm['value']
            elif charm['type'] == 'per_color_bonus':
                charm_chips += colors_list.count(charm['color']) * charm['value']  # Rainbow doesn't count for specific colors
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
            elif charm['type'] == 'few_dice_bonus':
                if num_dice_used <= charm['max_dice']:
                    charm_chips += charm['value']
            elif charm['type'] == 'empty_slot_mult':
                empty_slots = self.max_charms - len(self.equipped_charms)
                charm_mult_add *= (1 + empty_slots)  # x1 for each empty + this one? Adjust as needed
            elif charm['type'] == 'per_value_bonus':
                count = 0
                for _, value in held_rolls:
                    if (charm['parity'] == 'even' and value % 2 == 0) or (charm['parity'] == 'odd' and value % 2 != 0):
                        count += 1
                charm_chips += count * charm['value']
            elif charm['type'] == 'rainbow_mult_bonus':
                if is_rainbow:
                    charm_color_mult_add += charm['value']
            elif charm['type'] == 'sacrifice_mult':
                charm_mult_add *= self.score_mult  # Add this for dagger; adjust if self.score_mult is pre-set elsewhere (e.g., cap at 10.0)
            # Skip Mime, Debt for now

        total_modifier = (base_modifier + charm_color_mult_add) * charm_mult_add  # Removed * self.score_mult (now handled in loop)

        if hand_type in self.hand_multipliers:
            total_modifier *= self.hand_multipliers[hand_type]  # Apply Prism Pack multiplier

        # Apply Special Silence (skip Glass mult if silenced)
        silence_glass = False
        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Special Silence':
            silence_glass = True

        glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass')
        glass_mult = (4 ** glass_count) if not silence_glass else 1.0  # x4 per held Glass, or 1 if silenced

        # If Mime equipped (and not disabled), double the Glass mult (retrigger)
        has_mime = any(c['type'] == 'retrigger_held' for idx, c in enumerate(self.equipped_charms) if idx not in self.disabled_charms)
        if has_mime and not silence_glass:
            glass_mult *= (4 ** glass_count)  # Apply again for retrigger

        total_modifier *= glass_mult

        # Apply Multiplier Mute (cap total_modifier)
        if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Multiplier Mute':
            total_modifier = min(total_modifier, 1.5)

        final_score = int((base_score + charm_chips) * total_modifier)  # Round to int for clean display
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

                # New: Calculate Glass mult from current held rolls
                held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
                glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass')
                glass_mult = 4 ** glass_count  # Base x4 per held Glass

                # If Mime equipped (and not disabled), double the Glass mult (retrigger)
                has_mime = any(c['type'] == 'retrigger_held' for idx, c in enumerate(self.equipped_charms) if idx not in self.disabled_charms)
                if has_mime:
                    glass_mult *= (4 ** glass_count)  # Apply again for retrigger

                if glass_mult > 1.0:
                    modifier_parts.append(f"Glass x{glass_mult}")

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
        
        print("DEBUG: Generated shop charms:", [c['name'] for c in self.shop_charms])  # Optional: Confirm no dups (remove after test)

    def reroll_shop(self):
        if self.coins >= self.shop_reroll_cost:
            self.coins -= self.shop_reroll_cost
            self.shop_reroll_cost += 3
            self.generate_shop()

    def apply_rune_effect(self, rune, die_list=None):
        name = rune['name']
        if die_list is None:
            die_list = []

        print(f"Applying {name} to {len(die_list)} dice")  # Debug: Confirm call

        if name == 'Mystic Fool Rune':
            # Create copy of last rune (track self.last_rune in game; assume set on apply)
            if hasattr(self, 'last_rune') and self.last_rune:
                self.rune_tray.append(copy.deepcopy(self.last_rune)) if len(self.rune_tray) < 2 else print("Tray full")  # Or add to inventory

        elif name == 'Mystic Luck Rune':
            if len(die_list) > 0:
                die_list[0]['enhancements'].append('Lucky')

        elif name == 'Mystic Oracle Rune':
            # Create 2 random Upgrade Runes (placeholder; add UPGRADE_RUNES list in data.py if implementing hand upgrades)
            for _ in range(2):
                upgrade = random.choice(data.UPGRADE_RUNES) if hasattr(data, 'UPGRADE_RUNES') else {}  # Stub
                self.rune_tray.append(upgrade) if len(self.rune_tray) < 2 else print("Tray full")

        elif name == 'Mystic Mult Rune':
            for die in die_list[:2]:
                die['enhancements'].append('Mult')

        elif name == 'Mystic Emperor Rune':
            for _ in range(2):
                new_rune = random.choice(data.MYSTIC_RUNES)
                self.rune_tray.append(copy.deepcopy(new_rune)) if len(self.rune_tray) < 2 else print("Tray full")

        elif name == 'Mystic Bonus Rune':
            for die in die_list[:2]:
                die['enhancements'].append('Bonus')

        elif name == 'Mystic Wild Rune':
            if len(die_list) > 0:
                die_list[0]['color'] = 'Rainbow'
                die_list[0]['enhancements'].append('Wild')

        elif name == 'Mystic Steel Rune':
            if len(die_list) > 0:
                die_list[0]['enhancements'].append('Steel')

        elif name == 'Mystic Fragile Rune':
            if len(die_list) > 0:
                die_list[0]['enhancements'].append('Fragile')

        elif name == 'Mystic Wealth Rune':
            self.coins = min(self.coins * 2, self.coins + 20)  # Double max +20

        elif name == 'Mystic Fate Rune':
            # Random edition (placeholder; add EDITIONS if implementing)
            if self.bag:
                die = random.choice(self.bag)
                edition = random.choice(['Foil', 'Holo', 'Poly'])
                die['enhancements'].append(edition)
                die['enhancements'].append('Fate')  # Track

        elif name == 'Mystic Strength Rune':
            for die in die_list[:2]:
                # Harmonize faces: Duplicate mid-high
                faces = sorted(die['faces'])  # Assume [1,2,3,4,5,6]
                die['faces'] = faces[2:] + faces[3:5] + [faces[-1]]  # e.g., [3,4,5,6,4,5,6] but trim to 6
                die['faces'] = die['faces'][:6]  # Ensure 6
                die['enhancements'].append('Strength')

        elif name == 'Mystic Sacrifice Rune':
            for die in die_list[:2]:
                value = 5 if die['color'] in BASE_COLORS else 10  # Example coins
                self.coins += value
                self.bag.remove(die)  # Destroy
                if die in self.full_bag:
                    self.full_bag.remove(die)  # Update full_bag

        elif name == 'Mystic Transmute Rune':
            if len(die_list) == 2:
                target, source = die_list[0], die_list[1]
                target['color'] = source['color']
                target['faces'] = copy.deepcopy(source['faces'])
                target['enhancements'].append('Transmute')

        elif name == 'Mystic Balance Rune':
            total = sum(c['cost'] for c in self.equipped_charms)  # Example sell value = cost
            self.coins += min(total, 50)

        elif name == 'Mystic Gold Rune':
            if len(die_list) > 0:
                die_list[0]['color'] = 'Gold'

        elif name == 'Mystic Stone Rune':
            if len(die_list) > 0:
                die_list[0]['enhancements'].append('Stone')
                die_list[0]['faces'] = [4] * 6  # Fixed mid value; adjust

        elif name == 'Mystic Red Rune':
            for die in die_list[:3]:
                print(f"Changing die {die['id']} to Red")  # Debug
                die['color'] = 'Red'
                die['enhancements'].append('Red')

        elif name == 'Mystic Blue Rune':
            for die in die_list[:3]:
                print(f"Changing die {die['id']} to Blue")  # Debug
                die['color'] = 'Blue'
                die['enhancements'].append('Blue')

        elif name == 'Mystic Green Rune':
            for die in die_list[:3]:
                die['color'] = 'Green'
                die['enhancements'].append('Green')

        elif name == 'Mystic Judgement Rune':
            charm = random.choice([c for c in data.CHARMS_POOL if c['rarity'] == 'Common'])
            if len(self.equipped_charms) < 5:  # Hardcoded max from your code
                self.equipped_charms.append(charm)

        elif name == 'Mystic Purple Rune':
            for die in die_list[:3]:
                die['color'] = 'Purple'
                die['enhancements'].append('Purple')

        elif name == 'Mystic Yellow Rune':
            for die in die_list[:3]:
                die['color'] = 'Yellow'
                die['enhancements'].append('Yellow')

        elif name == 'Mystic Silver Rune':
            if len(die_list) > 0:
                die_list[0]['color'] = 'Silver'
                die_list[0]['enhancements'].append('Silver')
            else:
                print("No die selected for Silver Rune")  # Debug; optional error message in game

        self.last_rune = rune  # Track for Fool
        self.refresh_bag()
        self.temp_message = f"Applied {name}!"

    def refresh_bag(self):
        """Force update bag visuals after rune apply."""
        # Update full_bag to match bag (if needed for persistence)
        self.full_bag = [d for d in self.full_bag if d in self.bag] + [d for d in self.bag if d not in self.full_bag]  # Sync
        # If in shop/game, force redraw (state will handle in next draw call)
        print("Bag refreshed")  # Debug; remove later

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
from cmath import rect
import math  # For ceil in bag rows
import random  # For rolling dice and drawing from bag
import pygame  # For graphics and input handling
import time  # For animation delays
import copy
import sys
import os
sys.path.insert(0, '.')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Ensure root directory is always included
import data
import screens
import savegame
from scoring import evaluate_hand, get_stencil_mult, apply_enhancement_retrigger
from d20_boon import D20BoonSystem
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
            self.splash_image = pygame.Surface((838, 1248))  # Fallback blank
            self.splash_image.fill((0, 0, 0))  # Black if missing

        # Pre-load other assets (icons, sounds, etc.) here as before
        # e.g., your charm pre-load loop, mixer.init(), Sound loads

        self.d20_boon = D20BoonSystem()
        self.show_challenges_screen = False  # New flag for the screen
        self.challenges_mode = "main"     # main / fusion / rolling / result
        self.selected_fusion = None
        self.challenges_anim_time = 0

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
            'Gambler\'s Grimoire': resource_path('assets/icons/gamblers_grimoire_icon.png'),
            'Advantage Amulet': resource_path('assets/icons/advantage_amulet_icon.png'),
            'Fate\'s Favor': resource_path('assets/icons/fates_favor_icon.png'),
            'Luck\'s Locket': resource_path('assets/icons/lucks_locket_icon.png'),
            'Rune Relic': resource_path('assets/icons/rune_relic_icon.png'),
            'Envy Echo': resource_path('assets/icons/envy_echo_icon.png'),
            'Gluttony Glyph': resource_path('assets/icons/gluttony_glyph_icon.png'),
            'Yellow Prism': resource_path('assets/icons/yellow_prism_icon.png'),
            'Sloth Sigil': resource_path('assets/icons/sloth_sigil_icon.png'),
            'Face Forgery': resource_path('assets/icons/face-forgery-icon.png'),
            'Queen\'s Quill': resource_path('assets/icons/queens-quill-icon.png'),
            'Ace\'s Aura': resource_path('assets/icons/aces-aura-icon.png'),
            'Interest Idol': resource_path('assets/icons/interest-idol-icon.png'),
            'Synergy Scroll': resource_path('assets/icons/synergy-scroll-icon.png'),
            'Enhance Elixir': resource_path('assets/icons/enhance-elixir-icon.png'),
            'Discard Drake': resource_path('assets/icons/discard-drake-icon.png'),
            'Wild Warden': resource_path('assets/icons/wild-warden-icon.png'),
            'Kind Keeper': resource_path('assets/icons/kind-keeper-icon.png'),
            'Final Forge': resource_path('assets/icons/final-forge-icon.png'),
            'Buy Boon': resource_path('assets/icons/buy-boon-icon.png'),
            'Echo Ember': resource_path('assets/icons/echo-ember-icon.png'),
            'Triple Threat': resource_path('assets/icons/triple-threat-icon.png'),
            'Disadvantage Dice': resource_path('assets/icons/disadvantage-dice-icon.png'),
            'Stat Roller': resource_path('assets/icons/stat-roller-icon.png'),
            'Critical Hit': resource_path('assets/icons/critical-hit-icon.png'),
            'Saving Throw': resource_path('assets/icons/saving-throw-icon.png'),
            'Homebrew Hazard': resource_path('assets/icons/homebrew-hazard-icon.png'),
            'Greedy Gambler': resource_path('assets/icons/greedy-gambler-icon.png'),
            'Retrigger Rune': resource_path('assets/icons/retrigger-rune-icon.png'),
            'Economy Echo': resource_path('assets/icons/economy-echo-icon.png'),
            'Break Buffer': resource_path('assets/icons/break-buffer-icon.png'),
            'Whirlwind Wild': resource_path('assets/icons/wild-whirl-icon.png'),
            'Discard Dynamo': resource_path('assets/icons/discard-dynamo-icon.png'),
            'Rune Recycler': resource_path('assets/icons/rune-recycler-icon.png'),
            'Kind King': resource_path('assets/icons/kind-king-icon.png'),
            'Final Flourish': resource_path('assets/icons/final-flourish-icon.png'),
            'Dragon\'s Dice': resource_path('assets/icons/dragons-dice-icon.png'),
            'Bardic Blade': resource_path('assets/icons/bardic-blade-icon.png'),
            'Druid\'s Dream': resource_path('assets/icons/druids-dream-icon.png'),
            'Sorcerer\'s Surge': resource_path('assets/icons/sorcerers-surge-icon.png'),
            'Familiar\'s Foresight': resource_path('assets/icons/familiars-foresight-icon.png'),
            'Cloak of Cunning': resource_path('assets/icons/cloak-of-cunning-icon.png'),
            'Spellbook Scribe': resource_path('assets/icons/spellbook-scribe-icon.png'),
            'Necromancer\'s Needle': resource_path('assets/icons/necromancers-needle-icon.png'),
            'Triboulet Token': resource_path('assets/icons/triboulet-token-icon.png'),
            'Wee Widget': resource_path('assets/icons/wee-widget-icon.png'),
            'Flower Pot Prism': resource_path('assets/icons/flower-pot-prism-icon.png'),
            'Glass Globe': resource_path('assets/icons/glass-globe-icon.png'),
            'Obelisk Orb': resource_path('assets/icons/obelisk-orb-icon.png'),
            'Burglar Bag': resource_path('assets/icons/burglar-bag-icon.png'),
            'Steel Seal': resource_path('assets/icons/steel-seal-icon.png'),
            'Dusk Die': resource_path('assets/icons/dusk-die-icon.png'),
            'Loyalty Luck': resource_path('assets/icons/loyalty-luck-icon.png'),
            'Marble Mystic': resource_path('assets/icons/marble-mystic-icon.png'),
            'Joker Die': resource_path('assets/icons/joker-die-icon.png'),
            'Space Sphere': resource_path('assets/icons/space-sphere-icon.png'),
            'Ice Shard': resource_path('assets/icons/ice-shard-icon.png'),
            'Hiker Hex': resource_path('assets/icons/hiker-hex-icon.png'),
            'Square Sphere': resource_path('assets/icons/square-sphere-icon.png'),
            'Cloud Cube': resource_path('assets/icons/cloud-cube-icon.png'),
            'Rocket Rune': resource_path('assets/icons/rocket-rune-icon.png'),
            'Luchador Lens': resource_path('assets/icons/luchador-lens-icon.png'),
            'Gift Glyph': resource_path('assets/icons/gift-glyph-icon.png'),
            'Turtle Token': resource_path('assets/icons/turtle-token-icon.png'),
            'Erosion Edge': resource_path('assets/icons/erosion-edge-icon.png'),
            'Reserved Relic': resource_path('assets/icons/reserved-relic-icon.png'),
            'Lucky Labyrinth': resource_path('assets/icons/lucky-labyrinth-icon.png'),
            'Bull Bead': resource_path('assets/icons/bull-bead-icon.png'),
            'Trading Token': resource_path('assets/icons/trading-token-icon.png'),
            'Castle Cube': resource_path('assets/icons/castle-cube-icon.png'),
            'Acrobat Amulet': resource_path('assets/icons/acrobat-amulet-icon.png'),
            'Monopoly Mortgage': resource_path('assets/icons/monopoly-mortgage-icon.png'),
            'Life Milestone': resource_path('assets/icons/life-milestone-icon.png'),
            'UNO Draw 2': resource_path('assets/icons/uno-uno-icon.png'),
            'UNO Skip': resource_path('assets/icons/uno-skip-icon.png')
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
        
        self.is_endless = False

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
        self.used_uno_this_blind = False  # For UNO Draw 2
        self.uno_charm_rect = None  # Rect for UNO Draw 2 charm icon

        self.theme = THEME

        self.held_advantage = False  # Separate hold for advantage die
        self.has_advantage = False
        self.advantage_value = None
        self.use_advantage = False
        self.center_die_rect = None
        self.advantage_die_rect = None
        self.initial_auto_roll_done = False  # For auto-roll in rolling phase
        self.original_center_value = None  # Save original 3rd die value for revert

        

        # New for Fate's Favor
        self.used_fates_favor_this_blind = False
        self.fates_advantage_index = -1  # -1 means no advantage active
        self.fates_advantage_value = None
        self.held_fates_advantage = False
        self.selecting_fates_die = False  # Flag for die selection mode after charm click

        # In ChromaRollGame._init_defaults (after self.used_fates_favor_this_blind = False)
        self.used_buy_boon_this_turn = False  # Reset in new_turn
        self.selecting_buy_boon_die = False  # Flag for selection mode
        self.buy_boon_target_index = -1  # Selected die index
        self.buy_boon_shifts_left = 2  # Max shifts per use (reset on activation)
        self.buy_boon_up_rect = None  # Temp for up arrow
        self.buy_boon_down_rect = None  # Temp for down arrow
        self.buy_boon_confirm_rect = None  # Temp for confirm button

        # For disadvantage dice charm
        self.used_disadvantage_this_turn = False  # Reset in new_turn
        self.selecting_disadvantage_die = False  # Selection mode
        self.disadvantage_target_index = -1  # Selected die
        self.disadvantage_confirm_rect = None  # Confirm button
        self.used_whirlwind_this_blind = False  # Per blind (resets in advance blind)
        self.selecting_whirlwind_die = False  # Selection mode
        self.whirlwind_target_index = -1  # Selected die for free reroll
        self.selecting_bag_swap = False
        self.swap_use_left = 1
        self.swap_source_index = -1
        self.selecting_bag_die = False
        self.destroyed_dice = []  # NEW: Track removed dice for Needle revival (preserves color/enh)
        
        # New for Gambler's Grimoire
        self.used_rune_cast_this_shop = False
        self.round_locket_coins = 0
        self.round_base_lucky_coins = 0
        self.is_last_hand = False
        self.first_discard_this_turn = True
        self.last_state_was_rune = False
        self.uno_skip_used = False  # NEW: Init for UNO Skip (one-time boss skip flag)
        self.from_shop_rune_use = False  # NEW: Flag for shop rune entry (force fresh pull)

        # In __init__, after dedup CHARMS_POOL
        for c in data.CHARMS_POOL:
            if 'sell_value' not in c:
                c['sell_value'] = c['cost'] // 2  # Default half cost; adjust if full refund

        self._init_defaults()  # Call after one-time setups

    def get_hand_type_and_score(self, is_preview=True):
        """Wrapper so old calls keep working perfectly."""
        return evaluate_hand(self, is_preview)

    def calculate_score(self):
        """Old wrapper — returns just the final score number."""
        _, _, _, final_score, _, _ = evaluate_hand(self, is_preview=False)
        return final_score

    def _init_defaults(self):
        self.bag = create_dice_bag()  # Create dice bag (mutable list for removal)
        self.hand = []  # Current hand of dice
        self.full_bag = [d.copy() for d in self.bag]  # Template of all owned dice
        self.rolls = []  # Current rolls: list of (die, value)
        self.held = [False] * NUM_DICE_IN_HAND  # Track held dice
        self.discard_selected = [False] * NUM_DICE_IN_HAND  # Track selected for discard
        self.rerolls_left = MAX_REROLLS if not DEBUG_UNLIMITED_REROLLS else -1  # FIXED: Custom flag
        self.rerolls_left_initial = self.rerolls_left
        self.discards_left = MAX_DISCARDS  # Discards per round
        self.discard_used_this_round = False  # Track if discard was used in the current hand's discard phase
        self.first_discard_this_turn = True
        self.hands_left = MAX_HANDS  # Hands (scores) per round
        self.coins = 0  # Chroma Coins for upgrades
        # **INSERT: Initialize round and blind (after coins or state vars)**
        self.current_round = 1  # Start at Stake 1; adjust if 0-based
        self.current_blind = 'Small'  # Or None if unset until blinds
        self.luchador_disable_active = False  # **INSERT: Luchador flag (start false)**
        self.extra_coins = 0  # For tracking bonus coins from gold and silver dice
        if DEBUG and DEBUG_INFINITE_COINS:
            self.coins = 999999  # Infinite coins for debug (large value to simulate infinity without breaking int ops)
        self.round_score = 0  # Score for current blind/round
        self.achievement_progress = 0  # FUTURE: Track for unlocks; ignore for now
        self.confirmed_hands_this_round = 0
        self.current_stake = 1  # Current stake level
        self.next_blind_number = 1
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
        self.mult = 1.0  # Base multiplier for buffs
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
        self.pending_prism_pack = False      # Set on current-blind win → free pack in next shop
        self.boon_hand_type_mult = {}        # e.g. {'Large Straight': 2.0} for the whole next blind

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
        self.final_discard_mult = 0  # NEW: For Acrobat Amulet (+2 on last discard)
        self.hand_play_counts = {ht: 0 for ht in data.HAND_TYPES}  # Track counts per hand type

    def update_hand_text(self):
        """Updates the texts showing current hand and modifier."""
        if self.is_discard_phase:
            # Show placeholders during discard phase
            self.current_hand_text = "Current Hand: Nothing (0 base) = 0 total"
            self.current_modifier_text = "Modifiers: None"
        else:
            held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
            if not held_rolls:
                self.current_hand_text = "Current Hand: Nothing (0 base) = 0 total"
                self.current_modifier_text = "Modifiers: None"
            else:
                hand_type, base_score, modifier_desc, final_score, charm_chips, charm_color_mult_add = self.get_hand_type_and_score(is_preview=True)
                self.current_hand_text = f"Current Hand: {hand_type} ({base_score} base + {charm_chips} charms) = {final_score} total"
                self.current_modifier_text = f"Modifiers: {modifier_desc}"

                # BLOCKED type warning
                if hasattr(self, 'intensified_disabled_type') and self.intensified_disabled_type:
                    self.current_hand_text = f"BLOCKED: {self.intensified_disabled_type} — " + self.current_hand_text
                    if hand_type == self.intensified_disabled_type:
                        self.current_hand_text += f" (0 score—adapt!)"

                # Dimmed warning
                if hasattr(self, 'intensified_dimmed_color') and self.intensified_dimmed_color:
                    affected = any(die['color'] == self.intensified_dimmed_color for die, _ in held_rolls)
                    if affected:
                        self.current_hand_text += f" — Dimmed {self.intensified_dimmed_color}: -20% values!"

                # Build modifier parts
                modifier_parts = []
                if modifier_desc and modifier_desc != "None":
                    modifier_parts.append(modifier_desc)

                stencil_mult = get_stencil_mult(self)  # ← fixed, no longer self.get_stencil_mult()
                if stencil_mult > 1.0:
                    modifier_parts.append(f"Stencil x{stencil_mult}")

                # Dagger
                has_active_dagger = any(charm['type'] == 'sacrifice_mult' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))
                if self.score_mult > 1.0:
                    dagger_text = f"Dagger x{self.score_mult:.1f}"
                    if has_active_dagger:
                        modifier_parts.append(dagger_text)
                    else:
                        modifier_parts.append(dagger_text + " (disabled)")

                # Prism Pack hand boost
                hand_boost = self.hand_multipliers.get(hand_type, 1.0)
                if hand_boost > 1.0:
                    modifier_parts.append(f"{hand_type} {hand_boost:.1f}x")

                if modifier_parts:
                    self.current_modifier_text = "Modifiers: " + " + ".join(modifier_parts)
                else:
                    self.current_modifier_text = ""

        # Pre-wrap for drawing
        self.current_hand_lines = wrap_text(self.small_font, self.current_hand_text, max_width=450)
        self.current_modifier_lines = wrap_text(self.small_font, self.current_modifier_text, max_width=450)

    def update_advantage_flag(self):
        self.has_advantage = any(charm['type'] == 'advantage_choice' for charm in self.equipped_charms)
        # if DEBUG:
            # print("Debug: Advantage flag updated to", self.has_advantage)

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
    
    def get_blind_target(self, stake=None, blind_type=None):
        """Blind targets: Forgiving early, aggressive late scaling to reward charms/prisms.
        Stake 8 boss ~25k. Defaults to current stake/blind if not provided.
        """
        stake = stake or getattr(self, 'current_stake', 1)  # Safe default
        blind_type = (blind_type or getattr(self, 'current_blind', 'small')).lower()  # Normalize & default
        
        base = 200
        growth_rate = 1.8
        
        if blind_type == 'small':
            mult = 1.0
        elif blind_type == 'big':
            mult = 1.5
        elif blind_type == 'boss':
            mult = 2.0
        else:
            raise ValueError(f"Unknown blind_type: {blind_type}")
        
        target = base * mult * (growth_rate ** (stake - 1))
        
        # Safe endless check
        if getattr(self, 'is_endless', False) and stake > 8:
            endless_bonus = 1 + 0.15 * (stake - 8)
            target *= endless_bonus
        
        # NEW: Apply D20 target_mult if set (intensify downside, e.g., x1.5)
        if hasattr(self, 'target_mult') and self.target_mult != 1.0:
            target *= self.target_mult
            # print(f"DEBUG: Intensified target: base {int(target / self.target_mult)} -> {int(target)} (x{self.target_mult})")  # TEMP
        
        return int(math.ceil(target))

    def advance_blind(self):
        """Advances to the next blind or stake and resets the dice bag."""
        # print("DEBUG: advance_blind called")  # Confirm entry
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

        # NEW: Reset Acrobat Amulet flag per blind
        self.final_discard_mult = 0

        # NEW: Reset Spellbook Scribe flag per blind
        if hasattr(self, '_scribe_used_this_blind'):
            delattr(self, '_scribe_used_this_blind')

        # NEW: Reset Necromancer's Needle flag per blind
        if hasattr(self, '_needle_used_this_blind'):
            delattr(self, '_needle_used_this_blind')

        # NEW: Reset Rune Recycler flag per blind (allows 1 per shop cycle)
        if hasattr(self, '_recycler_used_this_blind'):
            delattr(self, '_recycler_used_this_blind')

        # NEW: Clear intensify states
        for attr in ['intensified_disabled_type', 'intensified_dimmed_color', 'intensified_locked_die_idx', 'intensified_global_color_mult', 'target_mult']:
            if hasattr(self, attr):
                delattr(self, attr)
        if hasattr(self, 'temp_intensify_mult'):
            del self.temp_intensify_mult

        # In advance_blind (after resets)
        # FIXED: Decrement buff duration only if set (tier 5 'next 2')
        if hasattr(self, 'intensify_buff_duration') and self.intensify_buff_duration > 0:
            self.intensify_buff_duration -= 1
            if self.intensify_buff_duration > 0:
                # Carry pending_mult for remaining duration
                self.pending_buff_mult = 4.0  # e.g., tier 5 x4
                print(f"DEBUG: Buff duration now {self.intensify_buff_duration} - carried pending_mult: {self.pending_buff_mult}")
            else:
                print("DEBUG: Buff duration expired - cleared")
                del self.intensify_buff_duration
        else:
            print("DEBUG: No buff duration to decrement")  # TEMP: Confirm skip

        # NEW: Clear D20 intensify state post-blind
        if hasattr(self, 'target_mult'):
            del self.target_mult
        if hasattr(self, 'temp_intensify_mult'):
            del self.temp_intensify_mult
        if hasattr(self, 'from_d20_intensify'):
            del self.from_d20_intensify
        self.intensified_buff = None  # Already cleared in enter, but safety

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
        self.used_whirlwind_this_blind = False
        self.selecting_whirlwind_die = False
        self.whirlwind_target_index = -1
        self.hands_left = MAX_HANDS
        self.discards_left = MAX_DISCARDS
        self.used_uno_this_blind = False  # Reset for new blind
        self.extra_coins = 0
        self.turn_initialized = False  # Reset for new round/turn
        # In advance_blind (ChromaRoll.py ~line 1620, after other resets)
        self.bag[:] = [copy.deepcopy(d) for d in self.full_bag]  # Refill bag from owned template
        print(f"DEBUG: Bag after refill in advance_blind: {len(self.bag)}")  # Should be 25
        if self.current_boss_effect and self.current_boss_effect['name'] == 'Charm Eclipse':
            self.disabled_charms = list(range(len(self.equipped_charms)))  # Ensure all current charms disabled

        # FIXED: Set dummy rolls after refill to avoid fresh pull on new GameState
        self.rolls = [(None, 0) for _ in range(5)]  # Empty hand for new blind
        self.hand = [None] * 5  # Clear hand
        self.has_rolled = False  # Reset for new blind

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

        self.cloak_used_this_game = False  # Set in init if needed

        # NEW: Rune Recycler - Reuse one random tray rune per shop (once per shop flag)
        recycler_active = any(charm['type'] == 'rune_reuse' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))  # FIXED: self.disabled_charms
        if recycler_active and any(self.rune_tray) and not getattr(self, '_recycler_used_this_shop', False):
            # Pick random non-None rune
            non_none_runes = [r for r in self.rune_tray if r is not None]
            if non_none_runes:
                reused_rune = random.choice(non_none_runes).copy()
                # Remove from tray by reference (find slot)
                for slot, rune in enumerate(self.rune_tray):
                    if rune is reused_rune:  # Exact match (better than name for dups)
                        self.rune_tray[slot] = None
                        break
                # Add as special pack (index 9, after rune packs 6-8)
                reused_rune['cost'] = 0  # Free reuse
                self.pack_choices.append(reused_rune)
                self.available_packs.append(9)  # Special index for draw (handle in pack_rects buy)
                self.temp_message = f"Rune Recycler: Reused {reused_rune['name']} in shop!"
                self.temp_message_start = time.time()
                self._recycler_used_this_shop = True  # Set flag for this shop
            else:
                print("DEBUG: Rune Recycler - tray empty, skipped")  # TEMP
        else:
            if getattr(self, '_recycler_used_this_shop', False):
                delattr(self, '_recycler_used_this_shop')  # Reset flag on next shop

        # NEW: Preserve pending buffs across blinds (for "next 2")
        if hasattr(self, 'pending_buff_mult'):
            # Keep for next; decrement duration if multi-blind (e.g., for Crit Success)
            pass  # Already queued

        # DEBUG: Final hands after all
        # print(f"DEBUG: Final hands_left after advance_blind: {self.hands_left}")

    

    def new_turn(self):
        """Starts a new turn: draw hand, set to value 1, reset holds and rerolls."""
        # print("DEBUG: new_turn called")  # Confirm entry
        #  print("DEBUG: Calling new_turn - pulling dice")  # Log to see when triggered
        self.hand = self.draw_hand()
        self.turn_initialized = True
        self.rerolls_left = MAX_REROLLS
        self.rolls = [(die, 1) for die in self.hand]  # Start with value 1 (single pip)
        self.held = [False] * NUM_DICE_IN_HAND
        self.held_advantage = False
        self.advantage_value = None
        self.discard_selected = [False] * NUM_DICE_IN_HAND
        self.confirmed_hands_this_round = 0
        self.lucky_triggers = 0  # Reset to 0 each new turn/hand
        self.turn += 1
        self.discard_used_this_round = False  # Reset per hand
        # In new_turn (after self.discard_used_this_round = False)
        # NEW: Increment per-charm local turns for equipped charms
        # Increment per-charm local turns for equipped charms
        self.used_buy_boon_this_turn = False
        self.selecting_buy_boon_die = False
        self.buy_boon_target_index = -1
        self.buy_boon_shifts_left = 2
        self.buy_boon_up_rect = None
        self.buy_boon_down_rect = None
        self.buy_boon_confirm_rect = None
        self.is_discard_phase = True  # Reset to discard phase
        self.has_rolled = False  # No initial roll yet
        self.round_locket_coins = 0
        self.round_base_lucky_coins = 0
        self.used_disadvantage_this_turn = False
        self.selecting_disadvantage_die = False
        self.disadvantage_target_index = -1
        self.disadvantage_confirm_rect = None
        self.is_last_hand = (self.hands_left == 1)

        # NEW: Sorcerer's Surge - Roll fixed mult per turn for kinds
        for charm in self.equipped_charms:
            if charm['type'] == 'surge_random':
                charm['surge_mult'] = random.randint(charm['range'][0], charm['range'][1])  # 2-5
                self.temp_message = f"Sorcerer's Surge: +{charm['surge_mult']}x on kinds this turn!"
                self.temp_message_start = time.time()
                break  # Assume one charm

        self.update_hand_text()  # Update initial hand text (now reflects Turtle bonus on first hand)
        # In new_turn():
        if not self.turn_initialized:  # Fixed: self, not game
            # ... (existing turn setup)
            self.apply_boss_face_shuffle()
            self.turn_initialized = True
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
            
            # ADD: Clear Fate's Favor state on reroll (duplicate goes away, charm unusable this hand)
            if self.fates_advantage_index != -1:
                self.fates_advantage_index = -1
                self.fates_advantage_value = None
                self.held_fates_advantage = False
                self.selecting_fates_die = False  # Safety
                # print("Debug: Cleared Fate's Favor on reroll")

            # Animate cycling for non-held dice
            # Play roll sound here (at start of reroll)
            self.sfx_channel.play(self.roll_sound)
            for frame in range(ANIMATION_FRAMES):
                for i in range(len(self.rolls)):
                    if not self.held[i]:
                        # NEW: Skip locked die (Roll Harmony)
                        if hasattr(self, 'intensified_locked_die_idx') and i == self.intensified_locked_die_idx:
                            continue  # No roll, stays original value
                        die_temp = self.rolls[i][0]  # Temp var for the die
                        faces = self.boss_shuffled_faces.get(die_temp['id'], die_temp['faces']) if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Face Shuffle' else die_temp['faces']
                        self.rolls[i] = (die_temp, random.choice(faces))
                # ADDED: Animate advantage if not held
                if self.has_advantage and not self.held_advantage:
                    self.advantage_value = random.randint(1, 6)
                self.screen.fill(THEME['background'])  # Clear screen
                screens.draw_game_screen(self)
                pygame.display.flip()  # Update screen during animation
                time.sleep(ANIMATION_DELAY)
            
            # Final actual roll (the last frame is the real one)
            for i in range(len(self.rolls)):
                if not self.held[i]:
                    if hasattr(self, 'intensified_locked_die_idx') and i == self.intensified_locked_die_idx:
                        continue
                    die = self.rolls[i][0]
                    faces = self.boss_shuffled_faces.get(die['id'], die['faces']) if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Face Shuffle' else die['faces']
                    self.rolls[i] = (die, random.choice(faces))

            # ADDED: Roll advantage if not held_advantage (independent)
            if self.has_advantage and not self.held_advantage:
                self.advantage_value = random.randint(1, 6)
                # print("Debug: Rerolled advantage value:", self.advantage_value)

            if not DEBUG_UNLIMITED_REROLLS:  # FIXED: Custom flag
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
                    self.destroyed_dice.append(die.copy())
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
                # NEW: Check for stake 8 boss win before popup
                if self.current_blind == 'Boss' and self.current_stake == 8:
                    # Stake 8 boss beaten: Transition to end prompt (skip popup for now)
                    from states.end_prompt import EndPromptState  # type: ignore  # Lazy import to avoid circular load
                    end_prompt = EndPromptState(self)
                    self.state_machine.change_state(end_prompt)
                    return  # Exit early to avoid further logic
                # **INSERT: Clear Luchador flag after Boss completion**
                if self.current_blind == 'Boss':
                    self.luchador_disable_active = False
                    # print("DEBUG: Luchador flag cleared after boss")
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
                    remains_coins = self.hands_left + self.discards_left
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
                                    f"Discards left: {discards_dollars}\n"
                                    f"Interest: {interest_dollars}\n"
                                    f"{extras_line}"
                                    f"Coins gained: {total_dollars}")
                self.coins += total_coins
                self.coins = max(0, self.coins)  # Clamp to prevent negative coins from penalties
                self.show_popup = True
            elif self.hands_left > 0:
                self.new_turn()  # Next hand in round
            else:
                # NEW: Check Cloak on reroll exhaustion (parallel to score_and_new_turn)
                print(f"DEBUG: Reroll loss check - rerolls_left={self.rerolls_left}")  # TEMP
                cloak_active = any(charm['type'] == 'loss_prevent' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))
                print(f"DEBUG: Cloak active on reroll fail? {cloak_active}")  # TEMP
                if cloak_active and not getattr(self, 'cloak_used_this_game', False):
                    print("DEBUG: Cloak triggered on reroll fail!")  # TEMP
                    # Find and destroy Cloak
                    for idx, charm in enumerate(self.equipped_charms):
                        if charm['type'] == 'loss_prevent':
                            del self.equipped_charms[idx]
                            break
                    # Repeat blind: Reset round vars + full refill
                    # Repeat blind: Reset round vars + refill bag from template (preserve mods)
                    self.round_score = 0
                    self.hands_left = MAX_HANDS
                    self.discards_left = MAX_DISCARDS
                    self.extra_coins = 0
                    self.rerolls_left = MAX_REROLLS  # Reset rerolls too
                    # NEW: Refill current bag from modded template (no recreate)
                    self.bag = [d.copy() for d in self.full_bag]  # Preserves enhancements/pouch extras
                    self.temp_message = "Cloak of Cunning saved you! Repeating the blind."
                    self.temp_message_start = time.time()
                    self.cloak_used_this_game = True
                    self.new_turn()  # Fresh hand
                    print(f"DEBUG: Cloak reroll repeat - bag now={len(self.bag)}")  # TEMP
                    return
                else:
                    # Game over - transition to state
                    self.state_machine.change_state(GameOverState(self))


                if hasattr(self, 'intensified_locked_die_idx') and self.intensified_locked_die_idx >= 0:
                    self.temp_message = f"Die {self.intensified_locked_die_idx + 1} locked—no reroll!"
                    self.temp_message_start = time.time()

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
            # NEW: Acrobat Amulet - +2 mult if this was the final discard (only if equipped and not disabled)
            has_acrobat = False
            for idx, charm in enumerate(self.equipped_charms):
                if charm['name'] == 'Acrobat Amulet' and idx not in self.disabled_charms:
                    has_acrobat = True
                    break
            if has_acrobat and self.discards_left == 0:
                self.final_discard_mult = 2  # Or charm['value'] if you want to use the data.py value
                self.temp_message = "Acrobat Amulet: +2 mult on next score (final discard)!"
                self.temp_message_start = time.time()
            self.update_hand_text()
            self.discard_used_this_round = True
            # Trading Token: Destroy 1 die for coins on first discard
            if self.first_discard_this_turn and selected_count == 1:
                self.first_discard_this_turn = False
                for charm in self.equipped_charms:
                    if charm['type'] == 'discard_destroy_coin':
                        destroyed_die = self.hand[selected_indices[0]]  # The selected die
                        self.bag = [d for d in self.bag if d['id'] != destroyed_die['id']]
                        self.full_bag = [d for d in self.full_bag if d['id'] != destroyed_die['id']]
                        self.coins += charm['value']  # +3
                        self.temp_message = f"Destroyed die for +{charm['value']} coins!"
                        self.temp_message_start = time.time()
                        print(f"DEBUG: Trading Token destroy die ID {destroyed_die['id']} in hand{self.turn}, full_bag now {len(self.full_bag)}")
                        break  # Assume one charm
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
        # ALWAYS reset rerolls here—moved outside debug for normal play
        
        if self.show_popup:
            return  # Block actions during popup
        
        # Apply Hiker Hex per-die bonus if equipped and not disabled
        held_rolls = [(die, value) for i, (die, value) in enumerate(self.rolls) if self.held[i]]
        for idx, charm in enumerate(self.equipped_charms):
            if charm['type'] == 'die_bonus_perm' and idx not in self.disabled_charms:
                # print("Hiker Hex: Applying +4 to", len(held_rolls), "dice")
                for die, _ in held_rolls:
                    die_id = die.get('id')
                    # if die_id is None:
                        # print("Warning: Die missing 'id'")  # If no 'id', add unique IDs to all dice in init
                    for bag_die in self.full_bag:
                        if bag_die.get('id') == die_id:
                            current_bonus = bag_die.get('score_bonus', 0)
                            bag_die['score_bonus'] = current_bonus + charm['value']
                            # print(f"Updated bag die {die_id}: now {bag_die['score_bonus']}")
                            break  # No need to loop further
                break

        # score = self.calculate_score() # Old: Calculate score again
        score = final_score  # Use pre-calculated final score
        # print("Computed score:", score, "(base:", base_score, "chips:", charm_chips, "modifier:", 1 + charm_mono_add)  # Add this debug to see components
        self.round_score += score

        

        # NEW: Increment Ice Shard hands_played on score (per played hand, no reset)
        for charm in self.equipped_charms:
            if charm['name'] == 'Ice Shard':
                if 'hands_played' not in charm:
                    charm['hands_played'] = 0
                charm['hands_played'] += 1

        # Apply Ice Shard decay to this hand's score
        for charm in self.equipped_charms:
            if charm['name'] == 'Ice Shard':
                hands_played = charm['hands_played']
                decay_bonus = max(0, charm['start'] - (charm['decay'] * (hands_played - 1)))
                self.round_score += decay_bonus

        # NEW: Increment Loyalty Luck local_turns on score (per played turn)
        for charm in self.equipped_charms:
            if charm['name'] == 'Loyalty Luck':
                if 'local_turns' not in charm:
                    charm['local_turns'] = 1  # Safety (shouldn't hit)
                else:
                    charm['local_turns'] += 1
                # print(f"DEBUG: Loyalty Luck local_turns now {charm['local_turns']} after score")  # Temp—remove after

        # Apply Square Sphere permanent bonus on charm if equipped, not disabled, and exactly 4 dice scored
        for idx, charm in enumerate(self.equipped_charms):
            if charm['name'] == 'Square Sphere' and idx not in self.disabled_charms:
                if len(held_rolls) == 4:
                    charm['permanent_bonus'] = charm.get('permanent_bonus', 0) + charm['value']
                    # print("Square Sphere charm bonus applied (4 dice): now", charm['permanent_bonus'])  # Debug
                break

        for idx, charm in enumerate(self.equipped_charms):
            if charm['type'] == 'score_conditional' and idx not in self.disabled_charms:
                self.permanent_score_bonus = getattr(self, 'permanent_score_bonus', 0) + charm['value']
                # print("Square Sphere permanent bonus applied: now", self.permanent_score_bonus)  # Debug, remove later
                break

        # Apply Lucky Labyrinth permanent bonus on charm if equipped and triggers >0
        for idx, charm in enumerate(self.equipped_charms):
            if charm['name'] == 'Lucky Labyrinth' and idx not in self.disabled_charms:
                triggers = self.lucky_triggers
                if triggers > 0:
                    charm['permanent_bonus'] = charm.get('permanent_bonus', 0.0) + (charm['value'] * triggers)
                    # print("Lucky Labyrinth permanent bonus applied:", charm['permanent_bonus'])  # Debug, remove later
                break

        # Accumulate sound for lucky triggers but don't add coins yet
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

        # Accumulate extra coins from Gold/Silver but don't add to self.coins yet
        gold_silver_coins = 0
        for i, (die, _) in enumerate(self.rolls):
            if die['color'] == 'Gold' and self.held[i]:
                self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                gold_silver_coins += 1
            elif die['color'] == 'Silver' and not self.held[i]:
                self.sfx_channel.play(self.coin_sound)  # Play per coin gain
                gold_silver_coins += 1
        # Add extra coin bonuses from charms
        charm_extra_coins = 0
        for charm in self.equipped_charms:
            if charm['type'] == 'extra_coin_bonus':
                for j, (die, _) in enumerate(self.rolls):
                    if die['color'] == charm['color']:
                        if (charm['color'] == 'Gold' and self.held[j]) or (charm['color'] == 'Silver' and not self.held[j]):
                            charm_extra_coins += charm['value']
        self.extra_coins += gold_silver_coins + charm_extra_coins  # Accumulate in extra_coins for now

        # Compute dynamic Glass break chance and penalty from charms
        glass_break_chance = 0.25
        glass_break_penalty = 0
        for charm in self.equipped_charms:
            if charm['type'] == 'glass_mod':
                glass_break_chance = charm['break_chance']
                glass_break_penalty = charm['break_penalty']

        # Main break loop (with Break Buffer mod):
        for i, (die, value) in enumerate(self.rolls):  # Use value here (scored face)
            if die['color'] == 'Glass' and self.held[i]:
                # NEW: Check for Break Buffer active (only on 1-3, 33% chance)
                has_break_buffer = any(c['type'] == 'break_reduce' and idx not in self.disabled_charms for idx, c in enumerate(self.equipped_charms))
                effective_chance = glass_break_chance if not has_break_buffer else (0.33 if value <= 3 else 0.0)
                
                if random.random() < effective_chance:
                    print(f"DEBUG: Breaking die '{die['color']}' ID '{die['id']}' held {self.held[i]} RNG {random.random()}, full_bag now {len(self.full_bag)}")  # Keep for debug
                    self.sfx_channel.play(self.break_sound)
                    # FIXED: Temp - bag only
                    self.bag = [d for d in self.bag if d['id'] != die['id']]
                    self.destroyed_dice.append(die.copy())
                    # self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]  # Comment/remove
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

            # Mime retrigger break loop (same, with Break Buffer mod):
            for i, (die, value) in enumerate(self.rolls):  # Use value here too
                if die['color'] == 'Glass' and self.held[i]:
                    # NEW: Reuse Break Buffer check (respects mod on retrigger)
                    has_break_buffer = any(c['type'] == 'break_reduce' and idx not in self.disabled_charms for idx, c in enumerate(self.equipped_charms))
                    effective_chance = glass_break_chance if not has_break_buffer else (0.33 if value <= 3 else 0.0)
                    
                    if random.random() < effective_chance:
                        print(f"DEBUG: Mime Breaking die '{die['color']}' ID '{die['id']}'...")  # Debug
                        self.sfx_channel.play(self.break_sound)
                        self.bag = [d for d in self.bag if d['id'] != die['id']]
                        self.destroyed_dice.append(die.copy())
                        # self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]  # Comment/remove
                        self.coins -= glass_break_penalty
                        self.broken_dice.append(i)
                        self.break_effect_start = time.time()

            # NEW: Synergy Scroll - Retrigger enhancements on held dice
            synergy_equipped = any(charm['name'] == 'Synergy Scroll' and idx not in self.disabled_charms 
                                for idx, charm in enumerate(self.equipped_charms))

            if synergy_equipped:
                synergy_score_delta = 0
                synergy_coin_delta = 0
                for i, (die, _) in enumerate(self.rolls):
                    if self.held[i]:
                        delta_score, delta_coins = self.apply_enhancement_retrigger(die, i)
                        synergy_score_delta += delta_score
                        synergy_coin_delta += delta_coins
                
                score += synergy_score_delta  # Add to this hand's score
                self.extra_coins += synergy_coin_delta  # Flows to total_coins/popup

        self.hands_left -= 1
        print(f"DEBUG: full_bag before score hand{self.turn}: {len(self.full_bag)}")  # Per hand
        self.hands_left = max(0, self.hands_left)  # Clamp to prevent negative (after decrement)
        # Note: Turtle decay applied in GameState.enter (blind start hook) for net adjustment
    
        if self.round_score >= self.get_blind_target():
            # Compute dynamic interest max from charms
            dynamic_interest_max = INTEREST_MAX
            for charm in self.equipped_charms:
                if charm['type'] == 'interest_max_bonus':
                    dynamic_interest_max += charm['value']
            
            # Compute base interest
            base_interest = min(self.coins, dynamic_interest_max) // INTEREST_RATE

            # Compute interest bonus from charms (e.g., Interest Idol adds +value per 10 coins)
            interest_bonus = 0
            capped_coins = min(self.coins, dynamic_interest_max)  # Reuse the cap
            for charm in self.equipped_charms:
                if charm['type'] == 'interest_bonus':
                    interest_bonus += charm['value'] * (capped_coins // INTEREST_RATE)  # Now capped!
            
            # Total interest including bonus
            interest = base_interest + interest_bonus

            # NEW: Unified rune gains collection (after interest, before remains_coins)
            rune_gains_lines = []  # Collect per-rune strings
            total_rune_coins = 0

            # Loop for coin-granting runes
            for idx, charm in enumerate(self.equipped_charms):
                if idx in self.disabled_charms:
                    continue
                rune_gain = 0
                gain_desc = ""
                
                if charm['type'] == 'coin_per_face':  # Cloud Cube
                    bag_size = len(self.full_bag)
                    rune_gain = (bag_size // 6) * charm['value']  # E.g., 25//6=4 *1=4
                    gain_desc = f"{bag_size} dice"
                
                elif charm['type'] == 'coin_scaling':  # Rocket Rune
                    defeated = charm.get('boss_defeated', 0)
                    rune_gain = charm['base'] + (defeated * charm['boss'])  # E.g., 1 + 2*1=3
                    gain_desc = f"base + {defeated} bosses"
                
                # Add future ones here, e.g.:
                # elif charm['type'] == 'coin_per_color':
                #     green_count = sum(1 for die, _ in held_rolls if die['color'] == 'Green')
                #     rune_gain = green_count * charm['value']
                #     gain_desc = f"{green_count} greens"
                
                if rune_gain > 0:
                    total_rune_coins += rune_gain
                    rune_gains_lines.append(f"{charm['name']}: ${rune_gain} ({gain_desc})")
                    # print(f"{charm['name']}: +{rune_gain} coins ({gain_desc})")  # Debug

            # NEW: Boss defeat increment for Rocket (after gain calc, for next time)
            if self.current_blind == 'Boss':
                for charm in self.equipped_charms:
                    if charm['type'] == 'coin_scaling':
                        charm['boss_defeated'] = charm.get('boss_defeated', 0) + 1
                        # print(f"Rocket Rune: Boss #{charm['boss_defeated']} defeated—next gain +{charm['boss']}")
                        break

            if self.green_pouch_active:
                remains_coins = (self.hands_left * 2) + (self.discards_left * 1)
                hands_dollars = '$$' * self.hands_left
                discards_dollars = '$' * self.discards_left
                interest_dollars = ''
            else:
                remains_coins = self.hands_left + self.discards_left
                hands_dollars = '$' * self.hands_left
                discards_dollars = '$' * self.discards_left
                interest_dollars = '$' * interest if interest >= 0 else str(interest)
            
            # Accumulate Luck's Locket coins for this hand but don't add to self.coins yet
            luck_locket_coins_this_hand = 0
            for charm in self.equipped_charms:
                if charm['name'] == "Luck's Locket" and self.lucky_triggers > 0:
                    luck_locket_coins_this_hand += charm['value'] * self.lucky_triggers
            self.round_locket_coins += luck_locket_coins_this_hand

            # Accumulate base lucky coins for this hand but don't add to self.coins yet
            base_lucky_coins_this_hand = self.lucky_triggers * 1
            self.round_base_lucky_coins += base_lucky_coins_this_hand

            # Visual representations (standardized to '$' * coins) - moved before total_coins for dollars only
            luck_locket_dollars = '$' * self.round_locket_coins if self.round_locket_coins > 0 else ''
            luck_locket_line = f"Luck Bonus: {luck_locket_dollars}\n" if self.round_locket_coins > 0 else ""
            
            base_lucky_dollars = '$' * self.round_base_lucky_coins if self.round_base_lucky_coins > 0 else ''
            base_lucky_line = f"Lucky Coins: {base_lucky_dollars}\n" if self.round_base_lucky_coins > 0 else ""
            
            extras_dollars = '$' * self.extra_coins if self.extra_coins > 0 else ''
            extras_line = f"Extras: {extras_dollars}\n" if self.extra_coins > 0 else ""

            # NEW: Rune block for popup
            rune_block = ""
            if rune_gains_lines:
                rune_block = "Rune Gains:\n" + "\n".join(rune_gains_lines) + "\n"

            
            # NEW: Echo Ember coins (unused discards at end)
            echo_ember_bonus = 0
            for charm in self.equipped_charms:
                if charm['type'] == 'coin_per_discard' and idx not in self.disabled_charms:
                    echo_ember_bonus += charm['value'] * self.discards_left  # Unused discards
            echo_ember_line = f"Echo Coins: ${echo_ember_bonus}\n" if echo_ember_bonus > 0 else ""

            # NEW: Gift Glyph sell bonus (after rune gains, before popup)
            gift_bonus = 0
            for idx, charm in enumerate(self.equipped_charms):
                if charm['type'] == 'sell_bonus' and idx not in self.disabled_charms:
                    for eq_charm in self.equipped_charms:  # Loop all equipped (including self)
                        eq_charm['sell_value'] = eq_charm.get('sell_value', eq_charm['cost']) + charm['value']
                        gift_bonus += charm['value']  # Track for popup if wanted
                    # print(f"Gift Glyph: +{charm['value']} sell to {len(self.equipped_charms)} charms")  # Debug, remove later
                    break

            coin_gen_bonus = 0
            for idx, charm in enumerate(self.equipped_charms):
                if charm['type'] == 'coin_gen' and idx not in self.disabled_charms:
                    unused_hands = self.hands_left # Unused at round end
                    coin_gen_bonus += charm['value'] * unused_hands

            # For popup (add to dollar line):
            coin_gen_dollars = '$' * coin_gen_bonus if coin_gen_bonus > 0 else ''
            coin_gen_line = f"Echo Coins: {coin_gen_dollars}\n" if coin_gen_bonus > 0 else ""

            # Total coins including accumulated Luck's Locket, base lucky, and runes
            total_coins = remains_coins + interest + self.extra_coins + self.round_locket_coins + self.round_base_lucky_coins + total_rune_coins + coin_gen_bonus + echo_ember_bonus

            total_dollars = '$' * abs(total_coins) if total_coins >= 0 else str(total_coins)

            # ADD: Clear Fate's Favor after scoring (advantage goes away for next hand)
            if self.fates_advantage_index != -1:
                self.fates_advantage_index = -1
                self.fates_advantage_value = None
                self.held_fates_advantage = False
                self.selecting_fates_die = False  # Safety
                # print("Debug: Cleared Fate's Favor after scoring")
            
            # NEW: Set flag for final boss win and award coins/clear accumulators
            final_boss_win = (self.current_blind == 'Boss' and self.current_stake == 8)
            self.coins += total_coins  # Add all coins at the end
            self.coins = max(0, self.coins)  # Clamp to prevent negative coins from penalties
            self.extra_coins = 0
            self.round_locket_coins = 0
            self.round_base_lucky_coins = 0
            self.lucky_triggers = 0
            self.blind_won = True  # Set win flag if not already

            # In win block (after self.coins += total_coins)
            if hasattr(self, 'intensified_buff') and self.intensified_buff:
                buff = self.intensified_buff
                # Apply immediate (e.g., coins)
                self.coins += buff.get('coins', 0)
                # Queue pack for next shop
                if buff.get('free_pack'):
                    self.pending_free_pack = buff['free_pack']  # Add to defaults; consume in generate_shop
                # Temp mults (store for next blind/hand)
                if 'mult_this' in buff:
                    self.temp_intensified_mult = buff['mult_this']  # Apply in calculate_score
                if 'mult_next' in buff:
                    self.pending_buff_mult = buff['mult_next']  # Set in advance_blind
                if 'mult_next_2' in buff:
                    self.pending_buff_mult = buff['mult_next_2']
                    self.intensify_buff_duration = 2  # Counter; decrement in advance_blind
                # NEW: Queue "next hand" (e.g., Hue Dimming 2x on first hand of next blind)
                if 'mult_next_hand' in buff:
                    self.pending_buff_mult = buff['mult_next_hand']  # e.g., 2.0; overrides if multiple
                if buff.get('extra_discard'):
                    self.discards_left += buff.get('extra_discard')
                if 'mult_next' in buff and hasattr(self, 'intensified_disabled_type') and self.intensified_disabled_type:
                    self.pending_type_mult = {self.intensified_disabled_type: buff['mult_next']}  # e.g., {'Large Straight': 2.0}
                if buff.get('extra_reroll'):
                    self.rerolls_left += buff.get('extra_reroll')
                    print(f"DEBUG: Added {buff.get('extra_reroll', 0)} reroll(s) from {buff.get('name', 'Unknown')}")  # TEMP
                del self.intensified_buff  # Clear
                print(f"DEBUG: Rewarded {buff.get('name', 'Unknown')}: {buff}")  # TEMP: Safe name access

            # NEW: Increment Turtle rounds_passed on round win (early, to avoid exits; for next enter)
            # print("DEBUG: Win block reached—checking Turtle increment")
            turtle_incremented = False
            for charm in self.equipped_charms:
                if charm['type'] == 'hands_decay':
                    old_passed = charm.get('rounds_passed', 0)
                    charm['rounds_passed'] = old_passed + 1
                    # print(f"Turtle Token WIN: Incremented from {old_passed} to {charm['rounds_passed']} for next round")
                    turtle_incremented = True
                    break
            # if not turtle_incremented:
                # print("DEBUG: No Turtle Token found for increment (not equipped?)")
            
            # **INSERT: Clear Luchador flag after blind completion**
            if self.current_blind == 'Boss':
                self.luchador_disable_active = False
                # print("DEBUG: Luchador flag cleared after boss")

            if final_boss_win:
                # Skip popup, direct to prompt
                from states.end_prompt import EndPromptState  # type: ignore
                end_prompt = EndPromptState(self)
                self.state_machine.change_state(end_prompt)
                return  # Exit early
            
            # Normal win: Show popup
            self.popup_message = (f"{self.current_blind} Blind Beaten! Score: {self.round_score}/{int(self.get_blind_target())}\n"
                                f"Hands left: {hands_dollars}\n"
                                f"Discards Left: {discards_dollars}\n"
                                f"Interest: {interest_dollars}\n"
                                f"{extras_line}"
                                f"{luck_locket_line}"  # Luck's Locket accumulated
                                f"{base_lucky_line}"  # Base 'Lucky' accumulated
                                f"{rune_block}"  # NEW: Rune gains block
                                f"{coin_gen_line}"  # Coin Generation charms
                                f"{echo_ember_line}"  # NEW: Echo Ember from unused discards
                                f"Coins gained: {total_dollars}")
            self.show_popup = True
        elif self.hands_left > 0:
            self.new_turn()  # Next hand in round
        else:
            # NEW: Cloak of Cunning - Prevent loss once per game, repeat blind
            cloak_active = any(charm['type'] == 'loss_prevent' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))
            if cloak_active and not getattr(self, 'cloak_used_this_game', False):
                print("DEBUG: Cloak triggered on score fail!")  # TEMP
                # Find and destroy Cloak
                for idx, charm in enumerate(self.equipped_charms):
                    if charm['type'] == 'loss_prevent':
                        del self.equipped_charms[idx]
                        break
                # Repeat blind: Reset round vars + full refill
                # Repeat blind: Reset round vars + refill bag from template (preserve mods)
                self.round_score = 0
                self.hands_left = MAX_HANDS
                self.discards_left = MAX_DISCARDS
                self.extra_coins = 0
                self.rerolls_left = MAX_REROLLS  # Reset rerolls too
                # NEW: Refill current bag from modded template (no recreate)
                self.bag = [d.copy() for d in self.full_bag]  # Preserves enhancements/pouch extras
                self.temp_message = "Cloak of Cunning saved you! Repeating the blind."
                self.temp_message_start = time.time()
                self.cloak_used_this_game = True
                self.new_turn()  # Fresh hand
                print(f"DEBUG: Cloak score repeat - bag now={len(self.bag)}")  # TEMP
                return  # No over
            else:
                # Game over - transition to state
                self.state_machine.change_state(GameOverState(self))

        if hasattr(self, 'intensified_buff') and self.intensified_buff is not None:
            buff = self.intensified_buff
            self.mult += buff.get('mult', 0)  # e.g., +2x
            # Add other buff effects (e.g., self.coins += buff.get('coins', 0))
            print(f"DEBUG: Applied intensified buff: {buff}")  # TEMP: Confirm on use
            del self.intensified_buff  # Clear after apply
        else:
            print("DEBUG: No intensified buff to apply")  # TEMP: Confirm skip

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
        # print(f"Debug: toggle_hold {index} - before flip: held[{index}] = {self.held[index]}, held_fates_advantage = {self.held_fates_advantage}")  # Debug swap
        self.held[index] = not self.held[index]
        # print(f"Debug: toggle_hold {index} - after flip: held[{index}] = {self.held[index]}")
        
        # Existing amulet exclusion
        if index == 2 and self.held[index] and self.has_advantage and self.held_advantage:
            self.held_advantage = False
            # print("Debug: Unheld amulet advantage due to holding original - held_advantage =", self.held_advantage)
        
        # For Fate's Favor: Flip original and unhold advantage if held
        if index == self.fates_advantage_index:
            if self.held[index] and self.held_fates_advantage:
                self.held_fates_advantage = False
                # print(f"Debug: Unheld Fate's advantage due to holding original - held_fates_advantage = {self.held_fates_advantage}")
            elif not self.held[index] and self.held_fates_advantage:
                self.held_fates_advantage = False  # Optional: Unhold advantage if unholding original
                # print(f"Debug: Unheld Fate's advantage due to unholding original - held_fates_advantage = {self.held_fates_advantage}")
        
        self.update_hand_text()
        # print(f"Debug: toggle_hold {index} - after update_hand_text: held[{index}] = {self.held[index]}, held_fates_advantage = {self.held_fates_advantage}")  # Check no revert
    
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

    def check_equipped_charms(self):
        self.has_advantage = any(charm['type'] == 'advantage_choice' for charm in self.equipped_charms)
        # Call this after equipping or loading charms

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
                # print(f"DEBUG: Hover on {charm['name']} - building tooltip")  # Temp debug—remove after
                
                if charm['name'] == 'Enhance Elixir':
                    # Compute total like in get_hand_type_and_score
                    held_rolls = [(die, value) for j, (die, value) in enumerate(self.game.rolls) if self.game.held[j]]
                    total_enhancements = sum(len(die.get('enhancements', [])) for die, _ in held_rolls)
                    mult_add = charm['value'] * total_enhancements  # 0.25 * 5 = 1.25
                    tooltip_text += f"\n(Preview: +{mult_add} ({total_enhancements} enhancements))"
                if charm['type'] == 'sacrifice_mult':
                    tooltip_text += f" (Current mult: x{self.score_mult})"
                    if self.score_mult < 10.0:
                        tooltip_text += " (max x10)"
                elif charm['type'] == 'empty_slot_mult':
                    current_mult = self.get_stencil_mult()
                    tooltip_text += f" (Current: x{current_mult})"
                
                # Loyalty Luck tooltip (inside hover if)
                # print(f"DEBUG: Charm name exact: '{charm['name']}'")  # Temp—remove after
                if charm['name'] == 'Loyalty Luck':
                    local_turn = charm.get('local_turns', 0)
                    every = charm.get('every', 6)
                    if local_turn % every == 0:
                        tooltip_text += f"\nActive: +{charm['value']} mult this turn"
                    else:
                        turns_left = every - (local_turn % every)
                        tooltip_text += f"\nNext in {turns_left} turns"

                # NEW: Set rect for UNO if equipped
                if charm['name'] == 'UNO Draw 2':
                    self.uno_charm_rect = rect
                    # print(f"DEBUG: UNO rect set at {rect} (slot {i})")  # Confirm set
                
                
                
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
        # NEW: Reset UNO Skip flag on full restart (one per run)
        self.uno_skip_used = False
        self.turn_initialized = False  # Reset for new round/turn
        self.current_stake = 1
        self.cloak_used_this_game = False  # NEW: Reset on full restart
        self.destroyed_dice = []  # NEW: Clear on full restart
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
        # NEW: Reset Turtle rounds_passed on full restart
        for charm in self.equipped_charms:
            if charm['type'] == 'hands_decay':
                charm['rounds_passed'] = 0
                break

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
        
        # Filter pool to exclude owned (as before)
        available_pool = [c for c in data.CHARMS_POOL if c['name'] not in [e['name'] for e in self.equipped_charms]]
        
        # ADD: Gambler's Grimoire - add free random rune if not used this shop
        active_charms = [c for idx, c in enumerate(self.equipped_charms) if idx not in self.disabled_charms]
        # print(f"Debug: generate_shop - active_charms = {[c['name'] for c in active_charms]}, used_rune_cast_this_shop = {self.used_rune_cast_this_shop}")

        if any(c['type'] == 'rune_cast' for c in active_charms) and not self.used_rune_cast_this_shop:
            if hasattr(data, 'MYSTIC_RUNES') and data.MYSTIC_RUNES:
                random_rune = random.choice(data.MYSTIC_RUNES).copy()
                random_rune['cost'] = 0
                random_rune['free_grimoire'] = True
                self.shop_charms.append(random_rune)
                self.used_rune_cast_this_shop = True
                # print(f"Debug: Added free random rune '{random_rune['name']}' from Gambler's Grimoire")
                
                # Store for bottom draw and remove from shop_charms to avoid top draw
                self.grimoire_rune = random_rune
                self.shop_charms.remove(random_rune)
                # print("Debug: Stored grimoire_rune for bottom draw = ", self.grimoire_rune['name'])
                # print("Debug: Removed grimoire_rune from shop_charms - now = ", [c['name'] for c in self.shop_charms])
            
        # FIXED: Add pending free pack *before* random (ensures append)
        if hasattr(self, 'pending_free_pack'):
            pack_id = 0 if self.pending_free_pack == 'prism' else 3  # Basic Prism or Dice
            self.available_packs.append(pack_id)
            print(f"DEBUG: Added free {self.pending_free_pack} pack (ID {pack_id}) - available_packs now: {self.available_packs}")
            del self.pending_free_pack

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
        print(f"DEBUG: Adding rune to tray: {rune['name']}")  # Add
        for k in range(len(self.rune_tray)):
            if self.rune_tray[k] is None:
                self.rune_tray[k] = copy.deepcopy(rune)
                print(f"DEBUG: Added to slot {k}")  # Add
                return True
        self.temp_message = "Rune tray full - discard a rune first."
        print("DEBUG: Tray full – skipped")  # Add
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
            

    def apply_rune_effect(self, rune, die_list=None):
        if die_list is None:
            die_list = []
        name = rune['name']
        max_dice = rune.get('max_dice', 0)
        # Bypass max_dice limit in debug mode
        if not (DEBUG and max_dice > 0) and max_dice > 0 and len(die_list) == 0:
            self.temp_message = f"Select at least 1 die for {name}!"
            return
        if not (DEBUG and max_dice > 0) and len(die_list) > max_dice:
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
                    print(f"DEBUG: Sacrifice remove die ID {die['id']}, full_bag now {len(self.full_bag)}")
                # NEW: Save to destroyed for Needle
                self.destroyed_dice.append(die.copy())

        elif name == 'Mystic Transmute Rune':
            if len(die_list) != 2:
                self.temp_message = "Select exactly 2 dice!"
                return
            target, source = die_list  # First selected = target (#1), second = source (#2)
            target['color'] = source['color']
            target['faces'] = source['faces'][:]
            if 'enhancements' not in target:
                target['enhancements'] = []  # Initialize if missing
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
        """Force update bag visuals after rune apply; sync mods to full_bag without length loss."""
        # FIXED: One-way sync: Update full_bag with bag mods (by ID), preserve length/add if needed
        for mod_die in self.bag:  # Loop modded bag items
            die_id = mod_die.get('id')
            if die_id:  # Skip if no ID
                matched = False
                for full_idx, full_die in enumerate(self.full_bag):
                    if full_die.get('id') == die_id:
                        # Copy mods to full_bag (deep for nested lists like faces/enh)
                        self.full_bag[full_idx] = copy.deepcopy(mod_die)
                        matched = True
                        break
                if not matched:  # New item in bag? Add it (e.g., future rune add)
                    self.full_bag.append(copy.deepcopy(mod_die))
                    print(f"DEBUG: Added new die ID {die_id} to full_bag after rune")  # Optional
        # No remove: Ignore "missing" on-screen rolls—full_bag stays 25
        print(f"DEBUG: full_bag after one-way sync: {len(self.full_bag)} (mods propagated)")  # Optional debug
        # If in shop/game, force redraw (state will handle in next draw call)

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
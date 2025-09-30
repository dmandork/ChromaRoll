from cmath import rect
import math  # For ceil in bag rows
import random  # For rolling dice and drawing from bag
import pygame  # For graphics and input handling
import sys  # For exiting the game
import time  # For animation delays
import copy
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller temp path
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Debug flag: Set to True to force specific colors for testing (overrides random draw) and enable unlimited rerolls
DEBUG = True
DEBUG_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # Example: All different colors for rainbow testing
# DEBUG_COLORS = ['Glass', 'Glass', 'Glass', 'Glass', 'Glass']  # Example: All Glass colors for break testing
# DEBUG_COLORS = ['Gold', 'Gold', 'Gold', 'Silver', 'Silver']  # Example: All Gold and Silver colors for extra coin testing

# Define constants
COLORS = {'Red': (255, 0, 0), 'Blue': (0, 0, 255), 'Green': (0, 255, 0),
          'Purple': (128, 0, 128), 'Yellow': (255, 255, 0),
          'Gold': (255, 215, 0), 'Silver': (192, 192, 192), 'Glass': (173, 216, 230),
          'Rainbow': (255, 255, 255),  # Placeholder for cycling animation
          'Black': (0, 0, 0)
          }  # RGB values for colors
BASE_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # For base dice pack icons
SPECIAL_COLORS = ['Gold', 'Silver', 'Glass', 'Rainbow']  # For the special pack choices
CHARM_BG_COLORS = {
    'Dagger Charm': (200, 0, 0),  # Red for danger
    'Full House Party Charm': (180, 140, 100),  # Light brown
    'Reroll Recycler Charm': COLORS['Green'],
    'Fragile Fortune Charm': COLORS['Glass'],  # Light blue
    'Basic Charm': (200, 200, 200),  # Light gray
    'Zany Charm': (150, 50, 150),  # Purple for whimsy
    'Mad Charm': (100, 200, 100),  # Green for envy
    'Crazy Charm': (255, 100, 0),  # Orange for chaotic
    'Droll Charm': (100, 100, 200),  # Blue for calm
    'Sly Charm': (50, 150, 50),  # Dark green for cunning
    'Wily Charm': (200, 150, 50),  # Goldish for value
    'Clever Charm': (150, 150, 50),  # Yellow-brown for intellect
    'Devious Charm': (100, 0, 100),  # Dark purple for trickery
    'Half Charm': (0, 100, 200),  # Cool blue for low
    'Stencil Charm': (50, 50, 50),  # Dark gray for empty
    'Four Fingers Charm': (210, 180, 140),  # Light tan for hand
    'Mime Charm': (150, 150, 150),  # Medium gray for invisible
    # Color-specific charms omitted - fallback to white or their die color
}
THEME = {
    'background': (10, 50, 10),  # Deep casino felt green (darker than your (0, 80, 0) for mood)
    'panel_bg': (20, 70, 20),  # Slightly lighter green for panels (less flat)
    'button_bg': (80, 120, 80),  # Muted green buttons (with gold hover below)
    'button_hover': (120, 180, 50),  # Glowy green-gold on hover
    'border': (0, 0, 0),  # Black borders (keep or change to (50, 50, 50) for softer gray)
    'text': (220, 220, 220),  # Off-white text for readability on dark bg
    'highlight': (200, 160, 0),  # Warm gold for holds/coins (brighter than your (255, 215, 0) for retro shine)
    'font_main_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Pixel for main
    'font_main_size': 36,
    'font_small_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Vintage for small
    'font_small_size': 24,
    'font_tiny_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Same for tiny, or mix
    'font_tiny_size': 20,
}
DICE_DESCRIPTIONS = {
    'Red': 'Add 1 Red Die',
    'Blue': 'Add 1 Blue Die',
    'Green': 'Add 1 Green Die',
    'Purple': 'Add 1 Purple Die',
    'Yellow': 'Add 1 Yellow Die',
    'Gold': 'Gold Die: +1 coin when held in score',
    'Silver': 'Silver Die: +1 coin when not held in score',
    'Glass': 'Glass Die: x4 mult when held, 25% chance to break',
    'Rainbow': 'Rainbow Die: Acts as wild for color bonuses (mono & rainbow)'}  # Descriptions for each die color
DICE_PER_COLOR = 5  # 5 dice per color, totaling 25
SPLASH_DURATION_PAN = 4.0  # Seconds to pan up
SPLASH_BUTTON_WIDTH = 200
SPLASH_BUTTON_HEIGHT = 50
SPLASH_BUTTON_SPACING = 20
SPLASH_DURATION_HOLD = 1.0  # Seconds to hold at top
SPLASH_DURATION_ZOOM_OUT = 4.0  # Full duration for seamless zoom
SPLASH_INITIAL_ZOOM = 2.0  # Start zoomed (bottom focus)
SPLASH_FINAL_ZOOM = 1.0  # End at fit
SPLASH_SKIP_KEYS = [pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]  # Keys to skip
SPLASH_EASING = 'out_cubic'  # 'in_cubic' for slow start, 'out_cubic' for slow end—tweak
NUM_DICE_IN_HAND = 5  # Draw 5 dice per turn
MAX_REROLLS = 2  # Initial roll + 2 rerolls = 3 total rolls per turn (ignored in debug)
DICE_FACES = [1, 2, 3, 4, 5, 6]  # Standard faces; modifiable later
INITIAL_WIDTH, INITIAL_HEIGHT = 1024, 600 # Or try 1280, 720 for a 16:9 aspect ratio
DIE_SIZE = 100  # Size of each die square
HELD_DIE_SCALE = 0.9  # Scale factor for held dice (10% smaller)
DOT_RADIUS = 10  # Size of dots on dice
BUTTON_WIDTH, BUTTON_HEIGHT = 150, 50  # Button size
SMALL_DIE_SIZE = 20  # Size for bag visual squares
SMALL_DIE_SPACING = 5  # Spacing for bag visual
ANIMATION_FRAMES = 20  # Number of frames for roll animation
ANIMATION_DELAY = 0.025  # Delay between animation frames
DIE_BORDER_RADIUS = 20  # Radius for rounded corners on dice
SMALL_DIE_BORDER_RADIUS = 5  # Radius for rounded corners on small bag dice
MAX_HANDS = 4  # Base hands (scores) per round
MAX_DISCARDS = 3  # Base discards per round
# DISCARD_PER_USE = 2  # Max dice to discard per use (1-2)
# TABLE_GREEN = (0, 100, 0)  # Card table green background
BASE_TARGETS = {'Small': 100, 'Big': 200, 'Boss': 300}  # Base blind targets (scale by stake)
POPUP_WIDTH, POPUP_HEIGHT = 300, 300  # Enlarged popup size for beaten blind
POPUP_ANIMATION_DELAY = 0.5  # Delay for $ animation in popup
CHARM_SIZE = 100  # Size for charm icons
TOOLTIP_PADDING = 10
CHARM_BOX_WIDTH = 140
CHARM_BOX_HEIGHT = 140
CHARM_SPACING = 20
CHARM_DIE_SIZE = 100  # Size for charm die representation
CHARM_DIE_BORDER_RADIUS = 20  # Rounded corners for die look
DAGGER_MULT_PER_COST = 0.25
MAX_DAGGER_MULT = 10.0
LEFT_BUTTON_X = 50
RIGHT_BUTTON_X = INITIAL_WIDTH - BUTTON_WIDTH - 50  # Will be dynamic
CENTER_LEFT_X = INITIAL_WIDTH // 2 - BUTTON_WIDTH - 20  # Will be dynamic
CENTER_RIGHT_X = INITIAL_WIDTH // 2 + 20  # Will be dynamic
INTEREST_RATE = 10  # Coins per extra coin
INTEREST_MAX = 50  # Max coins for interest calculation
TOOLTIP_MAX_WIDTH = 300  # Max width for tooltip before wrapping
PACK_BOOST = 0.5  # Multiplier boost per pack use
HAND_TYPES = ['Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind', 'Full House', 'Small Straight', 'Large Straight']
# Add this constant near the top, after other constants like HAND_TYPES
BOSS_EFFECTS = [
    {'name': 'Hold Ban', 'desc': 'You cannot hold any dice between rerolls.', 'difficulty': 'Hard'},
    {'name': 'Reroll Ration', 'desc': 'Rerolls left reduced by 1 for the round.', 'difficulty': 'Easy'},
    {'name': 'Discard Drought', 'desc': 'Discards left reduced by 1 for the round.', 'difficulty': 'Easy'},
    {'name': 'Reroll Penalty', 'desc': 'Each reroll costs 1 coin (deducted immediately).', 'difficulty': 'Easy'},
    {'name': 'Hold Limit', 'desc': 'You can only hold up to 3 dice between rerolls.', 'difficulty': 'Medium'},
    {'name': 'Discard Cap', 'desc': 'Discard phase limited to 2 dice max per use.', 'difficulty': 'Easy'},
    {'name': 'Score Dip', 'desc': 'Base hand scores reduced by 10% for the round.', 'difficulty': 'Easy'},
    {'name': 'Target Bump', 'desc': 'Blind target increased by 20%.', 'difficulty': 'Medium'},
    {'name': 'Color Fade', 'desc': 'No monochrome or rainbow bonuses applied this round.', 'difficulty': 'Medium'},
    {'name': 'Fragile Flip', 'desc': 'Glass dice break chance increased to 50%.', 'difficulty': 'Medium'},
    {'name': 'Charm Glitch', 'desc': 'One random equipped charm is disabled for the round.', 'difficulty': 'Medium'},
    {'name': 'Face Shuffle', 'desc': 'Dice faces are randomized (e.g., non-standard values like duplicates or missing numbers).', 
     'difficulty': 'Medium'},
    {'name': 'Coin Freeze', 'desc': 'No extra coins from Gold/Silver this round.', 'difficulty': 'Medium'},
    {'name': 'Rainbow Restriction', 'desc': 'Rainbow dice only count as one fixed color (random per round) for bonuses.', 
     'difficulty': 'Medium'},
    {'name': 'Glass Guard', 'desc': 'Glass dice cannot be held (auto-unheld after rolls).', 'difficulty': 'Medium'},
    {'name': 'Charm Tax', 'desc': 'Each equipped charm reduces hands left by 0.5 (rounded down).', 'difficulty': 'Medium'},
    {'name': 'Mono Mixup', 'desc': 'Monochrome bonuses halved if more than one color is present (even Rainbows).', 
     'difficulty': 'Medium'},
    {'name': 'Reroll Rebound', 'desc': 'After each reroll, one random held die is unheld.', 'difficulty': 'Medium'},
    {'name': 'Hand Trim', 'desc': 'Hands left reduced by 1 for the round.', 'difficulty': 'Hard'},
    {'name': 'Break Surge', 'desc': 'Glass break chance increases by 10% per reroll used.', 'difficulty': 'Hard'},
    {'name': 'Special Silence', 'desc': 'All special die effects disabled (no Gold coins, Silver extras, Glass mult, Rainbow wild).', 
     'difficulty': 'Hard'},
    {'name': 'Die Drain', 'desc': 'One random die is removed from your hand after each reroll.', 'difficulty': 'Hard'},
    {'name': 'Charm Eclipse', 'desc': 'All equipped charms are disabled for the round.', 'difficulty': 'Hard'},
    {'name': 'Value Vault', 'desc': 'All rolled values are inverted (1=6, 2=5, etc.), messing with straights and high/low strategies.', 
     'difficulty': 'Hard'},
    {'name': 'Blind Boost', 'desc': 'Blind target increased by 30%, but +1 extra discard.', 'difficulty': 'Hard'},
    {'name': 'Special Swap', 'desc': 'All special dice effects are inverted (e.g., Gold gives coins when not held, Silver when held).', 
     'difficulty': 'Hard'},
    {'name': 'Discard Delay', 'desc': 'Discard phase only available after first reroll.', 'difficulty': 'Hard'},
    {'name': 'Multiplier Mute', 'desc': 'All multipliers (charms, hands, colors) capped at x1.5.', 'difficulty': 'Hard'},
    {'name': 'Bag Bottleneck', 'desc': 'Bag refills only half full after depletion (fewer redraw options).', 'difficulty': 'Hard'},
    {'name': 'Hold Hazard', 'desc': 'Held dice have a 20% chance to reroll anyway on next roll.', 'difficulty': 'Hard'}
]
BAG_COLOR = (139, 69, 19)  # Brown for bag
BAG_BORDER_RADIUS = 15  # Rounded corners for bag
BAG_PADDING = 10  # Padding around dice grid in bag
UI_PANEL_COLOR = (0, 80, 0)  # Slightly darker green
UI_PANEL_BORDER_RADIUS = 10
UI_PANEL_WIDTH = 150
UI_PANEL_HEIGHT = 140  # Increased for coins
MULTIPLIERS_BUTTON_SIZE = 50
MULTIPLIERS_PANEL_WIDTH = 150
MULTIPLIERS_PANEL_HEIGHT = len(HAND_TYPES) * 25 + 20
PACK_BOX_SIZE = 60
SMALL_ICON_DIE_SIZE = 15
COLOR_CYCLE = list(COLORS.keys())
CYCLE_SPEED = 0.5  # Seconds per color change
# Inner icon sizing for fitting inside die frame
INNER_ICON_SCALE = 0.8  # 80% of die size (e.g., 80x80 for 100x100 die)
INNER_ICON_PADDING = 10  # Pixels of padding around inner icon (adjust for fit)
DIE_BACKGROUND_COLOR = (255, 255, 255)  # White for the die face
DIE_BORDER_COLOR = (0, 0, 0)  # Black border, like game dice
DIE_BORDER_WIDTH = 2  # Thin border

POUCHES = [
    {'name': 'Red Pouch', 'color': 'Red', 'desc': 'Aggro focus: +1 discard per round, extra 2 Red dice.', 
     'bonus': {'extra_dice': {'Red': 2}, 'discards': 1}, 'unlocked': True},
    {'name': 'Blue Pouch', 'color': 'Blue', 'desc': 'Control: +1 hand per round, extra 1 Blue die and 1 Silver die.', 
     'bonus': {'extra_dice': {'Blue': 1, 'Silver': 1}, 'hands': 1}, 'unlocked': True},
    {'name': 'Yellow Pouch', 'color': 'Yellow', 'desc': 'Balanced: +10 starting coins, even split of base colors.', 
     'bonus': {'coins': 10}, 'unlocked': True},
    {'name': 'Green Pouch', 'color': 'Green', 'desc': 
     'Economy: +2 coins per unused hand and +1 per unused discard at round end, extra 1 Green die and 1 Gold die.', 
     'bonus': {'extra_dice': {'Green': 1, 'Gold': 1}}, 'unlocked': True},
    {'name': 'Black Pouch', 'color': 'Black', 'desc': 'High-risk: +1 charm slot, -1 hand per round, extra 1 random special die.', 
     'bonus': {'charm_slots': 1, 'hands': -1, 'extra_dice': {'random_special': 1}}, 'unlocked': False},  # Example; add random logic in apply_pouch
    {'name': 'Ghost Pouch', 'color': 'Glass', 'desc': 'Risky: Higher special dice in shops, start with 1 Glass die.', 
     'bonus': {'extra_dice': {'Glass': 1}}, 'unlocked': False},  # Shop chance via flag
    {'name': 'Erratic Pouch', 'color': 'Rainbow', 'desc': 'Chaotic: Randomize starting bag colors/faces.', 
     'bonus': {'randomize_bag': True}, 'unlocked': False},
    {'name': 'Plasma Pouch', 'color': 'Purple', 'desc': 'Balanced scorer: Average base score and mult, x1.5 blind targets.', 
     'bonus': {'balance_score': True, 'blind_mult': 1.5}, 'unlocked': False}
]


# Dot positions for each face value (1-6)
DOT_POSITIONS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75), (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)]
}

# Represent each die as a dictionary
def create_dice_bag():
    """Creates the bag of 25 dice, 5 per color, each with standard faces."""
    bag = []
    color_names = ['Red', 'Blue', 'Green', 'Purple', 'Yellow'] # Base colors only
    for color in color_names:
        for i in range(1, DICE_PER_COLOR + 1):
            die = {
                'id': f"{color}{i}",
                'color': color,
                'faces': DICE_FACES[:]  # Copy list for future modifications
            }
            bag.append(die)
    return bag

# Game class to manage state and visuals
class ChromaRollGame:
    def __init__(self):
        pygame.init()  # Initialize Pygame

        THEME = {
            'background': (10, 50, 10),  # Deep casino felt green (darker than your (0, 80, 0) for mood)
            'panel_bg': (20, 70, 20),  # Slightly lighter green for panels (less flat)
            'button_bg': (80, 120, 80),  # Muted green buttons (with gold hover below)
            'button_hover': (120, 180, 50),  # Glowy green-gold on hover
            'border': (0, 0, 0),  # Black borders (keep or change to (50, 50, 50) for softer gray)
            'text': (220, 220, 220),  # Off-white text for readability on dark bg
            'highlight': (200, 160, 0),  # Warm gold for holds/coins (brighter than your (255, 215, 0) for retro shine)
            'font_main_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Pixel for main
            'font_main_size': 36,
            'font_small_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Vintage for small
            'font_small_size': 24,
            'font_tiny_path': resource_path('assets/fonts/VT323-Regular.ttf'),  # Same for tiny, or mix
            'font_tiny_size': 20,
        }
        
        self.screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)  # Resizable window
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Chroma Roll")  # Set title
        self.font = pygame.font.Font(THEME['font_main_path'], THEME['font_main_size'])  # Font for text
        self.small_font = pygame.font.Font(THEME['font_small_path'], THEME['font_small_size'])  # Smaller font for hand/modifier info
        self.tiny_font = pygame.font.Font(THEME['font_tiny_path'], THEME['font_tiny_size'])  # Even smaller for top texts
        self.bag = create_dice_bag()  # Create dice bag (mutable list for removal)
        self.hand = []  # Current hand of dice
        self.full_bag = [d.copy() for d in self.bag]  # Template of all owned dice
        # gold_die = {'id': 'Gold1', 'color': 'Gold', 'faces': DICE_FACES[:]}       #Temporary code for adding a gold dice to bag
        # self.full_bag.append(gold_die)                                            #Temporary code for adding a gold dice to bag
        # self.bag.append(copy.deepcopy(gold_die))                                  #Temporary code for adding a gold dice to bag
        # silver_die = {'id': 'Silver1', 'color': 'Silver', 'faces': DICE_FACES[:]} #Temporary code for adding a silver dice to bag
        # self.full_bag.append(silver_die)                                          #Temporary code for adding a silver dice to bag
        # self.bag.append(copy.deepcopy(silver_die))                                #Temporary code for adding a silver dice to bag
        # glass_die = {'id': 'Glass1', 'color': 'Glass', 'faces': DICE_FACES[:]}      #Temporary code for adding a glass dice to bag
        # self.full_bag.append(glass_die)                                             #Temporary code for adding a glass dice to bag
        # self.bag.append(copy.deepcopy(glass_die))                                   #Temporary code for adding a glass dice to bag
        # glass_die = {'id': 'Glass2', 'color': 'Glass', 'faces': DICE_FACES[:]}      #Temporary code for adding a glass dice to bag
        # self.full_bag.append(glass_die)                                             #Temporary code for adding a glass dice to bag
        # self.bag.append(copy.deepcopy(glass_die))                                   #Temporary code for adding a glass dice to bag
        # rainbow_die = {'id': 'Rainbow1', 'color': 'Rainbow', 'faces': DICE_FACES[:]}  #Temporary code for adding a rainbow dice to bag
        # self.full_bag.append(rainbow_die)                                             #Temporary code for adding a rainbow dice to bag
        # self.bag.append(copy.deepcopy(rainbow_die))                                   #Temporary code for adding a rainbow dice to bag
        # rainbow_die = {'id': 'Rainbow2', 'color': 'Rainbow', 'faces': DICE_FACES[:]}  #Temporary code for adding a rainbow dice to bag
        # self.full_bag.append(rainbow_die)                                             #Temporary code for adding a rainbow dice to bag
        # self.bag.append(copy.deepcopy(rainbow_die))                                   #Temporary code for adding a rainbow dice to bag
        # rainbow_die = {'id': 'Rainbow3', 'color': 'Rainbow', 'faces': DICE_FACES[:]}  #Temporary code for adding a rainbow dice to bag
        # self.full_bag.append(rainbow_die)                                             #Temporary code for adding a rainbow dice to bag
        # self.bag.append(copy.deepcopy(rainbow_die))                                   #Temporary code for adding a rainbow dice to bag
        # rainbow_die = {'id': 'Rainbow4', 'color': 'Rainbow', 'faces': DICE_FACES[:]}  #Temporary code for adding a rainbow dice to bag
        # self.full_bag.append(rainbow_die)                                             #Temporary code for adding a rainbow dice to bag
        # self.bag.append(copy.deepcopy(rainbow_die))                                   #Temporary code for adding a rainbow dice to bag
        # rainbow_die = {'id': 'Rainbow5', 'color': 'Rainbow', 'faces': DICE_FACES[:]}  #Temporary code for adding a rainbow dice to bag
        # self.full_bag.append(rainbow_die)                                             #Temporary code for adding a rainbow dice to bag
        # self.bag.append(copy.deepcopy(rainbow_die))                                   #Temporary code for adding a rainbow dice to bag
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
        self.previous_state = self.game_state  # Init to starting state
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
        self.hand_multipliers = {ht: 1.0 for ht in HAND_TYPES}  # Multipliers for hand types
        self.pack_choices = []  # Choices for pack selection
        self.confirm_sell_index = -1  # Index of charm to confirm sell
        self.shop_reroll_cost = 5  # Initial reroll cost for shop
        self.available_packs = random.sample([0, 1, 2, 3, 4], 2)  # Random 2 from 5 packs
        self.multipliers_hover = False  # For showing multipliers panel
        self.charms_pool = [
            {'name': 'Basic Charm', 'rarity': 'Common', 'cost': 2, 'desc': '+10 to all final scores.', 'type': 'flat_bonus', 'value': 10},

            {'name': 'Red Greed Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Red die scored.', 'type': 
             'per_color_bonus', 'color': 'Red', 'value': 5},

            {'name': 'Blue Lust Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Blue die scored.', 'type': 
             'per_color_bonus', 'color': 'Blue', 'value': 5},

            {'name': 'Green Wrath Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Green die scored.', 'type': 
             'per_color_bonus', 'color': 'Green', 'value': 5},

            {'name': 'Purple Glutton Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Purple die scored.', 'type': 
             'per_color_bonus', 'color': 'Purple', 'value': 5},

            {'name': 'Yellow Jolly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Yellow die scored.', 'type': 
             'per_color_bonus', 'color': 'Yellow', 'value': 5},

            {'name': 'Zany Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+40 score if hand contains a 3 of a Kind.', 'type': 
             'hand_bonus', 'hands': ['3 of a Kind'], 'value': 40},

            {'name': 'Mad Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+30 score if hand contains a 2 Pair.', 'type': 'hand_bonus', 
             'hands': ['2 Pair'], 'value': 30},

            {'name': 'Crazy Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+35 score if hand contains a Small or Large Straight.', 
             'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 35},

            {'name': 'Droll Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to monochrome multipliers.', 'type': 
             'mono_mult_bonus', 'value': 0.5},

            {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 
             'hand_bonus', 'hands': ['Pair'], 'value': 50},

            {'name': 'Wily Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+100 base score if hand contains a 3 of a Kind.', 'type': 
             'hand_bonus', 'hands': ['3 of a Kind'], 'value': 100},

            {'name': 'Clever Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+80 base score if hand contains a 2 Pair.', 'type': 
             'hand_bonus', 'hands': ['2 Pair'], 'value': 80},

            {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': 
             ['Small Straight', 'Large Straight'], 'value': 100},

            {'name': 'Half Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+20 score if hand uses 3 or fewer dice.', 'type': 
             'few_dice_bonus', 'max_dice': 3, 'value': 20},

            {'name': 'Stencil Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 
             'x1 multiplier for each empty charm slot (including this one).', 'type': 'empty_slot_mult', 'value': 1.0},

            {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},

            {'name': 'Mime Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
             'Retrigger effects of held dice (e.g., double Gold coins, Glass mult/break chance).', 'type': 'retrigger_held'},

            {'name': 'Debt Charm', 'rarity': 'Common', 'cost': 2, 'desc': 'Allows going into negative coins for shop buys (up to -5).', 
             'type': 'negative_coins', 'limit': -5},

            {'name': 'Dagger Charm', 'rarity': 'Rare', 'cost': 10, 'desc': 
             'When blind starts, sacrifice a charm to the right and add 0.25x its cost to your score multiplier permanently. (Max 10x)', 
             'type': 'sacrifice_mult'},

            {'name': 'Golden Touch Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+2 coins per Gold die held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Gold', 'value': 2},

            {'name': 'Silver Lining Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+2 coins per Silver die not held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Silver', 
             'value': 2},

            {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
             'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 
             'break_penalty': 5},

            {'name': 'Even Stevens Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per even-valued die scored.', 'type': 
             'per_value_bonus', 'parity': 'even', 'value': 5},

            {'name': 'Oddball Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per odd-valued die scored.', 'type': 
             'per_value_bonus', 'parity': 'odd', 'value': 5},

            {'name': 'Rainbow Prism Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to rainbow multipliers.', 'type': 
             'rainbow_mult_bonus', 'value': 0.5},

            {'name': 'Full House Party Charm', 'rarity': 'Rare', 'cost': 6, 'desc': '+150 base score if hand contains a Full House.', 
             'type': 'hand_bonus', 'hands': ['Full House'], 'value': 150},

            {'name': 'Quadruple Threat Charm', 'rarity': 'Rare', 'cost': 7, 'desc': '+200 base score if hand contains a 4 of a Kind.', 
             'type': 'hand_bonus', 'hands': ['4 of a Kind'], 'value': 200},

            {'name': 'Reroll Recycler Charm', 'rarity': 'Rare', 'cost': 8, 'desc': 
             'Gain 1 extra reroll in the turn if you use a discard.', 'type': 'reroll_recycler'},

            {'name': 'Interest Booster Charm', 'rarity': 'Common', 'cost': 3, 'desc': 
             'Increases max coins for interest calculation by 20.', 'type': 'interest_max_bonus', 'value': 20},
        ]

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

        pygame.mixer.init()  # Init mixer
        self.roll_sound = pygame.mixer.Sound(resource_path('assets/audio/roll.wav'))  # Load
        self.roll_sound.set_volume(0.5)  # Quiet default
        self.break_sound = pygame.mixer.Sound(resource_path('assets/audio/break.wav'))
        self.break_sound.set_volume(0.7)  # Louder for impact
        self.coin_sound = pygame.mixer.Sound(resource_path('assets/audio/coin.wav'))
        self.coin_sound.set_volume(0.4)

        # In ChromaRollGame __init__, add:
        self.current_boss_effect = None  # Current active boss effect dict, or None
        self.disabled_charms = []  # For effects like Charm Glitch/Eclipse: list of indices or names
        self.boss_reroll_count = 0  # Track rerolls used for effects like Break Surge
        self.boss_rainbow_color = None  # For Rainbow Restriction: fixed color for the round
        self.boss_shuffled_faces = {}  # Die ID to shuffled faces for Face Shuffle
        self.upcoming_boss_effect = None  # Preview of the Boss effect for the current round
        self.upcoming_boss_effect = random.choice(BOSS_EFFECTS)  # Initial preview for first round

        self.debug_boss_dropdown_open = False  # Flag for dropdown panel
        self.debug_boss_scroll_offset = 0  # For scrolling long list
        self.debug_boss_selected = None  # Temp for selection

        self.selected_pouch = None  # Track chosen pouch for bonuses
        self.green_pouch_active = False  # Flag for Green Pouch effect
        self.pouch_offset = 0  # For carousel scrolling
        self.unlocks = {}  # Future: Track unlocks, e.g., self.unlocks['Black Pouch'] = False; for now, use pouch['unlocked']
        self.tutorial_step = 0  # Current step in tutorial (0-5)
        self.tutorial_mode = False  # Flag if in tutorial
        self.tutorial_completed = False  # Track if finished (for future skips/unlocks)
        self.pouches = POUCHES
        if DEBUG:
            for pouch in self.pouches[4:]:  # Indices 4-7 for 5-8
                pouch['unlocked'] = True

    def draw_rounded_element(self, rect, fill_color, border_color=(0, 0, 0), border_width=2, radius=20, inner_content=None):
        """Draws a rounded rectangle with optional border and inner content.
        - inner_content: A function that takes the rect and draws inside it (e.g., dots or icons).
        """
        # Draw filled rounded rect
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=radius)
        
        # Add border if needed
        if border_width > 0:
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=radius)
        
        # Draw inner content if provided (call the function with rect)
        if inner_content:
            inner_content(rect)

    def draw_custom_button(self, rect, text, is_hover=False, is_red=False):
        """Draws a retro pixel button with hover and text (no bevel)."""
        bg_color = THEME['button_bg'] if not is_red else (150, 50, 50)  # Green default, red for discard
        hover_color = THEME['button_hover'] if not is_red else (200, 100, 100)
        border_color = THEME['border']
        
        # Base rounded rect with fill
        self.draw_rounded_element(rect, bg_color, border_color=border_color, border_width=2, radius=10)
        
        # Hover glow (gold outline)
        if is_hover:
            glow_rect = rect.inflate(4, 4)
            pygame.draw.rect(self.screen, THEME['highlight'], glow_rect, 2, border_radius=12)
        
        # Centered text
        text_surf = self.font.render(text, True, THEME['text'])
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def grayscale_surface(self, surface):
        """Create a grayscale version of the surface for disabled charms."""
        gray_surf = surface.copy()
        for x in range(gray_surf.get_width()):
            for y in range(gray_surf.get_height()):
                r, g, b, a = gray_surf.get_at((x, y))
                avg = (r + g + b) // 3
                gray_surf.set_at((x, y), (avg, avg, avg, a))
        return gray_surf

    def get_bag_color(self):
        """Returns the bag color based on selected pouch, fallback to default brown."""
        if self.selected_pouch and 'color' in self.selected_pouch:
            return COLORS.get(self.selected_pouch['color'], BAG_COLOR)
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
                empty_slots = self.max_charms - len(self.equipped_charms) + 1  # +1 including itself
                return charm['value'] * empty_slots
        return 1.0  # No stencil, x1 (no effect)

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
            self.upcoming_boss_effect = random.choice(BOSS_EFFECTS)  # Pre-generate for preview

        if self.current_blind == 'Boss':
            self.current_boss_effect = self.upcoming_boss_effect or random.choice(BOSS_EFFECTS)  # Use preview if set
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
                    # Remove one random die from hand (non-held? or any)
                    if len(self.hand) > 1:  # Don't drain to 0
                        drain_i = random.randint(0, len(self.hand) - 1)
                        del self.hand[drain_i]
                        del self.rolls[drain_i]
                        del self.held[drain_i]
                        del self.discard_selected[drain_i]
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
            self.roll_sound.play()
            for frame in range(ANIMATION_FRAMES):
                for i in range(len(self.rolls)):
                    if not self.held[i]:
                        die_temp = self.rolls[i][0]  # Temp var for the die
                        faces = self.boss_shuffled_faces.get(die_temp['id'], die_temp['faces']) if self.current_blind == 'Boss' and self.current_boss_effect and self.current_boss_effect['name'] == 'Face Shuffle' else die_temp['faces']
                        self.rolls[i] = (die_temp, random.choice(faces))
                self.screen.fill(THEME['background'])  # Clear screen
                self.draw_game_screen()
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
                    self.coin_sound.play()  # Play per coin gain
                    self.extra_coins += 1
                elif die['color'] == 'Silver' and not self.held[i]:
                    self.coin_sound.play()  # Play per coin gain
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
        self.roll_sound.play()
        # Animate rolling for all dice
        for frame in range(ANIMATION_FRAMES):
            self.rolls = [(die, random.choice(die['faces'])) for die in self.hand]
            self.screen.fill(THEME['background'])  # Clear screen
            self.draw_game_screen()
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
                self.coin_sound.play()  # Play per coin gain
                self.extra_coins += 1
            elif die['color'] == 'Silver' and not self.held[i]:
                self.coin_sound.play()  # Play per coin gain
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
                self.break_sound.play()
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
                    self.break_sound.play()
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
            self.current_hand_text = ""  # Blank during discard phase
            self.current_modifier_text = ""
        else:
            hand_type, base_score, modifier_desc, final_score, charm_chips, charm_mono_add = self.get_hand_type_and_score()
            self.current_hand_text = f"Current Hand: {hand_type} ({base_score} base + {charm_chips} charms) = {final_score} total"

            # Build modifier parts
            modifier_parts = []
            if modifier_desc:  # Assuming modifier_desc is the color mod string (e.g., "Monochrome x2.0")
                modifier_parts.append(modifier_desc)

            if charm_mono_add > 0:
                modifier_parts.append(f"{charm_mono_add:.1f}x charms")

            stencil_mult = self.get_stencil_mult()
            if stencil_mult > 1.0:
                modifier_parts.append(f"Stencil x{stencil_mult}")

            # Check if dagger charm is equipped and not disabled
            has_active_dagger = any(charm['type'] == 'sacrifice_mult' and idx not in self.disabled_charms for idx, charm in enumerate(self.equipped_charms))
            dagger_text = f"{self.score_mult:.1f} dagger"
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

            # Set modifier text with "Modifiers: " prefix and " + " joins
            if modifier_parts:
                self.current_modifier_text = "Modifiers: " + " + ".join(modifier_parts)
            else:
                self.current_modifier_text = ""

    def draw_dice(self):
        """Draws the current rolls on the screen."""
        total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
        start_x = (self.width - total_dice_width) // 2
        current_time = time.time()  # For animation
        for i, (die, value) in enumerate(self.rolls):
            x = start_x + i * (DIE_SIZE + 20)
            y = self.height - DIE_SIZE - 100
            size = DIE_SIZE * HELD_DIE_SCALE if self.held[i] else DIE_SIZE
            offset = (DIE_SIZE - DIE_SIZE * HELD_DIE_SCALE) / 2 if self.held[i] else 0
            color = die['color']
            if color == 'Rainbow':
                color_index = int(current_time / CYCLE_SPEED) % len(BASE_COLORS)
                color_rgb = COLORS[BASE_COLORS[color_index]]
            else:
                color_rgb = COLORS[color]
            # Draw die background with rounded corners
            rect = pygame.Rect(x + offset, y + offset, size, size)

            # New: Mini-function for dots (moves your existing loop here)
            def _draw_dots(inner_rect):
                for pos in DOT_POSITIONS.get(value, []):
                    dot_x = inner_rect.x + pos[0] * inner_rect.width  # Updated to use inner_rect (was x + offset + pos[0] * size)
                    dot_y = inner_rect.y + pos[1] * inner_rect.height  # Updated to use inner_rect (was y + offset + pos[1] * size)
                    pygame.draw.circle(self.screen, (0, 0, 0), (dot_x, dot_y), DOT_RADIUS)
            # Highlight if selected for discard (red border outside black)
            if self.discard_selected[i]:
                outer_rect = pygame.Rect(x + offset - 3, y + offset - 3, size + 6, size + 6)
                pygame.draw.rect(self.screen, (255, 0, 0), outer_rect, 3, border_radius=DIE_BORDER_RADIUS)
            # Draw dots
            self.draw_rounded_element(rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=DIE_BORDER_RADIUS, inner_content=_draw_dots)

    def draw_buttons(self):
        """Draws the action buttons; in debug, add Score button; add Discard in discard phase."""
        reroll_rect = None
        discard_rect = None
        start_roll_rect = None
        score_rect = None
        end_turn_rect = None
        bottom_y = self.height - BUTTON_HEIGHT - 20
        left_button_x = 50
        right_button_x = self.width - BUTTON_WIDTH - 50
        center_left_x = self.width // 2 - BUTTON_WIDTH - 20
        center_right_x = self.width // 2 + 20
        mouse_pos = pygame.mouse.get_pos()  # For hover

        if self.is_discard_phase:
            discard_rect = pygame.Rect(left_button_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            self.draw_custom_button(discard_rect, "Discard", is_hover=discard_rect.collidepoint(mouse_pos), is_red=True)

            start_roll_rect = pygame.Rect(right_button_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            self.draw_custom_button(start_roll_rect, "Start Roll", is_hover=start_roll_rect.collidepoint(mouse_pos))

        else:
            reroll_rect = pygame.Rect(center_left_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            button_text = "Reroll" if (self.rerolls_left > 0 or DEBUG) else "Draw and Score"
            self.draw_custom_button(reroll_rect, button_text, is_hover=reroll_rect.collidepoint(mouse_pos))

            end_turn_rect = pygame.Rect(center_right_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            self.draw_custom_button(end_turn_rect, "End Turn", is_hover=end_turn_rect.collidepoint(mouse_pos))

        if DEBUG:
            score_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, bottom_y - BUTTON_HEIGHT - 10, BUTTON_WIDTH, BUTTON_HEIGHT)
            self.draw_custom_button(score_rect, "Score & New", is_hover=score_rect.collidepoint(mouse_pos))

        return reroll_rect, discard_rect, start_roll_rect, score_rect, end_turn_rect

    def draw_popup(self):
        """Draws the beaten blind popup with a single Continue button and $ animation."""
        popup_rect = pygame.Rect(self.width // 2 - POPUP_WIDTH // 2, 200, POPUP_WIDTH, POPUP_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), popup_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), popup_rect, 3)  # White border

        # Split message into lines and render with animation for $
        lines = self.popup_message.split('\n')
        for i, line in enumerate(lines):
            text = self.tiny_font.render(line, True, (THEME['text']))
            self.screen.blit(text, (popup_rect.x + (POPUP_WIDTH - text.get_width()) // 2, popup_rect.y + 20 + i * 30))

        # Draw single Continue button
        continue_rect = pygame.Rect(popup_rect.x + (POPUP_WIDTH - BUTTON_WIDTH) // 2, popup_rect.y + POPUP_HEIGHT - 70, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), continue_rect)
        continue_text = self.tiny_font.render("Continue", True, (THEME['text']))
        self.screen.blit(continue_text, (continue_rect.x + (BUTTON_WIDTH - continue_text.get_width()) // 2, continue_rect.y + 10))

        return continue_rect
    
    def draw_pause_menu(self):
        """Draws the pause popup with options: Main Menu, Quit, Return."""
        # Dim background
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Centered popup rect (reuse POPUP sizes)
        popup_x = (self.width - POPUP_WIDTH) // 2
        popup_y = (self.height - POPUP_HEIGHT) // 2
        popup_rect = pygame.Rect(popup_x, popup_y, POPUP_WIDTH, POPUP_HEIGHT)
        pygame.draw.rect(self.screen, THEME['background'], popup_rect, border_radius=20)  # Green bg, rounded
        pygame.draw.rect(self.screen, (0, 0, 0), popup_rect, 2, border_radius=20)  # Border
        
        # Title
        title_text = self.font.render("Paused", True, (THEME['text']))
        self.screen.blit(title_text, (popup_x + (POPUP_WIDTH - title_text.get_width()) // 2, popup_y + 20))
        
        # Draw buttons using rects
        button_rects = self.get_pause_button_rects()
        for rect, opt in button_rects:
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            text = self.font.render(opt, True, (THEME['text']))
            self.screen.blit(text, (rect.x + (BUTTON_WIDTH - text.get_width()) // 2, rect.y + 10))
    
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

    def draw_tooltip(self, x, y, text):
        lines = self.word_wrap(text, self.small_font, TOOLTIP_MAX_WIDTH)
        line_height = self.small_font.get_height()
        width = max(self.small_font.size(line)[0] for line in lines) + TOOLTIP_PADDING * 2
        height = len(lines) * line_height + TOOLTIP_PADDING * 2
        if x + width > self.width:
            x = self.width - width
        tooltip_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (100, 100, 100), tooltip_rect)
        for i, line in enumerate(lines):
            desc_surface = self.small_font.render(line, True, (THEME['text']))
            self.screen.blit(desc_surface, (x + TOOLTIP_PADDING, y + TOOLTIP_PADDING + i * line_height))

    def word_wrap(self, text, font, max_width):
        paragraphs = text.split('\n')
        lines = []
        for para in paragraphs:
            words = para.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
        return lines

    def draw_charm_die(self, rect, charm, index=None):
        """Draws a charm as a die with icon inside. Grays out if disabled using built-in Pygame transform."""
        # Determine if disabled
        is_disabled = index is not None and index in self.disabled_charms
        
        # Draw die background (white face with border) - gray the background too if disabled for better effect
        bg_color = (128, 128, 128) if is_disabled else DIE_BACKGROUND_COLOR

        # Get charm-specific bg if defined, else fallback to DIE_BACKGROUND_COLOR
        charm_bg = CHARM_BG_COLORS.get(charm['name'], DIE_BACKGROUND_COLOR)

        # Gray if disabled
        bg_color = (128, 128, 128) if is_disabled else charm_bg
        
        # Inner icon rect (padded and scaled)
        def _draw_inner_charm(inner_rect):
            inner_size = int(CHARM_SIZE * INNER_ICON_SCALE)  # e.g., 80 for 100 size
            inner_sub_rect = inner_rect.inflate(-INNER_ICON_PADDING * 2, -INNER_ICON_PADDING * 2)  # Changed name
            inner_sub_rect.size = (inner_size, inner_size)  # Changed name
            inner_sub_rect.center = inner_rect.center  # Changed to use inner_rect for centering (outer)
            
            # Load icon from cache
            path = self.charm_icon_paths.get(charm['name'])
            if path and path in self.charm_icon_cache:
                icon_surf = self.charm_icon_cache[path].copy()  # Always copy to avoid modifying cache
                
                # Apply grayscale if disabled
                if is_disabled:
                    icon_surf = pygame.transform.grayscale(icon_surf)  # Built-in grayscale (returns new surface)
                
                # Blit icon
                self.screen.blit(icon_surf, inner_sub_rect.topleft)
            else:
                # Create a temporary surface for fallback drawing (to allow grayscaling)
                fallback_surf = pygame.Surface((inner_size, inner_size), pygame.SRCALPHA)  # Transparent for clean blit
                fallback_surf.fill((0, 0, 0, 0))  # Transparent background (drawings only)
                
                # Call draw_charm_fallback but adapted to draw on fallback_surf instead of self.screen
                # We'll replicate the logic here, but adjust coordinates to be relative to fallback_surf (0,0)
                name = charm['name']
                center_x = inner_size // 2
                center_y = inner_size // 2
                
                # Replicate fallback drawing logic, but on fallback_surf
                if name == 'Basic Charm':
                    text = self.tiny_font.render('+10', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name in ['Red Greed Charm', 'Blue Lust Charm', 'Green Wrath Charm', 'Purple Glutton Charm', 'Yellow Jolly Charm']:
                    # Get color from name (e.g., 'Red' from 'Red Greed Charm')
                    color_name = name.split()[0]  # First word is color
                    color = COLORS.get(color_name, (200, 200, 200))  # Fallback gray if mismatch
                    
                    # Draw inner colored die face (square, rounded, colored bg, black border) on fallback_surf - full size
                    inner_die_size = inner_size  # Full size for colored die
                    inner_die_x = 0
                    inner_die_y = 0
                    inner_die_rect = pygame.Rect(inner_die_x, inner_die_y, inner_die_size, inner_die_size)
                    pygame.draw.rect(fallback_surf, color, inner_die_rect, border_radius=CHARM_DIE_BORDER_RADIUS // 2)  # Colored background
                    pygame.draw.rect(fallback_surf, (0, 0, 0), inner_die_rect, 2, border_radius=CHARM_DIE_BORDER_RADIUS // 2)  # Black border
                    
                    # Draw 5 black dots (from DOT_POSITIONS[5])
                    dot_positions = DOT_POSITIONS[5]  # [(0.25,0.25), (0.25,0.75), (0.5,0.5), (0.75,0.25), (0.75,0.75)]
                    dot_radius = DOT_RADIUS // 2  # Smaller for charm scale (5 instead of 10)
                    for pos in dot_positions:
                        dot_x = inner_die_x + int(pos[0] * inner_die_size)
                        dot_y = inner_die_y + int(pos[1] * inner_die_size)
                        pygame.draw.circle(fallback_surf, (0, 0, 0), (dot_x, dot_y), dot_radius)  # Black dots
                elif name == 'Zany Charm':
                    text = self.tiny_font.render('3OK', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Mad Charm':
                    text = self.tiny_font.render('2P', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Crazy Charm':
                    # Scale line length
                    line_length = int(15 * INNER_ICON_SCALE * 2)  # Original 30, scaled
                    pygame.draw.line(fallback_surf, (0, 0, 0), (center_x - line_length // 2, center_y), (center_x + line_length // 2, center_y), 3)
                elif name == 'Droll Charm':
                    scaled_radius = int(inner_size // 4)
                    pygame.draw.circle(fallback_surf, (0, 0, 0), (center_x, center_y), scaled_radius, 2)
                elif name == 'Sly Charm':
                    text = self.tiny_font.render('P+50', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Wily Charm':
                    text = self.tiny_font.render('3OK+100', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Clever Charm':
                    text = self.tiny_font.render('2P+80', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Devious Charm':
                    text = self.tiny_font.render('Str+100', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Half Charm':
                    text = self.tiny_font.render('≤3', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Stencil Charm':
                    text = self.tiny_font.render('[]x', True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                elif name == 'Four Fingers Charm':
                    # Scale hand drawing (reduce sizes by scale factor)
                    scale_factor = INNER_ICON_SCALE
                    palm_rect = pygame.Rect(center_x - int(15 * scale_factor), center_y - int(5 * scale_factor), int(30 * scale_factor), int(20 * scale_factor))
                    pygame.draw.rect(fallback_surf, (200, 200, 200), palm_rect, border_radius=5)
                    pygame.draw.rect(fallback_surf, (0, 0, 0), palm_rect, 2, border_radius=5)
                    finger_positions = [-12, -4, 4, 12]
                    for fp in finger_positions:
                        scaled_fp = int(fp * scale_factor)
                        pygame.draw.line(fallback_surf, (0, 0, 0), (center_x + scaled_fp, center_y + int(5 * scale_factor)), (center_x + scaled_fp, center_y - int(8 * scale_factor)), 3)
                        tip_start = (center_x + scaled_fp, center_y - int(8 * scale_factor))
                        tip_end = (center_x + scaled_fp + (scaled_fp // 8), center_y - int(20 * scale_factor))
                        pygame.draw.line(fallback_surf, (0, 0, 0), tip_start, tip_end, 2)
                    thumb_base = (center_x - int(15 * scale_factor), center_y + int(5 * scale_factor))
                    thumb_knuckle = (center_x - int(20 * scale_factor), center_y + int(10 * scale_factor))
                    thumb_tip = (center_x - int(25 * scale_factor), center_y + int(15 * scale_factor))
                    pygame.draw.line(fallback_surf, (0, 0, 0), thumb_base, thumb_knuckle, 3)
                    pygame.draw.line(fallback_surf, (0, 0, 0), thumb_knuckle, thumb_tip, 2)
                elif name == 'Mime Charm':
                    # Scale box
                    box_size = int(15 * INNER_ICON_SCALE * 2)  # Original 30
                    pygame.draw.rect(fallback_surf, (0, 0, 0), (center_x - box_size // 2, center_y - box_size // 2, box_size, box_size), 2)
                    pygame.draw.line(fallback_surf, (0, 0, 0), (center_x - box_size // 2, center_y - box_size // 2), (center_x - box_size // 2, center_y + box_size // 2), 2)
                    pygame.draw.line(fallback_surf, (0, 0, 0), (center_x + box_size // 2, center_y - box_size // 2), (center_x + box_size // 2, center_y + box_size // 2), 2)
                elif charm['type'] == 'sacrifice_mult':
                    self.draw_dagger_icon(rect)  # Assuming this draws on the full rect; scale if needed
                # Add any other fallback drawings for charms not in the icon paths (scale similarly if complex)
                else:
                    # Fallback for unmapped charms: text with name to debug
                    text = self.tiny_font.render(charm['name'][:10], True, (0, 0, 0))
                    fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
                
                # Apply grayscale if disabled (on the fallback_surf)
                if is_disabled:
                    fallback_surf = pygame.transform.grayscale(fallback_surf)  # Grayscale the drawings
                
                # Blit the fallback_surf onto the screen at inner_rect
                self.screen.blit(fallback_surf, inner_sub_rect.topleft)  # Changed name

        self.draw_rounded_element(rect, bg_color, border_color=DIE_BORDER_COLOR, border_width=DIE_BORDER_WIDTH, radius=CHARM_DIE_BORDER_RADIUS, inner_content=_draw_inner_charm)  # <--- Replaced call

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
                self.draw_tooltip(x, y + CHARM_SIZE + TOOLTIP_PADDING, tooltip_text)
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

    def draw_game_screen(self):
        """Draws the main game screen."""
        mouse_pos = pygame.mouse.get_pos()  # Get mouse_pos at the top for use in hover checks
        self.draw_dice()
        # After drawing dice, add break effect
        if self.broken_dice and self.break_icon:
            current_time = time.time()
            elapsed = current_time - self.break_effect_start
            if elapsed < self.break_effect_duration:
                alpha = int(255 * (elapsed / self.break_effect_duration))  # Fade in from 0 to 255
                overlay = self.break_icon.copy()  # Copy to modify alpha
                overlay.set_alpha(alpha)
                for idx in self.broken_dice:
                    # Get die position (same as in dice draw loop)
                    total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
                    start_x = (self.width - total_dice_width) // 2
                    x = start_x + idx * (DIE_SIZE + 20)
                    size = DIE_SIZE * HELD_DIE_SCALE if self.held[idx] else DIE_SIZE
                    offset = (DIE_SIZE - size) / 2 if self.held[idx] else 0
                    die_rect = pygame.Rect(x + offset, self.height - DIE_SIZE - 100 + offset, size, size)
                    # Blit overlay centered on die
                    overlay_rect = overlay.get_rect(center=die_rect.center)
                    self.screen.blit(overlay, overlay_rect)
            else:
                # Reset after duration
                self.broken_dice = []
                self.break_effect_start = 0
        self.draw_text()
        self.draw_bag_visual()
        # Add equipped charms drawing loop here (with grayscale for disabled)
        for i, charm in enumerate(self.equipped_charms):
            x = 50 + i * (CHARM_SIZE + 10)  # Note: 10 is original spacing; update if changed
            y = 10  # Top for game screen
            rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
            self.draw_charm_die(rect, charm, index=i)  # Draw directly with frame, icon, and grayscale if disabled
            # Add tooltip on hover
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
                self.draw_tooltip(x, y + CHARM_SIZE + TOOLTIP_PADDING, tooltip_text)
        # Removed self.draw_charms() to eliminate duplicate drawing and tooltip issues
        self.draw_buttons()
        self.draw_ui_panel()
        if self.temp_message and time.time() - self.temp_message_start < self.temp_message_duration:
            msg_text = self.small_font.render(self.temp_message, True, (255, 255, 0))  # Yellow warning
            self.screen.blit(msg_text, (self.width // 2 - msg_text.get_width() // 2, 380))  # Near-center, above dice (adjust y if needed, e.g., 120 for more space)
        # In draw_game_screen(), after self.screen.fill(THEME['background']) or other early UI draws (e.g., after drawing charms and before bag)
        if self.current_boss_effect:
            effect_str = f"Boss Effect: {self.current_boss_effect['name']} - {self.current_boss_effect['desc']}"
            max_width = 300  # Adjust to fit space next to bag (e.g., 300px wide for wrapping)
            lines = []
            words = effect_str.split()
            current_line = ""
            for word in words:
                test_line = current_line + word + " "
                if self.small_font.size(test_line)[0] > max_width:
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    current_line = test_line
            lines.append(current_line.strip())  # Add last line
            
            # Position: Left and down of bag (assume bag at top-right; place mid-right but lower)
            text_x = self.width - max_width + 10  # Right-aligned with padding from edge
            text_y = 200  # Down from top (below charms/bag start; adjust if bag y=50, to 200 for below)
            line_spacing = self.small_font.get_height() + 5  # Vertical gap
            
            for i, line in enumerate(lines):
                boss_text = self.small_font.render(line, True, (255, 0, 0))  # Red text
                self.screen.blit(boss_text, (text_x, text_y + i * line_spacing))

        if self.game_state == 'pause_menu':
            self.draw_pause_menu()  # Draw over game screen
        multipliers_button_rect = pygame.Rect(self.width - MULTIPLIERS_BUTTON_SIZE - 10, self.height - MULTIPLIERS_BUTTON_SIZE - 100, MULTIPLIERS_BUTTON_SIZE, MULTIPLIERS_BUTTON_SIZE)
        pygame.draw.rect(self.screen, (100, 100, 100), multipliers_button_rect)
        button_text = self.tiny_font.render("M", True, (THEME['text']))
        self.screen.blit(button_text, (multipliers_button_rect.x + 20, multipliers_button_rect.y + 15))
        if multipliers_button_rect.collidepoint(mouse_pos):
            panel_x = self.width - MULTIPLIERS_PANEL_WIDTH - 10
            panel_y = self.height - MULTIPLIERS_PANEL_HEIGHT - MULTIPLIERS_BUTTON_SIZE - 120
            panel_rect = pygame.Rect(panel_x, panel_y, MULTIPLIERS_PANEL_WIDTH, MULTIPLIERS_PANEL_HEIGHT)
            self.draw_rounded_element(panel_rect, UI_PANEL_COLOR, border_color=(0, 0, 0), border_width=2, radius=UI_PANEL_BORDER_RADIUS, inner_content=None)
            y_offset = panel_y + 10
            for ht, mult in self.hand_multipliers.items():
                mult_text = self.tiny_font.render(f"{ht}: x{mult:.1f}", True, (THEME['text']))
                self.screen.blit(mult_text, (panel_x + 10, y_offset))
                y_offset += 25
        if self.show_popup:
            self.draw_popup()

    def draw_splash_screen(self):
        mouse_pos = pygame.mouse.get_pos()  # For hover
        if self.splash_start_time == 0:
            self.splash_start_time = time.time()
        if not hasattr(self, 'splash_total_start') or self.splash_total_start == 0:
            self.splash_total_start = time.time()

        time_elapsed = time.time() - self.splash_start_time
        total_elapsed = time.time() - self.splash_total_start
        image_width, image_height = self.splash_image.get_size()

        # Safeguard with total_elapsed
        total_duration = SPLASH_DURATION_PAN + SPLASH_DURATION_HOLD + SPLASH_DURATION_ZOOM_OUT
        if total_elapsed >= total_duration:
            self.splash_phase = 'done'

        # Fill background for sides
        self.screen.fill((19, 16, 59))  # Or Dark Blue matching pool in splash image

        current_zoom = SPLASH_INITIAL_ZOOM
        visible_height = self.height / current_zoom
        focus_y = 0

        if self.splash_phase == 'pan':
            progress = min(time_elapsed / SPLASH_DURATION_PAN, 1.0)
            if SPLASH_EASING == 'out_cubic':
                easing_progress = 1 - (1 - progress) ** 3
            else:
                easing_progress = progress ** 3

            start_focus_y = image_height - visible_height / 2
            end_focus_y = visible_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress

            if time_elapsed >= SPLASH_DURATION_PAN:
                self.splash_phase = 'hold'
                self.splash_start_time = time.time()

        elif self.splash_phase == 'hold':
            visible_height = self.height / SPLASH_INITIAL_ZOOM
            focus_y = visible_height / 2
            if time_elapsed >= SPLASH_DURATION_HOLD:
                self.splash_phase = 'zoom_out'
                self.splash_start_time = time.time()

        elif self.splash_phase == 'zoom_out':
            progress = min(time_elapsed / SPLASH_DURATION_ZOOM_OUT, 1.0)
            if SPLASH_EASING == 'out_cubic':
                easing_progress = 1 - (1 - progress) ** 3
            else:
                easing_progress = progress ** 3

            fit_zoom = self.height / image_height
            current_zoom = SPLASH_INITIAL_ZOOM - (SPLASH_INITIAL_ZOOM - fit_zoom) * easing_progress
            visible_height = self.height / current_zoom

            start_focus_y = (self.height / SPLASH_INITIAL_ZOOM) / 2
            end_focus_y = image_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress

            if time_elapsed >= SPLASH_DURATION_ZOOM_OUT:
                self.splash_phase = 'done'

        elif self.splash_phase == 'done':
            fit_zoom = self.height / image_height
            current_zoom = fit_zoom
            visible_height = self.height / current_zoom
            focus_y = image_height / 2

        # Derive view_y, clamp, scale, and blit (do this before button so button is on top)
        view_y = max(0, focus_y - visible_height / 2)
        view_y = min(view_y, image_height - visible_height)

        scaled_width = int(image_width * current_zoom)
        scaled_height = int(image_height * current_zoom)
        scaled_image = pygame.transform.smoothscale(self.splash_image, (scaled_width, scaled_height))

        x_pos = (self.width - scaled_width) // 2
        y_pos = -int(view_y * current_zoom)

        self.screen.blit(scaled_image, (x_pos, y_pos))

        # Draw "Start Game" button after image (only in 'done')
        if self.splash_phase == 'done':
            # Buttons (below image or centered)
            # Buttons (spread across bottom with spacing)
            button_y = self.height - SPLASH_BUTTON_HEIGHT - 50  # Bottom padding
            total_buttons_width = 3 * SPLASH_BUTTON_WIDTH + 2 * SPLASH_BUTTON_SPACING  # For 3 buttons
            start_x = self.width // 2 - total_buttons_width // 2  # Center group

            new_game_rect = pygame.Rect(start_x, button_y, SPLASH_BUTTON_WIDTH, SPLASH_BUTTON_HEIGHT)
            self.draw_custom_button(new_game_rect, "New Game", is_hover=new_game_rect.collidepoint(mouse_pos))

            load_game_rect = pygame.Rect(start_x + SPLASH_BUTTON_WIDTH + SPLASH_BUTTON_SPACING, button_y, SPLASH_BUTTON_WIDTH, SPLASH_BUTTON_HEIGHT)
            self.draw_custom_button(load_game_rect, "Load Game", is_hover=load_game_rect.collidepoint(mouse_pos))

            quit_rect = pygame.Rect(start_x + 2 * (SPLASH_BUTTON_WIDTH + SPLASH_BUTTON_SPACING), button_y, SPLASH_BUTTON_WIDTH, SPLASH_BUTTON_HEIGHT)
            self.draw_custom_button(quit_rect, "Quit", is_hover=quit_rect.collidepoint(mouse_pos), is_red=True)  # Red for quit

            return new_game_rect, load_game_rect, quit_rect  # If returned for events

    def draw_init_screen(self):
        """Draws the pouch selection screen with carousel."""
        self.screen.fill(THEME['background'])
        title_text = self.font.render("Choose Your Pouch", True, (THEME['text']))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))
        
        visible_count = 4  # Show 4 at a time
        pouch_rects = []
        box_size = 150
        spacing = 50
        total_width = visible_count * box_size + (visible_count - 1) * spacing
        start_x = (self.width - total_width) // 2
        mouse_pos = pygame.mouse.get_pos()
        
        visible_pouches = POUCHES[self.pouch_offset:self.pouch_offset + visible_count]
        for i, pouch in enumerate(visible_pouches):
            x = start_x + i * (box_size + spacing)
            y = self.height // 3
            rect = pygame.Rect(x, y, box_size, box_size)
            bag_color = COLORS.get(pouch['color'], BAG_COLOR) if pouch.get('unlocked', False) else (100, 100, 100)  # Gray if locked
            pygame.draw.rect(self.screen, bag_color, rect, border_radius=BAG_BORDER_RADIUS)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2, border_radius=BAG_BORDER_RADIUS)
            # Small dice icons peeking out
            inner_rect = pygame.Rect(rect.x + 10, rect.y + 10, box_size - 20, box_size - 20)
            self.draw_pack_icon(inner_rect, 3, [pouch['color']])
            
            # Name below (gray if locked)
            name_color = (THEME['text']) if pouch.get('unlocked', False) else (150, 150, 150)
            name_text = self.small_font.render(pouch['name'], True, name_color)
            self.screen.blit(name_text, (x + (box_size - name_text.get_width()) // 2, y + box_size + 10))
            
            pouch_rects.append((rect, pouch))
            
            # Tooltip on hover (add unlock info if locked)
            if rect.collidepoint(mouse_pos):
                tooltip_text = pouch['desc']
                if not pouch.get('unlocked', False):
                    tooltip_text += "\n(Locked: Win a run to unlock)"  # Customize condition
                self.draw_tooltip(x, y + box_size + 40, tooltip_text)
        
        # Arrows (right always if more, left if offset > 0)
        arrow_size = 40
        right_arrow_rect = None
        left_arrow_rect = None
        if self.pouch_offset + visible_count < len(POUCHES):
            right_arrow_rect = pygame.Rect(self.width - arrow_size - 20, self.height // 2 - arrow_size // 2, arrow_size, arrow_size)
            # Draw right triangle
            points = [(right_arrow_rect.left, right_arrow_rect.centery - 10), (right_arrow_rect.left, right_arrow_rect.centery + 10), (right_arrow_rect.right, right_arrow_rect.centery)]
            pygame.draw.polygon(self.screen, (255, 255, 255), points)
        if self.pouch_offset > 0:
            left_arrow_rect = pygame.Rect(20, self.height // 2 - arrow_size // 2, arrow_size, arrow_size)
            # Draw left triangle
            points = [(left_arrow_rect.right, left_arrow_rect.centery - 10), (left_arrow_rect.right, left_arrow_rect.centery + 10), (left_arrow_rect.left, left_arrow_rect.centery)]
            pygame.draw.polygon(self.screen, (255, 255, 255), points)
        
        # Tutorial button (bottom center) - Stub for now; expand later
        tutorial_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height - BUTTON_HEIGHT - 50, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), tutorial_rect)
        tutorial_text = self.font.render("Tutorial", True, (THEME['text']))
        self.screen.blit(tutorial_text, (tutorial_rect.x + 20, tutorial_rect.y + 10))
        
        return pouch_rects, tutorial_rect, left_arrow_rect, right_arrow_rect
    
    def draw_tutorial_screen(self):
        """Draws the tutorial screen with overlays on mock states."""
        # Save old states to restore after draw
        old_hand = self.hand[:]
        old_rolls = self.rolls[:]
        old_held = self.held[:]
        old_discard_selected = self.discard_selected[:]
        old_is_discard_phase = self.is_discard_phase
        old_has_rolled = self.has_rolled
        old_shop_charms = self.shop_charms[:]
        old_multipliers_hover = self.multipliers_hover
        old_show_popup = self.show_popup
        old_popup_message = self.popup_message

        # Mock data for steps
        mock_colors = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # Varied for visual interest
        mock_dice = [{'id': f'Mock{i}', 'color': mock_colors[i % 5], 'faces': DICE_FACES} for i in range(NUM_DICE_IN_HAND)]
        if self.tutorial_step in [1, 2, 3]:  # Discard, Roll/Hold, Scoring - mock hand/dice
            self.hand = mock_dice
            if self.tutorial_step == 2:  # Step 3: Fixed faces 6,6,2,3,4 and hold first two
                self.rolls = [(mock_dice[0], 6), (mock_dice[1], 6), (mock_dice[2], 2), (mock_dice[3], 3), (mock_dice[4], 4)]
                self.held = [True, True, False, False, False]  # Hold the two 6's (appear smaller)
            else:
                self.rolls = [(die, 1) for die in mock_dice]  # Fixed to 1 pip for other steps
            self.discard_selected = [False] * NUM_DICE_IN_HAND
            if self.tutorial_step == 1:  # Step 2: Show red border on first 2 dice for discard example
                self.discard_selected[0] = True
                self.discard_selected[1] = True
            self.is_discard_phase = (self.tutorial_step == 1)  # Force discard mode for step 2
            self.has_rolled = (self.tutorial_step > 1)  # Show as rolled for steps 3-4
        if self.tutorial_step == 3:  # Scoring - force multipliers panel
            self.multipliers_hover = True  # Open combos panel (assume this triggers it)
        if self.tutorial_step == 4:  # Shop - use specific real charms
            self.shop_charms = [
                {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 100},
                {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},
                {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 'break_penalty': 5},
                {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 50}
            ]  # Exact real charms with your provided dicts (icons via resource_path in draw_shop_screen)

        # Draw underlying mock screen based on step
        if self.tutorial_step == 0:  # Step 1: Pouch selection
            self.draw_init_screen()  # Mock init screen
        elif self.tutorial_step in [1, 2, 3]:  # Steps 2-4: Game phases
            self.draw_game_screen()  # Draws with mock data
        elif self.tutorial_step == 4:  # Step 5: Shop/charms
            self.draw_shop_screen()  # With specific real charms (static, no rotation)
        elif self.tutorial_step == 5:  # Step 6: Blinds progression
            self.draw_blinds_screen()  # Mock blinds

        # Restore old states
        self.hand = old_hand
        self.rolls = old_rolls
        self.held = old_held
        self.discard_selected = old_discard_selected
        self.is_discard_phase = old_is_discard_phase
        self.has_rolled = old_has_rolled
        self.shop_charms = old_shop_charms
        self.multipliers_hover = old_multipliers_hover
        self.show_popup = old_show_popup
        self.popup_message = old_popup_message

        # Overlay semi-transparent background for focus
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-black
        self.screen.blit(overlay, (0, 0))

        # Instructions per step (centered popup-style)
        instructions = [
            "Step 1: Choose Your Pouch\nSelect a starting pouch for bonuses.\nClick a pouch to proceed.",
            "Step 2: Discard Phase\nSelect dice to discard before rolling.\nClick dice to toggle, then 'Discard' button.",
            "Step 3: Roll and Hold\nRoll dice, hold keepers by clicking.\nReroll non-held up to 2 times.",
            "Step 4: Scoring\nForm hands like Pair or Straight.\nClick 'Score' to add points.",
            "Step 5: Shop and Charms\nBuy charms for bonuses.\nDrag to equip, buy/sell in shop.",
            "Step 6: Blinds Progression\nBeat Small/Big/Boss blinds.\nScore enough to advance stakes!"
        ]
        lines = instructions[self.tutorial_step].split('\n')
        y_offset = self.height // 2 - 50 - (len(lines) * 20 // 2)
        if self.tutorial_step == 5:  # Step 6: Shift text down to avoid covering blinds
            y_offset += 100  # Move down by 100 pixels (adjust if needed)
        for line in lines:
            text = self.font.render(line, True, (THEME['text']))
            text_rect = text.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 40  # Spacing

        # Arrows for specific steps (point down to buttons)
        arrow_color = (255, 255, 0)  # Yellow
        arrow_width = 20
        arrow_height = 30
        if self.tutorial_step == 1:  # Step 2: Arrows to discard (bottom left) and start roll (bottom right)
            arrow_offset = -20  # Pixels to shift down (as per your change)
            # Arrow above discard button (bottom left, using LEFT_BUTTON_X)
            button_x = LEFT_BUTTON_X + BUTTON_WIDTH // 2
            button_y = self.height - BUTTON_HEIGHT - 50  # Adjust -50 based on your bottom_y padding in draw_buttons
            points = [
                (button_x - arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top left (wide base above, shifted down)
                (button_x + arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top right
                (button_x, button_y - arrow_offset)   # Bottom point (toward button, shifted down)
            ]
            pygame.draw.polygon(self.screen, arrow_color, points)
            
            # Arrow above start roll button (bottom right, using RIGHT_BUTTON_X)
            button_x = RIGHT_BUTTON_X + BUTTON_WIDTH // 2
            points = [
                (button_x - arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top left
                (button_x + arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top right
                (button_x, button_y - arrow_offset)   # Bottom point
            ]
            pygame.draw.polygon(self.screen, arrow_color, points)
        elif self.tutorial_step == 2:  # Step 3: Arrows below held dice (first two with 6 pips), pointing up
            # Calculate dice positions (mirror your draw_hand logic)
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.width - total_dice_width) // 2
            die_y = self.height - DIE_SIZE - 100  # Base y for dice
            arrow_offset = 25  # Shift down slightly (adjust 5-15 if needed)
            for i in range(2):  # First two dice
                size = DIE_SIZE * HELD_DIE_SCALE  # Held size
                offset = (DIE_SIZE - size) / 2
                die_x = start_x + i * (DIE_SIZE + 20) + offset
                arrow_x = die_x + size // 2  # Center under die
                arrow_y = die_y + size + offset + arrow_offset + 10  # Below die, with gap + shift down
                points = [
                    (arrow_x, arrow_y - arrow_height),  # Top point (toward die, small y)
                    (arrow_x - arrow_width // 2, arrow_y),  # Bottom left (large y)
                    (arrow_x + arrow_width // 2, arrow_y)   # Bottom right
                ]
                pygame.draw.polygon(self.screen, arrow_color, points)
        elif self.tutorial_step == 3:  # Step 4: Arrow to "M" button, pointing up from underneath
            m_button_x = self.width - MULTIPLIERS_BUTTON_SIZE + 13.5  # Shifted right by 13.5
            m_button_y = self.height - MULTIPLIERS_BUTTON_SIZE - 95  # Shifted up by 95 (lower y = higher on screen)
            points = [
                (m_button_x, m_button_y + MULTIPLIERS_BUTTON_SIZE),  # Top point (toward "M" bottom)
                (m_button_x - arrow_width // 2, m_button_y + MULTIPLIERS_BUTTON_SIZE + arrow_height),  # Bottom left (wide base below)
                (m_button_x + arrow_width // 2, m_button_y + MULTIPLIERS_BUTTON_SIZE + arrow_height)   # Bottom right
            ]
            pygame.draw.polygon(self.screen, arrow_color, points)
        # (Keep any other ifs for later steps)

        # Get mouse for hover (add at top of draw_tutorial_screen if not there)
        mouse_pos = pygame.mouse.get_pos()

        # Next/Advance button (top right)
        next_rect = pygame.Rect(self.width - BUTTON_WIDTH - 20, 20, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.draw_custom_button(next_rect, "Next", is_hover=next_rect.collidepoint(mouse_pos))

        # Skip button (top left)
        skip_rect = pygame.Rect(20, 20, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.draw_custom_button(skip_rect, "Skip Tutorial", is_hover=skip_rect.collidepoint(mouse_pos), is_red=True)  # Red for skip/cancel

        return next_rect, skip_rect

    def draw_bag_visual(self):
        """Draws a brown bag with rounded corners and black border, with dice inside."""
        num_dice = len(self.bag)
        if num_dice > 30:
            columns = 6
        else:
            columns = 5
        rows = math.ceil(num_dice / columns)
        grid_width = columns * (SMALL_DIE_SIZE + SMALL_DIE_SPACING) - SMALL_DIE_SPACING
        grid_height = rows * (SMALL_DIE_SIZE + SMALL_DIE_SPACING) - SMALL_DIE_SPACING
        bag_width = grid_width + 2 * BAG_PADDING
        bag_height = grid_height + 2 * BAG_PADDING
        bag_x = self.width - bag_width - 10
        bag_y = 50
        bag_rect = pygame.Rect(bag_x, bag_y, bag_width, bag_height)
        # In draw_game_screen or draw_bag_visual (update the rect draw line)
        bag_color = self.get_bag_color()
        # Draw upside-down triangle at bottom of Z-order
        triangle_points = [
            (bag_x + bag_width // 2, bag_y + 10),  # bottom tip
            (bag_x + bag_width // 2 - 15, bag_y - 10),  # top left
            (bag_x + bag_width // 2 + 15, bag_y - 10)   # top right
        ]
        pygame.draw.polygon(self.screen, bag_color, triangle_points)
        pygame.draw.polygon(self.screen, (0, 0, 0), triangle_points, 2)
        self.draw_rounded_element(bag_rect, bag_color, border_color=(0, 0, 0), border_width=2, radius=BAG_BORDER_RADIUS, inner_content=None)

        sorted_bag = sorted(self.bag, key=lambda d: list(COLORS.keys()).index(d['color']))
        start_x = bag_x + BAG_PADDING
        start_y = bag_y + BAG_PADDING
        index = 0
        current_time = time.time()  # For animation
        for row in range(rows):
            y = start_y + row * (SMALL_DIE_SIZE + SMALL_DIE_SPACING)
            for col in range(columns):
                if index < num_dice:
                    die = sorted_bag[index]
                    x = start_x + col * (SMALL_DIE_SIZE + SMALL_DIE_SPACING)
                    rect = pygame.Rect(x, y, SMALL_DIE_SIZE, SMALL_DIE_SIZE)
                    color = die['color']
                    if color == 'Rainbow':
                        color_index = int(current_time / CYCLE_SPEED) % len(BASE_COLORS)
                        color_rgb = COLORS[BASE_COLORS[color_index]]
                    else:
                        color_rgb = COLORS[color]
                    self.draw_rounded_element(rect, color_rgb, border_color=(0, 0, 0), border_width=1, radius=SMALL_DIE_BORDER_RADIUS, inner_content=None)
                    index += 1
                else:
                    break

    def draw_blinds_screen(self):
        """Draws the blinds selection screen with three boxes for all blinds, horizontally."""
        mouse_pos = pygame.mouse.get_pos()  # For hover
        self.screen.fill(THEME['background'])
        title_text = self.font.render(f"Stake {self.current_stake}", True, (THEME['text']))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 10))
        if self.upcoming_boss_effect is None:
            self.upcoming_boss_effect = random.choice(BOSS_EFFECTS)  # Fallback generate if not set

        blind_order = ['Small', 'Big', 'Boss']
        box_width, box_height = 150, 100
        box_spacing = 50  # Spacing between blind boxes (pixels)
        total_blinds_width = 3 * box_width + 2 * box_spacing
        start_x = (self.width - total_blinds_width) // 2
        start_y = self.height // 3
        for i, blind in enumerate(blind_order):
            x = start_x + i * (box_width + box_spacing)
            rect = pygame.Rect(x, start_y, box_width, box_height)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            # Highlight current blind
            if blind == self.current_blind:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 3)
            blind_text = self.small_font.render(f"{blind} Blind", True, (THEME['text']))
            self.screen.blit(blind_text, (rect.x + (box_width - blind_text.get_width()) // 2, rect.y + 20))
            target_text = self.small_font.render(f"Score: {int(self.get_blind_target(blind))}", True, (THEME['text']))
            self.screen.blit(target_text, (rect.x + (box_width - target_text.get_width()) // 2, rect.y + 50))
            
            # Preview for Boss
            if blind == 'Boss' and self.upcoming_boss_effect:
                effect_str = f"Effect: {self.upcoming_boss_effect['name']} - {self.upcoming_boss_effect['desc']}"
                # Simple wrap if too long (split into lines if > box_width * 1.5)
                lines = []
                words = effect_str.split()
                current_line = ""
                for word in words:
                    if self.small_font.render(current_line + word, True, (255, 0, 0)).get_width() > box_width * 1.5:
                        lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                lines.append(current_line.strip())
                
                y_offset = rect.y + box_height + 10  # Start below box
                for line in lines:
                    effect_text = self.small_font.render(line, True, (255, 0, 0))  # Red for warning
                    self.screen.blit(effect_text, (rect.x + (box_width - effect_text.get_width()) // 2, y_offset))  # Center
                    y_offset += effect_text.get_height() + 5  # Vertical spacing
            elif blind == 'Boss':  # Fallback if no effect (e.g., bug)
                fallback_text = self.small_font.render("Effect: Random", True, (255, 0, 0))
                self.screen.blit(fallback_text, (rect.x + (box_width - fallback_text.get_width()) // 2, rect.y + box_height + 10))

        coins_text = self.small_font.render(f"Coins: {self.coins}", True, (THEME['text']))
        self.screen.blit(coins_text, (self.width // 2 - coins_text.get_width() // 2, self.height // 10 + 50))

        continue_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height // 2 + 150, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.draw_custom_button(continue_rect, "Continue", is_hover=continue_rect.collidepoint(mouse_pos))
        
        debug_button_rect = None
        up_rect = None
        down_rect = None

        if DEBUG:
            # Debug Boss Select Button
            debug_button_text = self.small_font.render("Select Boss (Debug)", True, (0, 255, 0))  # Green for debug
            debug_button_rect = pygame.Rect(self.width - 200, self.height - 100, 180, 40)  # Bottom-right; adjust
            pygame.draw.rect(self.screen, (50, 50, 50), debug_button_rect, border_radius=5)
            self.screen.blit(debug_button_text, (debug_button_rect.x + 10, debug_button_rect.y + 10))
            debug_jump_text = self.small_font.render("Jump to Boss (Debug)", True, (0, 255, 0))  # Green for debug
            debug_jump_rect = pygame.Rect(self.width - 200, self.height - 60, 180, 40)  # Above the select button; adjust y to avoid overlap
            pygame.draw.rect(self.screen, (50, 50, 50), debug_jump_rect, border_radius=5)
            self.screen.blit(debug_jump_text, (debug_jump_rect.x + 10, debug_jump_rect.y + 10))
            
            if self.debug_boss_dropdown_open:
                # Dropdown Panel: Scrollable list
                panel_width, panel_height = 300, 300  # Size for ~10-15 visible items
                
                # Position: Above the button, hugging right side
                panel_x = self.width - panel_width - 10  # Hug right with padding
                panel_y = debug_button_rect.y - panel_height - 10  # Above button with padding
                
                # Adaptive: If above clips top, shift below as fallback
                if panel_y < 0:
                    panel_y = debug_button_rect.y + debug_button_rect.height + 10
                
                pygame.draw.rect(self.screen, (20, 20, 20), (panel_x, panel_y, panel_width, panel_height))  # Dark panel
                
                item_height = 25  # Each effect row
                visible_items = panel_height // item_height
                total_items = len(BOSS_EFFECTS)
                
                # Scroll arrows (simple up/down buttons)
                up_rect = pygame.Rect(panel_x + panel_width - 30, panel_y, 30, 30)
                down_rect = pygame.Rect(panel_x + panel_width - 30, panel_y + panel_height - 30, 30, 30)
                pygame.draw.rect(self.screen, (100, 100, 100), up_rect)
                pygame.draw.rect(self.screen, (100, 100, 100), down_rect)
                self.screen.blit(self.small_font.render("^", True, (THEME['text'])), (up_rect.x + 10, up_rect.y + 5))
                self.screen.blit(self.small_font.render("v", True, (THEME['text'])), (down_rect.x + 10, down_rect.y + 5))

                # Render visible effects
                for i in range(self.debug_boss_scroll_offset, min(self.debug_boss_scroll_offset + visible_items, total_items)):
                    effect = BOSS_EFFECTS[i]
                    item_text = self.small_font.render(f"{effect['name']}: {effect['desc'][:30]}...", True, (THEME['text']))  # Truncate long desc
                    item_y = panel_y + (i - self.debug_boss_scroll_offset) * item_height + 5
                    self.screen.blit(item_text, (panel_x + 10, item_y))
        
        # Update return to include debug rects
        return continue_rect, debug_button_rect, up_rect, down_rect, debug_jump_rect

    def draw_game_over_screen(self):
        """Draws the game over screen."""
        self.screen.fill(THEME['background'])
        title_text = self.font.render("Game Over", True, (255, 0, 0))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 5))

        score_text = self.small_font.render(f"Final Score: {self.round_score}", True, (THEME['text']))
        self.screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 5 + 100))
        coins_text = self.small_font.render(f"Coins: {self.coins}", True, (THEME['text']))
        self.screen.blit(coins_text, (self.width // 2 - coins_text.get_width() // 2, self.height // 5 + 150))
        stake_text = self.small_font.render(f"Reached Stake: {self.current_stake}", True, (THEME['text']))
        self.screen.blit(stake_text, (self.width // 2 - stake_text.get_width() // 2, self.height // 5 + 200))

        restart_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height // 5 + 300, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), restart_rect)
        restart_text = self.font.render("Restart", True, (THEME['text']))
        self.screen.blit(restart_text, (restart_rect.x + 20, restart_rect.y + 10))
        
        return restart_rect

    def draw_pack_select_screen(self):
        """Draws the pack selection screen."""
        self.screen.fill(THEME['background'])
        title_text = self.font.render("Choose Hand to Boost (+0.5x mult)", True, (THEME['text']))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        choice_rects = []
        total_width = len(self.pack_choices) * 120 + (len(self.pack_choices) - 1) * 10
        start_x = (self.width - total_width) // 2
        for i, hand_type in enumerate(self.pack_choices):
            x = start_x + i * (120 + 10)
            y = self.height // 2 - 60
            choice_rect = pygame.Rect(x, y, 120, 120)
            self.draw_hand_type_icon(choice_rect, hand_type)
            choice_rects.append(choice_rect)
            # Inside the for loop after drawing choice_rect
            if choice_rect.collidepoint(pygame.mouse.get_pos()):
                tooltip_text = f"Upgrade {hand_type} by +0.5x mult"
                self.draw_tooltip(choice_rect.x, choice_rect.y + choice_rect.height + 5, tooltip_text)

        return choice_rects

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
            for dot_pos in DOT_POSITIONS.get(value, []):
                dot_x = die_rect.x + dot_pos[0] * die_size
                dot_y = die_rect.y + dot_pos[1] * die_size
                pygame.draw.circle(self.screen, (0, 0, 0), (int(dot_x), int(dot_y)), 2)

    def draw_dice_select_screen(self):
        """Draws the dice selection screen for choosing a die from pack."""
        self.screen.fill(THEME['background'])
        title_text = self.font.render("Choose a Die to Add", True, (THEME['text']))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        choice_rects = []
        total_width = len(self.pack_choices) * 120 + (len(self.pack_choices) - 1) * 10
        start_x = (self.width - total_width) // 2
        current_time = time.time()  # For animation
        for i, color in enumerate(self.pack_choices):
            x = start_x + i * (120 + 10)
            y = self.height // 2 - 60
            choice_rect = pygame.Rect(x, y, 120, 120)
            die_rect = pygame.Rect(choice_rect.x + 10, choice_rect.y + 10, DIE_SIZE, DIE_SIZE)
            if color == 'Rainbow':
                color_index = int(current_time / CYCLE_SPEED) % len(BASE_COLORS)
                color_rgb = COLORS[BASE_COLORS[color_index]]
            else:
                color_rgb = COLORS[color]
            pygame.draw.rect(self.screen, color_rgb, die_rect, border_radius=DIE_BORDER_RADIUS)
            pygame.draw.rect(self.screen, (0, 0, 0), die_rect, 2, border_radius=DIE_BORDER_RADIUS)
            # Single pip
            pygame.draw.circle(self.screen, (0, 0, 0), die_rect.center, DOT_RADIUS)
            choice_rects.append((choice_rect, color))
        mouse_pos = pygame.mouse.get_pos()
        for rect, color in choice_rects:
            if rect.collidepoint(mouse_pos):
                tooltip_text = DICE_DESCRIPTIONS.get(color, f"Add 1 {color} Die")  # Fallback
                self.draw_tooltip(rect.x, rect.y + CHARM_BOX_HEIGHT + 30, tooltip_text)
                break

        return choice_rects

    def draw_confirm_sell_popup(self):
        """Draws a small confirmation popup for selling a charm."""
        popup_width, popup_height = 300, 150
        popup_rect = pygame.Rect(self.width // 2 - popup_width // 2, self.height // 2 - popup_height // 2, popup_width, popup_height)
        pygame.draw.rect(self.screen, (100, 100, 100), popup_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), popup_rect, 3)

        message_text = self.small_font.render("Are you sure you want to sell this charm?", True, (THEME['text']))
        self.screen.blit(message_text, (popup_rect.x + (popup_width - message_text.get_width()) // 2, popup_rect.y + 30))

        yes_rect = pygame.Rect(popup_rect.x + 50, popup_rect.y + 80, 100, 40)
        pygame.draw.rect(self.screen, (0, 150, 0), yes_rect)
        yes_text = self.small_font.render("Yes", True, (THEME['text']))
        self.screen.blit(yes_text, (yes_rect.x + (100 - yes_text.get_width()) // 2, yes_rect.y + 10))

        no_rect = pygame.Rect(popup_rect.x + popup_width - 150, popup_rect.y + 80, 100, 40)
        pygame.draw.rect(self.screen, (150, 0, 0), no_rect)
        no_text = self.small_font.render("No", True, (THEME['text']))
        self.screen.blit(no_text, (no_rect.x + (100 - no_text.get_width()) // 2, no_rect.y + 10))

        return yes_rect, no_rect

    def reset_game(self):
        """Resets the game to initial state."""
        self.current_stake = 1
        self.current_blind = 'Small'
        self.coins = 0
        self.equipped_charms = []
        self.shop_charms = []
        self.hand_multipliers = {ht: 1.0 for ht in HAND_TYPES}
        self.pack_choices = []
        self.confirm_sell_index = -1
        self.bag = create_dice_bag()        
        self.full_bag = [d.copy() for d in self.bag]
        self.round_score = 0
        self.hands_left = MAX_HANDS
        self.discards_left = MAX_DISCARDS
        self.score_mult = 1.0
        self.shop_reroll_cost = 5
        self.available_packs = random.sample([0, 1, 2, 3, 4], 2)
        self.multipliers_hover = False  # For showing multipliers panel
        self.charms_pool = [
            {'name': 'Basic Charm', 'rarity': 'Common', 'cost': 2, 'desc': '+10 to all final scores.', 'type': 'flat_bonus', 
             'value': 10},
            {'name': 'Red Greed Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Red die scored.',
             'type': 'per_color_bonus', 'color': 'Red', 'value': 5},
            {'name': 'Blue Lust Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Blue die scored.',
             'type': 'per_color_bonus', 'color': 'Blue', 'value': 5},
            {'name': 'Green Wrath Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Green die scored.',
             'type': 'per_color_bonus', 'color': 'Green', 'value': 5},
            {'name': 'Purple Glutton Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Purple die scored.',
             'type': 'per_color_bonus', 'color': 'Purple', 'value': 5},
            {'name': 'Yellow Jolly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Yellow die scored.',
             'type': 'per_color_bonus', 'color': 'Yellow', 'value': 5},
            {'name': 'Zany Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+40 score if hand contains a 3 of a Kind.',
             'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 40},
            {'name': 'Mad Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+30 score if hand contains a 2 Pair.', 'type': 'hand_bonus',
              'hands': ['2 Pair'], 'value': 30},
            {'name': 'Crazy Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+35 score if hand contains a Small or Large Straight.', 
             'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 35},
            {'name': 'Droll Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to monochrome multipliers.', 
             'type': 'mono_mult_bonus', 'value': 0.5},
            {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 
             'type': 'hand_bonus', 'hands': ['Pair'], 'value': 50},
            {'name': 'Wily Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+100 base score if hand contains a 3 of a Kind.', 
             'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 100},
            {'name': 'Clever Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+80 base score if hand contains a 2 Pair.', 
             'type': 'hand_bonus', 'hands': ['2 Pair'], 'value': 80},
            {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 
             'hands': ['Small Straight', 'Large Straight'], 'value': 100},
            {'name': 'Half Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+20 score if hand uses 3 or fewer dice.', 
             'type': 'few_dice_bonus', 'max_dice': 3, 'value': 20},
            {'name': 'Stencil Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 
             'x1 multiplier for each empty charm slot (including this one).', 'type': 'empty_slot_mult', 'value': 1.0},
            {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},
            {'name': 'Mime Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
             'Retrigger effects of held dice (e.g., double Gold coins, Glass mult/break chance).', 'type': 'retrigger_held'},
            {'name': 'Debt Charm', 'rarity': 'Common', 'cost': 2, 'desc': 'Allows going into negative coins for shop buys (up to -5).',
              'type': 'negative_coins', 'limit': -5},
            {'name': 'Dagger Charm', 'rarity': 'Rare', 'cost': 10, 
             'desc': 'When blind starts, sacrifice a charm to the right and add 0.25x its cost to your score multiplier permanently. (Max 10x)', 
             'type': 'sacrifice_mult'},
            {'name': 'Golden Touch Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+2 coins per Gold die held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Gold', 'value': 2},
            {'name': 'Silver Lining Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
             '+2 coins per Silver die not held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Silver', 
             'value': 2},
            {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
             'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 
             'break_penalty': 5},
            {'name': 'Even Stevens Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per even-valued die scored.', 'type': 
             'per_value_bonus', 'parity': 'even', 'value': 5},
            {'name': 'Oddball Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per odd-valued die scored.', 'type': 
             'per_value_bonus', 'parity': 'odd', 'value': 5},
            {'name': 'Rainbow Prism Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to rainbow multipliers.', 'type': 
             'rainbow_mult_bonus', 'value': 0.5},
            {'name': 'Full House Party Charm', 'rarity': 'Rare', 'cost': 6, 'desc': '+150 base score if hand contains a Full House.', 
             'type': 'hand_bonus', 'hands': ['Full House'], 'value': 150},
            {'name': 'Quadruple Threat Charm', 'rarity': 'Rare', 'cost': 7, 'desc': '+200 base score if hand contains a 4 of a Kind.', 
             'type': 'hand_bonus', 'hands': ['4 of a Kind'], 'value': 200},
            {'name': 'Reroll Recycler Charm', 'rarity': 'Rare', 'cost': 8, 'desc': 
             'Gain 1 extra reroll in the turn if you use a discard.', 'type': 'reroll_recycler'},
            {'name': 'Interest Booster Charm', 'rarity': 'Common', 'cost': 3, 'desc': 
             'Increases max coins for interest calculation by 20.', 'type': 'interest_max_bonus', 'value': 20},
        ]
        self.selected_pouch = None
        self.green_pouch_active = False
        self.upcoming_boss_effect = None

    def apply_pouch(self, pouch):
        """Applies the selected pouch's bonuses to the game state."""
        self.selected_pouch = pouch
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

    def draw_text(self):
        """Draws current hand info, score, rerolls, discards, etc."""
        # Current hand type and score
        hand_text = self.small_font.render(self.current_hand_text, True, (THEME['text']))
        self.screen.blit(hand_text, (50, 120))
        
        # Color modifier with special handling for "(disabled)"
        if " (disabled)" in self.current_modifier_text:
            base_modifier = self.current_modifier_text.replace(" (disabled)", "")
            base_render = self.small_font.render(base_modifier, True, THEME['text'])
            disabled_render = self.small_font.render(" (disabled)", True, (255, 0, 0))  # Red for disabled
            self.screen.blit(base_render, (50, 150))
            self.screen.blit(disabled_render, (50 + base_render.get_width(), 150))  # Append right after base
        else:
            modifier_text = self.small_font.render(self.current_modifier_text, True, (THEME['text']))
            self.screen.blit(modifier_text, (50, 150))
        
        # Score
        score_text = self.small_font.render(f"Score: {self.round_score}/{int(self.get_blind_target())}", True, (THEME['text']))
        self.screen.blit(score_text, (50, 180))

    def draw_pack_icon(self, pack_rect, num_dice, cycle_colors=COLOR_CYCLE):
        """Draws animated dice pack icon."""
        box_size = min(pack_rect.width, pack_rect.height) - 20  # Smaller inner box to center
        box_rect = pygame.Rect(pack_rect.x + (pack_rect.width - box_size) // 2, pack_rect.y + (pack_rect.height - box_size) // 2, box_size, box_size)
        pygame.draw.rect(self.screen, (0, 0, 0), box_rect, 2)

        inner_rect = box_rect.inflate(-10, -10)  # Same padding as prism

        current_time = time.time()
        if num_dice <= 3:  # Horizontal row for small num
            spacing = box_size / (num_dice + 1)  # Even spacing
            for i in range(num_dice):
                color_index = int((current_time + i * 0.2) % len(cycle_colors))
                color = cycle_colors[color_index]
                x = box_rect.x + spacing * (i + 1) - SMALL_ICON_DIE_SIZE // 2
                y = box_rect.y + box_size // 2 - SMALL_ICON_DIE_SIZE // 2  # Center vertically
                die_rect = pygame.Rect(x, y, SMALL_ICON_DIE_SIZE, SMALL_ICON_DIE_SIZE)
                pygame.draw.rect(self.screen, COLORS[color], die_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), die_rect, 1)
                # Single pip
                pygame.draw.circle(self.screen, (0, 0, 0), die_rect.center, 2)
        else:  # Grid for larger num (e.g., 2x2 for 4)
            cols = math.ceil(math.sqrt(num_dice))  # Simple grid
            rows = math.ceil(num_dice / cols)
            cell_size = box_size / max(cols, rows)
            for i in range(num_dice):
                color_index = int((current_time + i * 0.2) % len(cycle_colors))
                color = cycle_colors[color_index]
                col = i % cols
                row = i // cols
                x = box_rect.x + col * cell_size + (cell_size - SMALL_ICON_DIE_SIZE) // 2
                y = box_rect.y + row * cell_size + (cell_size - SMALL_ICON_DIE_SIZE) // 2
                die_rect = pygame.Rect(x, y, SMALL_ICON_DIE_SIZE, SMALL_ICON_DIE_SIZE)
                pygame.draw.rect(self.screen, COLORS[color], die_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), die_rect, 1)
                # Single pip
                pygame.draw.circle(self.screen, (0, 0, 0), die_rect.center, 2)


    def draw_ui_panel(self):
        """Draws the UI panel with hands, discards, rolls left."""
        panel_x = 50
        panel_y = self.height - BUTTON_HEIGHT - 20 - UI_PANEL_HEIGHT - 10  # Above discard button
        panel_rect = pygame.Rect(panel_x, panel_y, UI_PANEL_WIDTH, UI_PANEL_HEIGHT)
        self.draw_rounded_element(panel_rect, THEME['panel_bg'], border_color=THEME['border'], border_width=2, radius=UI_PANEL_BORDER_RADIUS, inner_content=None)

        # Texts inside
        hands_text = self.tiny_font.render(f"Hands: {self.hands_left}", True, (THEME['text']))
        self.screen.blit(hands_text, (panel_x + 10, panel_y + 10))
        discards_text = self.tiny_font.render(f"Discards: {self.discards_left}", True, (THEME['text']))
        self.screen.blit(discards_text, (panel_x + 10, panel_y + 40))
        rolls_text = self.tiny_font.render(f"Rolls Left: {self.rerolls_left if self.rerolls_left >= 0 else '∞'}", True, (THEME['text']))
        self.screen.blit(rolls_text, (panel_x + 10, panel_y + 70))
        coins_text = self.tiny_font.render(f"Coins: {self.coins}", True, (THEME['text']))
        self.screen.blit(coins_text, (panel_x + 10, panel_y + 100))

    def generate_shop(self):
        self.shop_reroll_cost = 5
        all_packs = [0, 1, 2, 3, 4, 5]
        weights = [1, 1, 1, 1, 1, 0.5]  # Lower for special (rarer)
        self.available_packs = random.choices(all_packs, weights=weights, k=2)
        num_shop = min(3, len(self.charms_pool))
        available_pool = [c for c in self.charms_pool if c['name'] not in [e['name'] for e in self.equipped_charms]]
        self.shop_charms = random.sample(available_pool, min(num_shop, len(available_pool)))

    def reroll_shop(self):
        if self.coins >= self.shop_reroll_cost:
            self.coins -= self.shop_reroll_cost
            self.shop_reroll_cost += 3
            self.generate_shop()

    def draw_shop_screen(self):
        """Draws the shop screen with equipped charms (sell), shop charms (buy), and Prism Packs."""
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(THEME['background'])

        # Reposition "Shop" text to top left, above equipped charms
        shop_y = 40  # Above charms at y=150; adjust if charms y changes
        shop_text = self.font.render("Shop", True, (THEME['text']))  # Or your exact text/color
        shop_text_x = 50  # Top left with padding (matches LEFT_BUTTON_X)
        self.screen.blit(shop_text, (shop_text_x, shop_y))

        # Reposition "Coins" text below "Shop" (still top left)
        coins_y = shop_y + 40  # Below "Shop" for stacking
        coins_text = self.font.render(f"Coins: {self.coins}", True, (THEME['text']))  # Or your format
        coins_text_x = 50  # Same left alignment
        self.screen.blit(coins_text, (coins_text_x, coins_y))

        # Position reroll button top left, right of "Coins" text
        reroll_x = coins_text_x + coins_text.get_width() + 20  # Right of coins with padding
        reroll_y = coins_y - 10  # Align vertically with coins (slight offset if needed)
        reroll_rect = pygame.Rect(reroll_x, reroll_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.draw_custom_button(reroll_rect, "Reroll (5)", is_hover=reroll_rect.collidepoint(mouse_pos))  # Assuming mouse_pos defined at top of method

        # Define large panel for purchasables (shop charms and packs, expanded for future additions)
        panel_width = int(self.width * 0.9)  # 90% width for more space
        panel_height = int(self.height * 0.7)  # 70% height to cover more unused area, leaving room above/below
        panel_x = (self.width - panel_width) // 2  # Center horizontally
        panel_y = 280  # Below equipped charms and titles, to enclose shop items
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # Draw panel background with rounded corners
        pygame.draw.rect(self.screen, UI_PANEL_COLOR, panel_rect, border_radius=15)

        # Draw black border with rounded corners
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, width=2, border_radius=15)

        # Equipped charms horizontal at top (outside panel)
        equipped_title = self.small_font.render("Equipped Charms", True, (THEME['text']))
        self.screen.blit(equipped_title, (50, 120))
        
        # Initialize lists and hover here
        sell_rects = []
        equipped_rects = []
        equipped_hover = None
        
        for i, charm in enumerate(self.equipped_charms):
            if i == self.dragging_charm_index and self.dragging_shop:
                continue
            x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
            y = 150
            eq_rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            icon_rect = pygame.Rect(eq_rect.x + (CHARM_BOX_WIDTH - CHARM_DIE_SIZE) // 2, eq_rect.y + 10, CHARM_DIE_SIZE, CHARM_DIE_SIZE)  # Adjusted padding
            self.draw_charm_die(icon_rect, charm)
            sell_val = charm['cost'] // 2
            sell_label = self.tiny_font.render(f"Sell: {sell_val}", True, (THEME['text']))
            self.screen.blit(sell_label, (eq_rect.x + 5, eq_rect.y + CHARM_BOX_HEIGHT - 30))  # Moved lower
            sell_rect = pygame.Rect(eq_rect.x + CHARM_BOX_WIDTH - 60, eq_rect.y + CHARM_BOX_HEIGHT - 30, 50, 20)
            pygame.draw.rect(self.screen, (150, 0, 0), sell_rect)
            sell_text = self.tiny_font.render("Sell", True, (THEME['text']))
            self.screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 3))
            sell_rects.append(sell_rect)
            equipped_rects.append(eq_rect)
            if eq_rect.collidepoint(mouse_pos):
                tooltip_text = charm['name'] + ": " + charm['desc']
                if charm['type'] == 'sacrifice_mult':
                    tooltip_text += f" (Current mult: x{self.score_mult})"
                    if self.score_mult < 10.0:
                        tooltip_text += " (max x10)"
                elif charm['type'] == 'empty_slot_mult':
                    current_mult = self.get_stencil_mult()
                    tooltip_text += f" (Current: x{current_mult})"
                equipped_hover = (x, y + CHARM_BOX_HEIGHT + 5, tooltip_text)
        
        # Draw dragged charm in shop
        if self.dragging_charm_index != -1 and self.dragging_shop:
            charm = self.equipped_charms[self.dragging_charm_index]
            x = mouse_pos[0] - self.drag_offset_x
            y = mouse_pos[1] - self.drag_offset_y
            rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)  # Use shop box size
            self.draw_charm_die(rect, charm)

        # Inner padding for items inside panel
        inner_padding = 20

        # Shop charms horizontal inside panel (top section, leaving space below for future)
        shop_title = self.small_font.render("Shop Charms", True, (THEME['text']))
        self.screen.blit(shop_title, (panel_x + inner_padding, panel_y + inner_padding - 20))  # Title inside/top of panel
        
        # Initialize lists and hover here
        buy_rects = []
        shop_rects = []
        shop_hover = None
        
        shop_charms_y = panel_y + inner_padding
        for i, charm in enumerate(self.shop_charms):
            x = panel_x + inner_padding + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
            y = shop_charms_y
            shop_rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            icon_rect = pygame.Rect(shop_rect.x + (CHARM_BOX_WIDTH - CHARM_DIE_SIZE) // 2, shop_rect.y + 10, CHARM_DIE_SIZE, CHARM_DIE_SIZE)
            self.draw_charm_die(icon_rect, charm)
            cost_label = self.tiny_font.render(f"Cost: {charm['cost']}", True, (THEME['text']))
            self.screen.blit(cost_label, (shop_rect.x + 5, shop_rect.y + CHARM_BOX_HEIGHT - 30))
            buy_rect = pygame.Rect(shop_rect.x + CHARM_BOX_WIDTH - 60, shop_rect.y + CHARM_BOX_HEIGHT - 30, 50, 20)
            pygame.draw.rect(self.screen, (0, 150, 0), buy_rect)
            buy_text = self.tiny_font.render("Buy", True, (THEME['text']))
            self.screen.blit(buy_text, (buy_rect.x + 10, buy_rect.y + 3))
            buy_rects.append(buy_rect)
            shop_rects.append(shop_rect)
            if shop_rect.collidepoint(mouse_pos):
                tooltip_text = charm['name'] + ": " + charm['desc']
                if charm['type'] == 'empty_slot_mult':
                    preview_mult = charm['value'] * (self.max_charms - len(self.equipped_charms))
                    tooltip_text += f" (If bought: x{preview_mult})"
                shop_hover = (x, y + CHARM_BOX_HEIGHT + 5, tooltip_text)

        # Packs section inside panel (below shop charms, with space for future additions above/below/sides)
        pack_title = self.small_font.render("Packs", True, (THEME['text']))
        self.screen.blit(pack_title, (panel_x + inner_padding, shop_charms_y + CHARM_BOX_HEIGHT + 20))  # Below shop charms

        pack_y = shop_charms_y + CHARM_BOX_HEIGHT + 50  # Space below charms
        pack_rects = []
        pack_costs = [3, 5, 7, 3, 5, 9]
        pack_choices_num = [2, 3, 5, 3, 4, 3]
        pack_names = ["Basic Prism (1 of 2)", "Standard Prism (1 of 3)", "Premium Prism (1 of 5)", "Dice Pack (1 of 3)", "Dice Pack (1 of 4)", "Special Dice Pack (1 of 3)"]
        pack_x_start = panel_x + inner_padding  # Left-aligned (restore original start)
        pack_x = pack_x_start
        for pack_idx in self.available_packs:
            x = pack_x
            y = pack_y
            pack_rect = pygame.Rect(x, y, 80, 80)  # Restore local size=80 (larger, less cramped)
            # Draw icon centered (updated methods handle)
            if pack_idx in [0,1,2]:
                self.draw_prism_pack_icon(pack_idx, pack_rect.x, pack_rect.y + 10)
            else:
                cycle = BASE_COLORS if pack_idx in [3,4] else SPECIAL_COLORS
                self.draw_pack_icon(pack_rect, pack_choices_num[pack_idx], cycle)
            if pack_rect.collidepoint(mouse_pos):
                tooltip_text = f"{pack_names[pack_idx]}\nCost: {pack_costs[pack_idx]}"
                tooltip_y = pack_rect.y + 80 + 5  # Lowered
                if tooltip_y + 50 > self.height:
                    tooltip_y = pack_rect.y - 60
                self.draw_tooltip(pack_rect.x, tooltip_y, tooltip_text)
            pack_rects.append((pack_rect, pack_idx))
            pack_x += 80 + 10  # Restore tighter spacing (adjust to 20 if still cramped)

        # Draw tooltips after all elements
        if equipped_hover:
            self.draw_tooltip(*equipped_hover)
        if shop_hover:
            self.draw_tooltip(*shop_hover)

        # Current hand multipliers panel in top right corner
        mult_title = self.small_font.render("Hand Multipliers", True, (THEME['text']))
        mult_x = self.width - 200  # Far right with padding
        mult_y = 50  # Top, aligned with "Shop"
        self.screen.blit(mult_title, (mult_x, mult_y))
        y_offset = mult_y + 30  # Below title
        for ht, mult in self.hand_multipliers.items():
            mult_text = self.tiny_font.render(f"{ht}: x{mult:.1f}", True, (THEME['text']))
            self.screen.blit(mult_text, (mult_x, y_offset))
            y_offset += 25

        # Position continue button left of hand multipliers (top right, aligned with title)
        continue_x = mult_x - BUTTON_WIDTH - 20  # Left of multipliers with padding
        continue_y = mult_y  # Align with multipliers title
        continue_rect = pygame.Rect(continue_x, continue_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.draw_custom_button(continue_rect, "Continue", is_hover=continue_rect.collidepoint(mouse_pos))  # No is_red for positive action
        
        return continue_rect, sell_rects, buy_rects, equipped_rects, shop_rects, pack_rects, reroll_rect
    
    def draw_prism_pack_icon(self, pack_idx, x, y):
        box_rect = pygame.Rect(x, y, PACK_BOX_SIZE, PACK_BOX_SIZE)
        self.draw_rounded_element(box_rect, (200, 200, 200), border_color=(0, 0, 0), border_width=2, radius=10)

        # Inner icon: Blit image if cached, else fallback
        inner_rect = box_rect.inflate(-10, -10)  # Padded

        if pack_idx in self.pack_icon_cache:
            icon_surf = self.pack_icon_cache[pack_idx]
            icon_rect = icon_surf.get_rect(center=inner_rect.center)
            self.screen.blit(icon_surf, icon_rect)
        else:
            # Fallback: Old 5 pips (or add print("Missing pack icon") for debug)
            dot_radius = inner_rect.width // 10
            positions = DOT_POSITIONS[5]
            for pos in positions:
                dot_x = inner_rect.x + int(pos[0] * inner_rect.width)
                dot_y = inner_rect.y + int(pos[1] * inner_rect.height)
                pygame.draw.circle(self.screen, (0, 0, 0), (dot_x, dot_y), dot_radius)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            clock = pygame.time.Clock()  # Add at top of run()
            self.screen.fill(THEME['background'])  # Card table green background

            # Initialize conditional rects to None to prevent UnboundLocalError
            continue_rect = None
            pouch_rects = None
            tutorial_rect = None
            sell_rects = None
            buy_rects = None
            equipped_rects = None
            shop_rects = None
            pack_rects = None
            reroll_rect = None
            choice_rects = None  # For pack_select and dice_select
            yes_rect = None
            no_rect = None
            restart_rect = None

            # Draw base for current or previous (if paused)
            draw_state = self.previous_state if self.game_state == 'pause_menu' else self.game_state

            if self.game_state == 'splash':
                self.draw_splash_screen()
            elif self.game_state == 'game':
                self.draw_game_screen()
            # In the draw section of run() (before for event loop), change the 'init' elif to unpack all 4 returns
            elif self.game_state == 'init':
                pouch_rects, tutorial_rect, left_arrow_rect, right_arrow_rect = self.draw_init_screen()
            elif self.game_state == 'blinds':
                continue_rect = self.draw_blinds_screen()
            elif self.game_state == 'shop':
                continue_rect, sell_rects, buy_rects, equipped_rects, shop_rects, pack_rects, reroll_rect = self.draw_shop_screen()
            elif self.game_state == 'pack_select':
                choice_rects = self.draw_pack_select_screen()
            elif self.game_state == 'dice_select':
                choice_rects = self.draw_dice_select_screen()
            elif self.game_state == 'confirm_sell':
                self.draw_shop_screen()  # Redraw shop underneath popup
                yes_rect, no_rect = self.draw_confirm_sell_popup()
            elif self.game_state == 'game_over':
                restart_rect = self.draw_game_over_screen()
            elif self.game_state == 'tutorial':
                next_rect, skip_rect = self.draw_tutorial_screen()

            if self.show_popup:
                self.draw_popup()

            # Overlay pause if active
            if self.game_state == 'pause_menu':
                self.draw_pause_menu()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == 'pause_menu':
                            self.game_state = self.previous_state  # Exit pause and restore previous state
                        elif self.game_state == 'splash':
                            self.game_state = 'blinds'  # Skip splash on ESC
                        else:
                            self.previous_state = self.game_state  # Save current state
                            self.game_state = 'pause_menu'  # Enter pause
                    if self.game_state == 'tutorial':
                        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                            self.tutorial_step += 1
                            if self.tutorial_step > 5:
                                self.tutorial_completed = True
                                self.tutorial_mode = False
                                self.game_state = 'init'
                        elif event.key == pygame.K_ESCAPE:
                            self.tutorial_completed = True
                            self.tutorial_mode = False
                            self.game_state = 'init'  # Skip on ESC
                    # ... existing other KEYDOWN code ...
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = max(event.w, 600), max(event.h, 400)
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    changed_state = False  # Step 1: Add flag
                    # Start of the corrected splash handling block.
                    # This replaces your entire old splash if-elif structure.
                    # It checks if the state is 'splash' and handles phase-specific logic without mid-state changes.
                    if self.game_state == 'splash':
                        if self.splash_phase == 'done':
                            # Button rect (re-calc for click)
                            button_rect = pygame.Rect((self.width - SPLASH_BUTTON_WIDTH) // 2, self.height - SPLASH_BUTTON_HEIGHT - 50, SPLASH_BUTTON_WIDTH, SPLASH_BUTTON_HEIGHT)
                            if button_rect.collidepoint(mouse_pos):                                
                                self.game_state = 'init'  # Start game
                                changed_state = True  # Step 2: Set flag on state change
                        else:
                            self.splash_phase = 'done'  # Jump directly to done to show button immediately
                    # End of the corrected splash handling block.
                    elif self.game_state == 'init':
                        # No re-call to draw_init_screen() - use pre-computed rects from draw section
                        for rect, pouch in pouch_rects:
                            if rect.collidepoint(mouse_pos) and pouch.get('unlocked', False):
                                self.apply_pouch(pouch)
                                self.game_state = 'blinds'
                                break
                        if tutorial_rect and tutorial_rect.collidepoint(mouse_pos):
                            self.tutorial_mode = True
                            self.game_state = 'tutorial'
                            self.tutorial_step = 0  # Start from beginning
                        if left_arrow_rect and left_arrow_rect.collidepoint(mouse_pos):
                            self.pouch_offset = max(0, self.pouch_offset - 4)
                        if right_arrow_rect and right_arrow_rect.collidepoint(mouse_pos):
                            self.pouch_offset += 4

                    elif self.game_state == 'tutorial':
                        next_rect, skip_rect = self.draw_tutorial_screen()  # Re-compute if needed
                        if next_rect.collidepoint(mouse_pos):
                            self.tutorial_step += 1
                            if self.tutorial_step > 5:  # After last step
                                self.tutorial_completed = True
                                self.tutorial_mode = False
                                self.game_state = 'init'  # Return to pouch selection
                        if skip_rect.collidepoint(mouse_pos):
                            self.tutorial_completed = True
                            self.tutorial_mode = False
                            self.game_state = 'init'  # Skip to init

                    if changed_state:
                        continue  # Step 3: Skip further processing this event

                    if self.game_state == 'game':
                        if self.show_popup:
                            continue_rect = self.draw_popup()
                            if continue_rect and continue_rect.collidepoint(mouse_pos):
                                self.show_popup = False
                                self.advance_blind()  # Delayed reset of hands, discards, bag
                                self.generate_shop()
                                self.game_state = 'shop'  # Go to shop after popup
                                changed_state = True  # Optional: Add for robustness if this change could cause issues
                        else:
                            # Check clicks on dice
                            for i in range(NUM_DICE_IN_HAND):
                                total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
                                start_x = (self.width - total_dice_width) // 2
                                x = start_x + i * (DIE_SIZE + 20)
                                size = DIE_SIZE * HELD_DIE_SCALE if self.held[i] else DIE_SIZE
                                offset = (DIE_SIZE - DIE_SIZE * HELD_DIE_SCALE) / 2 if self.held[i] else 0
                                die_rect = pygame.Rect(x + offset, self.height - DIE_SIZE - 100 + offset, size, size)
                                if die_rect.collidepoint(mouse_pos):
                                    if self.is_discard_phase:
                                        self.toggle_discard(i)
                                    else:
                                        self.toggle_hold(i)
                            # Check button clicks
                            reroll_rect, discard_rect, start_roll_rect, score_rect, end_turn_rect = self.draw_buttons()
                            if reroll_rect and reroll_rect.collidepoint(mouse_pos):
                                self.reroll()
                            if discard_rect and discard_rect.collidepoint(mouse_pos):
                                self.discard()
                            if start_roll_rect and start_roll_rect.collidepoint(mouse_pos):
                                self.start_roll_phase()
                            if DEBUG and score_rect and score_rect.collidepoint(mouse_pos):
                                self.score_and_new_turn()
                            if end_turn_rect and end_turn_rect.collidepoint(mouse_pos):
                                self.score_and_new_turn()
                            # Drag charms in game
                            for i in range(len(self.equipped_charms)):
                                x = 50 + i * (CHARM_SIZE + 10)
                                y = 10
                                rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
                                if rect.collidepoint(mouse_pos):
                                    self.dragging_charm_index = i
                                    self.dragging_shop = False
                                    self.drag_offset_x = mouse_pos[0] - x
                                    self.drag_offset_y = mouse_pos[1] - y
                                    break
                    # Note: I've added 'changed_state = True' in 'game' to 'shop' change as an example for robustness, but you can remove if not needed. Add similar for other state changes if they cause similar errors.
                    if changed_state:
                        continue  # Optional: Add another check here if more blocks below could be affected
                    elif self.game_state == 'blinds':
                        continue_rect, debug_button_rect, up_rect, down_rect, debug_jump_rect = self.draw_blinds_screen()  # Unpack with jump_rect
                        if continue_rect and continue_rect.collidepoint(mouse_pos):
                            self.game_state = 'game'
                            self.new_turn()
                        if DEBUG:
                            if debug_button_rect and debug_button_rect.collidepoint(mouse_pos):
                                self.debug_boss_dropdown_open = not self.debug_boss_dropdown_open  # Toggle panel
                            if self.debug_boss_dropdown_open:
                                if up_rect and up_rect.collidepoint(mouse_pos):
                                    self.debug_boss_scroll_offset = max(0, self.debug_boss_scroll_offset - 1)
                                if down_rect and down_rect.collidepoint(mouse_pos):
                                    self.debug_boss_scroll_offset = min(len(BOSS_EFFECTS) - (300 // 25), self.debug_boss_scroll_offset + 1)  # Hardcode panel_height=300, item_height=25
                                # Click on item: Calc clicked index
                                panel_x, panel_y = debug_button_rect.x - 300, debug_button_rect.y - 300  # Match draw position
                                item_height = 25
                                for i in range(self.debug_boss_scroll_offset, min(self.debug_boss_scroll_offset + (300 // item_height), len(BOSS_EFFECTS))):
                                    item_rect = pygame.Rect(panel_x, panel_y + (i - self.debug_boss_scroll_offset) * item_height, 370, item_height)  # Full row clickable
                                    if item_rect.collidepoint(mouse_pos):
                                        self.upcoming_boss_effect = BOSS_EFFECTS[i]
                                        self.debug_boss_dropdown_open = False  # Close on select
                                        break
                        if DEBUG and debug_jump_rect and debug_jump_rect.collidepoint(mouse_pos):
                            self.current_blind = 'Boss'
                            self.current_boss_effect = self.upcoming_boss_effect or random.choice(BOSS_EFFECTS)  # Activate preview or random
                            # Quick reset states (mimic advance_blind)
                            self.disabled_charms = []
                            self.boss_reroll_count = 0
                            self.boss_rainbow_color = None
                            self.boss_shuffled_faces = {}
                            # Apply effect setups (copy from advance_blind 'Boss' block)
                            effect_name = self.current_boss_effect['name']
                            if effect_name == 'Charm Glitch' and self.equipped_charms:
                                self.disabled_charms = [random.randint(0, len(self.equipped_charms) - 1)]
                            elif effect_name == 'Charm Eclipse':
                                self.disabled_charms = list(range(len(self.equipped_charms)))
                            elif effect_name == 'Rainbow Restriction':
                                self.boss_rainbow_color = random.choice(BASE_COLORS)
                            elif effect_name == 'Face Shuffle':
                                for die in self.full_bag:
                                    faces = DICE_FACES[:]
                                    random.shuffle(faces)
                                    self.boss_shuffled_faces[die['id']] = faces
                            elif effect_name == 'Charm Tax':
                                tax = len(self.equipped_charms) // 2
                                self.hands_left = max(0, self.hands_left - tax)
                            elif effect_name == 'Hand Trim':
                                self.hands_left = max(0, self.hands_left - 1)
                            elif effect_name == 'Reroll Ration':
                                self.rerolls_left = max(0, self.rerolls_left - 1)
                            elif effect_name == 'Discard Drought':
                                self.discards_left = max(0, self.discards_left - 1)
                            elif effect_name == 'Blind Boost':
                                self.discards_left += 1
                            # Reset round elements
                            self.round_score = 0
                            self.bag[:] = [copy.deepcopy(d) for d in self.full_bag]  # Refill
                            self.game_state = 'game'  # Jump to game state
                            self.new_turn()  # Start Boss turn
                    elif self.game_state == 'pause_menu':
                        button_rects = self.get_pause_button_rects()
                        for rect, opt in button_rects:
                            if rect.collidepoint(mouse_pos):
                                if opt == "Return to Game":
                                    self.game_state = self.previous_state  # Restore previous (e.g., shop)
                                elif opt == "Main Menu":
                                    self.reset_game()
                                    self.game_state = 'init'
                                elif opt == "Quit":
                                    running = False
                                break
                        # No draw here—handled in main loop
                    elif self.game_state == 'shop':
                        if continue_rect and continue_rect.collidepoint(mouse_pos):
                            self.game_state = 'blinds'
                            self.shop_charms = []  # Clear shop
                        # Handle sell
                        for i, sell_rect in enumerate(sell_rects or []):  # Add or [] to handle None
                            if sell_rect.collidepoint(mouse_pos):
                                self.confirm_sell_index = i
                                self.game_state = 'confirm_sell'
                                break
                        # Handle buy charms
                        for i, buy_rect in enumerate(buy_rects or []):
                            if buy_rect.collidepoint(mouse_pos):
                                charm = self.shop_charms.pop(i)
                                cost = charm['cost']
                                has_debt = any(c['type'] == 'negative_coins' for c in self.equipped_charms)
                                min_coins = -5 if has_debt else 0
                                if len(self.equipped_charms) < self.max_charms and self.coins - cost >= min_coins:
                                    self.equipped_charms.append(charm)
                                    self.coins -= cost
                                else:
                                    self.shop_charms.insert(i, charm)  # Put back if can't buy
                                break
                        # Handle Prism Pack buy
                        pack_costs = [3, 5, 7, 3, 5, 9]
                        pack_choices_num = [2, 3, 5, 3, 4, 3]
                        for pack_rect, pack_idx in pack_rects or []:
                            if pack_rect.collidepoint(mouse_pos):
                                cost = pack_costs[pack_idx]
                                has_debt = any(c['type'] == 'negative_coins' for c in self.equipped_charms)
                                min_coins = -5 if has_debt else 0
                                if self.coins >= cost or (self.coins - cost >= min_coins):
                                    self.coins -= cost
                                    if pack_idx in [0,1,2]:
                                        self.pack_choices = random.sample(HAND_TYPES, pack_choices_num[pack_idx])
                                        self.game_state = 'pack_select'
                                        # Hand packs might not remove if infinite; add if needed: self.available_packs.remove(pack_idx)
                                    else:  # All dice packs (base 3-4, special 5)
                                        if pack_idx == 5:  # Special dice packs
                                            self.pack_choices = random.sample(SPECIAL_COLORS, 3)
                                        else:  # Base dice packs
                                            self.pack_choices = random.sample(BASE_COLORS, pack_choices_num[pack_idx])
                                        self.game_state = 'dice_select'
                                        self.available_packs.remove(pack_idx)  # Now removes for all dice packs
                                    break
                        # Handle reroll
                        if reroll_rect and reroll_rect.collidepoint(mouse_pos):
                            self.reroll_shop()
                        # Drag charms in shop (equipped)
                        for i in range(len(self.equipped_charms)):
                            x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
                            y = 150
                            rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
                            if rect.collidepoint(mouse_pos):
                                self.dragging_charm_index = i
                                self.dragging_shop = True
                                self.drag_offset_x = mouse_pos[0] - x
                                self.drag_offset_y = mouse_pos[1] - y
                                break
                    elif self.game_state == 'pack_select':
                        for j, choice_rect in enumerate(choice_rects or []):
                            if choice_rect.collidepoint(mouse_pos):
                                chosen = self.pack_choices[j]
                                self.hand_multipliers[chosen] += PACK_BOOST
                                self.pack_choices = []
                                self.game_state = 'shop'
                                break
                    elif self.game_state == 'dice_select':
                        for choice_rect, color in choice_rects or []:
                            if choice_rect.collidepoint(mouse_pos):
                                # Add new die to bag
                                new_id = f"{color}{len([d for d in self.bag if d['color'] == color]) + 1}"
                                new_die = {'id': new_id, 'color': color, 'faces': DICE_FACES[:]}
                                self.bag.append(new_die)
                                self.full_bag.append(copy.deepcopy(new_die))
                                self.pack_choices = []
                                self.game_state = 'shop'
                                break
                    elif self.game_state == 'confirm_sell':
                        if yes_rect.collidepoint(mouse_pos):
                            charm = self.equipped_charms.pop(self.confirm_sell_index)
                            sell_val = charm['cost'] // 2
                            self.coins += sell_val
                            self.charms_pool.append(charm)  # Add back to pool
                            self.confirm_sell_index = -1
                            self.game_state = 'shop'
                        elif no_rect.collidepoint(mouse_pos):
                            self.confirm_sell_index = -1
                            self.game_state = 'shop'
                    elif self.game_state == 'game_over':
                        if restart_rect and restart_rect.collidepoint(mouse_pos):
                            self.reset_game()
                            self.game_state = 'blinds'
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging_charm_index != -1:
                        # Dragging, but since we draw in loop, no need for action here
                        pass
                elif event.type == pygame.MOUSEBUTTONUP:
                    # In MOUSEBUTTONUP (dragging release):
                    if self.dragging_charm_index != -1:
                        mouse_pos = pygame.mouse.get_pos()
                        target_index = -1
                        if self.dragging_shop:
                            for i in range(len(self.equipped_charms)):
                                x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
                                y = 150
                                rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
                                if rect.collidepoint(mouse_pos):
                                    target_index = i
                                    break
                        else:
                            for i in range(len(self.equipped_charms)):
                                x = 50 + i * (CHARM_SIZE + 10)  # Note: 10 is original spacing; update if changed
                                y = 10
                                rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
                                if rect.collidepoint(mouse_pos):
                                    target_index = i
                                    break
                        if target_index != -1 and target_index != self.dragging_charm_index:
                            self.equipped_charms[self.dragging_charm_index], self.equipped_charms[target_index] = self.equipped_charms[target_index], self.equipped_charms[self.dragging_charm_index]
                        self.dragging_charm_index = -1
                        self.dragging_shop = False
                        # After: self.equipped_charms[self.dragging_charm_index], self.equipped_charms[target_index] = ...
                        # Remap disabled indices if swapped
                        if self.dragging_charm_index in self.disabled_charms:
                            self.disabled_charms.remove(self.dragging_charm_index)
                            self.disabled_charms.append(target_index)
                        elif target_index in self.disabled_charms:
                            self.disabled_charms.remove(target_index)
                            self.disabled_charms.append(self.dragging_charm_index)
            # At loop end, before flip:
            clock.tick(60)

            pygame.display.flip()  # Update screen

        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = ChromaRollGame()
    game.run()
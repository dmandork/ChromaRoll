from cmath import rect
import random  # For rolling dice and drawing from bag
import pygame  # For graphics and input handling
import sys  # For exiting the game
import time  # For animation delays
import math  # For ceil in bag rows
import copy

# Debug flag: Set to True to force specific colors for testing (overrides random draw) and enable unlimited rerolls
DEBUG = False
DEBUG_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # Example: All different colors for rainbow testing

# Define constants
COLORS = {'Red': (255, 0, 0), 'Blue': (0, 0, 255), 'Green': (0, 255, 0),
          'Purple': (128, 0, 128), 'Yellow': (255, 255, 0),
          'Gold': (255, 215, 0), 'Silver': (192, 192, 192), 'Glass': (173, 216, 230),
          'Rainbow': (255, 255, 255)  # Placeholder for cycling animation
          }  # RGB values for colors
BASE_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # For base dice pack icons
SPECIAL_COLORS = ['Gold', 'Silver', 'Glass', 'Rainbow']  # For the special pack choices
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
NUM_DICE_IN_HAND = 5  # Draw 5 dice per turn
MAX_REROLLS = 2  # Initial roll + 2 rerolls = 3 total rolls per turn (ignored in debug)
DICE_FACES = [1, 2, 3, 4, 5, 6]  # Standard faces; modifiable later
INITIAL_WIDTH, INITIAL_HEIGHT = 800, 600  # Smaller initial window size
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
TABLE_GREEN = (0, 100, 0)  # Card table green background
BASE_TARGETS = {'Small': 100, 'Big': 200, 'Boss': 300}  # Base blind targets (scale by stake)
POPUP_WIDTH, POPUP_HEIGHT = 300, 250  # Enlarged popup size for beaten blind
POPUP_ANIMATION_DELAY = 0.5  # Delay for $ animation in popup
CHARM_SIZE = 50  # Size for charm icons
TOOLTIP_PADDING = 10
CHARM_BOX_WIDTH = 120
CHARM_BOX_HEIGHT = 80
CHARM_SPACING = 10
CHARM_DIE_SIZE = 50  # Size for charm die representation
CHARM_DIE_BORDER_RADIUS = 10  # Rounded corners for die look
LEFT_BUTTON_X = 50
RIGHT_BUTTON_X = INITIAL_WIDTH - BUTTON_WIDTH - 50  # Will be dynamic
CENTER_LEFT_X = INITIAL_WIDTH // 2 - BUTTON_WIDTH - 20  # Will be dynamic
CENTER_RIGHT_X = INITIAL_WIDTH // 2 + 20  # Will be dynamic
INTEREST_RATE = 10  # Coins per extra coin
INTEREST_MAX = 50  # Max coins for interest calculation
TOOLTIP_MAX_WIDTH = 300  # Max width for tooltip before wrapping
PACK_BOOST = 0.5  # Multiplier boost per pack use
HAND_TYPES = ['Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind', 'Full House', 'Small Straight', 'Large Straight']
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
        
        self.screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)  # Resizable window
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption("Chroma Roll")  # Set title
        self.font = pygame.font.SysFont(None, 36)  # Font for text
        self.small_font = pygame.font.SysFont(None, 24)  # Smaller font for hand/modifier info
        self.tiny_font = pygame.font.SysFont(None, 20)  # Even smaller for top texts
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
        self.game_state = 'blinds'  # 'game', 'blinds', 'shop', 'game_over', 'pack_select', 'confirm_sell'
        self.show_popup = False  # Flag for beaten blind popup
        self.popup_message = ""  # Message for beaten blind popup
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
            {'name': 'Basic Charm', 'rarity': 'Common', 'cost': 2, 'desc': '+4 to all final scores.', 'type': 'flat_bonus', 'value': 4},
            {'name': 'Red Greed Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Red die scored.', 'type': 'per_color_bonus', 'color': 'Red', 'value': 3},
            {'name': 'Blue Lust Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Blue die scored.', 'type': 'per_color_bonus', 'color': 'Blue', 'value': 3},
            {'name': 'Green Wrath Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Green die scored.', 'type': 'per_color_bonus', 'color': 'Green', 'value': 3},
            {'name': 'Purple Glutton Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Purple die scored.', 'type': 'per_color_bonus', 'color': 'Purple', 'value': 3},
            {'name': 'Yellow Jolly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+8 score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 8},
            {'name': 'Zany Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+12 score if hand contains a 3 of a Kind.', 'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 12},
            {'name': 'Mad Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+10 score if hand contains a 2 Pair.', 'type': 'hand_bonus', 'hands': ['2 Pair'], 'value': 10},
            {'name': 'Crazy Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+12 score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 12},
            {'name': 'Droll Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to monochrome multipliers.', 'type': 'mono_mult_bonus', 'value': 0.5},
            {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 50},
            {'name': 'Wily Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+100 base score if hand contains a 3 of a Kind.', 'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 100},
            {'name': 'Clever Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+80 base score if hand contains a 2 Pair.', 'type': 'hand_bonus', 'hands': ['2 Pair'], 'value': 80},
            {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 100},
            {'name': 'Half Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+20 score if hand uses 3 or fewer dice.', 'type': 'few_dice_bonus', 'max_dice': 3, 'value': 20},
            {'name': 'Stencil Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 'x1 multiplier for each empty charm slot (including this one).', 'type': 'empty_slot_mult', 'value': 1.0},
            {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},
            {'name': 'Mime Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 'Retrigger held dice effects (placeholder).', 'type': 'retrigger_held'},
            {'name': 'Debt Charm', 'rarity': 'Common', 'cost': 2, 'desc': 'Allows going into negative coins for shop buys (up to -5).', 'type': 'negative_coins', 'limit': -5},
            {'name': 'Dagger Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 'When blind starts, sacrifice a charm to the right and add 0.5x its cost to your score multiplier permanently.', 'type': 'sacrifice_mult'},
            {'name': 'Golden Touch Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+2 coins per Gold die held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Gold', 'value': 2},
            {'name': 'Silver Lining Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+2 coins per Silver die not held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Silver', 'value': 2},
            {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 'break_penalty': 5},
            {'name': 'Even Stevens Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per even-valued die scored.', 'type': 'per_value_bonus', 'parity': 'even', 'value': 5},
            {'name': 'Oddball Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per odd-valued die scored.', 'type': 'per_value_bonus', 'parity': 'odd', 'value': 5},
            {'name': 'Rainbow Prism Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to rainbow multipliers.', 'type': 'rainbow_mult_bonus', 'value': 0.5},
            {'name': 'Full House Party Charm', 'rarity': 'Rare', 'cost': 6, 'desc': '+150 base score if hand contains a Full House.', 'type': 'hand_bonus', 'hands': ['Full House'], 'value': 150},
            {'name': 'Quadruple Threat Charm', 'rarity': 'Rare', 'cost': 7, 'desc': '+200 base score if hand contains a 4 of a Kind.', 'type': 'hand_bonus', 'hands': ['4 of a Kind'], 'value': 200},
            {'name': 'Reroll Recycler Charm', 'rarity': 'Uncommon', 'cost': 4, 'desc': 'Gain 1 extra reroll per round if you use a discard.', 'type': 'extra_reroll_on_discard'},
            {'name': 'Interest Booster Charm', 'rarity': 'Common', 'cost': 3, 'desc': 'Increases max coins for interest calculation by 20.', 'type': 'interest_max_bonus', 'value': 20},
        ]

    # Function to draw a hand of dice from the bag
    def draw_hand(self, num_dice=NUM_DICE_IN_HAND):
        """Randomly draws unique dice from the bag without replacement. Resets bag if too low."""
        if len(self.bag) < num_dice:
            self.bag[:] = [copy.deepcopy(d) for d in self.full_bag]  # Repopulate from owned template
        if DEBUG:
            # Debug mode: Force specific colors without removing from bag
            hand = []
            for color in DEBUG_COLORS:
                available = [d for d in self.bag if d['color'] == color]
                if available:
                    selected = random.choice(available)
                    hand.append(selected)
                    # Do not remove in debug to allow repeated same colors
            return hand[:num_dice]  # Ensure exactly num_dice
        else:
            hand = random.sample(self.bag, num_dice)
            for die in hand:
                self.bag.remove(die)  # Remove drawn dice from bag
            return hand
    
    def get_blind_target(self, blind=None):
        """Returns the score target for the given or current blind, scaled by stake."""
        blind = blind or self.current_blind
        base_target = BASE_TARGETS[blind]
        return base_target * (1 + (self.current_stake - 1) * 0.5)  # Scale by 50% per stake

    def advance_blind(self):
        """Advances to the next blind or stake and resets the dice bag."""
        blind_order = ['Small', 'Big', 'Boss']
        current_index = blind_order.index(self.current_blind)
        if current_index < len(blind_order) - 1:
            self.current_blind = blind_order[current_index + 1]
        else:
            self.current_stake += 1
            self.current_blind = 'Small'
        self.round_score = 0
        self.hands_left = MAX_HANDS
        self.discards_left = MAX_DISCARDS
        self.extra_coins = 0
        self.bag[:] = [copy.deepcopy(d) for d in self.full_bag]  # Refill bag from owned template
        # Handle Dagger charm
        i = 0
        while i < len(self.equipped_charms) - 1:
            if self.equipped_charms[i]['type'] == 'sacrifice_mult':
                sacrificed = self.equipped_charms.pop(i + 1)
                self.score_mult += sacrificed['cost'] * 0.5
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

    def roll_hand(self):
        """Rolls each die in the hand, returning list of (die, value)."""
        return [(die, random.choice(die['faces'])) for die in self.hand]

    def reroll(self):
        """Rerolls non-held dice with animation if rerolls left, else scores and new turn."""
        if self.is_discard_phase:
            return  # Can't reroll during discard phase
        if self.rerolls_left > 0 or DEBUG:  # Always allow reroll in debug
            # Animate cycling for non-held dice
            for frame in range(ANIMATION_FRAMES):
                for i in range(len(self.rolls)):
                    if not self.held[i]:
                        self.rolls[i] = (self.rolls[i][0], random.choice(self.rolls[i][0]['faces']))
                self.screen.fill(TABLE_GREEN)  # Clear screen
                self.draw_game_screen()
                pygame.display.flip()  # Update screen during animation
                time.sleep(ANIMATION_DELAY)
            
            # Final actual roll (the last frame is the real one)
            for i in range(len(self.rolls)):
                if not self.held[i]:
                    die = self.rolls[i][0]
                    self.rolls[i] = (die, random.choice(die['faces']))
            
            if not DEBUG:
                self.rerolls_left -= 1
            self.update_hand_text()  # Update after reroll
        else:
            # Score and advance hand or end round
            score = self.calculate_score()
            self.round_score += score
            # Accumulate extra coins from Gold/Silver
            for i, (die, _) in enumerate(self.rolls):
                if die['color'] == 'Gold' and self.held[i]:
                    self.extra_coins += 1
                elif die['color'] == 'Silver' and not self.held[i]:
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
                    # Break: Remove from full_bag and bag
                    self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                    self.bag = [d for d in self.bag if d['id'] != die['id']]
                    self.coins -= glass_break_penalty  # Apply penalty if any
            self.hands_left -= 1
            if self.round_score >= self.get_blind_target():
                remains_coins = self.hands_left + self.discards_left if not DEBUG else 0
                # Compute dynamic interest max from charms
                dynamic_interest_max = INTEREST_MAX
                for charm in self.equipped_charms:
                    if charm['type'] == 'interest_max_bonus':
                        dynamic_interest_max += charm['value']
                interest = min(self.coins, dynamic_interest_max) // INTEREST_RATE
                total_coins = remains_coins + interest
                total_coins += self.extra_coins
                hands_dollars = '$' * self.hands_left
                discards_dollars = '$' * self.discards_left
                interest_dollars = '$' * interest if interest >= 0 else str(interest)
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
            # Draw new dice
            new_dice = self.draw_hand(selected_count)
            # Replace at the selected positions with value 1 (single pip)
            for idx, new_die in zip(selected_indices, new_dice):
                self.hand[idx] = new_die
                self.rolls[idx] = (new_die, 1)  # Set to 1 for single pip
            self.held = [False] * NUM_DICE_IN_HAND
            self.discard_selected = [False] * NUM_DICE_IN_HAND
            if self.discard_used_this_round:
                for charm in self.equipped_charms:
                    if charm['type'] == 'extra_reroll_on_discard':
                        self.rerolls_left += 1  # Extra reroll if discard was used
                self.discard_used_this_round = False  # Reset after applying
            self.discards_left -= 1
            self.discard_used_this_round = True
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
        # Animate rolling for all dice
        for frame in range(ANIMATION_FRAMES):
            self.rolls = [(die, random.choice(die['faces'])) for die in self.hand]
            self.screen.fill(TABLE_GREEN)  # Clear screen
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
                self.extra_coins += 1
            elif die['color'] == 'Silver' and not self.held[i]:
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
                # Break: Remove from full_bag and bag
                self.full_bag = [d for d in self.full_bag if d['id'] != die['id']]
                self.bag = [d for d in self.bag if d['id'] != die['id']]
                self.coins -= glass_break_penalty  # Apply penalty if any
        self.hands_left -= 1
        if self.round_score >= self.get_blind_target():
            remains_coins = self.hands_left + self.discards_left if not DEBUG else 0
            # Compute dynamic interest max from charms
            dynamic_interest_max = INTEREST_MAX
            for charm in self.equipped_charms:
                if charm['type'] == 'interest_max_bonus':
                    dynamic_interest_max += charm['value']
            interest = min(self.coins, dynamic_interest_max) // INTEREST_RATE
            total_coins = remains_coins + interest
            total_coins += self.extra_coins
            hands_dollars = '$' * self.hands_left
            discards_dollars = '$' * self.discards_left
            interest_dollars = '$' * interest if interest >= 0 else str(interest)
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

        has_four_fingers = any(c['type'] == 'short_straight' for c in self.equipped_charms)

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

        # Apply charms
        charm_chips = 0
        charm_color_mult_add = 0.0  # Renamed from charm_mono_add
        charm_mult_add = 1.0
        is_mono = 'Mono' in modifier_desc
        is_rainbow = 'Rainbow' in modifier_desc
        num_dice_used = len(held_rolls)  # Approximate "uses" as unique values? Wait, it's len(held_rolls)
        is_small_straight = any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small))
        is_large_straight = sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large))
        for charm in self.equipped_charms:
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
            # Skip Mime, Debt, Dagger for now

        total_modifier = (base_modifier + charm_color_mult_add) * charm_mult_add * self.score_mult
        if hand_type in self.hand_multipliers:
            total_modifier *= self.hand_multipliers[hand_type]  # Apply Prism Pack multiplier
        glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass')
        total_modifier *= (4 ** glass_count)  # x4 per held Glass
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
            self.current_modifier_text = f"Color Modifier: {modifier_desc}" + (f" + {charm_mono_add:.1f}x charms" if charm_mono_add > 0 else "") + (f" x {self.score_mult:.1f} dagger" if self.score_mult > 1.0 else "")

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
            pygame.draw.rect(self.screen, color_rgb, rect, border_radius=DIE_BORDER_RADIUS)
            # Draw black border
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2, border_radius=DIE_BORDER_RADIUS)
            # Highlight if selected for discard (red border outside black)
            if self.discard_selected[i]:
                outer_rect = pygame.Rect(x + offset - 3, y + offset - 3, size + 6, size + 6)
                pygame.draw.rect(self.screen, (255, 0, 0), outer_rect, 3, border_radius=DIE_BORDER_RADIUS)
            # Draw dots
            for pos in DOT_POSITIONS.get(value, []):
                dot_x = x + offset + pos[0] * size
                dot_y = y + offset + pos[1] * size
                pygame.draw.circle(self.screen, (0, 0, 0), (dot_x, dot_y), DOT_RADIUS)

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

        if self.is_discard_phase:
            discard_rect = pygame.Rect(left_button_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(self.screen, (100, 100, 100), discard_rect)
            discard_text = self.font.render("Discard", True, (255, 255, 255))
            self.screen.blit(discard_text, (discard_rect.x + 20, discard_rect.y + 10))

            start_roll_rect = pygame.Rect(right_button_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(self.screen, (100, 100, 100), start_roll_rect)
            start_roll_text = self.font.render("Start Roll", True, (255, 255, 255))
            self.screen.blit(start_roll_text, (start_roll_rect.x + 10, start_roll_rect.y + 10))
        else:
            reroll_rect = pygame.Rect(center_left_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(self.screen, (100, 100, 100), reroll_rect)
            button_text = "Reroll" if (self.rerolls_left > 0 or DEBUG) else "Draw and Score"
            reroll_text = self.font.render(button_text, True, (255, 255, 255))
            self.screen.blit(reroll_text, (reroll_rect.x + 20, reroll_rect.y + 10))

            end_turn_rect = pygame.Rect(center_right_x, bottom_y, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(self.screen, (100, 100, 100), end_turn_rect)
            end_turn_text = self.font.render("End Turn", True, (255, 255, 255))
            self.screen.blit(end_turn_text, (end_turn_rect.x + 20, end_turn_rect.y + 10))

        if DEBUG:
            score_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, bottom_y - BUTTON_HEIGHT - 10, BUTTON_WIDTH, BUTTON_HEIGHT)
            pygame.draw.rect(self.screen, (100, 100, 100), score_rect)
            score_text = self.font.render("Score & New", True, (255, 255, 255))
            self.screen.blit(score_text, (score_rect.x + 10, score_rect.y + 10))

        return reroll_rect, discard_rect, start_roll_rect, score_rect, end_turn_rect

    def draw_popup(self):
        """Draws the beaten blind popup with a single Continue button and $ animation."""
        popup_rect = pygame.Rect(self.width // 2 - POPUP_WIDTH // 2, 200, POPUP_WIDTH, POPUP_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), popup_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), popup_rect, 3)  # White border

        # Split message into lines and render with animation for $
        lines = self.popup_message.split('\n')
        for i, line in enumerate(lines):
            text = self.tiny_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (popup_rect.x + (POPUP_WIDTH - text.get_width()) // 2, popup_rect.y + 20 + i * 30))

        # Draw single Continue button
        continue_rect = pygame.Rect(popup_rect.x + (POPUP_WIDTH - BUTTON_WIDTH) // 2, popup_rect.y + POPUP_HEIGHT - 70, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), continue_rect)
        continue_text = self.tiny_font.render("Continue", True, (255, 255, 255))
        self.screen.blit(continue_text, (continue_rect.x + (BUTTON_WIDTH - continue_text.get_width()) // 2, continue_rect.y + 10))

        return continue_rect

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
            desc_surface = self.small_font.render(line, True, (255, 255, 255))
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

    def draw_charm_die(self, rect, charm):
        """Draws a charm as a white die square with black border, and icon if applicable."""
        name = charm['name']
        bg_color = (255, 255, 255)  # Default white
        if name in ['Red Greed Charm', 'Blue Lust Charm', 'Green Wrath Charm', 'Purple Glutton Charm']:
            bg_color = COLORS[charm['color']]
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=CHARM_DIE_BORDER_RADIUS)  # Fill
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 2, border_radius=CHARM_DIE_BORDER_RADIUS)  # Black border
        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        if name == 'Basic Charm':
            text = self.tiny_font.render('+4', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name in ['Red Greed Charm', 'Blue Lust Charm', 'Green Wrath Charm', 'Purple Glutton Charm']:
            text_color = (0, 0, 0)
            text = self.tiny_font.render('+3', True, text_color)
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Yellow Jolly Charm':
            # New icon: two small dice for pair
            pygame.draw.rect(self.screen, (0, 0, 0), (center_x - 15, center_y - 10, 10, 10), 2)
            pygame.draw.rect(self.screen, (0, 0, 0), (center_x + 5, center_y - 10, 10, 10), 2)
            text = self.tiny_font.render('+8', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y + 5))
        elif name == 'Droll Charm':
            text = self.tiny_font.render('+0.5x', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Mad Charm':
            # Simple mad face: angry eyes, frown
            pygame.draw.line(self.screen, (0, 0, 0), (center_x - 15, center_y - 10), (center_x - 5, center_y - 5), 2)  # Left eye
            pygame.draw.line(self.screen, (0, 0, 0), (center_x + 5, center_y - 5), (center_x + 15, center_y - 10), 2)  # Right eye
            pygame.draw.arc(self.screen, (0, 0, 0), (center_x - 10, center_y + 5, 20, 10), 3.14, 0, 2)  # Frown
        elif name == 'Crazy Charm':
            # Simple silly face: dot eyes, smile with tongue
            pygame.draw.circle(self.screen, (0, 0, 0), (center_x - 10, center_y - 5), 2)  # Left eye
            pygame.draw.circle(self.screen, (0, 0, 0), (center_x + 10, center_y - 5), 2)  # Right eye
            pygame.draw.arc(self.screen, (0, 0, 0), (center_x - 10, center_y - 5, 20, 20), 3.14, 0, 2)  # Smile
            pygame.draw.line(self.screen, (0, 0, 0), (center_x + 5, center_y + 5), (center_x + 10, center_y + 10), 2)  # Tongue
        elif name == 'Debt Charm':
            text = self.tiny_font.render('-5', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Zany Charm':
            text = self.tiny_font.render('3!', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Sly Charm':
            text = self.tiny_font.render('2+', True, (150, 150, 150))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Wily Charm':
            text = self.tiny_font.render('3x', True, (255, 165, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Clever Charm':
            text = self.tiny_font.render('2P', True, (0, 0, 255))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Devious Charm':
            # Simple arrow: line with triangle head
            pygame.draw.line(self.screen, (128, 0, 128), (center_x - 15, center_y), (center_x + 15, center_y), 2)
            pygame.draw.polygon(self.screen, (128, 0, 128), [(center_x + 15, center_y), (center_x + 10, center_y - 5), (center_x + 10, center_y + 5)])
        elif name == 'Half Charm':
            text = self.tiny_font.render('≤3', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Stencil Charm':
            text = self.tiny_font.render('[]x', True, (0, 0, 0))
            self.screen.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
        elif name == 'Four Fingers Charm':
            # More detailed hand: rounded palm, segmented fingers (4 + thumb)
            # Palm: filled rounded rectangle for body
            palm_rect = pygame.Rect(center_x - 15, center_y - 5, 30, 20)
            pygame.draw.rect(self.screen, (200, 200, 200), palm_rect, border_radius=5)  # Light gray fill for palm
            pygame.draw.rect(self.screen, (0, 0, 0), palm_rect, 2, border_radius=5)  # Black outline
            # Fingers: 4 segmented (two lines each for joints)
            finger_positions = [-12, -4, 4, 12]  # Slightly spread out
            for fp in finger_positions:
                # Base segment (wrist to knuckle)
                pygame.draw.line(self.screen, (0, 0, 0), (center_x + fp, center_y + 5), (center_x + fp, center_y - 8), 3)
                # Tip segment (knuckle to fingertip, slightly angled for curve)
                tip_start = (center_x + fp, center_y - 8)
                tip_end = (center_x + fp + (fp // 8), center_y - 20)  # Slight outward angle
                pygame.draw.line(self.screen, (0, 0, 0), tip_start, tip_end, 2)
            # Thumb: two segments, angled outward
            thumb_base = (center_x - 15, center_y + 5)
            thumb_knuckle = (center_x - 20, center_y + 10)
            thumb_tip = (center_x - 25, center_y + 15)
            pygame.draw.line(self.screen, (0, 0, 0), thumb_base, thumb_knuckle, 3)
            pygame.draw.line(self.screen, (0, 0, 0), thumb_knuckle, thumb_tip, 2)
        elif name == 'Mime Charm':
            # Box with hands: rect + two vertical lines
            pygame.draw.rect(self.screen, (0, 0, 0), (center_x - 15, center_y - 15, 30, 30), 2)
            pygame.draw.line(self.screen, (0, 0, 0), (center_x - 15, center_y - 15), (center_x - 15, center_y + 15), 2)  # Left hand
            pygame.draw.line(self.screen, (0, 0, 0), (center_x + 15, center_y - 15), (center_x + 15, center_y + 15), 2)  # Right hand
        elif charm['type'] == 'sacrifice_mult':
            self.draw_dagger_icon(rect)  # Overlay dagger icon

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
        mouse_pos = pygame.mouse.get_pos()
        for i, charm in enumerate(self.equipped_charms):
            if i == self.dragging_charm_index and not self.dragging_shop:
                continue
            x = 50 + i * (CHARM_SIZE + 10)
            y = 10
            rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
            self.draw_charm_die(rect, charm)
            if rect.collidepoint(mouse_pos):
                tooltip_text = charm['name'] + ": " + charm['desc']
                if charm['type'] == 'sacrifice_mult':
                    tooltip_text += f" (Current mult: x{self.score_mult})"
                self.draw_tooltip(x, y + CHARM_SIZE + 5, tooltip_text)
        # Draw dragged charm
        if self.dragging_charm_index != -1 and not self.dragging_shop:
            charm = self.equipped_charms[self.dragging_charm_index]
            x = mouse_pos[0] - self.drag_offset_x
            y = mouse_pos[1] - self.drag_offset_y
            rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
            self.draw_charm_die(rect, charm)

    def draw_game_screen(self):
        """Draws the main game screen."""
        self.draw_dice()
        self.draw_text()
        self.draw_bag_visual()
        self.draw_charms()
        self.draw_buttons()
        self.draw_ui_panel()
        mouse_pos = pygame.mouse.get_pos()
        multipliers_button_rect = pygame.Rect(self.width - MULTIPLIERS_BUTTON_SIZE - 10, self.height - MULTIPLIERS_BUTTON_SIZE - 100, MULTIPLIERS_BUTTON_SIZE, MULTIPLIERS_BUTTON_SIZE)
        pygame.draw.rect(self.screen, (100, 100, 100), multipliers_button_rect)
        button_text = self.tiny_font.render("M", True, (255, 255, 255))
        self.screen.blit(button_text, (multipliers_button_rect.x + 20, multipliers_button_rect.y + 15))
        if multipliers_button_rect.collidepoint(mouse_pos):
            panel_x = self.width - MULTIPLIERS_PANEL_WIDTH - 10
            panel_y = self.height - MULTIPLIERS_PANEL_HEIGHT - MULTIPLIERS_BUTTON_SIZE - 120
            panel_rect = pygame.Rect(panel_x, panel_y, MULTIPLIERS_PANEL_WIDTH, MULTIPLIERS_PANEL_HEIGHT)
            pygame.draw.rect(self.screen, UI_PANEL_COLOR, panel_rect, border_radius=UI_PANEL_BORDER_RADIUS)
            pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, 2, border_radius=UI_PANEL_BORDER_RADIUS)
            y_offset = panel_y + 10
            for ht, mult in self.hand_multipliers.items():
                mult_text = self.tiny_font.render(f"{ht}: x{mult:.1f}", True, (255, 255, 255))
                self.screen.blit(mult_text, (panel_x + 10, y_offset))
                y_offset += 25
        if self.show_popup:
            self.draw_popup()

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
        # Draw upside-down triangle at bottom of Z-order
        triangle_points = [
            (bag_x + bag_width // 2, bag_y + 10),  # bottom tip
            (bag_x + bag_width // 2 - 15, bag_y - 10),  # top left
            (bag_x + bag_width // 2 + 15, bag_y - 10)   # top right
        ]
        pygame.draw.polygon(self.screen, BAG_COLOR, triangle_points)
        pygame.draw.polygon(self.screen, (0, 0, 0), triangle_points, 2)
        pygame.draw.rect(self.screen, BAG_COLOR, bag_rect, border_radius=BAG_BORDER_RADIUS)
        pygame.draw.rect(self.screen, (0, 0, 0), bag_rect, 2, border_radius=BAG_BORDER_RADIUS)

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
                    pygame.draw.rect(self.screen, color_rgb, rect, border_radius=SMALL_DIE_BORDER_RADIUS)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, 1, border_radius=SMALL_DIE_BORDER_RADIUS)
                    index += 1
                else:
                    break

    def draw_blinds_screen(self):
        """Draws the blinds selection screen with three boxes for all blinds, horizontally."""
        self.screen.fill(TABLE_GREEN)
        title_text = self.font.render(f"Stake {self.current_stake}", True, (255, 255, 255))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 10))

        blind_order = ['Small', 'Big', 'Boss']
        box_width, box_height = 150, 100
        box_spacing = 50
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
            blind_text = self.small_font.render(f"{blind} Blind", True, (255, 255, 255))
            self.screen.blit(blind_text, (rect.x + (box_width - blind_text.get_width()) // 2, rect.y + 20))
            target_text = self.small_font.render(f"Score: {int(self.get_blind_target(blind))}", True, (255, 255, 255))
            self.screen.blit(target_text, (rect.x + (box_width - target_text.get_width()) // 2, rect.y + 50))

        coins_text = self.small_font.render(f"Coins: {self.coins}", True, (255, 255, 255))
        self.screen.blit(coins_text, (self.width // 2 - coins_text.get_width() // 2, self.height // 10 + 50))

        continue_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height // 2 + 150, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), continue_rect)
        continue_text = self.font.render("Continue", True, (255, 255, 255))
        self.screen.blit(continue_text, (continue_rect.x + 20, continue_rect.y + 10))
        
        return continue_rect

    def draw_game_over_screen(self):
        """Draws the game over screen."""
        self.screen.fill(TABLE_GREEN)
        title_text = self.font.render("Game Over", True, (255, 0, 0))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 5))

        score_text = self.small_font.render(f"Final Score: {self.round_score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 5 + 100))
        coins_text = self.small_font.render(f"Coins: {self.coins}", True, (255, 255, 255))
        self.screen.blit(coins_text, (self.width // 2 - coins_text.get_width() // 2, self.height // 5 + 150))
        stake_text = self.small_font.render(f"Reached Stake: {self.current_stake}", True, (255, 255, 255))
        self.screen.blit(stake_text, (self.width // 2 - stake_text.get_width() // 2, self.height // 5 + 200))

        restart_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height // 5 + 300, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), restart_rect)
        restart_text = self.font.render("Restart", True, (255, 255, 255))
        self.screen.blit(restart_text, (restart_rect.x + 20, restart_rect.y + 10))
        
        return restart_rect

    def draw_pack_select_screen(self):
        """Draws the pack selection screen."""
        self.screen.fill(TABLE_GREEN)
        title_text = self.font.render("Choose Hand to Boost (+0.5x mult)", True, (255, 255, 255))
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
        self.screen.fill(TABLE_GREEN)
        title_text = self.font.render("Choose a Die to Add", True, (255, 255, 255))
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

        message_text = self.small_font.render("Are you sure you want to sell this charm?", True, (255, 255, 255))
        self.screen.blit(message_text, (popup_rect.x + (popup_width - message_text.get_width()) // 2, popup_rect.y + 30))

        yes_rect = pygame.Rect(popup_rect.x + 50, popup_rect.y + 80, 100, 40)
        pygame.draw.rect(self.screen, (0, 150, 0), yes_rect)
        yes_text = self.small_font.render("Yes", True, (255, 255, 255))
        self.screen.blit(yes_text, (yes_rect.x + (100 - yes_text.get_width()) // 2, yes_rect.y + 10))

        no_rect = pygame.Rect(popup_rect.x + popup_width - 150, popup_rect.y + 80, 100, 40)
        pygame.draw.rect(self.screen, (150, 0, 0), no_rect)
        no_text = self.small_font.render("No", True, (255, 255, 255))
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
            {'name': 'Basic Charm', 'rarity': 'Common', 'cost': 2, 'desc': '+4 to all final scores.', 'type': 'flat_bonus', 'value': 4},
            {'name': 'Red Greed Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Red die scored.', 'type': 'per_color_bonus', 'color': 'Red', 'value': 3},
            {'name': 'Blue Lust Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Blue die scored.', 'type': 'per_color_bonus', 'color': 'Blue', 'value': 3},
            {'name': 'Green Wrath Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Green die scored.', 'type': 'per_color_bonus', 'color': 'Green', 'value': 3},
            {'name': 'Purple Glutton Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+3 score per Purple die scored.', 'type': 'per_color_bonus', 'color': 'Purple', 'value': 3},
            {'name': 'Yellow Jolly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+8 score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 8},
            {'name': 'Zany Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+12 score if hand contains a 3 of a Kind.', 'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 12},
            {'name': 'Mad Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+10 score if hand contains a 2 Pair.', 'type': 'hand_bonus', 'hands': ['2 Pair'], 'value': 10},
            {'name': 'Crazy Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+12 score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 12},
            {'name': 'Droll Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to monochrome multipliers.', 'type': 'mono_mult_bonus', 'value': 0.5},
            {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 50},
            {'name': 'Wily Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+100 base score if hand contains a 3 of a Kind.', 'type': 'hand_bonus', 'hands': ['3 of a Kind'], 'value': 100},
            {'name': 'Clever Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+80 base score if hand contains a 2 Pair.', 'type': 'hand_bonus', 'hands': ['2 Pair'], 'value': 80},
            {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 100},
            {'name': 'Half Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+20 score if hand uses 3 or fewer dice.', 'type': 'few_dice_bonus', 'max_dice': 3, 'value': 20},
            {'name': 'Stencil Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 'x1 multiplier for each empty charm slot (including this one).', 'type': 'empty_slot_mult', 'value': 1.0},
            {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},
            {'name': 'Mime Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 'Retrigger held dice effects (placeholder).', 'type': 'retrigger_held'},
            {'name': 'Debt Charm', 'rarity': 'Common', 'cost': 2, 'desc': 'Allows going into negative coins for shop buys (up to -5).', 'type': 'negative_coins', 'limit': -5},
            {'name': 'Dagger Charm', 'rarity': 'Rare', 'cost': 7, 'desc': 'When blind starts, sacrifice a charm to the right and add 0.5x its cost to your score multiplier permanently.', 'type': 'sacrifice_mult'},
        ]

    def draw_text(self):
        """Draws current hand info, score, rerolls, discards, etc."""
        # Current hand type and score
        hand_text = self.small_font.render(self.current_hand_text, True, (255, 255, 255))
        self.screen.blit(hand_text, (50, 70))
        # Color modifier
        modifier_text = self.small_font.render(self.current_modifier_text, True, (255, 255, 255))
        self.screen.blit(modifier_text, (50, 100))
        # Score
        score_text = self.small_font.render(f"Score: {self.round_score}/{int(self.get_blind_target())}", True, (255, 255, 255))
        self.screen.blit(score_text, (50, 130))

    def draw_pack_icon(self, pack_rect, num_dice, cycle_colors=COLOR_CYCLE):
        """Draws animated dice pack icon."""
        box_rect = pygame.Rect(pack_rect.x + (CHARM_BOX_WIDTH - PACK_BOX_SIZE) // 2, pack_rect.y + (CHARM_BOX_HEIGHT - PACK_BOX_SIZE) // 2, PACK_BOX_SIZE, PACK_BOX_SIZE)
        pygame.draw.rect(self.screen, (0, 0, 0), box_rect, 2)
        current_time = time.time()
        for i in range(num_dice):
            color_index = int((current_time + i * 0.2) % len(cycle_colors))
            color = cycle_colors[color_index]
            if num_dice == 3:
                x = box_rect.x + 5 + i * (SMALL_ICON_DIE_SIZE + 5)
                y = box_rect.y + (PACK_BOX_SIZE - SMALL_ICON_DIE_SIZE) // 2
            else:  # 4 dice, 2x2
                x = box_rect.x + 5 + (i % 2) * (SMALL_ICON_DIE_SIZE + 10)
                y = box_rect.y + 5 + (i // 2) * (SMALL_ICON_DIE_SIZE + 10)
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
        pygame.draw.rect(self.screen, UI_PANEL_COLOR, panel_rect, border_radius=UI_PANEL_BORDER_RADIUS)
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, 2, border_radius=UI_PANEL_BORDER_RADIUS)

        # Texts inside
        hands_text = self.tiny_font.render(f"Hands: {self.hands_left}", True, (255, 255, 255))
        self.screen.blit(hands_text, (panel_x + 10, panel_y + 10))
        discards_text = self.tiny_font.render(f"Discards: {self.discards_left}", True, (255, 255, 255))
        self.screen.blit(discards_text, (panel_x + 10, panel_y + 40))
        rolls_text = self.tiny_font.render(f"Rolls Left: {self.rerolls_left if self.rerolls_left >= 0 else '∞'}", True, (255, 255, 255))
        self.screen.blit(rolls_text, (panel_x + 10, panel_y + 70))
        coins_text = self.tiny_font.render(f"Coins: {self.coins}", True, (255, 255, 255))
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
        self.screen.fill(TABLE_GREEN)
        title_text = self.font.render("Shop", True, (255, 255, 255))
        self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        coins_text = self.small_font.render(f"Coins: {self.coins}", True, (255, 255, 255))
        self.screen.blit(coins_text, (self.width // 2 - coins_text.get_width() // 2, 100))

        # Equipped charms horizontal at top
        equipped_title = self.small_font.render("Equipped Charms", True, (255, 255, 255))
        self.screen.blit(equipped_title, (50, 120))
        sell_rects = []
        equipped_hover = None
        equipped_rects = []
        for i, charm in enumerate(self.equipped_charms):
            if i == self.dragging_charm_index and self.dragging_shop:
                continue
            x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
            y = 150
            eq_rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            icon_rect = pygame.Rect(eq_rect.x + (CHARM_BOX_WIDTH - CHARM_DIE_SIZE) // 2, eq_rect.y + 5, CHARM_DIE_SIZE, CHARM_DIE_SIZE)
            self.draw_charm_die(icon_rect, charm)
            sell_val = charm['cost'] // 2
            sell_label = self.tiny_font.render(f"Sell: {sell_val}", True, (255, 255, 255))
            self.screen.blit(sell_label, (eq_rect.x + 5, eq_rect.y + 60))
            sell_rect = pygame.Rect(eq_rect.x + 60, eq_rect.y + 60, 50, 20)
            pygame.draw.rect(self.screen, (150, 0, 0), sell_rect)
            sell_text = self.tiny_font.render("Sell", True, (255, 255, 255))
            self.screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 3))
            sell_rects.append(sell_rect)
            equipped_rects.append(eq_rect)
            if eq_rect.collidepoint(mouse_pos):
                tooltip_text = charm['name'] + ": " + charm['desc']
                if charm['type'] == 'sacrifice_mult':
                    tooltip_text += f" (Current mult: x{self.score_mult})"
                equipped_hover = (x, y + CHARM_BOX_HEIGHT + 5, tooltip_text)
        # Draw dragged charm in shop
        if self.dragging_charm_index != -1 and self.dragging_shop:
            charm = self.equipped_charms[self.dragging_charm_index]
            x = mouse_pos[0] - self.drag_offset_x
            y = mouse_pos[1] - self.drag_offset_y
            rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            self.draw_charm_die(rect, charm)

        # Shop charms horizontal below
        shop_title = self.small_font.render("Shop Charms", True, (255, 255, 255))
        self.screen.blit(shop_title, (50, 300))
        buy_rects = []
        shop_hover = None
        shop_rects = []
        for i, charm in enumerate(self.shop_charms):
            x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
            y = 330
            shop_rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            icon_rect = pygame.Rect(shop_rect.x + (CHARM_BOX_WIDTH - CHARM_DIE_SIZE) // 2, shop_rect.y + 5, CHARM_DIE_SIZE, CHARM_DIE_SIZE)
            self.draw_charm_die(icon_rect, charm)
            cost_label = self.tiny_font.render(f"Cost: {charm['cost']}", True, (255, 255, 255))
            self.screen.blit(cost_label, (shop_rect.x + 5, shop_rect.y + 60))
            buy_rect = pygame.Rect(shop_rect.x + 60, shop_rect.y + 60, 50, 20)
            pygame.draw.rect(self.screen, (0, 150, 0), buy_rect)
            buy_text = self.tiny_font.render("Buy", True, (255, 255, 255))
            self.screen.blit(buy_text, (buy_rect.x + 10, buy_rect.y + 3))
            buy_rects.append(buy_rect)
            shop_rects.append(shop_rect)
            if shop_rect.collidepoint(mouse_pos):
                shop_hover = (x, y + CHARM_BOX_HEIGHT + 5, charm['name'] + ": " + charm['desc'])

        # Packs section below shop charms
        pack_title = self.small_font.render("Packs", True, (255, 255, 255))
        self.screen.blit(pack_title, (50, 450))
        pack_rects = []
        pack_costs = [3, 5, 7, 3, 5, 9]  # 9 for special
        pack_choices_num = [2, 3, 5, 3, 4, 3]  # 3 choices
        pack_names = ["Basic Prism (1 of 2)", "Standard Prism (1 of 3)", "Premium Prism (1 of 5)", "Dice Pack (1 of 3)", "Dice Pack (1 of 4)", "Special Dice Pack (1 of 3)"]
        pack_x = 50
        for pack_idx in self.available_packs:
            x = pack_x
            y = 480
            pack_rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
            # pygame.draw.rect(self.screen, (100, 100, 100), pack_rect)  # Remove gray box
            if pack_idx in [0,1,2]:
                self.draw_prism_pack_icon(pack_rect)
            else:
                if pack_idx in [3,4]:  # Base dice packs
                    cycle = BASE_COLORS
                elif pack_idx == 5:  # Special dice pack
                    cycle = SPECIAL_COLORS
                else:
                    cycle = COLOR_CYCLE  # Fallback
                self.draw_pack_icon(pack_rect, pack_choices_num[pack_idx], cycle)
            if pack_rect.collidepoint(mouse_pos):
                tooltip_text = f"{pack_names[pack_idx]}\nCost: {pack_costs[pack_idx]}"
                self.draw_tooltip(pack_rect.x, pack_rect.y + CHARM_BOX_HEIGHT + 5, tooltip_text)
            pack_rects.append((pack_rect, pack_idx))
            pack_x += CHARM_BOX_WIDTH + CHARM_SPACING

        # Current hand multipliers panel on the right
        mult_title = self.small_font.render("Hand Multipliers", True, (255, 255, 255))
        self.screen.blit(mult_title, (self.width - 200, 120))
        y_offset = 150
        for ht, mult in self.hand_multipliers.items():
            mult_text = self.tiny_font.render(f"{ht}: x{mult:.1f}", True, (255, 255, 255))
            self.screen.blit(mult_text, (self.width - 200, y_offset))
            y_offset += 25

        # Change reroll_rect to bottom center
        reroll_text = self.font.render(f"Shop Reroll ({self.shop_reroll_cost})", True, (255, 255, 255))
        reroll_width = reroll_text.get_width() + 50  # Add padding to fit text
        reroll_rect = pygame.Rect(self.width // 2 - reroll_width // 2, self.height - BUTTON_HEIGHT - 120, reroll_width, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), reroll_rect)
        self.screen.blit(reroll_text, (reroll_rect.x + (reroll_width - reroll_text.get_width()) // 2, reroll_rect.y + 10))
        
        # Draw tooltips after all elements
        if equipped_hover:
            self.draw_tooltip(*equipped_hover)
        if shop_hover:
            self.draw_tooltip(*shop_hover)

        # Continue button
        continue_rect = pygame.Rect(self.width // 2 - BUTTON_WIDTH // 2, self.height - BUTTON_HEIGHT - 50, BUTTON_WIDTH, BUTTON_HEIGHT)
        pygame.draw.rect(self.screen, (100, 100, 100), continue_rect)
        continue_text = self.font.render("Continue", True, (255, 255, 255))
        self.screen.blit(continue_text, (continue_rect.x + 20, continue_rect.y + 10))
        
        return continue_rect, sell_rects, buy_rects, equipped_rects, shop_rects, pack_rects, reroll_rect

    def draw_prism_pack_icon(self, pack_rect):
        """Draws prism pack icon with 5 white dice in 5-pip pattern."""
        box_rect = pygame.Rect(pack_rect.x + (CHARM_BOX_WIDTH - PACK_BOX_SIZE) // 2, pack_rect.y + (CHARM_BOX_HEIGHT - PACK_BOX_SIZE) // 2, PACK_BOX_SIZE, PACK_BOX_SIZE)
        pygame.draw.rect(self.screen, (0, 0, 0), box_rect, 2)
        positions = [
            (0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)
        ]
        for pos in positions:
            x = box_rect.x + pos[0] * box_rect.width
            y = box_rect.y + pos[1] * box_rect.height
            die_rect = pygame.Rect(x - SMALL_ICON_DIE_SIZE // 2, y - SMALL_ICON_DIE_SIZE // 2, SMALL_ICON_DIE_SIZE, SMALL_ICON_DIE_SIZE)
            pygame.draw.rect(self.screen, (255, 255, 255), die_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), die_rect, 1)
            # Single pip in center
            pygame.draw.circle(self.screen, (0, 0, 0), die_rect.center, 2)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            self.screen.fill(TABLE_GREEN)  # Card table green background

            if self.game_state == 'game':
                self.draw_game_screen()
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

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.game_state == 'game':
                        if self.show_popup:
                            continue_rect = self.draw_popup()
                            if continue_rect and continue_rect.collidepoint(mouse_pos):
                                self.show_popup = False
                                self.advance_blind()  # Delayed reset of hands, discards, bag
                                self.generate_shop()
                                self.game_state = 'shop'  # Go to shop after popup
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
                    elif self.game_state == 'blinds':
                        if continue_rect and continue_rect.collidepoint(mouse_pos):
                            self.game_state = 'game'
                            self.new_turn()
                    elif self.game_state == 'shop':
                        if continue_rect and continue_rect.collidepoint(mouse_pos):
                            self.game_state = 'blinds'
                            self.shop_charms = []  # Clear shop
                        # Handle sell
                        for i, sell_rect in enumerate(sell_rects):
                            if sell_rect.collidepoint(mouse_pos):
                                self.confirm_sell_index = i
                                self.game_state = 'confirm_sell'
                                break
                        # Handle buy charms
                        for i, buy_rect in enumerate(buy_rects):
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
                        for pack_rect, pack_idx in pack_rects:
                            if pack_rect.collidepoint(mouse_pos):
                                cost = pack_costs[pack_idx]
                                has_debt = any(c['type'] == 'negative_coins' for c in self.equipped_charms)
                                min_coins = -5 if has_debt else 0
                                if self.coins >= cost or (self.coins - cost >= min_coins):
                                    self.coins -= cost
                                    if pack_idx in [0,1,2]:
                                        self.pack_choices = random.sample(HAND_TYPES, pack_choices_num[pack_idx])
                                        self.game_state = 'pack_select'
                                    elif pack_idx == 5:  # Special dice packs
                                        self.pack_choices = random.sample(SPECIAL_COLORS, 3)
                                        self.game_state = 'dice_select'
                                    else:  # 3 or 4: base dice packs
                                        self.pack_choices = random.sample(BASE_COLORS, pack_choices_num[pack_idx])
                                        self.game_state = 'dice_select'
                                    self.available_packs.remove(pack_idx)
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
                        for j, choice_rect in enumerate(choice_rects):
                            if choice_rect.collidepoint(mouse_pos):
                                chosen = self.pack_choices[j]
                                self.hand_multipliers[chosen] += PACK_BOOST
                                self.pack_choices = []
                                self.game_state = 'shop'
                                break
                    elif self.game_state == 'dice_select':
                        for choice_rect, color in choice_rects:
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
                                x = 50 + i * (CHARM_SIZE + 10)
                                y = 10
                                rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
                                if rect.collidepoint(mouse_pos):
                                    target_index = i
                                    break
                        if target_index != -1 and target_index != self.dragging_charm_index:
                            self.equipped_charms[self.dragging_charm_index], self.equipped_charms[target_index] = self.equipped_charms[target_index], self.equipped_charms[self.dragging_charm_index]
                        self.dragging_charm_index = -1
                        self.dragging_shop = False

            pygame.display.flip()  # Update screen

        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = ChromaRollGame()
    game.run()
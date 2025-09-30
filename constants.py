import pygame  # Required for key constants like K_SPACE
import data

# Debug flag: Set to True to force specific colors for testing (overrides random draw) and enable unlimited rerolls
DEBUG = True
DEBUG_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # Example: All different colors for rainbow testing
# DEBUG_COLORS = ['Glass', 'Glass', 'Glass', 'Glass', 'Glass']  # Example: All Glass colors for break testing
# DEBUG_COLORS = ['Gold', 'Gold', 'Gold', 'Silver', 'Silver']  # Example: All Gold and Silver colors for extra coin testing

# Debug UI panel constants
DEBUG_PANEL_WIDTH = 800
DEBUG_PANEL_HEIGHT = 600
DEBUG_PANEL_X = 50
DEBUG_PANEL_Y = 50
DEBUG_BUTTON_TEXT = "Debug All Charms"
DEBUG_BUTTON_SIZE = (200, 50)
DEBUG_CHARM_LIST_SPACING = 30  # Increased from 10 to 30 for more room
DEBUG_CHARM_TEXT_PADDING = 10  # Padding between charm box and text
DEBUG_CHARM_ROW_HEIGHT = 200  # Total height per row (box + text + padding)

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
    'font_main_path': 'assets/fonts/VT323-Regular.ttf',  # Pixel for main
    'font_main_size': 36,
    'font_small_path': 'assets/fonts/VT323-Regular.ttf',  # Vintage for small
    'font_small_size': 24,
    'font_tiny_path': 'assets/fonts/VT323-Regular.ttf',  # Same for tiny, or mix
    'font_tiny_size': 20,
}

# ... all other constants like DIE_SIZE, MAX_REROLLS, etc.
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
DAGGER_MULT_PER_COST = 0.1  # Multiplier increase per cost of sacrificed charm
MAX_DAGGER_MULT = 5.0
LEFT_BUTTON_X = 50
RIGHT_BUTTON_X = INITIAL_WIDTH - BUTTON_WIDTH - 50  # Will be dynamic
CENTER_LEFT_X = INITIAL_WIDTH // 2 - BUTTON_WIDTH - 20  # Will be dynamic
CENTER_RIGHT_X = INITIAL_WIDTH // 2 + 20  # Will be dynamic
INTEREST_RATE = 10  # Coins per extra coin
INTEREST_MAX = 50  # Max coins for interest calculation
TOOLTIP_MAX_WIDTH = 300  # Max width for tooltip before wrapping
PACK_BOOST = 0.5  # Multiplier boost per pack use
# Add this constant near the top, after other constants like HAND_TYPES

BAG_COLOR = (139, 69, 19)  # Brown for bag
BAG_BORDER_RADIUS = 15  # Rounded corners for bag
BAG_PADDING = 10  # Padding around dice grid in bag
UI_PANEL_COLOR = (0, 80, 0)  # Slightly darker green
UI_PANEL_BORDER_RADIUS = 10
UI_PANEL_WIDTH = 150
UI_PANEL_HEIGHT = 140  # Increased for coins
MULTIPLIERS_BUTTON_SIZE = 50
MULTIPLIERS_PANEL_WIDTH = 175
MULTIPLIERS_PANEL_HEIGHT = len(data.HAND_TYPES) * 25 + 20
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


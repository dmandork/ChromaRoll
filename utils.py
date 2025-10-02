import os
import sys
import pygame
import constants

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller temp path
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Use script dir for dev
    return os.path.join(base_path, relative_path)

def draw_rounded_element(surface, rect, fill_color, border_color=(0, 0, 0), border_width=2, radius=20, inner_content=None):
    """Draws a rounded rectangle with optional border and inner content.
    - inner_content: A function that takes the rect and draws inside it (e.g., dots or icons).
    """
    # Draw filled rounded rect
    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)

    # Add border if needed
    if border_width > 0:
       pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

    # Draw inner content if provided (call the function with rect)
    if inner_content:
        inner_content(rect)

# Other helpers: grayscale_surface, get_bag_color, etc.

# Represent each die as a dictionary
def create_dice_bag():
    """Creates the bag of 25 dice, 5 per color, each with standard faces."""
    bag = []
    color_names = ['Red', 'Blue', 'Green', 'Purple', 'Yellow'] # Base colors only
    for color in color_names:
        for i in range(1, constants.DICE_PER_COLOR + 1):
            die = {
                'id': f"{color}{i}",
                'color': color,
                'faces': constants.DICE_FACES[:],  # Copy list for future modifications
                'enhancements': []  # New: Empty list for each die
            }
            bag.append(die)
    return bag

def grayscale_surface(surface):
    """Converts a Pygame surface to grayscale."""
    arr = pygame.surfarray.pixels3d(surface)
    avg = (arr[:,:,0] * 0.3 + arr[:,:,1] * 0.59 + arr[:,:,2] * 0.11).astype(arr.dtype)
    arr[:,:,0] = avg
    arr[:,:,1] = avg
    arr[:,:,2] = avg
    del arr  # Unlock surface
    return surface

def wrap_text(font, text, max_width):  # Or keep as word_wrap if preferred
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

def get_easing(t, mode='out_cubic'):
    """Easing function for animations (t: 0-1)."""
    if mode == 'out_cubic':
        return 1 - (1 - t) ** 3
    elif mode == 'in_cubic':
        return t ** 3
    return t  # Linear fallback
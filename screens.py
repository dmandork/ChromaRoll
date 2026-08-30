# screens.py
import pygame
import time
import random
import math
from utils import *  # For draw_rounded_element, get_easing, etc.
from constants import THEME # For THEME, SPLASH_*, etc.
import constants
import data  # For DICE_DESCRIPTIONS, etc. if needed in drawing
from data import ENH_DESC  # For enhancement descriptions in tooltips


# Play-screen layout (1024x600). Keep the left column flowing downward.
# Inset past the wood rail so charms/bag/rune tray sit on the felt.
TABLE_RAIL = 16
PLAY_PAD = TABLE_RAIL + 8
PLAY_CHARM_Y = TABLE_RAIL + 10
PLAY_BAG_Y = TABLE_RAIL + 18
HUD_TEXT_WIDTH = 500
WIN_POPUP_WIDTH = 520

# Casino table (play screen). Charms/bag/dice slots stay put.
TABLE_WOOD = (96, 54, 24)
TABLE_WOOD_DARK = (52, 28, 12)
TABLE_GOLD = (212, 176, 72)
TABLE_FELT_INLAY = (16, 76, 28)
TABLE_PLAQUE = (24, 44, 20)


def _format_coins(n):
    try:
        return f"${int(n):,}"
    except (TypeError, ValueError):
        return f"${n}"


def _payout_row(line):
    """Turn 'Hands left: $$$$' into ('Hands left', '$4') for the win plaque."""
    line = (line or "").strip()
    if not line:
        return None
    if ':' not in line:
        return ('', line)
    label, rest = line.split(':', 1)
    rest = rest.strip()
    if rest and set(rest) == {'$'}:
        rest = f"${len(rest)}"
    return (label.strip(), rest)


def play_die_slot(game, i):
    """Unscaled slot for hand die i. Same formula draw_dice / GameState clicks use."""
    total = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
    start_x = (game.width - total) // 2
    x = start_x + i * (constants.DIE_SIZE + 20)
    y = game.height - constants.DIE_SIZE - 100
    return pygame.Rect(x, y, constants.DIE_SIZE, constants.DIE_SIZE)


def draw_table_felt(game):
    """Wood rail + gold pinstripe + felt inlay. Does not move any click targets."""
    w, h = game.width, game.height
    game.screen.fill(TABLE_WOOD_DARK)
    pygame.draw.rect(game.screen, TABLE_WOOD, pygame.Rect(4, 4, w - 8, h - 8))
    rail = TABLE_RAIL
    felt = pygame.Rect(rail, rail, w - 2 * rail, h - 2 * rail)
    pygame.draw.rect(game.screen, constants.THEME['background'], felt)
    pygame.draw.rect(game.screen, TABLE_GOLD, felt, 2)
    inlay = felt.inflate(-14, -14)
    if inlay.width > 40 and inlay.height > 40:
        pygame.draw.rect(game.screen, TABLE_FELT_INLAY, inlay, border_radius=32)


def draw_dice_spots(game):
    """Blackjack-style betting boxes under the five dice. Hold/discard/lock live here only."""
    held = getattr(game, 'held', []) or []
    marked = getattr(game, 'discard_selected', []) or []
    locked_idx = getattr(game, 'intensified_locked_die_idx', None)
    for i in range(constants.NUM_DICE_IN_HAND):
        spot = play_die_slot(game, i).inflate(12, 12)
        fill, border, width = (10, 48, 18), TABLE_GOLD, 2
        if i < len(marked) and marked[i]:
            fill, border, width = (70, 22, 22), (220, 60, 60), 3
        elif locked_idx is not None and i == locked_idx:
            fill, border, width = (22, 78, 30), (255, 215, 0), 3
        elif i < len(held) and held[i]:
            fill, border, width = (22, 78, 30), (90, 210, 90), 3
        pygame.draw.rect(game.screen, fill, spot, border_radius=18)
        pygame.draw.rect(game.screen, border, spot, width, border_radius=18)


def _plaque_hand_name(game):
    text = getattr(game, 'current_hand_text', '') or ''
    if text.startswith('BLOCKED'):
        return text.split('—')[0].strip()[:42]
    if text.startswith('Current Hand: '):
        return text[len('Current Hand: '):].split(' (')[0].strip()
    return ''


def _plaque_preview(game):
    """Hand name, this-roll preview total, and '60 base + 0 charms' detail."""
    text = getattr(game, 'current_hand_text', '') or ''
    name = _plaque_hand_name(game)
    preview = None
    detail = ''
    if ' = ' in text and 'total' in text.lower():
        try:
            tail = text.rsplit(' = ', 1)[-1]
            digits = ''.join(c for c in tail if c.isdigit() or c == '-')
            if digits and digits != '-':
                preview = int(digits)
        except ValueError:
            preview = None
    if '(' in text and ')' in text:
        detail = text[text.find('(') + 1:text.find(')')]
        detail = detail.replace('.0 charms', ' charms').replace('.0 ', ' ')
    if getattr(game, 'is_discard_phase', False) or name in ('', 'Nothing'):
        return name or 'Nothing', None, ''
    return name, preview, detail


def draw_score_plaque(game):
    """Center score plaque: blind, round/target, this-roll preview if submitted."""
    gold = TABLE_GOLD
    text = constants.THEME['text']
    w, h = 340, 186
    dice_top = game.height - constants.DIE_SIZE - 100
    band_top = PLAY_CHARM_Y + constants.CHARM_SIZE + 8
    x = (game.width - w) // 2
    y = band_top + max(4, (dice_top - band_top - h) // 2)
    rect = pygame.Rect(x, y, w, h)
    draw_rounded_element(game.screen, rect, TABLE_PLAQUE, border_color=gold, border_width=2, radius=12)
    inner = rect.inflate(-10, -10)
    pygame.draw.rect(game.screen, gold, inner, 1, border_radius=8)
    cx = rect.centerx
    limit = inner.bottom - 6

    def line(font, msg, color, gap=1):
        nonlocal_y = line.y
        if not font or nonlocal_y >= limit:
            return
        surf = font.render(str(msg), True, color)
        if nonlocal_y + surf.get_height() > limit:
            return
        game.screen.blit(surf, (cx - surf.get_width() // 2, nonlocal_y))
        line.y = nonlocal_y + surf.get_height() + gap

    line.y = inner.y + 6
    blind = getattr(game, 'current_blind', 'Small') or 'Small'
    line(game.tiny_font, f"{blind.upper()} BLIND", gold, 2)
    try:
        target = int(game.get_blind_target())
    except Exception:
        target = 0
    score = int(getattr(game, 'round_score', 0) or 0)
    line(game.font, f"{score}  /  {target}", text, 4)
    hand_name, preview, detail = _plaque_preview(game)
    if getattr(game, 'is_discard_phase', False):
        line(game.tiny_font, "discard phase", (170, 180, 170), 2)
    elif hand_name and hand_name != 'Nothing':
        line(game.small_font, hand_name, text, 2)
        if preview is not None:
            line(game.small_font, f"this roll  {preview}", gold, 2)
            # Only show banked total when some score is already on the table.
            if score > 0 and target:
                line(game.tiny_font, f"if scored  {score + preview} / {target}", (200, 200, 170), 1)
        if detail:
            line(game.tiny_font, detail, (170, 180, 170), 1)
    else:
        line(game.tiny_font, "hold dice to preview", (170, 180, 170), 2)
    mod = getattr(game, 'current_modifier_text', '') or ''
    if mod.startswith('Modifiers: '):
        mod = mod[len('Modifiers: '):]
    if mod and mod != 'None':
        for wrapped in wrap_text(game.tiny_font, mod, w - 28)[:2]:
            line(game.tiny_font, wrapped, (210, 200, 150), 1)
    return rect


def bag_geometry(game, origin=None):
    """Bag + rune-tray rects. Shared by draw and click handlers so they cannot drift.

    origin: optional (x, y) top-left of the bag body. Play screen omits this
    (bag sits top-right). Shop popup passes a local origin.
    """
    num_dice = len(getattr(game, 'bag', []) or [])
    columns = 6 if num_dice > 30 else 5
    rows = max(1, math.ceil(num_dice / columns) if num_dice else 1)
    grid_w = columns * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING
    grid_h = rows * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING
    bag_w = grid_w + 2 * constants.BAG_PADDING
    bag_h = grid_h + 2 * constants.BAG_PADDING
    if origin is None:
        bag_x = game.width - bag_w - PLAY_PAD
        bag_y = PLAY_BAG_Y
    else:
        bag_x, bag_y = origin
    bag_rect = pygame.Rect(bag_x, bag_y, bag_w, bag_h)
    tray_w = 2 * constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING
    tray_x = max(bag_rect.left - tray_w - 10, 10)
    tray_y = bag_y
    tray_rects = [
        pygame.Rect(tray_x + i * (constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING),
                    tray_y, constants.TRAY_SLOT_SIZE, constants.TRAY_SLOT_SIZE)
        for i in range(2)
    ]
    return bag_rect, tray_rects


def bag_cells(game, origin=None):
    """(die, rect) in the same order draw_bag_visual paints them."""
    bag_rect, tray_rects = bag_geometry(game, origin=origin)
    bag = getattr(game, 'bag', []) or []
    num_dice = len(bag)
    columns = 6 if num_dice > 30 else 5
    rows = max(1, math.ceil(num_dice / columns) if num_dice else 1)
    order = list(constants.COLORS.keys())
    def _key(d):
        c = d.get('color') if d else None
        return order.index(c) if c in order else 99
    try:
        sorted_bag = sorted(bag, key=_key)
    except Exception:
        sorted_bag = list(bag)
    start_x = bag_rect.x + constants.BAG_PADDING
    start_y = bag_rect.y + constants.BAG_PADDING
    cells = []
    index = 0
    for row in range(rows):
        for col in range(columns):
            if index >= num_dice:
                break
            die = sorted_bag[index]
            x = start_x + col * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
            y = start_y + row * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
            cells.append((die, pygame.Rect(x, y, constants.SMALL_DIE_SIZE, constants.SMALL_DIE_SIZE)))
            index += 1
    return bag_rect, tray_rects, cells


def bag_die_at(game, j):
    visual = getattr(game, 'bag_visual_dice', None)
    if visual and 0 <= j < len(visual):
        return visual[j]
    bag = getattr(game, 'bag', []) or []
    if 0 <= j < len(bag):
        return bag[j]
    return None


def charm_tooltip_text(game, charm, index=None):
    """Name + desc + live values. Never restates the desc as a 'Preview:' line."""
    if not charm:
        return ""
    parts = [f"{charm.get('name', '?')}: {charm.get('desc', '')}"]
    ctype = charm.get('type')
    name = charm.get('name')
    rolls = getattr(game, 'rolls', []) or []
    held = getattr(game, 'held', []) or []

    def _held_rolls():
        out = []
        for i, item in enumerate(rolls):
            if i < len(held) and held[i] and item and item[0]:
                out.append(item)
        return out

    if ctype == 'sacrifice_mult':
        cur = getattr(game, 'score_mult', 1.0)
        cap = " (capped)" if cur >= 5.0 else " (max x5)"
        parts.append(f"Current: x{cur:.1f}{cap}")
    elif ctype == 'empty_slot_mult':
        equipped = getattr(game, 'equipped_charms', []) or []
        if charm in equipped and hasattr(game, 'get_stencil_mult'):
            parts.append(f"Current: x{game.get_stencil_mult():.1f}")
        else:
            empty = max(0, getattr(game, 'max_charms', 5) - len(equipped) - 1)
            parts.append(f"If bought: x{charm.get('value', 0.5) * empty:.1f}")

    if name == 'Obelisk Orb':
        parts.append(f"Most played: {getattr(game, 'most_played_hand', None) or 'None'}")
    if name == 'Lucky Labyrinth':
        parts.append(f"Permanent: +{charm.get('permanent_bonus', 0.0):.1f}")
    if name == 'Life Milestone':
        n = getattr(game, 'stake_milestones', 0)
        parts.append(f"Current: +{charm.get('value', 0) * n:.1f} ({n} milestones)")
    if name == 'Stat Roller':
        face_sum = sum(v for d, v in _held_rolls())
        parts.append(f"This hand: +{face_sum}")
    if ctype == 'mult_per_enhance':
        enhance_name = charm.get('enhance') or charm.get('enh')
        if enhance_name:
            bag = getattr(game, 'full_bag', None) or getattr(game, 'bag', []) or []
            n = sum(1 for d in bag if d and enhance_name in (d.get('enhancements') or []))
            parts.append(f"Now: +{charm.get('value', 0) * n:.1f} ({n} {enhance_name} in bag)")
        else:
            n = sum(len((die.get('enhancements') or [])) for die, _ in _held_rolls())
            parts.append(f"This hand: +{charm.get('value', 0) * n:.1f} ({n} enhancements)")
    if ctype == 'discard_mult':
        n = getattr(game, 'discards_used_this_round', 0)
        parts.append(f"Now: +{charm.get('value', 0) * n:.1f} ({n} discards)")
    if ctype == 'coin_per_wild':
        held_rolls = _held_rolls()
        if held_rolls:
            non = [die.get('color', '') for die, _ in held_rolls if die.get('color') != 'Rainbow']
            mono = len(set(non)) <= 1 if non else False
            wild = sum(1 for die, _ in held_rolls if die.get('color') == 'Rainbow' and mono)
            parts.append(f"This hand: +{charm.get('value', 1) * wild} coins ({wild} wilds)")
    if ctype == 'coin_per_discard':
        n = getattr(game, 'discards_left', 0)
        parts.append(f"If unused: +{charm.get('value', 0) * n} coins ({n} discards)")
    if ctype == 'coin_per_lucky':
        n = getattr(game, 'lucky_triggers', 0)
        if n:
            parts.append(f"This hand: +{charm.get('value', 0) * n} coins")
    if name == 'Ice Shard':
        hp = charm.get('hands_played', 0)
        bonus = max(0, charm.get('start', 100) - (charm.get('decay', 5) * hp))
        parts.append(f"This hand: +{bonus}")
    if name == 'Loyalty Luck':
        local_turn = charm.get('local_turns', 0)
        every = charm.get('every', 6) or 6
        if local_turn > 0 and local_turn % every == 0:
            parts.append(f"Active this turn: +{charm.get('value', 3)}")
        else:
            turns_left = every - (local_turn % every)
            parts.append(f"Next in {turns_left} turns")
    if name == 'Luchador Lens':
        if getattr(game, 'current_round', 0) == 8 and getattr(game, 'current_blind', '') == 'Boss':
            parts.append("Cannot disable final boss")
        elif getattr(game, 'current_boss_effect', None):
            parts.append(f"Click to sell — target: {game.current_boss_effect['name']}")
        else:
            parts.append("Click to sell and disable the next boss")
    if name == 'Gift Glyph':
        equipped = getattr(game, 'equipped_charms', []) or []
        total = sum(c.get('sell_value', c.get('cost', 0)) - c.get('cost', 0) for c in equipped if c is not charm)
        parts.append(f"Extra sell so far: +{total}")
    if ctype == 'score_conditional':
        parts.append(f"Permanent: +{charm.get('permanent_bonus', 0)}")
    if ctype == 'score_per_discard_color':
        color = charm.get('active_color') or 'picking…'
        parts.append(f"This round: {color}")
        parts.append(f"Permanent: +{charm.get('permanent_bonus', 0)}")
    if ctype == 'sell_double_lock':
        if charm.get('locked') or getattr(game, 'mortgage_used_this_round', False):
            parts.append("Used this shop — next shop")
        else:
            parts.append("Next sell: 2x coins")
    if ctype == 'hand_upgrade':
        parts.append("25% to boost the hand you just scored")
    if ctype == 'break_save':
        last = getattr(game, '_last_save_roll', None)
        if last is not None:
            result = "saved" if getattr(game, '_last_save_success', False) else "broke"
            parts.append(f"Last save: {last} ({result})")
        else:
            parts.append("Glass save: roll 4–6")
    if ctype == 'mult_final_discard' and getattr(game, 'final_discard_mult', 0) > 0:
        parts.append(f"Armed: +{game.final_discard_mult} on next score")
    if ctype == 'boss_skip' and getattr(game, 'uno_skip_used', False):
        parts.append("exhausted")
    if index is not None and index in (getattr(game, 'disabled_charms', []) or []):
        parts.append("Disabled this round by Boss Effect")
    return "\n".join(parts)


def charm_is_visually_disabled(game, charm, index=None):
    """Gray-out: boss disable, or Monopoly Mortgage locked for the rest of this shop."""
    if not charm:
        return False
    if index is not None and index in (getattr(game, 'disabled_charms', []) or []):
        return True
    if charm.get('locked'):
        return True
    if charm.get('type') == 'sell_double_lock' and getattr(game, 'mortgage_used_this_round', False):
        return True
    return False



def draw_splash_screen(game):
    mouse_pos = pygame.mouse.get_pos()  # For hover
    if game.splash_start_time == 0:
        game.splash_start_time = time.time()
    if not hasattr(game, 'splash_total_start') or game.splash_total_start == 0:
        game.splash_total_start = time.time()

    time_elapsed = time.time() - game.splash_start_time
    total_elapsed = time.time() - game.splash_total_start
    image_width, image_height = game.splash_image.get_size()

    # Safeguard with total_elapsed
    total_duration = constants.SPLASH_DURATION_PAN + constants.SPLASH_DURATION_HOLD + constants.SPLASH_DURATION_ZOOM_OUT
    if total_elapsed >= total_duration:
        game.splash_phase = 'done'

    # Fill background for sides
    game.screen.fill((19, 16, 59))  # Or Dark Blue matching pool in splash image

    current_zoom = constants.SPLASH_INITIAL_ZOOM
    visible_height = game.height / current_zoom
    focus_y = 0

    if game.splash_phase == 'pan':
        progress = min(time_elapsed / constants.SPLASH_DURATION_PAN, 1.0)
        easing_progress = get_easing(progress, constants.SPLASH_EASING)  # Replace inline with call

        start_focus_y = image_height - visible_height / 2
        end_focus_y = visible_height / 2
        focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress

        if time_elapsed >= constants.SPLASH_DURATION_PAN:
            game.splash_phase = 'hold'
            game.splash_start_time = time.time()

    elif game.splash_phase == 'hold':
        visible_height = game.height / constants.SPLASH_INITIAL_ZOOM
        focus_y = visible_height / 2
        if time_elapsed >= constants.SPLASH_DURATION_HOLD:
            game.splash_phase = 'zoom_out'
            game.splash_start_time = time.time()

    elif game.splash_phase == 'zoom_out':
        progress = min(time_elapsed / constants.SPLASH_DURATION_ZOOM_OUT, 1.0)
        easing_progress = get_easing(progress, constants.SPLASH_EASING)  # Replace inline with call

        fit_zoom = game.height / image_height
        current_zoom = constants.SPLASH_INITIAL_ZOOM - (constants.SPLASH_INITIAL_ZOOM - fit_zoom) * easing_progress
        visible_height = game.height / current_zoom

        start_focus_y = (game.height / constants.SPLASH_INITIAL_ZOOM) / 2
        end_focus_y = image_height / 2
        focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress

        if time_elapsed >= constants.SPLASH_DURATION_ZOOM_OUT:
            game.splash_phase = 'done'

    elif game.splash_phase == 'done':
        fit_zoom = game.height / image_height
        current_zoom = fit_zoom
        visible_height = game.height / current_zoom
        focus_y = image_height / 2

    # Derive view_y, clamp, scale, and blit (do this before button so button is on top)
    view_y = max(0, focus_y - visible_height / 2)
    view_y = min(view_y, image_height - visible_height)

    scaled_width = int(image_width * current_zoom)
    scaled_height = int(image_height * current_zoom)
    scaled_image = pygame.transform.smoothscale(game.splash_image, (scaled_width, scaled_height))

    x_pos = (game.width - scaled_width) // 2
    y_pos = -int(view_y * current_zoom)

    game.screen.blit(scaled_image, (x_pos, y_pos))

    # Draw "Start Game" button after image (only in 'done')
    if game.splash_phase == 'done':
        # Buttons (below image or centered)
        # Buttons (spread across bottom with spacing)
        button_y = game.height - constants.SPLASH_BUTTON_HEIGHT * 2 - constants.SPLASH_BUTTON_SPACING - 36
        total_buttons_width = 2 * constants.SPLASH_BUTTON_WIDTH + constants.SPLASH_BUTTON_SPACING
        start_x = game.width // 2 - total_buttons_width // 2

        new_game_rect = pygame.Rect(start_x, button_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, new_game_rect, "New Game", is_hover=new_game_rect.collidepoint(mouse_pos))

        load_game_rect = pygame.Rect(start_x + constants.SPLASH_BUTTON_WIDTH + constants.SPLASH_BUTTON_SPACING, button_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, load_game_rect, "Load Game", is_hover=load_game_rect.collidepoint(mouse_pos))

        ach_y = button_y + constants.SPLASH_BUTTON_HEIGHT + constants.SPLASH_BUTTON_SPACING
        achievements_rect = pygame.Rect(start_x, ach_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, achievements_rect, "Achievements", is_hover=achievements_rect.collidepoint(mouse_pos))

        quit_rect = pygame.Rect(start_x + constants.SPLASH_BUTTON_WIDTH + constants.SPLASH_BUTTON_SPACING, ach_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, quit_rect, "Quit", is_hover=quit_rect.collidepoint(mouse_pos), is_red=True)

        if game.temp_message and time.time() - game.temp_message_start < getattr(game, 'temp_message_duration', 3.0):
            msg = game.small_font.render(game.temp_message, True, (255, 220, 80))
            game.screen.blit(msg, (game.width // 2 - msg.get_width() // 2, button_y - 36))

        return new_game_rect, load_game_rect, achievements_rect, quit_rect
    
    return None, None, None, None

def draw_init_screen(game):
    mouse_pos = pygame.mouse.get_pos()  # Add this line for mouse_pos

    game.screen.fill(constants.THEME['background'])  # Fill background
    
    # Title
    title_text = game.font.render("Select Starting Pouch", True, constants.THEME['text'])
    game.screen.blit(title_text, (game.width // 2 - title_text.get_width() // 2, 50))
    
    # Carousel of pouches (show 3-5 at a time)
    visible_count = 4  # As in your image
    box_size = 200
    spacing = 20  # Adjusted for fit based on image
    start_x = (game.width - (visible_count * box_size + (visible_count - 1) * spacing)) // 2
    y = 150

    pouch_rects = []
    import achievements as ach
    for i in range(visible_count):
        if game.pouch_offset + i >= len(data.POUCHES):
            break
        pouch = data.POUCHES[game.pouch_offset + i]
        x = start_x + i * (box_size + spacing)
        rect = pygame.Rect(x, y, box_size, box_size)
        unlocked = ach.is_pouch_unlocked(game, pouch)
        
        # Use rounded element for nice border tied to theme
        fill_color = constants.COLORS[pouch['color']]
        if not unlocked:
            r, g, b = fill_color
            fill_color = (r // 3 + 40, g // 3 + 40, b // 3 + 40)
        draw_rounded_element(game.screen, rect, fill_color, border_color=constants.THEME['border'], border_width=2, radius=20)
        
        # Determine text color based on background brightness
        r, g, b = fill_color
        brightness = (r * 0.299 + g * 0.587 + b * 0.114)  # Perceived brightness
        text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)  # White on dark, black on light
        
        name_text = game.small_font.render(pouch['name'], True, text_color)
        game.screen.blit(name_text, (x + (box_size - name_text.get_width()) // 2, y + 10))
        
        # Wrap description text
        desc_lines = wrap_text(game.tiny_font, pouch['desc'], box_size - 20)  # Wrap to fit box width minus padding
        line_y = y + 40
        for line in desc_lines:
            desc_text = game.tiny_font.render(line, True, text_color)
            game.screen.blit(desc_text, (x + 10, line_y))
            line_y += game.tiny_font.get_height()

        if not unlocked:
            try:
                overlay = pygame.Surface((box_size, box_size), pygame.SRCALPHA)
                overlay.fill((10, 10, 10, 110))
                game.screen.blit(overlay, rect.topleft)
            except Exception:
                pass
            badge = pygame.Rect(x + 24, y + box_size - 36, box_size - 48, 24)
            pygame.draw.rect(game.screen, (20, 20, 20), badge, border_radius=6)
            lock_label = game.tiny_font.render("LOCKED", True, (230, 200, 80))
            game.screen.blit(lock_label, (badge.centerx - lock_label.get_width() // 2,
                                          badge.centery - lock_label.get_height() // 2))

        # Clean tooltip without code
        bonus = pouch.get('bonus') or {}
        bonus_text = []
        if 'extra_dice' in bonus:
            for color, count in bonus['extra_dice'].items():
                label = 'random special' if color == 'random_special' else color
                bonus_text.append(f"{count} extra {label} dice")
        if 'discards' in bonus:
            bonus_text.append(f"+{bonus['discards']} discards")
        if 'hands' in bonus:
            bonus_text.append(f"{bonus['hands']:+d} hands")
        if 'coins' in bonus:
            bonus_text.append(f"+{bonus['coins']} starting coins")
        if bonus.get('charm_slots'):
            bonus_text.append(f"+{bonus['charm_slots']} charm slot")
        if bonus.get('shop_special_boost'):
            bonus_text.append("more special dice in shops")
        if bonus.get('mix_bonus') or bonus.get('balance_score'):
            bonus_text.append("+chips for 3+ colors, -40 if one color")
        if bonus.get('blind_mult') and float(bonus.get('blind_mult') or 1) != 1.0:
            bonus_text.append(f"x{bonus['blind_mult']} blinds")
        if bonus.get('randomize_bag'):
            bonus_text.append("randomize starting bag")

        if unlocked:
            tooltip_text = pouch['desc']
            if bonus_text:
                tooltip_text += "\nBonus: " + ", ".join(bonus_text)
        else:
            tooltip_text = "LOCKED\n" + ach.pouch_unlock_hint(game, pouch)
        if rect.collidepoint(mouse_pos):
            draw_tooltip(game, x, y + box_size + 10, tooltip_text)
        pouch_rects.append(rect)

    # Tutorial button (bottom center)
    tutorial_rect = pygame.Rect(game.width // 2 - constants.BUTTON_WIDTH // 2, game.height - constants.BUTTON_HEIGHT - 50, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, tutorial_rect, "Tutorial", is_hover=tutorial_rect.collidepoint(mouse_pos))

    # Arrows for carousel (green buttons, fixed positions)
    arrow_size = 50
    arrow_offset = 10  # Adjusted to fit on screen
    left_arrow_rect = pygame.Rect(start_x - arrow_size - arrow_offset, y + box_size // 2 - arrow_size // 2, arrow_size, arrow_size)
    draw_custom_button(game, left_arrow_rect, "<", is_hover=left_arrow_rect.collidepoint(mouse_pos))

    right_arrow_rect = pygame.Rect(start_x + visible_count * (box_size + spacing) - spacing + arrow_offset, y + box_size // 2 - arrow_size // 2, arrow_size, arrow_size)
    draw_custom_button(game, right_arrow_rect, ">", is_hover=right_arrow_rect.collidepoint(mouse_pos))

    # New: Render temp_message if active (same logic as draw_game_screen)
    if game.temp_message and time.time() - game.temp_message_start < game.temp_message_duration:
        time_elapsed = time.time() - game.temp_message_start
        alpha = max(0, 255 * (1 - time_elapsed / game.temp_message_duration))
        
        text_surf = game.font.render(game.temp_message, True, (255, 0, 0))  # Red for errors
        text_surf = text_surf.convert_alpha()  # Ensure alpha support
        text_surf.set_alpha(int(alpha))  # Fade out
        # Adjusted position: Top center to avoid overlap with title/pouches
        game.screen.blit(text_surf, (game.width // 2 - text_surf.get_width() // 2, 20))  # Top of screen

    # Return any rects if needed (e.g., for buttons)
    return pouch_rects, tutorial_rect, left_arrow_rect, right_arrow_rect

def draw_game_screen(game):
    """Draws the main game screen."""
    game.screen.fill(constants.THEME['background'])
    mouse_pos = pygame.mouse.get_pos()
    draw_table_felt(game)
    draw_dice_spots(game)
    draw_dice(game)
    if game.broken_dice and game.break_icon:
        current_time = time.time()
        elapsed = current_time - game.break_effect_start
        if elapsed < game.break_effect_duration:
            alpha = int(255 * (elapsed / game.break_effect_duration))
            overlay = game.break_icon.copy()
            overlay.set_alpha(alpha)
            for idx in game.broken_dice:
                total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
                start_x = (game.width - total_dice_width) // 2
                x = start_x + idx * (constants.DIE_SIZE + 20)
                size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[idx] else constants.DIE_SIZE
                offset = (constants.DIE_SIZE - size) / 2 if game.held[idx] else 0
                die_rect = pygame.Rect(x + offset, game.height - constants.DIE_SIZE - 100 + offset, size, size)
                overlay_rect = overlay.get_rect(center=die_rect.center)
                game.screen.blit(overlay, overlay_rect)
        else:
            game.broken_dice = []
            game.break_effect_start = 0

    bag_rect, tray_rects = bag_geometry(game)
    draw_bag_visual(game)
    for i, slot_rect in enumerate(tray_rects):
        pygame.draw.rect(game.screen, (150, 150, 150), slot_rect, border_radius=5)
        if game.rune_tray[i]:
            text = game.tiny_font.render(f"#{game.rune_tray[i].get('id', i + 1)}", True, constants.THEME['text'])
            game.screen.blit(text, (slot_rect.centerx - text.get_width() // 2,
                                    slot_rect.centery - text.get_height() // 2))
        else:
            pygame.draw.rect(game.screen, (80, 80, 80), slot_rect, width=2)

    game.equipped_charm_rects = []
    game.uno_charm_rect = None
    charm_hover = None
    for i, charm in enumerate(game.equipped_charms):
        x = 50 + i * (constants.CHARM_SIZE + 10)
        y = PLAY_CHARM_Y
        rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
        game.equipped_charm_rects.append(rect)
        draw_charm_die(game, rect, charm, index=i)
        if charm.get('name') == 'UNO Draw 2':
            game.uno_charm_rect = rect
        if rect.collidepoint(mouse_pos):
            charm_hover = (x, y + constants.CHARM_SIZE + 4, charm_tooltip_text(game, charm, index=i))

    hud_y = PLAY_CHARM_Y + constants.CHARM_SIZE + 6
    dice_top = game.height - constants.DIE_SIZE - 100
    hud_limit = dice_top - 36
    draw_score_plaque(game)
    draw_d20_hud(game, hud_y, hud_limit)

    draw_buttons(game)
    draw_ui_panel(game)

    if game.temp_message and time.time() - game.temp_message_start < game.temp_message_duration:
        msg_text = game.small_font.render(game.temp_message, True, (255, 255, 0))
        msg_y = max(hud_limit - 4, dice_top - 28)
        game.screen.blit(msg_text, (game.width // 2 - msg_text.get_width() // 2, msg_y))

    if game.current_boss_effect:
        name = game.current_boss_effect.get('name', '')
        desc = game.current_boss_effect.get('desc', '')
        max_width = min(220, bag_rect.width + 40)
        text_x = bag_rect.x
        text_y = bag_rect.bottom + 8
        title = game.tiny_font.render(f"Boss: {name}", True, (255, 80, 80))
        game.screen.blit(title, (text_x, text_y))
        wrapped = wrap_text(game.tiny_font, desc, max_width)[:2]
        for i, line in enumerate(wrapped):
            surf = game.tiny_font.render(line, True, (255, 120, 120))
            game.screen.blit(surf, (text_x, text_y + 18 + i * 18))
        boss_hit = pygame.Rect(text_x, text_y, max_width, 18 + max(1, len(wrapped)) * 18)
        if boss_hit.collidepoint(mouse_pos) and not charm_hover:
            charm_hover = (text_x - 20, text_y + boss_hit.height, f"{name}: {desc}")

    multipliers_button_rect = pygame.Rect(
        game.width - constants.MULTIPLIERS_BUTTON_SIZE - 10,
        game.height - constants.MULTIPLIERS_BUTTON_SIZE - 100,
        constants.MULTIPLIERS_BUTTON_SIZE, constants.MULTIPLIERS_BUTTON_SIZE)
    pygame.draw.rect(game.screen, TABLE_WOOD, multipliers_button_rect, border_radius=8)
    pygame.draw.rect(game.screen, TABLE_GOLD, multipliers_button_rect, 2, border_radius=8)
    pay = game.tiny_font.render("PAY", True, TABLE_GOLD)
    table_lbl = game.tiny_font.render("TABLE", True, TABLE_GOLD)
    game.screen.blit(pay, (multipliers_button_rect.centerx - pay.get_width() // 2,
                           multipliers_button_rect.y + 8))
    game.screen.blit(table_lbl, (multipliers_button_rect.centerx - table_lbl.get_width() // 2,
                                 multipliers_button_rect.y + 24))
    if multipliers_button_rect.collidepoint(mouse_pos):
        panel_x = game.width - constants.MULTIPLIERS_PANEL_WIDTH - 10
        panel_y = game.height - constants.MULTIPLIERS_PANEL_HEIGHT - constants.MULTIPLIERS_BUTTON_SIZE - 120
        panel_rect = pygame.Rect(panel_x, panel_y, constants.MULTIPLIERS_PANEL_WIDTH, constants.MULTIPLIERS_PANEL_HEIGHT)
        draw_rounded_element(game.screen, panel_rect, constants.UI_PANEL_COLOR, border_color=(0, 0, 0),
                             border_width=2, radius=constants.UI_PANEL_BORDER_RADIUS, inner_content=None)
        y_offset = panel_y + 10
        for ht in data.HAND_TYPES:
            mult = game.hand_multipliers.get(ht, 1.0)
            mult_text = game.tiny_font.render(f"{ht}: x{mult:.1f}", True, (constants.THEME['text']))
            game.screen.blit(mult_text, (panel_x + 10, y_offset))
            y_offset += 25

    if game.show_popup:
        draw_popup(game)

    if game.hovered_hand_die is not None:
        i = game.hovered_hand_die
        if i < len(game.rolls):
            die, _ = game.rolls[i]
            desc = ''
            if 'enhancements' in die and die['enhancements']:
                for enh in die['enhancements']:
                    desc += f"{enh}: {ENH_DESC.get(enh, 'Unknown effect')}\n"
            bonus = die.get('score_bonus', 0)
            if bonus > 0:
                desc += f"+{bonus} Score Bonus\n"
            if desc:
                die_rect = game.hand_die_rects[i]
                draw_tooltip(game, die_rect.x, die_rect.y + die_rect.height + 10, desc.strip())

    if game.hovered_bag_die is not None:
        j = game.hovered_bag_die
        die = bag_die_at(game, j)
        if die and j < len(getattr(game, 'bag_die_rects', []) or []):
            desc = ''
            if 'enhancements' in die and die['enhancements']:
                for enh in die['enhancements']:
                    desc += f"{enh}: {ENH_DESC.get(enh, 'Unknown effect')}\n"
            bonus = die.get('score_bonus', 0)
            if bonus > 0:
                desc += f"+{bonus} Score Bonus\n"
            if desc:
                brect = game.bag_die_rects[j]
                draw_tooltip(game, brect.x, brect.y + brect.height + 10, desc.strip())

    if charm_hover:
        draw_tooltip(game, charm_hover[0], charm_hover[1], charm_hover[2])

def draw_shop_screen(game, skip_tooltips=False):
    """Draws the shop screen with equipped charms (sell), equipped charms (buy), and Prism Packs."""
    mouse_pos = pygame.mouse.get_pos()
    draw_table_felt(game)

    # Header inset so it sits on the felt, not the wood rail
    shop_y = TABLE_RAIL + 8
    shop_text = game.font.render("SHOP", True, TABLE_GOLD)
    shop_text_x = 50
    game.screen.blit(shop_text, (shop_text_x, shop_y))

    coins_y = shop_y + 34
    coins_text = game.font.render(_format_coins(game.coins), True, TABLE_GOLD)
    coins_text_x = 50
    game.screen.blit(coins_text, (coins_text_x, coins_y))

    reroll_x = coins_text_x + coins_text.get_width() + 16
    reroll_y = coins_y - 6
    reroll_rect = pygame.Rect(reroll_x, reroll_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, reroll_rect, "Reroll (5)", is_hover=reroll_rect.collidepoint(mouse_pos))

    bag_open = getattr(game, 'shop_bag_open', False)
    bag_toggle = pygame.Rect(reroll_rect.right + 12, reroll_rect.y, 56, constants.BUTTON_HEIGHT)
    bag_hover = bag_toggle.collidepoint(mouse_pos)
    bag_fill = (160, 110, 50) if bag_open or bag_hover else constants.BAG_COLOR
    pygame.draw.rect(game.screen, bag_fill, bag_toggle, border_radius=8)
    pygame.draw.rect(game.screen, (0, 0, 0), bag_toggle, 2, border_radius=8)
    tri = [
        (bag_toggle.centerx, bag_toggle.y + 6),
        (bag_toggle.centerx - 8, bag_toggle.y + 16),
        (bag_toggle.centerx + 8, bag_toggle.y + 16),
    ]
    pygame.draw.polygon(game.screen, (90, 50, 20), tri)
    bag_lbl = game.tiny_font.render("BAG", True, constants.THEME['text'])
    game.screen.blit(bag_lbl, (bag_toggle.centerx - bag_lbl.get_width() // 2, bag_toggle.bottom - bag_lbl.get_height() - 6))
    game.shop_bag_toggle_rect = bag_toggle
    game.shop_bag_panel_rect = None

    # Continue top-right first so tray/multipliers can sit around it
    continue_x = game.width - constants.BUTTON_WIDTH - TABLE_RAIL - 8
    continue_y = TABLE_RAIL + 8
    continue_rect = pygame.Rect(continue_x, continue_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, continue_rect, "Continue", is_hover=continue_rect.collidepoint(mouse_pos),
                       fill_color=constants.THEME.get('yes_button', (0, 150, 0)))

    tray_width = 2 * constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING
    tray_x = continue_rect.x - tray_width - 12
    tray_y = continue_rect.y
    tray_rects = []
    for i in range(2):
        slot_rect = pygame.Rect(tray_x + i * (constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING), tray_y, constants.TRAY_SLOT_SIZE, constants.TRAY_SLOT_SIZE)
        pygame.draw.rect(game.screen, (150, 150, 150), slot_rect, border_radius=5)
        if game.rune_tray[i]:
            text = game.tiny_font.render(game.rune_tray[i]['name'][:3], True, constants.THEME['text'])
            game.screen.blit(text, (slot_rect.centerx - text.get_width()//2, slot_rect.centery - text.get_height()//2))
        else:
            pygame.draw.rect(game.screen, (80, 80, 80), slot_rect, width=2)
        tray_rects.append(slot_rect)

    panel_width = int(game.width * 0.9)
    panel_x = (game.width - panel_width) // 2
    panel_y = 248
    panel_height = game.height - panel_y - 10
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    # Draw panel background with rounded corners
    pygame.draw.rect(game.screen, TABLE_FELT_INLAY, panel_rect, border_radius=15)
    pygame.draw.rect(game.screen, TABLE_GOLD, panel_rect, width=2, border_radius=15)

    # Equipped charms horizontal at top (outside panel)
    equipped_title = game.small_font.render("Equipped Charms", True, (constants.THEME['text']))
    game.screen.blit(equipped_title, (50, 96))

    # Initialize lists and hover here
    sell_rects = []
    equipped_rects = []
    equipped_hover = None
    max_slots = getattr(game, 'max_charms', 5) or 5
    game.shop_slot_rects = []
    for i in range(max_slots):
        x = 50 + i * (constants.CHARM_SIZE + 12)
        y = 118
        slot = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE + 22)
        game.shop_slot_rects.append(slot)
        if i >= len(game.equipped_charms) or (i == game.dragging_charm_index and game.dragging_shop):
            empty = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
            pygame.draw.rect(game.screen, (70, 90, 70), empty, 2, border_radius=10)

    for i, charm in enumerate(game.equipped_charms):
        if i == game.dragging_charm_index and game.dragging_shop:
            continue
        x = 50 + i * (constants.CHARM_SIZE + 12)
        y = 118
        eq_rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE + 22)
        icon_rect = pygame.Rect(eq_rect.x, eq_rect.y, constants.CHARM_SIZE, constants.CHARM_SIZE)
        draw_charm_die(game, icon_rect, charm, index=i)
        sell_val = charm.get('sell_value', charm['cost'] // 2)
        sell_label = game.tiny_font.render(f"Sell: {sell_val}", True, (constants.THEME['text']))
        game.screen.blit(sell_label, (eq_rect.x + 2, eq_rect.y + constants.CHARM_SIZE + 2))
        sell_rect = pygame.Rect(eq_rect.x + constants.CHARM_SIZE - 50, eq_rect.y + constants.CHARM_SIZE + 1, 48, 20)
        pygame.draw.rect(game.screen, (150, 36, 36), sell_rect, border_radius=4)
        pygame.draw.rect(game.screen, TABLE_GOLD, sell_rect, 1, border_radius=4)
        sell_text = game.tiny_font.render("Sell", True, (constants.THEME['text']))
        game.screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 3))
        sell_rects.append(sell_rect)
        equipped_rects.append(eq_rect)
        if eq_rect.collidepoint(mouse_pos):
            tooltip_text = charm_tooltip_text(game, charm, index=i)
            equipped_hover = (x, y + eq_rect.height + 4, tooltip_text)
    
    # Draw dragged charm in shop
    drag_i = getattr(game, 'dragging_charm_index', -1)
    if drag_i != -1 and game.dragging_shop and 0 <= drag_i < len(game.equipped_charms):
        charm = game.equipped_charms[drag_i]
        x = mouse_pos[0] - game.drag_offset_x
        y = mouse_pos[1] - game.drag_offset_y
        rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
        draw_charm_die(game, rect, charm, index=drag_i)

    # Inner padding for items inside panel
    inner_padding = 20

    # Shop charms horizontal inside panel (top section, leaving space below for future)
    shop_title = game.small_font.render("Shop Charms", True, (constants.THEME['text']))
    game.screen.blit(shop_title, (panel_x + inner_padding, panel_y + 6))
    shop_charms_y = panel_y + 28
    buy_rects = []
    shop_rects = []
    shop_hover = None
    pack_rects = []

    if game.shop_charms:
        for i, charm in enumerate(game.shop_charms):
            x = panel_x + inner_padding + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
            y = shop_charms_y
            shop_rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
            icon_rect = pygame.Rect(shop_rect.x + (constants.CHARM_BOX_WIDTH - constants.CHARM_DIE_SIZE) // 2, shop_rect.y + 10, constants.CHARM_DIE_SIZE, constants.CHARM_DIE_SIZE)
            draw_charm_die(game, icon_rect, charm)
            cost_label = game.tiny_font.render(f"Cost: {charm['cost']}", True, (constants.THEME['text']))
            game.screen.blit(cost_label, (shop_rect.x + 5, shop_rect.y + constants.CHARM_BOX_HEIGHT - 30))
            buy_rect = pygame.Rect(shop_rect.x + constants.CHARM_BOX_WIDTH - 60, shop_rect.y + constants.CHARM_BOX_HEIGHT - 30, 50, 20)
            pygame.draw.rect(game.screen, (0, 130, 50), buy_rect, border_radius=4)
            pygame.draw.rect(game.screen, TABLE_GOLD, buy_rect, 1, border_radius=4)
            buy_text = game.tiny_font.render("Buy", True, (constants.THEME['text']))
            game.screen.blit(buy_text, (buy_rect.x + 10, buy_rect.y + 3))
            buy_rects.append(buy_rect)
            shop_rects.append(shop_rect)
            if shop_rect.collidepoint(mouse_pos):
                tooltip_text = charm_tooltip_text(game, charm)
                shop_hover = (x, y + constants.CHARM_BOX_HEIGHT + 5, tooltip_text)
    else:
        # **INSERT: Empty shop charms message**
        no_shop_text = game.small_font.render("No charms available", True, (constants.THEME['text']))
        no_shop_y = shop_charms_y + 20  # Center in section
        game.screen.blit(no_shop_text, (panel_x + inner_padding, no_shop_y))

    # Packs section inside panel (below shop charms, with space for future additions above/below/sides)
    pack_title = game.small_font.render("Packs", True, (constants.THEME['text']))
    game.screen.blit(pack_title, (panel_x + inner_padding, shop_charms_y + constants.CHARM_BOX_HEIGHT + 6))
    pack_y = shop_charms_y + constants.CHARM_BOX_HEIGHT + 26
    pack_rects = []
    pack_costs = [3, 5, 7, 3, 5, 9, 4, 7, 9, 0, 0]  # idx 10 = FREE D20 prism
    pack_choices_num = [2, 3, 5, 3, 4, 3, 3, 5, 5, 1, 5]
    pack_names = [
        "Basic Prism (1 of 2)", "Standard Prism (1 of 3)", "Premium Prism (1 of 5)",
        "Dice Pack (1 of 3)", "Dice Pack (1 of 4)", "Special Dice Pack (1 of 3)",
        "Basic Rune Pack (1 of 3)", "Mega Rune Pack (1 of 5)", "Super Rune Pack (2 of 5)",
        "Reused Rune (Free)",
        "FREE Prism Pack (D20 Reward)",
    ]
    pack_select_num = [1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1]

    pack_x_start = panel_x + inner_padding
    PACK_TILE = 70
    PACK_GAP = 8
    pack_hover = None
    for n, pack_idx in enumerate(game.available_packs):
        pack_row = 0 if pack_idx <= 5 else 1
        idx_in_row = sum(1 for p in game.available_packs[:n] if (p <= 5) == (pack_idx <= 5))
        x = pack_x_start + idx_in_row * (PACK_TILE + PACK_GAP)
        y = pack_y + pack_row * (PACK_TILE + PACK_GAP)
        pack_rect = pygame.Rect(x, y, PACK_TILE, PACK_TILE)
        # Draw icon centered (your existing logic)
        if pack_idx in [0,1,2]:
            draw_prism_pack_icon(game, pack_idx, pack_rect.x, pack_rect.y + 10)
        elif pack_idx == 10:
            draw_prism_pack_icon(game, 2, pack_rect.x, pack_rect.y + 10)
            pygame.draw.rect(game.screen, (255, 215, 0), pack_rect, 3, border_radius=6)
            free_lbl = getattr(game, 'tiny_font', game.small_font).render("FREE", True, (255, 215, 0))
            game.screen.blit(free_lbl, (pack_rect.centerx - free_lbl.get_width() // 2, pack_rect.bottom - 18))
        elif pack_idx in [3,4,5]:
            cycle = constants.BASE_COLORS if pack_idx in [3,4] else constants.SPECIAL_COLORS
            draw_pack_icon(game, pack_rect, pack_choices_num[pack_idx], cycle)
        elif pack_idx in [6,7,8]: # Rune packs
            pygame.draw.rect(game.screen, constants.BAG_COLOR, pack_rect, border_radius=constants.BAG_BORDER_RADIUS)
            text = game.tiny_font.render(f"Rune ${pack_costs[pack_idx]}", True, constants.THEME['text'])
            game.screen.blit(text, (pack_rect.centerx - text.get_width()//2, pack_rect.centery - text.get_height()//2))
        # NEW: Draw reused rune (pack_idx=9)
        elif pack_idx == 9:
            reused_rune = game.pack_choices[-1]  # Last in choices
            pygame.draw.rect(game.screen, (150, 150, 150), pack_rect, border_radius=5)  # Gray box
            text = game.tiny_font.render(reused_rune['name'][:8], True, constants.THEME['text'])
            game.screen.blit(text, (pack_rect.centerx - text.get_width()//2, pack_rect.centery - text.get_height()//2))
        if not skip_tooltips and pack_rect.collidepoint(mouse_pos):
            tooltip_text = f"{pack_names[pack_idx]}\nCost: {pack_costs[pack_idx]}"
            pack_hover = (pack_rect.x, pack_rect.y + PACK_TILE + 5, tooltip_text)
        pack_rects.append((pack_rect, pack_idx))

    # ADD: Draw free Grimoire rune next to packs (using stored var)
    grimoire_rune = getattr(game, 'grimoire_rune', None) # Use stored var from gen
    if grimoire_rune:
        rune_row = 1 if any(p > 5 for p in game.available_packs) else 0
        n_in_row = sum(1 for p in game.available_packs if (p > 5) == (rune_row == 1))
        rune_x = pack_x_start + n_in_row * (PACK_TILE + PACK_GAP)
        rune_y = pack_y + rune_row * (PACK_TILE + PACK_GAP)
        if rune_x + PACK_TILE > panel_x + panel_width - inner_padding:
            rune_x = panel_x + panel_width - PACK_TILE - inner_padding
        rune_rect = pygame.Rect(rune_x, rune_y, PACK_TILE, PACK_TILE)
        icon_rect = pygame.Rect(rune_rect.x + 4, rune_rect.y + 4, PACK_TILE - 8, PACK_TILE - 8)
        draw_charm_die(game, icon_rect, grimoire_rune)
        free_label = game.tiny_font.render("Free", True, (constants.THEME['text']))
        game.screen.blit(free_label, (rune_rect.centerx - free_label.get_width() // 2, rune_rect.bottom - 16))
        # Claim is pack_idx -1 on rune_rect — do not append to buy_rects
        # (that list is 1:1 with shop_charms; an extra rect crashed shop_charms[i]).
        pack_rects.append((rune_rect, -1)) # Special index for buy
        if not skip_tooltips and rune_rect.collidepoint(mouse_pos):
            pack_hover = (rune_rect.x, rune_rect.y + PACK_TILE + 4,
                          grimoire_rune['name'] + ": " + grimoire_rune['desc'] + " (Free!)")

    # Draw tooltips once, after every shop element
    if not skip_tooltips and not bag_open:
        if equipped_hover:
            draw_tooltip(game, *equipped_hover)
        if shop_hover:
            draw_tooltip(game, *shop_hover)
        if pack_hover:
            draw_tooltip(game, *pack_hover)
        if bag_toggle.collidepoint(mouse_pos):
            draw_tooltip(game, bag_toggle.x, bag_toggle.bottom + 6, "Show dice bag")

    if not bag_open:
        mult_x = game.width - 200
        mult_y = continue_rect.bottom + 10
        rows = list(game.hand_multipliers.items())
        box_h = 22 + len(rows) * 16 + 8
        box = pygame.Rect(mult_x - 8, mult_y - 4, 188, min(box_h, 240 - mult_y))
        pygame.draw.rect(game.screen, TABLE_PLAQUE, box, border_radius=8)
        pygame.draw.rect(game.screen, TABLE_GOLD, box, 1, border_radius=8)
        mult_title = game.tiny_font.render("PAYTABLE", True, TABLE_GOLD)
        game.screen.blit(mult_title, (mult_x, mult_y))
        y_offset = mult_y + 18
        for ht, mult in rows:
            if y_offset + 16 > box.bottom - 4:
                break
            col = TABLE_GOLD if float(mult) > 1.0 else constants.THEME['text']
            mult_text = game.tiny_font.render(f"{ht}: x{mult:.1f}", True, col)
            game.screen.blit(mult_text, (mult_x, y_offset))
            y_offset += 16
    else:
        game.shop_bag_panel_rect = draw_shop_bag_popup(game, mouse_pos)

    return continue_rect, sell_rects, buy_rects, equipped_rects, shop_rects, pack_rects, reroll_rect, tray_rects

BLIND_ORDER = ['Small', 'Big', 'Boss']
BLIND_CARD_STYLE = {
    'Small': {
        'fill': (28, 68, 36), 'fill_now': (42, 96, 50), 'fill_past': (20, 40, 24),
        'accent': (212, 180, 72),
    },
    'Big': {
        'fill': (56, 62, 28), 'fill_now': (78, 88, 38), 'fill_past': (34, 38, 20),
        'accent': (220, 150, 52),
    },
    'Boss': {
        'fill': (78, 28, 32), 'fill_now': (104, 36, 40), 'fill_past': (44, 22, 24),
        'accent': (220, 70, 70),
    },
}


def blind_status(current_blind, name):
    try:
        ci = BLIND_ORDER.index(current_blind)
        ni = BLIND_ORDER.index(name)
    except ValueError:
        return 'future'
    if ni < ci:
        return 'past'
    if ni == ci:
        return 'current'
    return 'future'


def blinds_layout(game):
    """Stake-screen geometry. Charms/bag keep play-screen positions."""
    bag_rect, tray_rects = bag_geometry(game)
    n_charms = len(getattr(game, 'equipped_charms', []) or [])
    title_h, meta_h, gap = 40, 26, 10
    header_block = title_h + meta_h + gap
    if n_charms:
        header_y = PLAY_CHARM_Y + constants.CHARM_SIZE + 8
    else:
        header_y = PLAY_BAG_Y + 2
    btn_y = game.height - constants.BUTTON_HEIGHT - 28
    cards_top = max(header_y + header_block, bag_rect.bottom + 12)
    cards_bottom = btn_y - 28
    if cards_top > cards_bottom - 160:
        cards_top = min(cards_top, cards_bottom - 160)
    card_h = max(160, cards_bottom - cards_top)
    card_w, gap_x = 210, 20
    total = 3 * card_w + 2 * gap_x
    start_x = max(20, (game.width - total) // 2)
    cards = [
        pygame.Rect(start_x + i * (card_w + gap_x), cards_top, card_w, card_h)
        for i in range(3)
    ]
    btn_gap = 24
    btn_total = constants.BUTTON_WIDTH * 2 + btn_gap
    btn_x = game.width // 2 - btn_total // 2
    return {
        'bag': bag_rect,
        'tray': tray_rects,
        'header_y': header_y,
        'header_block': header_block,
        'cards': cards,
        'intensify': pygame.Rect(btn_x, btn_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT),
        'continue': pygame.Rect(
            btn_x + constants.BUTTON_WIDTH + btn_gap, btn_y,
            constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT),
    }


def _blinds_blit(game, font, text, color, x, y, center_x=None):
    if not font:
        return 0
    surf = font.render(str(text), True, color)
    if center_x is not None:
        x = center_x - surf.get_width() // 2
    game.screen.blit(surf, (x, y))
    return surf.get_height()


def draw_blinds_play_hud(game, mouse_pos):
    """Charms (play-screen left) + bag/tray (play-screen top-right)."""
    bag_rect, tray_rects = bag_geometry(game)
    draw_bag_visual(game)
    tray = getattr(game, 'rune_tray', None) or [None, None]
    for i, slot_rect in enumerate(tray_rects):
        pygame.draw.rect(game.screen, (150, 150, 150), slot_rect, border_radius=5)
        rune = tray[i] if i < len(tray) else None
        if rune:
            label = game.tiny_font.render(f"#{rune.get('id', i + 1)}", True, constants.THEME['text'])
            game.screen.blit(label, (slot_rect.centerx - label.get_width() // 2,
                                     slot_rect.centery - label.get_height() // 2))
        else:
            pygame.draw.rect(game.screen, (80, 80, 80), slot_rect, width=2)

    game.equipped_charm_rects = []
    charm_hover = None
    for i, charm in enumerate(getattr(game, 'equipped_charms', []) or []):
        x = 50 + i * (constants.CHARM_SIZE + 10)
        y = PLAY_CHARM_Y
        rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
        game.equipped_charm_rects.append(rect)
        draw_charm_die(game, rect, charm, index=i)
        if rect.collidepoint(mouse_pos):
            charm_hover = (x, y + constants.CHARM_SIZE + 4, charm_tooltip_text(game, charm, index=i))
    return bag_rect, charm_hover


def draw_blinds_screen(game):
    """Stake / blinds select: three tall cards, play-screen charms + bag."""
    mouse_pos = pygame.mouse.get_pos()
    game.screen.fill(constants.THEME['background'])
    if game.upcoming_boss_effect is None:
        game.upcoming_boss_effect = data.pick_boss_effect(getattr(game, 'current_stake', 1))
    if hasattr(game, 'update_advantage_flag'):
        game.update_advantage_flag()

    layout = blinds_layout(game)
    bag_rect, charm_hover = draw_blinds_play_hud(game, mouse_pos)

    theme_text = constants.THEME['text']
    gold = constants.THEME.get('highlight', (200, 160, 0))
    header_y = layout['header_y']
    stake = int(getattr(game, 'current_stake', 1) or 1)
    _blinds_blit(game, game.font, f"STAKE {stake}", theme_text, 0, header_y, center_x=game.width // 2)

    # One clustered meta row under the title so a fat coin count cannot
    # sit on the Small card. [pip] Name   $1,234   ●○○○○○○○
    pouch = getattr(game, 'current_pouch', None) or {}
    pouch_name = (pouch.get('name') or '').replace(' Pouch', '')
    pouch_color = constants.COLORS.get(pouch.get('color'), gold)
    coins = int(getattr(game, 'coins', 0) or 0)
    try:
        coin_label = f"${coins:,}"
    except (TypeError, ValueError):
        coin_label = f"${coins}"
    name_surf = game.tiny_font.render(pouch_name, True, theme_text) if pouch_name else None
    coin_surf = game.tiny_font.render(coin_label, True, gold)
    dots_w = 8 * 14
    pieces = 14 + (name_surf.get_width() + 10 if name_surf else 0) + coin_surf.get_width() + 16 + dots_w
    meta_x = game.width // 2 - pieces // 2
    meta_y = header_y + 38
    pygame.draw.circle(game.screen, pouch_color, (meta_x + 7, meta_y + 8), 7)
    pygame.draw.circle(game.screen, (0, 0, 0), (meta_x + 7, meta_y + 8), 7, 1)
    nx = meta_x + 18
    if name_surf:
        game.screen.blit(name_surf, (nx, meta_y))
        nx += name_surf.get_width() + 10
    game.screen.blit(coin_surf, (nx, meta_y))
    nx += coin_surf.get_width() + 16
    for i in range(8):
        cx = nx + 6 + i * 14
        if i + 1 < stake:
            pygame.draw.circle(game.screen, gold, (cx, meta_y + 8), 5)
        elif i + 1 == stake:
            pygame.draw.circle(game.screen, gold, (cx, meta_y + 8), 5, 2)
            pygame.draw.circle(game.screen, gold, (cx, meta_y + 8), 2)
        else:
            pygame.draw.circle(game.screen, (80, 100, 80), (cx, meta_y + 8), 5, 1)

    current = getattr(game, 'current_blind', 'Small') or 'Small'
    tooltip = None
    blind_rects = layout['cards']
    for i, blind in enumerate(BLIND_ORDER):
        rect = blind_rects[i]
        style = BLIND_CARD_STYLE[blind]
        status = blind_status(current, blind)
        if status == 'current':
            fill = style['fill_now']
            border = gold
            border_w = 3
        elif status == 'past':
            fill = style['fill_past']
            border = (0, 0, 0)
            border_w = 2
        else:
            fill = style['fill']
            border = (0, 0, 0)
            border_w = 2
        draw_rounded_element(game.screen, rect, fill, border_color=border, border_width=border_w, radius=16)
        accent = style['accent']
        cx = rect.centerx
        y = rect.y + 14
        y += _blinds_blit(game, game.tiny_font, blind.upper(), accent, 0, y, center_x=cx) + 2
        if status == 'past':
            y += _blinds_blit(game, game.tiny_font, "CLEARED", (160, 200, 160), 0, y, center_x=cx) + 6
        elif status == 'current':
            y += _blinds_blit(game, game.tiny_font, "UP NEXT", gold, 0, y, center_x=cx) + 6
        else:
            y += 10
        y += _blinds_blit(game, game.small_font, f"{blind} Blind", theme_text, 0, y, center_x=cx) + 8
        target = int(game.get_blind_target(game.current_stake, blind))
        y += _blinds_blit(game, game.font, str(target), theme_text, 0, y, center_x=cx) + 2
        y += _blinds_blit(game, game.tiny_font, "to beat", (170, 180, 170), 0, y, center_x=cx) + 10

        if blind == 'Boss':
            if game.current_boss_effect and game.current_boss_effect.get('name') == 'DISABLED':
                boss_name = "DISABLED"
                boss_desc = "Boss effect disabled by Luchador Lens!"
                boss_color = constants.THEME.get('disabled', (140, 140, 140))
            elif game.upcoming_boss_effect:
                boss_name = game.upcoming_boss_effect.get('name', 'Random')
                boss_desc = game.upcoming_boss_effect.get('desc', '')
                boss_color = accent
            else:
                boss_name = "Random"
                boss_desc = "Boss effect TBD"
                boss_color = accent
            y += _blinds_blit(game, game.small_font, boss_name, boss_color, 0, y, center_x=cx) + 2
            diff = ''
            if game.current_boss_effect and game.current_boss_effect.get('name') == 'DISABLED':
                diff = ''
            elif game.upcoming_boss_effect:
                diff = (game.upcoming_boss_effect.get('difficulty') or '').upper()
            if diff:
                diff_col = {'EASY': (160, 210, 140), 'MEDIUM': gold, 'HARD': accent}.get(diff, gold)
                y += _blinds_blit(game, game.tiny_font, diff, diff_col, 0, y, center_x=cx) + 4
            inner_w = rect.width - 24
            lines = wrap_text(game.tiny_font, boss_desc, inner_w)[:5]
            for line in lines:
                y += _blinds_blit(game, game.tiny_font, line, (220, 180, 180), 0, y, center_x=cx) + 1
            if rect.collidepoint(mouse_pos):
                tooltip = (rect.x, rect.bottom - 8, f"{boss_name}: {boss_desc}")

        if status == 'past':
            try:
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 70))
                game.screen.blit(overlay, rect.topleft)
            except Exception:
                pass

    intensify_rect = layout['intensify']
    continue_rect = layout['continue']
    boon = getattr(game, 'd20_boon', None)
    locked = bool(boon is not None and hasattr(boon, 'is_locked') and boon.is_locked())
    gated = not data.intensify_unlocked(getattr(game, 'current_stake', 1))
    if locked:
        hint = game.tiny_font.render("already rolled", True, (180, 190, 160))
        game.screen.blit(hint, (intensify_rect.centerx - hint.get_width() // 2,
                                intensify_rect.y - hint.get_height() - 4))
        draw_custom_button(game, intensify_rect, "Locked",
                           fill_color=constants.THEME.get('disabled', (100, 100, 100)))
    elif gated:
        hint = game.tiny_font.render(f"Unlocks at Stake {data.INTENSIFY_MIN_STAKE}", True, (180, 190, 160))
        game.screen.blit(hint, (intensify_rect.centerx - hint.get_width() // 2,
                                intensify_rect.y - hint.get_height() - 4))
        draw_custom_button(game, intensify_rect, "Intensify",
                           fill_color=constants.THEME.get('disabled', (100, 100, 100)))
    else:
        hint = game.tiny_font.render("optional D20 boon", True, (180, 190, 160))
        game.screen.blit(hint, (intensify_rect.centerx - hint.get_width() // 2,
                                intensify_rect.y - hint.get_height() - 4))
        draw_custom_button(game, intensify_rect, "Intensify",
                           is_hover=intensify_rect.collidepoint(mouse_pos))
    draw_custom_button(game, continue_rect, "Continue",
                       is_hover=continue_rect.collidepoint(mouse_pos),
                       fill_color=constants.THEME.get('yes_button', (0, 150, 0)))

    debug_button_rect = None
    up_rect = None
    down_rect = None
    debug_jump_rect = None
    debug_open = bool(constants.DEBUG and getattr(game, 'debug_play_open', False))
    if debug_open:
        debug_button_rect = pygame.Rect(game.width - 200, game.height - 100, 180, 40)
        debug_jump_rect = pygame.Rect(game.width - 200, game.height - 60, 180, 40)
        pygame.draw.rect(game.screen, (50, 50, 50), debug_button_rect, border_radius=5)
        pygame.draw.rect(game.screen, (50, 50, 50), debug_jump_rect, border_radius=5)
        sel = game.small_font.render("Select Boss (Debug)", True, (0, 255, 0))
        jmp = game.small_font.render("Jump to Boss (Debug)", True, (0, 255, 0))
        game.screen.blit(sel, (debug_button_rect.x + 10, debug_button_rect.y + 10))
        game.screen.blit(jmp, (debug_jump_rect.x + 10, debug_jump_rect.y + 10))
        if game.debug_boss_dropdown_open:
            panel_width, panel_height = 300, 300
            panel_x = game.width - panel_width - 10
            panel_y = debug_button_rect.y - panel_height - 10
            if panel_y < 0:
                panel_y = debug_button_rect.y + debug_button_rect.height + 10
            pygame.draw.rect(game.screen, (20, 20, 20), (panel_x, panel_y, panel_width, panel_height))
            item_height = 25
            visible_items = panel_height // item_height
            total_items = len(data.BOSS_EFFECTS)
            up_rect = pygame.Rect(panel_x + panel_width - 30, panel_y, 30, 30)
            down_rect = pygame.Rect(panel_x + panel_width - 30, panel_y + panel_height - 30, 30, 30)
            pygame.draw.rect(game.screen, (100, 100, 100), up_rect)
            pygame.draw.rect(game.screen, (100, 100, 100), down_rect)
            game.screen.blit(game.small_font.render("^", True, theme_text), (up_rect.x + 10, up_rect.y + 5))
            game.screen.blit(game.small_font.render("v", True, theme_text), (down_rect.x + 10, down_rect.y + 5))
            for i in range(game.debug_boss_scroll_offset, min(game.debug_boss_scroll_offset + visible_items, total_items)):
                effect = data.BOSS_EFFECTS[i]
                item_text = game.small_font.render(
                    f"{effect['name']}: {effect['desc'][:30]}...", True, theme_text)
                item_y = panel_y + (i - game.debug_boss_scroll_offset) * item_height + 5
                game.screen.blit(item_text, (panel_x + 10, item_y))

    msg = getattr(game, 'temp_message', None)
    if msg and time.time() - getattr(game, 'temp_message_start', 0) < getattr(game, 'temp_message_duration', 2):
        surf = game.small_font.render(msg, True, (255, 255, 0))
        game.screen.blit(surf, (game.width // 2 - surf.get_width() // 2, layout['continue'].y - 22))

    if bag_rect.collidepoint(mouse_pos) or any(
            r.collidepoint(mouse_pos) for r in getattr(game, 'bag_die_rects', []) or []):
        for j, brect in enumerate(getattr(game, 'bag_die_rects', []) or []):
            if not brect.collidepoint(mouse_pos):
                continue
            die = bag_die_at(game, j)
            if not die:
                continue
            lines = [f"{die.get('color', '?')} die"]
            for enh in die.get('enhancements') or []:
                lines.append(f"{enh}: {ENH_DESC.get(enh, 'enhancement')}")
            bonus = die.get('score_bonus', 0)
            if bonus:
                lines.append(f"+{bonus} score bonus")
            tooltip = (brect.x, brect.y + brect.height + 6, "\n".join(lines))
            break

    if charm_hover:
        draw_tooltip(game, charm_hover[0], charm_hover[1], charm_hover[2])
    elif tooltip:
        draw_tooltip(game, tooltip[0], tooltip[1], tooltip[2])

    return (layout['cards'], continue_rect, debug_button_rect, up_rect, down_rect,
            debug_jump_rect, intensify_rect)

def draw_tutorial_screen(game):
    """Draws the tutorial screen with overlays on mock states."""
    mouse_pos = pygame.mouse.get_pos()  # Define mouse_pos for hover checks
    game.screen.fill(constants.THEME['background'])  # Clears relics and prevents stacking
    # Save old states to restore after draw
    old_hand = game.hand[:]
    old_rolls = game.rolls[:]
    old_held = game.held[:]
    old_discard_selected = game.discard_selected[:]
    old_is_discard_phase = game.is_discard_phase
    old_has_rolled = game.has_rolled
    old_shop_charms = game.shop_charms[:]
    old_multipliers_hover = game.multipliers_hover
    old_show_popup = game.show_popup
    old_popup_message = game.popup_message

    # Mock data for steps
    mock_colors = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']  # Varied for visual interest
    mock_dice = [{'id': f'Mock{i}', 'color': mock_colors[i % 5], 'faces': constants.DICE_FACES} for i in range(constants.NUM_DICE_IN_HAND)]
    if game.tutorial_step in [1, 2, 3]:  # Discard, Roll/Hold, Scoring - mock hand/dice
        game.hand = mock_dice
        if game.tutorial_step == 2:  # Step 3: Fixed faces 6,6,2,3,4 and hold first two
            game.rolls = [(mock_dice[0], 6), (mock_dice[1], 6), (mock_dice[2], 2), (mock_dice[3], 3), (mock_dice[4], 4)]
            game.held = [True, True, False, False, False]  # Hold the two 6's (appear smaller)
        else:
            game.rolls = [(die, 1) for die in mock_dice]  # Fixed to 1 pip for other steps
        game.discard_selected = [False] * constants.NUM_DICE_IN_HAND
        if game.tutorial_step == 1:  # Step 2: Show red border on first 2 dice for discard example
            game.discard_selected[0] = True
            game.discard_selected[1] = True
        game.is_discard_phase = (game.tutorial_step == 1)  # Force discard mode for step 2
        game.has_rolled = (game.tutorial_step > 1)  # Show as rolled for steps 3-4
    if game.tutorial_step == 3:  # Scoring - force multipliers panel
        game.multipliers_hover = True  # Open combos panel (assume this triggers it)
    if game.tutorial_step == 4:  # Shop - use specific real charms
        game.shop_charms = [
            {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 100},
            {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},
            {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 'break_penalty': 5},
            {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 'hand_bonus', 'hands': ['Pair'], 'value': 50}
        ]  # Exact real charms with your provided dicts (icons via resource_path in draw_shop_screen)

    # Draw underlying mock screen based on step
    if game.tutorial_step == 0:  # Step 1: Pouch selection
        draw_init_screen(game)  # Mock init screen
    elif game.tutorial_step in [1, 2, 3]:  # Steps 2-4: Game phases
        draw_game_screen(game)  # Draws with mock data
    elif game.tutorial_step == 4:  # Step 5: Shop/charms
        draw_shop_screen(game)  # With specific real charms (static, no rotation)
    elif game.tutorial_step == 5:  # Step 6: Blinds progression
        draw_blinds_screen(game)  # Mock blinds

    # Restore old states
    game.hand = old_hand
    game.rolls = old_rolls
    game.held = old_held
    game.discard_selected = old_discard_selected
    game.is_discard_phase = old_is_discard_phase
    game.has_rolled = old_has_rolled
    game.shop_charms = old_shop_charms
    game.multipliers_hover = old_multipliers_hover
    game.show_popup = old_show_popup
    game.popup_message = old_popup_message

    # Overlay semi-transparent background for focus
    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Semi-black
    game.screen.blit(overlay, (0, 0))

    # Instructions per step (centered popup-style)
    instructions = [
        "Step 1: Choose Your Pouch\nSelect a starting pouch for bonuses.\nClick a pouch to proceed.",
        "Step 2: Discard Phase\nSelect dice to discard before rolling.\nClick dice to toggle, then 'Discard' button.",
        "Step 3: Roll and Hold\nRoll dice, hold keepers by clicking.\nReroll non-held up to 2 times.",
        "Step 4: Scoring\nForm hands like Pair or Straight.\nClick 'Score' to add points.",
        "Step 5: Shop and Charms\nBuy charms for bonuses.\nDrag to equip, buy/sell in shop.",
        "Step 6: Blinds Progression\nBeat Small/Big/Boss blinds.\nScore enough to advance stakes!"
    ]
    lines = instructions[game.tutorial_step].split('\n')

    # Opaque green panel behind text (insert here)
    panel_padding = 20  # Around text
    panel_width = max(game.font.render(line, True, (0,0,0)).get_width() for line in lines) + 2 * panel_padding
    panel_height = len(lines) * 40 + 2 * panel_padding - 20  # Spacing adjusted
    panel_x = game.width // 2 - panel_width // 2
    panel_y = game.height // 2 - panel_height // 2 - 20  # Center, slight up shift
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_surf.fill((constants.THEME['panel_bg'][0], constants.THEME['panel_bg'][1], constants.THEME['panel_bg'][2], 200))  # Green with 78% opacity
    game.screen.blit(panel_surf, (panel_x, panel_y))
    pygame.draw.rect(game.screen, (0, 0, 0), panel_rect, 3)  # Black border

    # Now draw text inside panel
    y_offset = panel_y + panel_padding  # Start inside panel with padding (increased top padding by +10 to fix stick out)
    for line in lines:
        text = game.font.render(line, True, (constants.THEME['text']))
        text_rect = text.get_rect(center=(game.width // 2, y_offset))
        game.screen.blit(text, text_rect)
        y_offset += 40  # Spacing

    if game.tutorial_step == 5:  # Step 6: Shift text down to avoid covering blinds
        y_offset += 100  # Move down by 100 pixels (adjust if needed)

    # Arrows for specific steps (point down to buttons)
    arrow_color = (255, 255, 0)  # Yellow
    arrow_width = 20
    arrow_height = 30
    if game.tutorial_step == 1:  # Step 2: Arrows to discard (bottom left) and start roll (bottom right)
        arrow_offset = -20  # Pixels to shift down (as per your change)
        # Arrow above discard button (bottom left, using LEFT_BUTTON_X)
        button_x = constants.LEFT_BUTTON_X + constants.BUTTON_WIDTH // 2
        button_y = game.height - constants.BUTTON_HEIGHT - 50  # Adjust -50 based on your bottom_y padding in draw_buttons
        points = [
            (button_x - arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top left (wide base above, shifted down)
            (button_x + arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top right
            (button_x, button_y - arrow_offset)   # Bottom point (toward button, shifted down)
        ]
        pygame.draw.polygon(game.screen, arrow_color, points)
        
        # Arrow above start roll button (bottom right, using RIGHT_BUTTON_X)
        button_x = constants.RIGHT_BUTTON_X + constants.BUTTON_WIDTH // 2
        points = [
            (button_x - arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top left
            (button_x + arrow_width // 2, button_y - arrow_height - arrow_offset),  # Top right
            (button_x, button_y - arrow_offset)   # Bottom point
        ]
        pygame.draw.polygon(game.screen, arrow_color, points)
    elif game.tutorial_step == 2:  # Step 3: Arrows below held dice (first two with 6 pips), pointing up
        # Calculate dice positions (mirror your draw_hand logic)
        total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
        start_x = (game.width - total_dice_width) // 2
        die_y = game.height - constants.DIE_SIZE - 100  # Base y for dice
        arrow_offset = 25  # Shift down slightly (adjust 5-15 if needed)
        for i in range(2):  # First two dice
            size = constants.DIE_SIZE * constants.HELD_DIE_SCALE  # Held size
            offset = (constants.DIE_SIZE - size) / 2
            die_x = start_x + i * (constants.DIE_SIZE + 20) + offset
            arrow_x = die_x + size // 2  # Center under die
            arrow_y = die_y + size + offset + arrow_offset + 10  # Below die, with gap + shift down
            points = [
                (arrow_x, arrow_y - arrow_height),  # Top point (toward die, small y)
                (arrow_x - arrow_width // 2, arrow_y),  # Bottom left (wide base below)
                (arrow_x + arrow_width // 2, arrow_y)   # Bottom right
            ]
            pygame.draw.polygon(game.screen, arrow_color, points)
    elif game.tutorial_step == 3:  # Step 4: Arrow to "M" button, pointing up from underneath
        m_button_x = game.width - constants.MULTIPLIERS_BUTTON_SIZE + 13.5  # Shifted right by 13.5
        m_button_y = game.height - constants.MULTIPLIERS_BUTTON_SIZE - 95  # Shifted up by 95 (lower y = higher on screen)
        points = [
            (m_button_x, m_button_y + constants.MULTIPLIERS_BUTTON_SIZE),  # Top point (toward "M" bottom)
            (m_button_x - arrow_width // 2, m_button_y + constants.MULTIPLIERS_BUTTON_SIZE + arrow_height),  # Bottom left (wide base below)
            (m_button_x + arrow_width // 2, m_button_y + constants.MULTIPLIERS_BUTTON_SIZE + arrow_height)   # Bottom right
        ]
        pygame.draw.polygon(game.screen, arrow_color, points)
    # (Keep any other ifs for later steps)

    # Skip button (top left)
    skip_rect = pygame.Rect(20, 20, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, skip_rect, "Skip Tutorial", is_hover=skip_rect.collidepoint(mouse_pos), is_red=True)  # Red for skip/cancel

    # Left/Right arrows (green buttons from init_screen snippet, side-placed at bottom)
    left_rect = None
    right_rect = None
    arrow_size = 50
    arrow_offset = 10  # Adjusted to fit on screen
    y = game.height - arrow_size - 20  # Bottom position with padding
    box_size = 100  # Approximate from init (adjust if needed)
    visible_count = 4  # From init image
    spacing = 20  # Approximate
    start_x = (game.width - visible_count * (box_size + spacing) + spacing) // 2  # Center the 'row' even if no pouches
    if game.tutorial_step > 0:  # Show left on step 1+
        left_rect = pygame.Rect(start_x - arrow_size - arrow_offset, y, arrow_size, arrow_size)
        draw_custom_button(game, left_rect, "<", is_hover=left_rect.collidepoint(mouse_pos))

    right_rect = pygame.Rect(start_x + visible_count * (box_size + spacing) - spacing + arrow_offset, y, arrow_size, arrow_size)
    draw_custom_button(game, right_rect, ">", is_hover=right_rect.collidepoint(mouse_pos))
    if game.tutorial_step == 5:  # On last step, add "Finish" text under right arrow
        finish_text = game.small_font.render("Finish", True, (constants.THEME['text']))
        text_x = right_rect.x + (arrow_size - finish_text.get_width()) // 2
        text_y = right_rect.y + arrow_size  # Under arrow with small gap
        game.screen.blit(finish_text, (text_x, text_y))

    return left_rect, right_rect, skip_rect

def draw_dice(game):
    """Draws the current rolls on the screen."""
    hand_rects = []
    total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
    start_x = (game.width - total_dice_width) // 2
    current_time = time.time()  # For animation
    for i, (die, value) in enumerate(game.rolls):
        x = start_x + i * (constants.DIE_SIZE + 20)
        y = game.height - constants.DIE_SIZE - 100
        size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[i] else constants.DIE_SIZE
        offset = (constants.DIE_SIZE - size) / 2 if game.held[i] else 0
        color = die['color']
        if color == 'Rainbow':
            color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
            color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
        else:
            color_rgb = constants.COLORS[color]
        # Draw die background with rounded corners
        rect = pygame.Rect(x + offset, y + offset, size, size)

        # Mini-function for dots
        def _draw_dots(inner_rect, dot_value):
            for pos in data.DOT_POSITIONS.get(dot_value, []):
                dot_x = inner_rect.x + pos[0] * inner_rect.width
                dot_y = inner_rect.y + pos[1] * inner_rect.height
                pygame.draw.circle(game.screen, (0, 0, 0), (dot_x, dot_y), constants.DOT_RADIUS)
        inner_content = lambda r: [
            _draw_dots(r, value),
            draw_enhancement_visuals(game, r, die)
        ]
        draw_rounded_element(game.screen, rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=constants.DIE_BORDER_RADIUS, inner_content=inner_content)

        # Fate's Favor / Roll Flow: pick-a-die mode (not hold/discard — those use the betting spots)
        if game.selecting_fates_die or getattr(game, 'selecting_advantage_die', False):
            pygame.draw.rect(game.screen, (0, 255, 0), rect, 2)

        # Fusion: gold ring on fused-color dice during an intensified blind
        boon = getattr(game, 'd20_boon', None)
        if boon and boon.active and boon.fused_color and die.get('color') == boon.fused_color:
            pygame.draw.rect(game.screen, constants.COLORS.get(boon.fused_color, (255, 215, 0)), rect.inflate(6, 6), 2, border_radius=constants.DIE_BORDER_RADIUS + 2)

        

        # Draw advantage duplicate if in rolling phase (Roll Flow / Amulet)
        if not game.is_discard_phase and game.has_advantage and game.advantage_value is not None:
            adv_index = getattr(game, 'd20_advantage_index', -1)
            if adv_index < 0:
                adv_index = 2
            x = start_x + adv_index * (constants.DIE_SIZE + 20)
            adv_y = (game.height - constants.DIE_SIZE - 100) - constants.DIE_SIZE - 10
            adv_size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held_advantage else constants.DIE_SIZE
            adv_offset = (constants.DIE_SIZE - adv_size) / 2 if game.held_advantage else 0
            adv_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
            game.advantage_die_rect = adv_rect
            
            # Draw duplicate (same color as the chosen die, but advantage_value)
            die = game.rolls[adv_index][0]
            color = die['color']
            if color == 'Rainbow':
                color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
                color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
            else:
                color_rgb = constants.COLORS[color]
            adv_inner_content = lambda r: [
                _draw_dots(r, game.advantage_value),
                draw_enhancement_visuals(game, r, die)
            ]
            draw_rounded_element(game.screen, adv_rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=constants.DIE_BORDER_RADIUS, inner_content=adv_inner_content)
            
            # Highlight if held
            if game.held_advantage:
                pygame.draw.rect(game.screen, (0, 255, 0), adv_rect, 2)

            # Refresh the original die rect (if held state changed size)
            if adv_index < len(game.rolls):
                orig_x = start_x + adv_index * (constants.DIE_SIZE + 20)
                orig_y = game.height - constants.DIE_SIZE - 100
                orig_size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[adv_index] else constants.DIE_SIZE
                orig_offset = (constants.DIE_SIZE - orig_size) / 2 if game.held[adv_index] else 0
                game.hand_die_rects[adv_index] = pygame.Rect(orig_x + orig_offset, orig_y + orig_offset, orig_size, orig_size)

    # New for Fate's Favor: Draw duplicate above selected die
    if not game.is_discard_phase and game.fates_advantage_index != -1 and game.fates_advantage_value is not None:
        i = game.fates_advantage_index
        x = start_x + i * (constants.DIE_SIZE + 20)
        adv_y = (game.height - constants.DIE_SIZE - 100) - constants.DIE_SIZE - 10
        adv_size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held_fates_advantage else constants.DIE_SIZE
        adv_offset = (constants.DIE_SIZE - adv_size) / 2 if game.held_fates_advantage else 0
        adv_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
        game.fates_advantage_die_rect = adv_rect  # For clicking
        
        die = game.rolls[i][0]
        color = die['color']
        if color == 'Rainbow':
            color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
            color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
        else:
            color_rgb = constants.COLORS[color]
        adv_inner_content = lambda r: [
            _draw_dots(r, game.fates_advantage_value),
            draw_enhancement_visuals(game, r, die)
        ]
        draw_rounded_element(game.screen, adv_rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=constants.DIE_BORDER_RADIUS, inner_content=adv_inner_content)
        
        if game.held_fates_advantage:
            pygame.draw.rect(game.screen, (0, 255, 0), adv_rect, 2)
        if game.held[i]:
            # Highlight original (existing logic in loop)
            pass

        return hand_rects, game.rolls  # Ensure return is at end

# In screens.py, update draw_bag_visual to use inner_content with lambda for enhancements (no need for draw_dots_or_icon if small dies have no pips; add if needed)
def draw_bag_visual(game, origin=None):
    """Draws a brown bag with rounded corners and black border, with dice inside."""
    bag_rect, _tray, cells = bag_cells(game, origin=origin)
    game.bag_die_rects = [rect for _die, rect in cells]
    game.bag_visual_dice = [die for die, _rect in cells]
    bag_x, bag_y, bag_width, bag_height = bag_rect.x, bag_rect.y, bag_rect.width, bag_rect.height
    bag_color = game.get_bag_color()
    triangle_points = [
        (bag_x + bag_width // 2, bag_y + 10),
        (bag_x + bag_width // 2 - 15, bag_y - 10),
        (bag_x + bag_width // 2 + 15, bag_y - 10)
    ]
    pygame.draw.polygon(game.screen, bag_color, triangle_points)
    pygame.draw.polygon(game.screen, (0, 0, 0), triangle_points, 2)
    draw_rounded_element(game.screen, bag_rect, bag_color, border_color=(0, 0, 0), border_width=2, radius=constants.BAG_BORDER_RADIUS, inner_content=None)
    for die, rect in cells:
        color = die['color']
        if color == 'Rainbow':
            color_index = int(time.time() / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
            color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
        else:
            color_rgb = constants.COLORS[color]
        inner_content = lambda r, d=die: draw_bag_enhancement_visuals(game, r, d)
        draw_rounded_element(game.screen, rect, color_rgb, border_color=(0, 0, 0), border_width=1, radius=constants.SMALL_DIE_BORDER_RADIUS, inner_content=inner_content)
    return bag_rect


def draw_shop_bag_popup(game, mouse_pos):
    """Centered overlay of the player's bag, opened from the shop BAG button."""
    bag = getattr(game, 'bag', []) or []
    probe, _, _ = bag_cells(game, origin=(0, 0))
    pad_x, pad_top, pad_bot = 16, 40, 16
    panel_w = probe.width + pad_x * 2
    panel_h = probe.height + pad_top + pad_bot
    panel_x = max(12, (game.width - panel_w) // 2)
    panel_y = max(80, (game.height - panel_h) // 2)
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    try:
        shade = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 130))
        game.screen.blit(shade, (0, 0))
    except Exception:
        pass
    pygame.draw.rect(game.screen, (50, 35, 20), panel, border_radius=12)
    pygame.draw.rect(game.screen, (0, 0, 0), panel, 2, border_radius=12)
    title = game.small_font.render(f"Dice Bag  ({len(bag)})", True, constants.THEME['text'])
    game.screen.blit(title, (panel.x + pad_x, panel.y + 8))
    hint = game.tiny_font.render("click BAG to close", True, (180, 180, 160))
    game.screen.blit(hint, (panel.right - hint.get_width() - pad_x, panel.y + 12))
    origin = (panel.x + pad_x, panel.y + pad_top)
    draw_bag_visual(game, origin=origin)
    # Hover a die → color / enhancements
    if mouse_pos:
        for j, rect in enumerate(getattr(game, 'bag_die_rects', []) or []):
            if rect.collidepoint(mouse_pos):
                die = bag_die_at(game, j)
                if not die:
                    continue
                lines = [f"{die.get('color', '?')} die"]
                for enh in die.get('enhancements') or []:
                    lines.append(f"{enh}: {ENH_DESC.get(enh, 'enhancement')}")
                bonus = die.get('score_bonus', 0)
                if bonus:
                    lines.append(f"+{bonus} score bonus")
                draw_tooltip(game, rect.x, rect.y + rect.height + 6, "\n".join(lines))
                break
    return panel

# In screens.py, add this function to handle enhancements visuals for hand dice (full animations)
# Call it inside draw_rounded_element's inner_content lambda, after drawing base dots/icon: draw_enhancement_visuals(game, r, die)
# You'll need to import time and random at top if not already: import time, import random

def draw_enhancement_visuals(game, die_rect, die):
    enhs = die.get('enhancements', [])
    if not enhs:
        return
    icon_size = 15
    start_x = die_rect.x + 5
    start_y = die_rect.y + die_rect.height - icon_size - 5  # Bottom row
    for idx, enh in enumerate(enhs):
        # Skip color-specific and Wild—no indicators needed; they render as normal dice
        if enh in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']:
            continue  # No visual, just apply color change
        x = start_x + idx * (icon_size + 5)
        color = (255, 255, 255)  # White default
        if enh == 'Lucky':
            color = (255, 215, 0)  # Gold
            pygame.draw.polygon(game.screen, color, [(x+7, start_y), (x, start_y+icon_size//2), (x+icon_size, start_y+icon_size//2)])  # Triangle star
        elif enh == 'Mult':
            text = game.tiny_font.render("x", True, (0, 255, 0))  # Green x
            game.screen.blit(text, (x, start_y))
        elif enh == 'Bonus':
            pygame.draw.circle(game.screen, (0, 255, 0), (x+7, start_y+7), 5)  # Green dot
        elif enh == 'Steel':
            pygame.draw.rect(game.screen, (169, 169, 169), pygame.Rect(x, start_y, icon_size, icon_size), 2)  # Gray border
        elif enh == 'Fragile':
            pygame.draw.line(game.screen, (255, 0, 0), (x, start_y), (x+icon_size, start_y+icon_size), 2)  # Red crack
        elif enh == 'Fate':
            text = game.tiny_font.render("E", True, (255, 0, 255))  # Magenta E for edition
            game.screen.blit(text, (x, start_y))
        elif enh == 'Strength':
            pygame.draw.polygon(game.screen, (0, 0, 255), [(x+7, start_y), (x, start_y+icon_size), (x+icon_size, start_y+icon_size)])  # Blue arrow
        elif enh == 'Sacrifice':
            pygame.draw.circle(game.screen, (255, 0, 0), (x+7, start_y+7), 7, 2)  # Red circle (destroyed)
        elif enh == 'Transmute':
            text = game.tiny_font.render("T", True, (128, 0, 128))  # Purple T
            game.screen.blit(text, (x, start_y))
        elif enh in ['Gold', 'Silver']:
            color = constants.COLORS[enh]
            pygame.draw.rect(game.screen, color, pygame.Rect(x, start_y, icon_size, icon_size))
        elif enh == 'Stone':
            pygame.draw.rect(game.screen, (128, 128, 128), pygame.Rect(x, start_y, icon_size, icon_size))  # Gray block
        # Add more if new enh (e.g., 'Judgement' no visual needed)

    # Color swaps (Red/Blue/etc.): Already handled by base die color, no extra visual needed
    # Non-die effects (Wealth, Balance, Judgement, Sacrifice, Transmute): Handled in apply, no ongoing visual

# For bag: Simpler static version (call in draw_bag_visual after each small die draw)
def draw_bag_enhancement_visuals(game, die_rect, die):
    enhs = die.get('enhancements', [])
    if not enhs:
        return
    icon_size = 15
    start_x = die_rect.x + 5
    start_y = die_rect.y + die_rect.height - icon_size - 5  # Bottom row
    for idx, enh in enumerate(enhs):
        # Skip color-specific and Wild—no indicators needed; they render as normal dice
        if enh in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']:
            continue  # No visual, just apply color change
        x = start_x + idx * (icon_size + 5)
        color = (255, 255, 255)  # White default
        if enh == 'Lucky':
            color = (255, 215, 0)  # Gold
            pygame.draw.polygon(game.screen, color, [(x+7, start_y), (x, start_y+icon_size//2), (x+icon_size, start_y+icon_size//2)])  # Triangle star
        elif enh == 'Mult':
            text = game.tiny_font.render("x", True, (0, 255, 0))  # Green x
            game.screen.blit(text, (x, start_y))
        elif enh == 'Bonus':
            pygame.draw.circle(game.screen, (0, 255, 0), (x+7, start_y+7), 5)  # Green dot
        elif enh == 'Steel':
            pygame.draw.rect(game.screen, (169, 169, 169), pygame.Rect(x, start_y, icon_size, icon_size), 2)  # Gray border
        elif enh == 'Fragile':
            pygame.draw.line(game.screen, (255, 0, 0), (x, start_y), (x+icon_size, start_y+icon_size), 2)  # Red crack
        elif enh == 'Fate':
            text = game.tiny_font.render("E", True, (255, 0, 255))  # Magenta E for edition
            game.screen.blit(text, (x, start_y))
        elif enh == 'Strength':
            pygame.draw.polygon(game.screen, (0, 0, 255), [(x+7, start_y), (x, start_y+icon_size), (x+icon_size, start_y+icon_size)])  # Blue arrow
        elif enh == 'Sacrifice':
            pygame.draw.circle(game.screen, (255, 0, 0), (x+7, start_y+7), 7, 2)  # Red circle (destroyed)
        elif enh == 'Transmute':
            text = game.tiny_font.render("T", True, (128, 0, 128))  # Purple T
            game.screen.blit(text, (x, start_y))
        elif enh in ['Gold', 'Silver']:
            color = constants.COLORS[enh]
            pygame.draw.rect(game.screen, color, pygame.Rect(x, start_y, icon_size, icon_size))
        elif enh == 'Stone':
            pygame.draw.rect(game.screen, (128, 128, 128), pygame.Rect(x, start_y, icon_size, icon_size))  # Gray block
        # Add more if new enh (e.g., 'Judgement' no visual needed)

def draw_ui_panel(game):
    """Hands / discards / rolls as rail plaques; coins as a chip stack."""
    panel_x = 50
    panel_y = game.height - constants.BUTTON_HEIGHT - 20 - constants.UI_PANEL_HEIGHT - 10
    gold = TABLE_GOLD
    text = constants.THEME['text']
    rolls = game.rerolls_left if getattr(game, 'rerolls_left', 0) >= 0 else '∞'
    rows = [
        ('HANDS', str(getattr(game, 'hands_left', 0))),
        ('DISCARDS', str(getattr(game, 'discards_left', 0))),
        ('ROLLS', str(rolls)),
    ]
    row_h = 28
    plate_w = constants.UI_PANEL_WIDTH
    for i, (label, value) in enumerate(rows):
        r = pygame.Rect(panel_x, panel_y + i * (row_h + 4), plate_w, row_h)
        pygame.draw.rect(game.screen, TABLE_PLAQUE, r, border_radius=6)
        pygame.draw.rect(game.screen, gold, r, 1, border_radius=6)
        lab = game.tiny_font.render(label, True, gold)
        val = game.tiny_font.render(value, True, text)
        game.screen.blit(lab, (r.x + 8, r.centery - lab.get_height() // 2))
        game.screen.blit(val, (r.right - val.get_width() - 8, r.centery - val.get_height() // 2))
    chip_y = panel_y + 3 * (row_h + 4) + 6
    chip_x = panel_x + 10
    for i, color in enumerate(((180, 40, 40), (40, 70, 170), (212, 176, 72))):
        pygame.draw.ellipse(game.screen, color, pygame.Rect(chip_x, chip_y - i * 4, 22, 10))
        pygame.draw.ellipse(game.screen, (20, 20, 20), pygame.Rect(chip_x, chip_y - i * 4, 22, 10), 1)
    coin_surf = game.tiny_font.render(_format_coins(getattr(game, 'coins', 0)), True, gold)
    game.screen.blit(coin_surf, (chip_x + 28, chip_y - 8))

def draw_custom_button(game, rect, text, is_hover=False, fill_color=None, is_red=False):
    """Draws a custom button with optional fill color and red variant."""
    # Use provided color or theme default
    button_color = fill_color if fill_color is not None else constants.THEME['button_bg']
    if is_red:
        button_color = (200, 0, 0)  # Red for danger (e.g., Quit)
    if is_hover:
        button_color = constants.THEME.get('button_hover', button_color)  # Fallback if no hover in THEME
    
    # Draw rounded rect for button
    pygame.draw.rect(game.screen, button_color, rect, border_radius=10)  # Rounded corners
    pygame.draw.rect(game.screen, constants.THEME['border'], rect, 2, border_radius=10)  # Border (assume 'border' in THEME; adjust if needed)
    
    # Text
    text_surf = game.small_font.render(text, True, constants.THEME['text'])
    text_x = rect.x + (rect.width - text_surf.get_width()) // 2
    text_y = rect.y + (rect.height - text_surf.get_height()) // 2
    game.screen.blit(text_surf, (text_x, text_y))

def draw_text(game, start_y=120, limit_y=None):
    """Hand type, modifiers, score as one downward column. Returns Y after the last line."""
    y = start_y
    step = game.small_font.get_height() + 2
    if limit_y is None:
        limit_y = game.height - constants.DIE_SIZE - 130
    for line in getattr(game, 'current_hand_lines', []) or []:
        if y + step > limit_y:
            break
        surf = game.small_font.render(line, True, THEME['text'])
        game.screen.blit(surf, (50, y))
        y += step
    for line in getattr(game, 'current_modifier_lines', []) or []:
        if y + step > limit_y:
            break
        if " (disabled)" in line:
            base_line = line.replace(" (disabled)", "")
            base_render = game.small_font.render(base_line, True, THEME['text'])
            disabled_render = game.small_font.render(" (disabled)", True, (255, 0, 0))
            game.screen.blit(base_render, (50, y))
            game.screen.blit(disabled_render, (50 + base_render.get_width(), y))
        else:
            game.screen.blit(game.small_font.render(line, True, THEME['text']), (50, y))
        y += step
    if y + step <= limit_y:
        score_text = game.small_font.render(
            f"Score: {game.round_score}/{int(game.get_blind_target())}", True, THEME['text'])
        game.screen.blit(score_text, (50, y))
        y += step
    return y

def draw_d20_hud(game, start_y=210, limit_y=None):
    """Live D20 banner under the score. Flows from start_y instead of a fixed 210."""
    boon = getattr(game, 'd20_boon', None)
    if not boon:
        return start_y
    lines = boon.hud_lines() if hasattr(boon, 'hud_lines') else []
    if not lines:
        return start_y
    font = getattr(game, 'tiny_font', game.small_font)
    y = start_y
    if limit_y is None:
        limit_y = game.height - constants.DIE_SIZE - 110
    for line in lines[:4]:
        if y + 18 > limit_y:
            break
        surf = font.render(line[:70], True, constants.THEME.get('highlight', (255, 215, 0)))
        game.screen.blit(surf, (50, y))
        y += 18
    return y

def draw_charm_die(game, rect, charm, index=None):
    """Draws a charm as a die with icon inside. Grays out if disabled using built-in Pygame transform."""

    # Determine if disabled (boss eclipse/glitch, or Mortgage spent this shop)
    is_disabled = charm_is_visually_disabled(game, charm, index)
    
    # Draw die background (white face with border) - gray the background too if disabled for better effect
    bg_color = (128, 128, 128) if is_disabled else constants.DIE_BACKGROUND_COLOR

    # Get charm-specific bg if defined, else fallback to DIE_BACKGROUND_COLOR
    charm_bg = constants.CHARM_BG_COLORS.get(charm['name'], constants.DIE_BACKGROUND_COLOR)

    # Gray if disabled
    bg_color = (128, 128, 128) if is_disabled else charm_bg
    
    # Inner icon rect (padded and scaled)
    def _draw_inner_charm(inner_rect):
        # NEW: Guard for missing 'type' (e.g., partial runes like Grimoire)
        if 'type' not in charm:
            # Simple placeholder: Draw the first letter of the name centered
            if 'name' in charm:
                abbr = charm['name'][0].upper()
            else:
                abbr = '?'  # Fallback if no name
            text_surf = game.tiny_font.render(abbr, True, constants.THEME['text'])
            text_rect = text_surf.get_rect(center=inner_rect.center)
            game.screen.blit(text_surf, text_rect)
            return  # Skip all type-specific drawing to avoid KeyError
        inner_size = int(constants.CHARM_SIZE * constants.INNER_ICON_SCALE)  # e.g., 80 for 100 size
        inner_sub_rect = inner_rect.inflate(-constants.INNER_ICON_PADDING * 2, -constants.INNER_ICON_PADDING * 2)  # Changed name
        inner_sub_rect.size = (inner_size, inner_size)  # Changed name
        inner_sub_rect.center = inner_rect.center  # Changed to use inner_rect for centering (outer)
        
        # Load icon from cache
        path = game.charm_icon_paths.get(charm['name'])
        if path and path in game.charm_icon_cache:
            icon_surf = game.charm_icon_cache[path].copy()  # Always copy to avoid modifying cache

            # Apply grayscale if disabled
            if is_disabled:
                icon_surf = pygame.transform.grayscale(icon_surf)  # Built-in grayscale (returns new surface)
            
            # Blit icon
            game.screen.blit(icon_surf, inner_sub_rect.topleft)
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
                text = game.tiny_font.render('+10', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name in ['Red Greed Charm', 'Blue Lust Charm', 'Green Wrath Charm', 'Purple Glutton Charm', 'Yellow Jolly Charm']:
                # Get color from name (e.g., 'Red' from 'Red Greed Charm')
                color_name = name.split()[0]  # First word is color
                color = constants.COLORS.get(color_name, (200, 200, 200))  # Fallback gray if mismatch
                
                # Draw inner colored die face (square, rounded, colored bg, black border) on fallback_surf - full size
                inner_die_size = inner_size  # Full size for colored die
                inner_die_x = 0
                inner_die_y = 0
                inner_die_rect = pygame.Rect(inner_die_x, inner_die_y, inner_die_size, inner_die_size)
                pygame.draw.rect(fallback_surf, color, inner_die_rect, border_radius=constants.CHARM_DIE_BORDER_RADIUS // 2)  # Colored background
                pygame.draw.rect(fallback_surf, (0, 0, 0), inner_die_rect, 2, border_radius=constants.CHARM_DIE_BORDER_RADIUS // 2)  # Black border

                # Draw 5 black dots (from DOT_POSITIONS[5])
                dot_positions = data.DOT_POSITIONS[5]  # [(0.25,0.25), (0.25,0.75), (0.5,0.5), (0.75,0.25), (0.75,0.75)]
                dot_radius = constants.DOT_RADIUS // 2  # Smaller for charm scale (5 instead of 10)
                for pos in dot_positions:
                    dot_x = inner_die_x + int(pos[0] * inner_die_size)
                    dot_y = inner_die_y + int(pos[1] * inner_die_size)
                    pygame.draw.circle(fallback_surf, (0, 0, 0), (dot_x, dot_y), dot_radius)  # Black dots
            elif name == 'Zany Charm':
                text = game.tiny_font.render('3OK', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Mad Charm':
                text = game.tiny_font.render('2P', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Crazy Charm':
                # Scale line length
                line_length = int(15 * constants.INNER_ICON_SCALE * 2)  # Original 30, scaled
                pygame.draw.line(fallback_surf, (0, 0, 0), (center_x - line_length // 2, center_y), (center_x + line_length // 2, center_y), 3)
            elif name == 'Droll Charm':
                scaled_radius = int(inner_size // 4)
                pygame.draw.circle(fallback_surf, (0, 0, 0), (center_x, center_y), scaled_radius, 2)
            elif name == 'Sly Charm':
                text = game.tiny_font.render('P+50', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Wily Charm':
                text = game.tiny_font.render('3OK+100', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Clever Charm':
                text = game.tiny_font.render('2P+80', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Devious Charm':
                text = game.tiny_font.render('Str+100', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Half Charm':
                text = game.tiny_font.render('≤3', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Stencil Charm':
                text = game.tiny_font.render('[]x', True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            elif name == 'Four Fingers Charm':
                # Scale hand drawing (reduce sizes by scale factor)
                scale_factor = constants.INNER_ICON_SCALE
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
                box_size = int(15 * constants.INNER_ICON_SCALE * 2)  # Original 30
                pygame.draw.rect(fallback_surf, (0, 0, 0), (center_x - box_size // 2, center_y - box_size // 2, box_size, box_size), 2)
                pygame.draw.line(fallback_surf, (0, 0, 0), (center_x - box_size // 2, center_y - box_size // 2), (center_x - box_size // 2, center_y + box_size // 2), 2)
                pygame.draw.line(fallback_surf, (0, 0, 0), (center_x + box_size // 2, center_y - box_size // 2), (center_x + box_size // 2, center_y + box_size // 2), 2)
            elif charm['type'] == 'sacrifice_mult':
                game.draw_dagger_icon(rect)  # Assuming this draws on the full rect; scale if needed
            # Add any other fallback drawings for charms not in the icon paths (scale similarly if complex)
            elif charm['type'] == 'rune':
                # Draw a rune symbol, e.g., a simple glyph or magic swirl
                # Example: Draw a circle with lines (customize based on your rune effects)
                pygame.draw.circle(game.screen, (200, 200, 255), inner_rect.center, 10)  # Magic glow
                # Or render a rune icon if you have assets
                # For now, fallback to the abbr drawing above if needed
            else:
                # Fallback for unmapped charms: text with name to debug
                text = game.tiny_font.render(charm['name'][:10], True, (0, 0, 0))
                fallback_surf.blit(text, (center_x - text.get_width() // 2, center_y - text.get_height() // 2))
            
            # Apply grayscale if disabled (on the fallback_surf)
            if is_disabled:
                fallback_surf = pygame.transform.grayscale(fallback_surf)  # Grayscale the drawings
            
            # Blit the fallback_surf onto the screen at inner_rect
            game.screen.blit(fallback_surf, inner_sub_rect.topleft)  # Changed name

    draw_rounded_element(game.screen, rect, bg_color, border_color=constants.DIE_BORDER_COLOR, border_width=constants.DIE_BORDER_WIDTH, radius=constants.CHARM_DIE_BORDER_RADIUS, inner_content=_draw_inner_charm)  # <--- Replaced call
    if is_disabled:
        try:
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            overlay.fill((20, 20, 20, 120))
            game.screen.blit(overlay, rect.topleft)
        except Exception:
            pass
        if charm and charm.get('type') == 'sell_double_lock':
            font = getattr(game, 'tiny_font', None) or getattr(game, 'small_font', None)
            if font:
                label = font.render("LOCKED", True, (230, 230, 230))
                game.screen.blit(label, (rect.centerx - label.get_width() // 2,
                                         rect.bottom - label.get_height() - 3))

def draw_tooltip(game, x, y, text):
    lines = wrap_text(game.small_font, text, constants.TOOLTIP_MAX_WIDTH)
    if not lines:
        return
    line_height = game.small_font.get_height()
    width = max(game.small_font.size(line)[0] for line in lines) + constants.TOOLTIP_PADDING * 2
    height = len(lines) * line_height + constants.TOOLTIP_PADDING * 2
    if x + width > game.width:
        x = max(0, game.width - width)
    if x < 0:
        x = 0
    if y + height > game.height:
        y = max(0, y - height - 8)
    if y < 0:
        y = 0
    tooltip_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(game.screen, (100, 100, 100), tooltip_rect)
    pygame.draw.rect(game.screen, constants.THEME.get('tooltip_border', (200, 200, 200)), tooltip_rect, 1)
    for i, line in enumerate(lines):
        desc_surface = game.small_font.render(line, True, constants.THEME['text'])
        game.screen.blit(desc_surface, (x + constants.TOOLTIP_PADDING, y + constants.TOOLTIP_PADDING + i * line_height))

def draw_pause_menu(game):
    """Draws the pause popup with options: Main Menu, Quit, Return."""
    # Dim background
    overlay = pygame.Surface((game.width, game.height))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(128)  # Semi-transparent black
    game.screen.blit(overlay, (0, 0))
    

    # Centered popup rect (reuse POPUP sizes)
    popup_x = (game.width - constants.POPUP_WIDTH) // 2
    popup_h = 400
    popup_y = (game.height - popup_h) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, constants.POPUP_WIDTH, popup_h)
    pygame.draw.rect(game.screen, constants.THEME['background'], popup_rect, border_radius=20)  # Green bg, rounded
    pygame.draw.rect(game.screen, (0, 0, 0), popup_rect, 2, border_radius=20)  # Border

    # Title
    title_text = game.font.render("Paused", True, (constants.THEME['text']))
    game.screen.blit(title_text, (popup_x + (constants.POPUP_WIDTH - title_text.get_width()) // 2, popup_y + 20))

    # Draw buttons using rects
    button_rects = game.get_pause_button_rects()  # Assuming this is still in ChromaRoll.py – fine as game.get_...
    for rect, opt in button_rects:
        pygame.draw.rect(game.screen, (100, 100, 100), rect)
        text = game.font.render(opt, True, (constants.THEME['text']))
        game.screen.blit(text, (rect.x + (constants.BUTTON_WIDTH - text.get_width()) // 2, rect.y + 10))

    # Mute button (position INSIDE the popup, e.g., bottom-right corner of popup)
    game.mute_button_rect = pygame.Rect(popup_x + constants.POPUP_WIDTH - 60, popup_y + popup_h - 60, 40, 40)  # Adjusted: Inside popup with padding
    icon = game.speaker_on_icon if not game.mute else game.speaker_off_icon  # Toggles based on state
    if icon:
        game.screen.blit(icon, game.mute_button_rect.topleft)
    else:
        # Text fallback (single button that changes label)
        pygame.draw.rect(game.screen, constants.THEME['button_bg'], game.mute_button_rect)
        label = "Mute" if not game.mute else "Unmute"  # Toggles text
        text = game.tiny_font.render(label, True, constants.THEME['text'])
        game.screen.blit(text, (game.mute_button_rect.centerx - text.get_width() // 2, game.mute_button_rect.centery - text.get_height() // 2))

    # Optional: Hover effect (subtle glow)
    if game.mute_button_rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(game.screen, constants.THEME['button_hover'], game.mute_button_rect, border_radius=5, width=2)  # Border glow

    # Return the rects for handle_event
    return button_rects, game.mute_button_rect

def draw_popup(game):
    """Beaten-blind payout plaque. Same Continue click box, casino styling."""
    raw_lines = [ln for ln in (game.popup_message or "").split('\n')]
    gold = TABLE_GOLD
    text_col = constants.THEME['text']
    # Dim the table behind the plaque
    try:
        shade = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        game.screen.blit(shade, (0, 0))
    except Exception:
        pass

    title = "BLIND BEATEN"
    score_line = ""
    rows = []
    for raw in raw_lines:
        s = (raw or "").strip()
        if not s:
            continue
        if "Beaten" in s and "Score:" in s:
            title = s.split("Score:")[0].replace("!", "").strip().upper()
            score_line = s.split("Score:", 1)[1].strip()
            continue
        row = _payout_row(s)
        if row:
            rows.append(row)

    font = game.small_font
    tiny = game.tiny_font
    line_h = 22
    btn_space = 70
    header_h = 78
    content_h = header_h + max(1, len(rows)) * line_h + btn_space
    dynamic_height = min(game.height - 40, max(240, content_h))
    popup_rect = pygame.Rect(
        game.width // 2 - WIN_POPUP_WIDTH // 2,
        max(20, (game.height - dynamic_height) // 2),
        WIN_POPUP_WIDTH, dynamic_height)
    draw_rounded_element(game.screen, popup_rect, TABLE_PLAQUE, border_color=gold, border_width=3, radius=14)
    inner = popup_rect.inflate(-10, -10)
    pygame.draw.rect(game.screen, gold, inner, 1, border_radius=10)

    cx = popup_rect.centerx
    y = popup_rect.y + 14
    t = game.font.render(title, True, gold)
    game.screen.blit(t, (cx - t.get_width() // 2, y))
    y += t.get_height() + 4
    if score_line:
        sc = font.render(score_line, True, text_col)
        game.screen.blit(sc, (cx - sc.get_width() // 2, y))
        y += sc.get_height() + 10

    max_text_y = popup_rect.bottom - btn_space
    label_x = popup_rect.x + 36
    value_x = popup_rect.right - 36
    for label, value in rows:
        if y + line_h > max_text_y:
            break
        if label.lower().startswith("coins gained"):
            lab = font.render(label, True, gold)
            val = font.render(value, True, gold)
        else:
            lab = tiny.render(label, True, (200, 200, 180)) if label else None
            val = tiny.render(value, True, text_col)
        if lab:
            game.screen.blit(lab, (label_x, y))
        if val:
            game.screen.blit(val, (value_x - val.get_width(), y))
        y += line_h

    button_y = popup_rect.y + dynamic_height - 62
    continue_rect = pygame.Rect(
        popup_rect.x + (WIN_POPUP_WIDTH - constants.BUTTON_WIDTH) // 2,
        button_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, continue_rect, "Continue",
                       is_hover=continue_rect.collidepoint(pygame.mouse.get_pos()),
                       fill_color=constants.THEME.get('yes_button', (0, 150, 0)))
    return continue_rect

def draw_instruction_popup(game, message):
        if message is None:
            return None  # Skip drawing if no message
        """Draws a simple instruction popup with Cancel button."""
        popup_width = 300  # Smaller for instructions
        popup_height = 150
        popup_rect = pygame.Rect(game.width // 2 - popup_width // 2, game.height // 2 - popup_height // 2, popup_width, popup_height)
        pygame.draw.rect(game.screen, (100, 100, 100), popup_rect)
        pygame.draw.rect(game.screen, (255, 255, 255), popup_rect, 3)  # White border

        # Render message (wrap if long)
        lines = wrap_text(game.tiny_font, message, popup_width - 40)  # Use utils.wrap_text
        for i, line in enumerate(lines):
            text = game.tiny_font.render(line, True, (constants.THEME['text']))
            game.screen.blit(text, (popup_rect.x + 20, popup_rect.y + 20 + i * 25))

        # Cancel button
        cancel_rect = pygame.Rect(popup_rect.x + (popup_width - constants.BUTTON_WIDTH) // 2, popup_rect.y + popup_height - 60, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        pygame.draw.rect(game.screen, (100, 100, 100), cancel_rect)
        cancel_text = game.tiny_font.render("Cancel", True, (constants.THEME['text']))
        game.screen.blit(cancel_text, (cancel_rect.x + (constants.BUTTON_WIDTH - cancel_text.get_width()) // 2, cancel_rect.y + 10))

        return cancel_rect

def draw_buttons(game):
    """Draws the action buttons; in debug, add Score button; add Discard in discard phase."""
    reroll_rect = None
    discard_rect = None
    start_roll_rect = None
    score_rect = None
    end_turn_rect = None
    bottom_y = game.height - constants.BUTTON_HEIGHT - 20
    left_button_x = 50
    right_button_x = game.width - constants.BUTTON_WIDTH - 50
    center_left_x = game.width // 2 - constants.BUTTON_WIDTH - 20
    center_right_x = game.width // 2 + 20
    mouse_pos = pygame.mouse.get_pos()  # For hover

    if game.is_discard_phase:
        discard_rect = pygame.Rect(left_button_x, bottom_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        draw_custom_button(game, discard_rect, "Discard", is_hover=discard_rect.collidepoint(mouse_pos), is_red=True)

        start_roll_rect = pygame.Rect(right_button_x, bottom_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        draw_custom_button(game, start_roll_rect, "Start Roll", is_hover=start_roll_rect.collidepoint(mouse_pos))

    else:
        reroll_rect = pygame.Rect(center_left_x, bottom_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        button_text = "Reroll" if (game.rerolls_left > 0 or constants.DEBUG) else "Draw and Score"
        draw_custom_button(game, reroll_rect, button_text, is_hover=reroll_rect.collidepoint(mouse_pos))

        end_turn_rect = pygame.Rect(center_right_x, bottom_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        draw_custom_button(game, end_turn_rect, "End Turn", is_hover=end_turn_rect.collidepoint(mouse_pos))

    return reroll_rect, discard_rect, start_roll_rect, score_rect, end_turn_rect


def draw_play_debug_bar(game):
    """DEBUG: a small DBG tab. Cheats only draw when game.debug_play_open is set.

    Returns [(rect, action), ...] — action 'toggle' flips the panel.
    """
    from debug_cheats import PLAY_DEBUG_ACTIONS
    rects = []
    font = getattr(game, 'tiny_font', None) or getattr(game, 'small_font', None)
    mouse = pygame.mouse.get_pos()
    bottom_y = game.height - constants.BUTTON_HEIGHT - 20
    tab_w, tab_h = 40, 28
    tab = pygame.Rect(8, bottom_y + (constants.BUTTON_HEIGHT - tab_h) // 2, tab_w, tab_h)
    open_ = bool(getattr(game, 'debug_play_open', False))
    tab_bg = (90, 120, 40) if (open_ or tab.collidepoint(mouse)) else (40, 55, 30)
    draw_rounded_element(game.screen, tab, tab_bg, radius=4)
    pygame.draw.rect(game.screen, (180, 200, 80), tab, 1)
    if font:
        surf = font.render("DBG", True, (220, 255, 160))
        game.screen.blit(surf, (tab.centerx - surf.get_width() // 2,
                                tab.centery - surf.get_height() // 2))
    rects.append((tab, 'toggle'))
    if not open_:
        return rects

    bw, bh, gap, pad = 90, 26, 4, 10
    cols = 2
    rows = (len(PLAY_DEBUG_ACTIONS) + cols - 1) // cols
    panel_w = pad * 2 + cols * bw + (cols - 1) * gap
    panel_h = pad * 2 + rows * bh + (rows - 1) * gap
    panel = pygame.Rect(8, tab.y - 8 - panel_h, panel_w, panel_h)
    if panel.y < 8:
        panel.y = 8
    draw_rounded_element(game.screen, panel, (18, 28, 16), radius=8)
    pygame.draw.rect(game.screen, (180, 200, 80), panel, 1)
    for i, (action, label) in enumerate(PLAY_DEBUG_ACTIONS):
        col, row = i % cols, i // cols
        rect = pygame.Rect(panel.x + pad + col * (bw + gap),
                           panel.y + pad + row * (bh + gap), bw, bh)
        hover = rect.collidepoint(mouse)
        bg = (70, 90, 40) if hover else (40, 55, 30)
        draw_rounded_element(game.screen, rect, bg, radius=4)
        pygame.draw.rect(game.screen, (180, 200, 80), rect, 1)
        if font:
            surf = font.render(label, True, (220, 255, 160))
            game.screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                                    rect.centery - surf.get_height() // 2))
        rects.append((rect, action))
    return rects


def draw_pack_icon(game, pack_rect, num_dice, cycle_colors=constants.COLOR_CYCLE):
    """Draws animated dice pack icon."""
    box_size = min(pack_rect.width, pack_rect.height) - 20  # Smaller inner box to center
    box_rect = pygame.Rect(pack_rect.x + (pack_rect.width - box_size) // 2, pack_rect.y + (pack_rect.height - box_size) // 2, box_size, box_size)
    pygame.draw.rect(game.screen, (0, 0, 0), box_rect, 2)

    inner_rect = box_rect.inflate(-10, -10)  # Same padding as prism

    current_time = time.time()
    if num_dice <= 3:  # Horizontal row for small num
        spacing = box_size / (num_dice + 1)  # Even spacing
        for i in range(num_dice):
            color_index = int((current_time + i * 0.2) % len(cycle_colors))
            color = cycle_colors[color_index]
            x = box_rect.x + spacing * (i + 1) - constants.SMALL_ICON_DIE_SIZE // 2
            y = box_rect.y + box_size // 2 - constants.SMALL_ICON_DIE_SIZE // 2  # Center vertically
            die_rect = pygame.Rect(x, y, constants.SMALL_ICON_DIE_SIZE, constants.SMALL_ICON_DIE_SIZE)
            pygame.draw.rect(game.screen, constants.COLORS[color], die_rect)
            pygame.draw.rect(game.screen, (0, 0, 0), die_rect, 1)
            # Single pip
            pygame.draw.circle(game.screen, (0, 0, 0), die_rect.center, 2)
    else:  # Grid for larger num (e.g., 2x2 for 4)
        cols = math.ceil(math.sqrt(num_dice))  # Simple grid
        rows = math.ceil(num_dice / cols)
        cell_size = box_size / max(cols, rows)
        for i in range(num_dice):
            color_index = int((current_time + i * 0.2) % len(cycle_colors))
            color = cycle_colors[color_index]
            col = i % cols
            row = i // cols
            x = box_rect.x + col * cell_size + (cell_size - constants.SMALL_ICON_DIE_SIZE) // 2
            y = box_rect.y + row * cell_size + (cell_size - constants.SMALL_ICON_DIE_SIZE) // 2
            die_rect = pygame.Rect(x, y, constants.SMALL_ICON_DIE_SIZE, constants.SMALL_ICON_DIE_SIZE)
            pygame.draw.rect(game.screen, constants.COLORS[color], die_rect)
            pygame.draw.rect(game.screen, (0, 0, 0), die_rect, 1)
            # Single pip
            pygame.draw.circle(game.screen, (0, 0, 0), die_rect.center, 2)

def draw_prism_pack_icon(game, pack_idx, x, y):
    box_rect = pygame.Rect(x, y, constants.PACK_BOX_SIZE, constants.PACK_BOX_SIZE)
    draw_rounded_element(game.screen, box_rect, (200, 200, 200), border_color=(0, 0, 0), border_width=2, radius=10)

    # Inner icon: Blit image if cached, else fallback
    inner_rect = box_rect.inflate(-10, -10)  # Padded

    if pack_idx in game.pack_icon_cache:
        icon_surf = game.pack_icon_cache[pack_idx]
        icon_rect = icon_surf.get_rect(center=inner_rect.center)
        game.screen.blit(icon_surf, icon_rect)
    else:
        # Fallback: Old 5 pips (or add print("Missing pack icon") for debug)
        dot_radius = inner_rect.width // 10
        positions = data.DOT_POSITIONS[5]
        for pos in positions:
            dot_x = inner_rect.x + int(pos[0] * inner_rect.width)
            dot_y = inner_rect.y + int(pos[1] * inner_rect.height)
            pygame.draw.circle(game.screen, (0, 0, 0), (dot_x, dot_y), dot_radius)

def draw_pack_select_screen(game):
    mouse_pos = pygame.mouse.get_pos()  # Add if not already for hovers

    game.screen.fill(constants.THEME['background'])  # Fill background
    
    # Title or instructions
    title_text = game.font.render("Select a Hand Type to Boost", True, constants.THEME['text'])
    game.screen.blit(title_text, (game.width // 2 - title_text.get_width() // 2, 50))

    # Display hand type choices (from data.HAND_TYPES or game.pack_choices)
    visible_count = len(game.pack_choices)  # Assuming pack_choices is list of hand types
    box_size = 150  # Adjust for fit
    spacing = 20
    start_x = (game.width - (visible_count * box_size + (visible_count - 1) * spacing)) // 2
    y = 150

    choice_rects = []
    for i, hand_type in enumerate(game.pack_choices):
        x = start_x + i * (box_size + spacing)
        rect = pygame.Rect(x, y, box_size, box_size)
        
        # Draw rounded box (themed)
        fill_color = constants.THEME['panel_bg']  # Or custom per hand type
        draw_rounded_element(game.screen, rect, fill_color, border_color=constants.THEME['border'], border_width=2, radius=20)
        
        # Hand type name
        name_text = game.small_font.render(hand_type, True, constants.THEME['text'])
        game.screen.blit(name_text, (x + (box_size - name_text.get_width()) // 2, y + 10))
        
        # Description (stub; adjust based on your code)
        desc = f"Boost {hand_type} by {constants.PACK_BOOST}x"
        desc_lines = wrap_text(game.tiny_font, desc, box_size - 20)
        line_y = y + 40
        for line in desc_lines:
            desc_text = game.tiny_font.render(line, True, constants.THEME['text'])
            game.screen.blit(desc_text, (x + 10, line_y))
            line_y += game.tiny_font.get_height()

        # Tooltip on hover
        tooltip_text = f"{hand_type}: {desc}"  # Or more detailed
        if rect.collidepoint(mouse_pos):
            draw_tooltip(game, rect.x, rect.y + rect.height + 5, tooltip_text)

        choice_rects.append(rect)  # Return rects for click handling (associate with index or hand_type)

    return choice_rects


def draw_achievements_screen(game, tab='quests', scroll_y=0, debug=False):
    """Quests + charm collection. Returns (back_rect, tab_rects, debug_rects, hover_tooltip)."""
    import achievements as ach
    mouse_pos = pygame.mouse.get_pos()
    game.screen.fill(constants.THEME['background'])
    pad = 16
    back_rect = pygame.Rect(pad, pad, 120, 40)
    draw_custom_button(game, back_rect, "Back", is_hover=back_rect.collidepoint(mouse_pos))

    title = game.font.render("Achievements", True, constants.THEME['text'])
    game.screen.blit(title, (game.width // 2 - title.get_width() // 2, 14))

    progress = getattr(game, 'progress', None) or ach.default_progress()
    n_ach = len(progress.get('unlocked_achievements') or [])
    n_locked = len(ach.locked_charm_names())
    n_charms = n_locked + (len(data.CHARMS_POOL) - n_locked)
    owned = len(progress.get('unlocked_charms') or [])
    # starter charms count as owned for the collection number
    starter = len(data.CHARMS_POOL) - n_locked
    shown_charms = starter + owned
    if progress.get('unlock_all'):
        shown_charms = len(data.CHARMS_POOL)
        n_ach = len(ach.ACHIEVEMENTS)
    sub = game.small_font.render(
        f"{n_ach}/{len(ach.ACHIEVEMENTS)} quests    {shown_charms}/{len(data.CHARMS_POOL)} charms",
        True, constants.THEME['text'])
    game.screen.blit(sub, (game.width // 2 - sub.get_width() // 2, 50))

    tab_y = 82
    quests_tab = pygame.Rect(game.width // 2 - 170, tab_y, 150, 36)
    charms_tab = pygame.Rect(game.width // 2 + 20, tab_y, 150, 36)
    draw_custom_button(game, quests_tab, "Quests", is_hover=tab == 'quests' or quests_tab.collidepoint(mouse_pos))
    draw_custom_button(game, charms_tab, "Charms", is_hover=tab == 'charms' or charms_tab.collidepoint(mouse_pos))
    if tab == 'quests':
        pygame.draw.rect(game.screen, constants.THEME.get('highlight', (200, 160, 0)), quests_tab, 2, border_radius=8)
    else:
        pygame.draw.rect(game.screen, constants.THEME.get('highlight', (200, 160, 0)), charms_tab, 2, border_radius=8)

    list_top = 128
    list_bottom = game.height - (70 if debug else 16)
    hover = None
    debug_rects = []

    have = set(progress.get('unlocked_achievements') or [])
    unlocked_charms = set(progress.get('unlocked_charms') or [])
    if progress.get('unlock_all'):
        have = {a['id'] for a in ach.ACHIEVEMENTS}
        unlocked_charms = set(ach.locked_charm_names())

    if tab == 'quests':
        row_h = 72
        content_h = len(ach.ACHIEVEMENTS) * row_h
        max_scroll = max(0, content_h - (list_bottom - list_top))
        scroll_y = max(0, min(scroll_y, max_scroll))
        clip = pygame.Rect(pad, list_top, game.width - pad * 2, list_bottom - list_top)
        old_clip = game.screen.get_clip()
        game.screen.set_clip(clip)
        y = list_top - scroll_y
        stats = progress.get('stats') or {}
        for a in ach.ACHIEVEMENTS:
            row = pygame.Rect(pad, y, game.width - pad * 2, row_h - 6)
            done = a['id'] in have
            bg = (30, 80, 30) if done else (20, 45, 20)
            pygame.draw.rect(game.screen, bg, row, border_radius=8)
            pygame.draw.rect(game.screen, (0, 0, 0), row, 1, border_radius=8)
            mark = "✓" if done else "○"
            mark_s = game.font.render(mark, True, (180, 220, 140) if done else (140, 140, 140))
            game.screen.blit(mark_s, (row.x + 10, row.y + 8))
            name_s = game.small_font.render(a['name'], True, constants.THEME['text'])
            game.screen.blit(name_s, (row.x + 50, row.y + 6))
            desc_s = game.tiny_font.render(a['desc'], True, (200, 200, 190))
            game.screen.blit(desc_s, (row.x + 50, row.y + 28))
            reward = ", ".join(a.get('unlocks') or [])
            col = (180, 220, 140) if done else (200, 180, 100)
            rew_s = game.tiny_font.render("Unlocks: " + reward, True, col)
            game.screen.blit(rew_s, (row.x + 50, row.y + 46))
            y += row_h
        game.screen.set_clip(old_clip)
    else:
        # Charm collection grid
        cell = 72
        gap = 8
        cols = max(1, (game.width - pad * 2) // (cell + gap))
        pool = list(data.CHARMS_POOL)
        content_h = ((len(pool) + cols - 1) // cols) * (cell + gap)
        max_scroll = max(0, content_h - (list_bottom - list_top))
        scroll_y = max(0, min(scroll_y, max_scroll))
        clip = pygame.Rect(pad, list_top, game.width - pad * 2, list_bottom - list_top)
        old_clip = game.screen.get_clip()
        game.screen.set_clip(clip)
        locked_set = set(ach.locked_charm_names())
        for i, charm in enumerate(pool):
            r = i // cols
            c = i % cols
            x = pad + c * (cell + gap)
            y = list_top - scroll_y + r * (cell + gap)
            rect = pygame.Rect(x, y, cell, cell)
            collected = (charm['name'] not in locked_set) or (charm['name'] in unlocked_charms)
            icon = pygame.Rect(rect.x + 6, rect.y + 6, cell - 12, cell - 12)
            draw_charm_die(game, icon, charm, index=None if collected else 0)
            if not collected:
                # force gray via overlay (index 0 + dummy disabled isn't set)
                try:
                    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    overlay.fill((10, 10, 10, 150))
                    game.screen.blit(overlay, rect.topleft)
                except Exception:
                    pass
                pygame.draw.rect(game.screen, (80, 80, 80), rect, 1, border_radius=6)
            else:
                pygame.draw.rect(game.screen, (0, 0, 0), rect, 1, border_radius=6)
            if rect.collidepoint(mouse_pos):
                if collected:
                    hover = (rect.x, rect.bottom + 4, charm['name'] + "\n" + charm.get('desc', ''))
                else:
                    a = ach.achievement_for_charm(charm['name'])
                    hint = a['desc'] if a else "Locked"
                    hover = (rect.x, rect.bottom + 4, "???\n" + hint)
        game.screen.set_clip(old_clip)

    if debug:
        u_rect = pygame.Rect(pad, game.height - 58, 160, 42)
        r_rect = pygame.Rect(pad + 170, game.height - 58, 160, 42)
        draw_custom_button(game, u_rect, "Unlock All", is_hover=u_rect.collidepoint(mouse_pos))
        draw_custom_button(game, r_rect, "Reset", is_hover=r_rect.collidepoint(mouse_pos), is_red=True)
        debug_rects = [(u_rect, 'unlock_all'), (r_rect, 'reset')]

    if hover:
        draw_tooltip(game, hover[0], hover[1], hover[2])

    return back_rect, {'quests': quests_tab, 'charms': charms_tab}, debug_rects, scroll_y

def draw_confirm_sell_popup(game):
    """Draws the confirm sell popup with wrapped and centered text."""
    popup_width = 300  # Adjust if your popup size is different
    popup_height = 150  # Adjust as needed
    popup_rect = pygame.Rect(game.width // 2 - popup_width // 2, game.height // 2 - popup_height // 2, popup_width, popup_height)
    pygame.draw.rect(game.screen, constants.THEME['panel_bg'], popup_rect)  # Gray background
    pygame.draw.rect(game.screen, constants.THEME['tooltip_border'], popup_rect, 3)  # White border

    # Message with wrapping and centering
    message = "Are you sure you want to sell this charm?"
    max_text_width = popup_width - 40  # Padding on sides
    wrapped_lines = wrap_text(game.small_font, message, max_text_width)  # Use your utils function

    y_offset = popup_rect.y + 20  # Start y for text
    for line in wrapped_lines:
        line_text = game.small_font.render(line, True, constants.THEME['text'])
        text_width = line_text.get_width()
        x_centered = popup_rect.x + (popup_width - text_width) // 2
        game.screen.blit(line_text, (x_centered, y_offset))
        y_offset += line_text.get_height() + 5  # Line spacing

    # Yes/No buttons (unchanged)
    yes_rect = pygame.Rect(popup_rect.x + 50, popup_rect.y + popup_height - 60, 100, 40)
    pygame.draw.rect(game.screen, constants.THEME['yes_button'], yes_rect)
    yes_text = game.small_font.render("Yes", True, constants.THEME['text'])
    game.screen.blit(yes_text, (yes_rect.x + (100 - yes_text.get_width()) // 2, yes_rect.y + 10))

    no_rect = pygame.Rect(popup_rect.x + popup_width - 150, popup_rect.y + popup_height - 60, 100, 40)
    pygame.draw.rect(game.screen, constants.THEME['no_button'], no_rect)
    no_text = game.small_font.render("No", True, constants.THEME['text'])
    game.screen.blit(no_text, (no_rect.x + (100 - no_text.get_width()) // 2, no_rect.y + 10))

    return yes_rect, no_rect

def draw_game_over_screen(game):
    """Draws the game over screen."""
    game.screen.fill(constants.THEME['background'])
    title_text = game.font.render("Game Over", True, (255, 0, 0))
    game.screen.blit(title_text, (game.width // 2 - title_text.get_width() // 2, game.height // 5))

    score_text = game.small_font.render(f"Final Score: {game.round_score}", True, (constants.THEME['text']))
    game.screen.blit(score_text, (game.width // 2 - score_text.get_width() // 2, game.height // 5 + 100))
    coins_text = game.small_font.render(f"Coins: {game.coins}", True, (constants.THEME['text']))
    game.screen.blit(coins_text, (game.width // 2 - coins_text.get_width() // 2, game.height // 5 + 150))
    stake_text = game.small_font.render(f"Reached Stake: {game.current_stake}", True, (constants.THEME['text']))
    game.screen.blit(stake_text, (game.width // 2 - stake_text.get_width() // 2, game.height // 5 + 200))

    restart_rect = pygame.Rect(game.width // 2 - constants.BUTTON_WIDTH // 2, game.height // 5 + 300, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    pygame.draw.rect(game.screen, (100, 100, 100), restart_rect)
    restart_text = game.small_font.render("Main Menu", True, (constants.THEME['text']))
    game.screen.blit(restart_text, (restart_rect.x + (constants.BUTTON_WIDTH - restart_text.get_width()) // 2,
                                   restart_rect.y + (constants.BUTTON_HEIGHT - restart_text.get_height()) // 2))
        
    return restart_rect

def draw_dice_select_screen(game):
    """Draws the dice selection screen for choosing a die from pack."""
    game.screen.fill(constants.THEME['background'])
    title_text = game.font.render("Choose a Die to Add", True, (constants.THEME['text']))
    game.screen.blit(title_text, (game.width // 2 - title_text.get_width() // 2, 50))

    choice_rects = []
    total_width = len(game.pack_choices) * 120 + (len(game.pack_choices) - 1) * 10
    start_x = (game.width - total_width) // 2
    current_time = time.time()  # For animation
    for i, color in enumerate(game.pack_choices):
        x = start_x + i * (120 + 10)
        y = game.height // 2 - 60
        choice_rect = pygame.Rect(x, y, 120, 120)
        die_rect = pygame.Rect(choice_rect.x + 10, choice_rect.y + 10, constants.DIE_SIZE, constants.DIE_SIZE)
        if color == 'Rainbow':
            color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
            color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
        else:
            color_rgb = constants.COLORS[color]
        inner_content = lambda r: [
            pygame.draw.circle(game.screen, (0, 0, 0), r.center, constants.DOT_RADIUS),  # Single pip
            draw_enhancement_visuals(game, r, {'color': color, 'enhancements': []})  # Stub die for preview
        ]
        draw_rounded_element(game.screen, die_rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=constants.DIE_BORDER_RADIUS, inner_content=inner_content)
        choice_rects.append((choice_rect, color))
    mouse_pos = pygame.mouse.get_pos()
    for rect, color in choice_rects:
        if rect.collidepoint(mouse_pos):
            tooltip_text = data.DICE_DESCRIPTIONS.get(color, f"Add 1 {color} Die")  # Fallback
            draw_tooltip(game, rect.x, rect.y + constants.CHARM_BOX_HEIGHT + 30, tooltip_text)
            break

    return choice_rects
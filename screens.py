# screens.py
import pygame
import time
import random
import math
from utils import *  # For draw_rounded_element, get_easing, etc.
import constants  # For THEME, SPLASH_*, etc.
import data  # For DICE_DESCRIPTIONS, etc. if needed in drawing

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
        button_y = game.height - constants.SPLASH_BUTTON_HEIGHT - 50  # Bottom padding
        total_buttons_width = 3 * constants.SPLASH_BUTTON_WIDTH + 2 * constants.SPLASH_BUTTON_SPACING  # For 3 buttons
        start_x = game.width // 2 - total_buttons_width // 2  # Center group

        new_game_rect = pygame.Rect(start_x, button_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, new_game_rect, "New Game", is_hover=new_game_rect.collidepoint(mouse_pos))

        load_game_rect = pygame.Rect(start_x + constants.SPLASH_BUTTON_WIDTH + constants.SPLASH_BUTTON_SPACING, button_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, load_game_rect, "Load Game", is_hover=load_game_rect.collidepoint(mouse_pos))

        quit_rect = pygame.Rect(start_x + 2 * (constants.SPLASH_BUTTON_WIDTH + constants.SPLASH_BUTTON_SPACING), button_y, constants.SPLASH_BUTTON_WIDTH, constants.SPLASH_BUTTON_HEIGHT)
        draw_custom_button(game, quit_rect, "Quit", is_hover=quit_rect.collidepoint(mouse_pos), is_red=True)  # Red for quit

        return new_game_rect, load_game_rect, quit_rect  # If returned for events
    
    return None, None, None  # Default return if not 'done'

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
    for i in range(visible_count):
        if game.pouch_offset + i >= len(data.POUCHES):
            break
        pouch = data.POUCHES[game.pouch_offset + i]
        x = start_x + i * (box_size + spacing)
        rect = pygame.Rect(x, y, box_size, box_size)
        
        # Use rounded element for nice border tied to theme
        fill_color = constants.COLORS[pouch['color']]
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

        # Clean tooltip without code
        bonus_text = []
        if 'extra_dice' in pouch['bonus']:
            for color, count in pouch['bonus']['extra_dice'].items():
                bonus_text.append(f"{count} extra {color} dice")
        if 'discards' in pouch['bonus']:
            bonus_text.append(f"+{pouch['bonus']['discards']} discards")
        if 'hands' in pouch['bonus']:
            bonus_text.append(f"+{pouch['bonus']['hands']} hands")
        if 'coins' in pouch['bonus']:
            bonus_text.append(f"+{pouch['bonus']['coins']} coins per unused reroll")
        # Add more bonus types if needed based on data.POUCHES

        tooltip_text = pouch['desc'] + "\nBonus: " + ", ".join(bonus_text)
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
        print("DEBUG: Rendering temp_message:", game.temp_message)  # Confirm trigger (remove after test)
        time_elapsed = time.time() - game.temp_message_start
        alpha = max(0, 255 * (1 - time_elapsed / game.temp_message_duration))
        print("DEBUG: Alpha value:", alpha)  # Should be ~255 initially (remove after test)
        
        text_surf = game.font.render(game.temp_message, True, (255, 0, 0))  # Red for errors
        text_surf = text_surf.convert_alpha()  # Ensure alpha support
        text_surf.set_alpha(int(alpha))  # Fade out
        # Adjusted position: Top center to avoid overlap with title/pouches
        game.screen.blit(text_surf, (game.width // 2 - text_surf.get_width() // 2, 20))  # Top of screen

    # Return any rects if needed (e.g., for buttons)
    return pouch_rects, tutorial_rect, left_arrow_rect, right_arrow_rect

def draw_game_screen(game):
    """Draws the main game screen."""
    game.screen.fill(constants.THEME['background'])  # Clears relics and prevents stacking
    mouse_pos = pygame.mouse.get_pos()  # Get mouse_pos at the top for use in hover checks
    draw_dice(game)
    # After drawing dice, add break effect
    if game.broken_dice and game.break_icon:
        current_time = time.time()
        elapsed = current_time - game.break_effect_start
        if elapsed < game.break_effect_duration:
            alpha = int(255 * (elapsed / game.break_effect_duration))  # Fade in from 0 to 255
            overlay = game.break_icon.copy()  # Copy to modify alpha
            overlay.set_alpha(alpha)
            for idx in game.broken_dice:
                # Get die position (same as in dice draw loop)
                total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
                start_x = (game.width - total_dice_width) // 2
                x = start_x + idx * (constants.DIE_SIZE + 20)
                size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[idx] else constants.DIE_SIZE
                offset = (constants.DIE_SIZE - size) / 2 if game.held[idx] else 0
                die_rect = pygame.Rect(x + offset, game.height - constants.DIE_SIZE - 100 + offset, size, size)
                # Blit overlay centered on die
                overlay_rect = overlay.get_rect(center=die_rect.center)
                game.screen.blit(overlay, overlay_rect)
        else:
            # Reset after duration
            game.broken_dice = []
            game.break_effect_start = 0
    draw_text(game)

    draw_bag_visual(game)
    # Add equipped charms drawing loop here (with grayscale for disabled)
    for i, charm in enumerate(game.equipped_charms):
        x = 50 + i * (constants.CHARM_SIZE + 10)  # Note: 10 is original spacing; update if changed
        y = 10  # Top for game screen
        rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
        draw_charm_die(game, rect, charm, index=i)  # Draw directly with frame, icon, and grayscale if disabled
        # Optional tooltip on hover
        if rect.collidepoint(mouse_pos):
            tooltip_text = charm['name'] + ": " + charm['desc']
            if charm['type'] == 'sacrifice_mult':
                tooltip_text += f" (Current mult: x{game.score_mult:.1f})"
                if game.score_mult < 10.0:
                    tooltip_text += " (max x10)"
            elif charm['type'] == 'empty_slot_mult':
                current_mult = game.get_stencil_mult()
                tooltip_text += f" (Current: x{current_mult:.1f})"
            if i in game.disabled_charms:
                tooltip_text += " (Disabled this round by Boss Effect)"
            draw_tooltip(game, x, y + constants.CHARM_SIZE + constants.TOOLTIP_PADDING, tooltip_text)
    # Removed self.draw_charms() to eliminate duplicate drawing and tooltip issues

    # Calculate bag_rect dynamically
    columns = 5
    rows = math.ceil(len(game.bag) / columns) if game.bag else 1
    bag_width = columns * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING + constants.BAG_PADDING * 2
    bag_height = rows * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING + constants.BAG_PADDING * 2
    bag_x = game.width - bag_width - 20
    bag_y = 50
    bag_rect = pygame.Rect(bag_x, bag_y, bag_width, bag_height)

    # New: Tray to the left of bag
    tray_width = 2 * constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING
    tray_x = max(bag_rect.left - tray_width - 10, 10)  # Left of bag, clamp to screen left
    tray_y = bag_rect.y  # Align top
    for i in range(2):
        slot_rect = pygame.Rect(tray_x + i * (constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING), tray_y, constants.TRAY_SLOT_SIZE, constants.TRAY_SLOT_SIZE)
        pygame.draw.rect(game.screen, (150, 150, 150), slot_rect, border_radius=5)
        if game.rune_tray[i]:
            text = game.tiny_font.render(f"#{game.rune_tray[i].get('id', i+1)}", True, constants.THEME['text'])
            game.screen.blit(text, (slot_rect.centerx - text.get_width()//2, slot_rect.centery - text.get_height()//2))
        else:
            pygame.draw.rect(game.screen, (255, 0, 0), slot_rect, width=2)  # Temp red debug to confirm visibility (remove after)

    draw_buttons(game)
    draw_ui_panel(game)
    if game.temp_message and time.time() - game.temp_message_start < game.temp_message_duration:
        msg_text = game.small_font.render(game.temp_message, True, (255, 255, 0))  # Yellow warning
        game.screen.blit(msg_text, (game.width // 2 - msg_text.get_width() // 2, 380))  # Near-center, above dice (adjust y if needed, e.g., 120 for more space)
    # In draw_game_screen(), after self.screen.fill(THEME['background']) or other early UI draws (e.g., after drawing charms and before bag)
    if game.current_boss_effect:
        effect_str = f"Boss Effect: {game.current_boss_effect['name']} - {game.current_boss_effect['desc']}"
        max_width = 300  # Adjust to fit space next to bag (e.g., 300px wide for wrapping)
        lines = []
        words = effect_str.split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if game.small_font.size(test_line)[0] > max_width:
                lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line = test_line
        lines.append(current_line.strip())  # Add last line
        
        # Position: Left and down of bag (assume bag at top-right; place mid-right but lower)
        text_x = game.width - max_width + 10  # Right-aligned with padding from edge
        text_y = 200  # Down from top (below charms/bag start; adjust if bag y=50, to 200 for below)
        line_spacing = game.small_font.get_height() + 5  # Vertical gap
        
        for i, line in enumerate(lines):
            boss_text = game.small_font.render(line, True, (255, 0, 0))  # Red text
            game.screen.blit(boss_text, (text_x, text_y + i * line_spacing))

    multipliers_button_rect = pygame.Rect(game.width - constants.MULTIPLIERS_BUTTON_SIZE - 10, game.height - constants.MULTIPLIERS_BUTTON_SIZE - 100, constants.MULTIPLIERS_BUTTON_SIZE, constants.MULTIPLIERS_BUTTON_SIZE)
    pygame.draw.rect(game.screen, (100, 100, 100), multipliers_button_rect)
    button_text = game.tiny_font.render("M", True, (constants.THEME['text']))
    game.screen.blit(button_text, (multipliers_button_rect.x + 20, multipliers_button_rect.y + 15))
    if multipliers_button_rect.collidepoint(mouse_pos):
        panel_x = game.width - constants.MULTIPLIERS_PANEL_WIDTH - 10
        panel_y = game.height - constants.MULTIPLIERS_PANEL_HEIGHT - constants.MULTIPLIERS_BUTTON_SIZE - 120
        panel_rect = pygame.Rect(panel_x, panel_y, constants.MULTIPLIERS_PANEL_WIDTH, constants.MULTIPLIERS_PANEL_HEIGHT)
        draw_rounded_element(game.screen, panel_rect, constants.UI_PANEL_COLOR, border_color=(0, 0, 0), border_width=2, radius=constants.UI_PANEL_BORDER_RADIUS, inner_content=None)
        y_offset = panel_y + 10
        for ht in data.HAND_TYPES:  # Iterate all types from data.py
            mult = game.hand_multipliers.get(ht, 1.0)  # Default 1.0 if not set
            mult_text = game.tiny_font.render(f"{ht}: x{mult:.1f}", True, (constants.THEME['text']))
            game.screen.blit(mult_text, (panel_x + 10, y_offset))
            y_offset += 25
        if y_offset > panel_y + 10:  # If any text, it's shown; else empty but panel visible
            pass
    if game.show_popup:
        draw_popup(game)

    # New: Build and return hand_rects, rolls, bag_rects, bag for animations in GameState
    hand_rects = []
    total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
    start_x = (game.width - total_dice_width) // 2
    for i in range(constants.NUM_DICE_IN_HAND):
        x = start_x + i * (constants.DIE_SIZE + 20)
        size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[i] else constants.DIE_SIZE
        offset = (constants.DIE_SIZE - size) / 2 if game.held[i] else 0
        die_rect = pygame.Rect(x + offset, game.height - constants.DIE_SIZE - 100 + offset, size, size)
        hand_rects.append(die_rect)
    
    bag_rects = []
    columns = 5
    rows = math.ceil(len(game.bag) / columns) if game.bag else 1
    for j in range(len(game.bag)):
        col = j % columns
        row = j // columns
        small_x = bag_x + constants.BAG_PADDING + col * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
        small_y = bag_y + constants.BAG_PADDING + row * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
        small_rect = pygame.Rect(small_x, small_y, constants.SMALL_DIE_SIZE, constants.SMALL_DIE_SIZE)
        bag_rects.append(small_rect)
    
    return hand_rects, game.rolls, bag_rects, game.bag  # Add this return

def draw_shop_screen(game, skip_tooltips=False):
    """Draws the shop screen with equipped charms (sell), shop charms (buy), and Prism Packs."""
    mouse_pos = pygame.mouse.get_pos()
    game.screen.fill(constants.THEME['background'])

    # Reposition "Shop" text to top left, above equipped charms
    shop_y = 40  # Above charms at y=150; adjust if charms y changes
    shop_text = game.font.render("Shop", True, (constants.THEME['text']))  # Or your exact text/color
    shop_text_x = 50  # Top left with padding (matches LEFT_BUTTON_X)
    game.screen.blit(shop_text, (shop_text_x, shop_y))

    # Reposition "Coins" text below "Shop" (still top left)
    coins_y = shop_y + 40  # Below "Shop" for stacking
    coins_text = game.font.render(f"Coins: {game.coins}", True, (constants.THEME['text']))  # Or your format
    coins_text_x = 50  # Same left alignment
    game.screen.blit(coins_text, (coins_text_x, coins_y))

    # Position reroll button top left, right of "Coins" text
    reroll_x = coins_text_x + coins_text.get_width() + 20  # Right of coins with padding
    reroll_y = coins_y - 10  # Align vertically with coins (slight offset if needed)
    reroll_rect = pygame.Rect(reroll_x, reroll_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, reroll_rect, "Reroll (5)", is_hover=reroll_rect.collidepoint(mouse_pos))

    # Calculate bag_rect dynamically (keep for consistency, even if not used for tray)
    columns = 5
    rows = math.ceil(len(game.bag) / columns) if game.bag else 1
    bag_width = columns * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING + constants.BAG_PADDING * 2
    bag_height = rows * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING + constants.BAG_PADDING * 2
    bag_x = game.width - bag_width - 20
    bag_y = 50
    bag_rect = pygame.Rect(bag_x, bag_y, bag_width, bag_height)

    # New: Tray underneath continue (use multipliers_button_rect as proxy; adjust if actual continue differs)
    multipliers_button_rect = pygame.Rect(game.width - constants.MULTIPLIERS_BUTTON_SIZE - 10, game.height - constants.MULTIPLIERS_BUTTON_SIZE - 100, constants.MULTIPLIERS_BUTTON_SIZE, constants.MULTIPLIERS_BUTTON_SIZE)  # From your code
    continue_rect = multipliers_button_rect  # Proxy; replace with actual continue_rect if defined
    tray_width = 2 * constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING
    tray_x = continue_rect.centerx - tray_width // 2  # Center under
    tray_y = continue_rect.bottom + 10  # Below
    tray_y = min(tray_y, game.height - constants.TRAY_SLOT_SIZE - 10)  # Clamp to bottom
    for i in range(2):
        slot_rect = pygame.Rect(tray_x + i * (constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING), tray_y, constants.TRAY_SLOT_SIZE, constants.TRAY_SLOT_SIZE)
        pygame.draw.rect(game.screen, (150, 150, 150), slot_rect, border_radius=5)
        if game.rune_tray[i]:
            text = game.tiny_font.render(f"#{game.rune_tray[i].get('id', i+1)}", True, constants.THEME['text'])
            game.screen.blit(text, (slot_rect.centerx - text.get_width()//2, slot_rect.centery - text.get_height()//2))
        else:
            pygame.draw.rect(game.screen, (255, 0, 0), slot_rect, width=2)  # Temp red debug (remove after)

    # Define large panel for purchasables (shop charms and packs, expanded for future additions)
    panel_width = int(game.width * 0.9)  # 90% width for more space
    panel_height = int(game.height * 0.7)  # 70% height to cover more unused area, leaving room above/below
    panel_x = (game.width - panel_width) // 2  # Center horizontally
    panel_y = 280  # Below equipped charms and titles, to enclose shop items
    panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

    # Draw panel background with rounded corners
    pygame.draw.rect(game.screen, constants.UI_PANEL_COLOR, panel_rect, border_radius=15)

    # Draw black border with rounded corners
    pygame.draw.rect(game.screen, (0, 0, 0), panel_rect, width=2, border_radius=15)

    # Equipped charms horizontal at top (outside panel)
    equipped_title = game.small_font.render("Equipped Charms", True, (constants.THEME['text']))
    game.screen.blit(equipped_title, (50, 120))

    # Initialize lists and hover here
    sell_rects = []
    equipped_rects = []
    equipped_hover = None

    for i, charm in enumerate(game.equipped_charms):
        if i == game.dragging_charm_index and game.dragging_shop:
            continue
        x = 50 + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
        y = 150
        eq_rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
        icon_rect = pygame.Rect(eq_rect.x + (constants.CHARM_BOX_WIDTH - constants.CHARM_DIE_SIZE) // 2, eq_rect.y + 10, constants.CHARM_DIE_SIZE, constants.CHARM_DIE_SIZE)  # Adjusted padding
        draw_charm_die(game, icon_rect, charm)
        sell_val = charm['cost'] // 2
        sell_label = game.tiny_font.render(f"Sell: {sell_val}", True, (constants.THEME['text']))
        game.screen.blit(sell_label, (eq_rect.x + 5, eq_rect.y + constants.CHARM_BOX_HEIGHT - 30))  # Moved lower
        sell_rect = pygame.Rect(eq_rect.x + constants.CHARM_BOX_WIDTH - 60, eq_rect.y + constants.CHARM_BOX_HEIGHT - 30, 50, 20)
        pygame.draw.rect(game.screen, (150, 0, 0), sell_rect)
        sell_text = game.tiny_font.render("Sell", True, (constants.THEME['text']))
        game.screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 3))
        sell_rects.append(sell_rect)
        equipped_rects.append(eq_rect)
        if eq_rect.collidepoint(mouse_pos):
            tooltip_text = charm['name'] + ": " + charm['desc']
            if charm['type'] == 'sacrifice_mult':
                tooltip_text += f" (Current mult: x{game.score_mult})"
                if game.score_mult < 10.0:
                    tooltip_text += " (max x10)"
            elif charm['type'] == 'empty_slot_mult':
                current_mult = game.get_stencil_mult()
                tooltip_text += f" (Current: x{current_mult})"
            equipped_hover = (x, y + constants.CHARM_BOX_HEIGHT + 5, tooltip_text)
    
    # Draw dragged charm in shop
    if game.dragging_charm_index != -1 and game.dragging_shop:
        charm = game.equipped_charms[game.dragging_charm_index]
        x = mouse_pos[0] - game.drag_offset_x
        y = mouse_pos[1] - game.drag_offset_y
        rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)  # Use shop box size
        draw_charm_die(game, rect, charm)

    # Inner padding for items inside panel
    inner_padding = 20

    # Shop charms horizontal inside panel (top section, leaving space below for future)
    shop_title = game.small_font.render("Shop Charms", True, (constants.THEME['text']))
    game.screen.blit(shop_title, (panel_x + inner_padding, panel_y + inner_padding - 20))  # Title inside/top of panel

    # Initialize lists and hover here
    buy_rects = []
    shop_rects = []
    shop_hover = None
    
    shop_charms_y = panel_y + inner_padding
    for i, charm in enumerate(game.shop_charms):
        x = panel_x + inner_padding + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
        y = shop_charms_y
        shop_rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
        icon_rect = pygame.Rect(shop_rect.x + (constants.CHARM_BOX_WIDTH - constants.CHARM_DIE_SIZE) // 2, shop_rect.y + 10, constants.CHARM_DIE_SIZE, constants.CHARM_DIE_SIZE)
        draw_charm_die(game, icon_rect, charm)
        cost_label = game.tiny_font.render(f"Cost: {charm['cost']}", True, (constants.THEME['text']))
        game.screen.blit(cost_label, (shop_rect.x + 5, shop_rect.y + constants.CHARM_BOX_HEIGHT - 30))
        buy_rect = pygame.Rect(shop_rect.x + constants.CHARM_BOX_WIDTH - 60, shop_rect.y + constants.CHARM_BOX_HEIGHT - 30, 50, 20)
        pygame.draw.rect(game.screen, (0, 150, 0), buy_rect)
        buy_text = game.tiny_font.render("Buy", True, (constants.THEME['text']))
        game.screen.blit(buy_text, (buy_rect.x + 10, buy_rect.y + 3))
        buy_rects.append(buy_rect)
        shop_rects.append(shop_rect)
        if shop_rect.collidepoint(mouse_pos):
            tooltip_text = charm['name'] + ": " + charm['desc']
            if charm['type'] == 'empty_slot_mult':
                preview_mult = charm['value'] * (game.max_charms - len(game.equipped_charms))
                tooltip_text += f" (If bought: x{preview_mult})"
            shop_hover = (x, y + constants.CHARM_BOX_HEIGHT + 5, tooltip_text)

    # Packs section inside panel (below shop charms, with space for future additions above/below/sides)
    pack_title = game.small_font.render("Packs", True, (constants.THEME['text']))
    game.screen.blit(pack_title, (panel_x + inner_padding, shop_charms_y + constants.CHARM_BOX_HEIGHT + 20))  # Below shop charms

    pack_y = shop_charms_y + constants.CHARM_BOX_HEIGHT + 50  # Space below charms
    pack_rects = []
    pack_costs = [3, 5, 7, 3, 5, 9, 4, 7, 9]  # Append rune pack costs
    pack_choices_num = [2, 3, 5, 3, 4, 3, 3, 5, 5]  # Append rune pack choices
    pack_names = [
        "Basic Prism (1 of 2)", "Standard Prism (1 of 3)", "Premium Prism (1 of 5)",
        "Dice Pack (1 of 3)", "Dice Pack (1 of 4)", "Special Dice Pack (1 of 3)",
        "Basic Rune Pack (1 of 3)", "Mega Rune Pack (1 of 5)", "Super Rune Pack (2 of 5)"
    ]  # Append rune pack names
    pack_x_start = panel_x + inner_padding  # Left-aligned (restore original start)
    pack_x = pack_x_start
    for pack_idx in game.available_packs:
        x = pack_x
        y = pack_y
        pack_rect = pygame.Rect(x, y, 80, 80)  # Restore local size=80 (larger, less cramped)
        # Draw icon centered (updated methods handle)
        if pack_idx in [0,1,2]:
            draw_prism_pack_icon(game, pack_idx, pack_rect.x, pack_rect.y + 10)
        elif pack_idx in [3,4,5]:
            cycle = constants.BASE_COLORS if pack_idx in [3,4] else constants.SPECIAL_COLORS
            draw_pack_icon(game, pack_rect, pack_choices_num[pack_idx], cycle)
        elif pack_idx in [6,7,8]:  # New: Generic brown rect for rune packs
            pygame.draw.rect(game.screen, constants.BAG_COLOR, pack_rect, border_radius=constants.BAG_BORDER_RADIUS)  # Generic brown
            text = game.small_font.render(f"Rune Pack ${pack_costs[pack_idx]}", True, constants.THEME['text'])
            game.screen.blit(text, (pack_rect.centerx - text.get_width()//2, pack_rect.centery))
        if not skip_tooltips and pack_rect.collidepoint(mouse_pos):
            tooltip_text = f"{pack_names[pack_idx]}\nCost: {pack_costs[pack_idx]}"
            tooltip_y = pack_rect.y + 80 + 5  # Lowered
            if tooltip_y + 50 > game.height:
                tooltip_y = pack_rect.y - 60
            draw_tooltip(game, pack_rect.x, tooltip_y, tooltip_text)
        pack_rects.append((pack_rect, pack_idx))
        pack_x += 80 + 10  # Restore tighter spacing (adjust to 20 if still cramped)

    # Draw tooltips after all elements
    if not skip_tooltips and equipped_hover:
        draw_tooltip(game, *equipped_hover)
    if not skip_tooltips and shop_hover:
        draw_tooltip(game, *shop_hover)

    # Current hand multipliers panel in top right corner
    mult_title = game.small_font.render("Hand Multipliers", True, (constants.THEME['text']))
    mult_x = game.width - 200  # Far right with padding
    mult_y = 50  # Top, aligned with "Shop"
    game.screen.blit(mult_title, (mult_x, mult_y))
    y_offset = mult_y + 30  # Below title
    for ht, mult in game.hand_multipliers.items():
        mult_text = game.tiny_font.render(f"{ht}: x{mult:.1f}", True, (constants.THEME['text']))
        game.screen.blit(mult_text, (mult_x, y_offset))
        y_offset += 25

    # Position continue button left of hand multipliers (top right, aligned with title)
    continue_x = mult_x - constants.BUTTON_WIDTH - 20  # Left of multipliers with padding
    continue_y = mult_y  # Align with multipliers title
    continue_rect = pygame.Rect(continue_x, continue_y, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    draw_custom_button(game, continue_rect, "Continue", is_hover=continue_rect.collidepoint(mouse_pos))  # No is_red for positive action

    return continue_rect, sell_rects, buy_rects, equipped_rects, shop_rects, pack_rects, reroll_rect

def draw_blinds_screen(game):
    """Draws the blinds selection screen with three boxes for all blinds, horizontally."""
    mouse_pos = pygame.mouse.get_pos()  # For hover
    game.screen.fill(constants.THEME['background'])
    title_text = game.font.render(f"Stake {game.current_stake}", True, (constants.THEME['text']))
    game.screen.blit(title_text, (game.width // 2 - title_text.get_width() // 2, game.height // 10))
    if game.upcoming_boss_effect is None:
        game.upcoming_boss_effect = random.choice(data.BOSS_EFFECTS)  # Fallback generate if not set

    blind_order = ['Small', 'Big', 'Boss']
    box_width, box_height = 150, 100
    box_spacing = 50  # Spacing between blind boxes (pixels)
    total_blinds_width = 3 * box_width + 2 * box_spacing
    start_x = (game.width - total_blinds_width) // 2
    start_y = game.height // 3
    for i, blind in enumerate(blind_order):
        x = start_x + i * (box_width + box_spacing)
        rect = pygame.Rect(x, start_y, box_width, box_height)
        pygame.draw.rect(game.screen, (100, 100, 100), rect)
        # Highlight current blind
        if blind == game.current_blind:
            pygame.draw.rect(game.screen, (255, 255, 255), rect, 3)
        blind_text = game.small_font.render(f"{blind} Blind", True, (constants.THEME['text']))
        game.screen.blit(blind_text, (rect.x + (box_width - blind_text.get_width()) // 2, rect.y + 20))
        target_text = game.small_font.render(f"Score: {int(game.get_blind_target(blind))}", True, (constants.THEME['text']))
        game.screen.blit(target_text, (rect.x + (box_width - target_text.get_width()) // 2, rect.y + 50))

        # Preview for Boss
        if blind == 'Boss' and game.upcoming_boss_effect:
            effect_str = f"Effect: {game.upcoming_boss_effect['name']} - {game.upcoming_boss_effect['desc']}"
            # Simple wrap if too long (split into lines if > box_width * 1.5)
            lines = []
            words = effect_str.split()
            current_line = ""
            for word in words:
                if game.small_font.render(current_line + word, True, (255, 0, 0)).get_width() > box_width * 1.5:
                    lines.append(current_line.strip())
                    current_line = word + " "
                else:
                    current_line += word + " "
            lines.append(current_line.strip())
            
            y_offset = rect.y + box_height + 10  # Start below box
            for line in lines:
                effect_text = game.small_font.render(line, True, (255, 0, 0))  # Red for warning
                game.screen.blit(effect_text, (rect.x + (box_width - effect_text.get_width()) // 2, y_offset))  # Center
                y_offset += effect_text.get_height() + 5  # Vertical spacing
        elif blind == 'Boss':  # Fallback if no effect (e.g., bug)
            fallback_text = game.small_font.render("Effect: Random", True, (255, 0, 0))
            game.screen.blit(fallback_text, (rect.x + (box_width - fallback_text.get_width()) // 2, rect.y + box_height + 10))

    coins_text = game.small_font.render(f"Coins: {game.coins}", True, (constants.THEME['text']))
    game.screen.blit(coins_text, (game.width // 2 - coins_text.get_width() // 2, game.height // 10 + 50))

    continue_rect = None  # Define all returns upfront
    debug_button_rect = None
    up_rect = None
    down_rect = None
    debug_jump_rect = None
    
    # Draw continue button (always)
    continue_rect = pygame.Rect(game.width // 2 - constants.BUTTON_WIDTH // 2, game.height // 2 + 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    pygame.draw.rect(game.screen, constants.THEME['button_bg'], continue_rect)
    continue_text = game.font.render("Continue", True, constants.THEME['text'])
    game.screen.blit(continue_text, (continue_rect.x + 20, continue_rect.y + 10))

    if constants.DEBUG:
        # Debug Boss Select Button
        debug_button_text = game.small_font.render("Select Boss (Debug)", True, (0, 255, 0))  # Green for debug
        debug_button_rect = pygame.Rect(game.width - 200, game.height - 100, 180, 40)  # Bottom-right; adjust
        pygame.draw.rect(game.screen, (50, 50, 50), debug_button_rect, border_radius=5)
        game.screen.blit(debug_button_text, (debug_button_rect.x + 10, debug_button_rect.y + 10))
        debug_jump_text = game.small_font.render("Jump to Boss (Debug)", True, (0, 255, 0))  # Green for debug
        debug_jump_rect = pygame.Rect(game.width - 200, game.height - 60, 180, 40)  # Above the select button; adjust y to avoid overlap
        pygame.draw.rect(game.screen, (50, 50, 50), debug_jump_rect, border_radius=5)
        game.screen.blit(debug_jump_text, (debug_jump_rect.x + 10, debug_jump_rect.y + 10))

        if game.debug_boss_dropdown_open:
            # Dropdown Panel: Scrollable list
            panel_width, panel_height = 300, 300  # Size for ~10-15 visible items
            
            # Position: Above the button, hugging right side
            panel_x = game.width - panel_width - 10  # Hug right with padding
            panel_y = debug_button_rect.y - panel_height - 10  # Above button with padding
            
            # Adaptive: If above clips top, shift below as fallback
            if panel_y < 0:
                panel_y = debug_button_rect.y + debug_button_rect.height + 10

            pygame.draw.rect(game.screen, (20, 20, 20), (panel_x, panel_y, panel_width, panel_height))  # Dark panel

            item_height = 25  # Each effect row
            visible_items = panel_height // item_height
            total_items = len(data.BOSS_EFFECTS)
            
            # Scroll arrows (simple up/down buttons)
            up_rect = pygame.Rect(panel_x + panel_width - 30, panel_y, 30, 30)
            down_rect = pygame.Rect(panel_x + panel_width - 30, panel_y + panel_height - 30, 30, 30)
            pygame.draw.rect(game.screen, (100, 100, 100), up_rect)
            pygame.draw.rect(game.screen, (100, 100, 100), down_rect)
            game.screen.blit(game.small_font.render("^", True, (constants.THEME['text'])), (up_rect.x + 10, up_rect.y + 5))
            game.screen.blit(game.small_font.render("v", True, (constants.THEME['text'])), (down_rect.x + 10, down_rect.y + 5))

            # Render visible effects
            for i in range(game.debug_boss_scroll_offset, min(game.debug_boss_scroll_offset + visible_items, total_items)):
                effect = data.BOSS_EFFECTS[i]
                item_text = game.small_font.render(f"{effect['name']}: {effect['desc'][:30]}...", True, (constants.THEME['text']))  # Truncate long desc
                item_y = panel_y + (i - game.debug_boss_scroll_offset) * item_height + 5
                game.screen.blit(item_text, (panel_x + 10, item_y))

    # Update return to include debug rects
    return continue_rect, debug_button_rect, up_rect, down_rect, debug_jump_rect

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
        total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
        start_x = (game.width - total_dice_width) // 2
        current_time = time.time()  # For animation
        for i, (die, value) in enumerate(game.rolls):
            x = start_x + i * (constants.DIE_SIZE + 20)
            y = game.height - constants.DIE_SIZE - 100
            size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if game.held[i] else constants.DIE_SIZE
            offset = (constants.DIE_SIZE - constants.DIE_SIZE * constants.HELD_DIE_SCALE) / 2 if game.held[i] else 0
            color = die['color']
            if color == 'Rainbow':
                color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
                color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
            else:
                color_rgb = constants.COLORS[color]
            # Draw die background with rounded corners
            rect = pygame.Rect(x + offset, y + offset, size, size)

            # New: Mini-function for dots (moves your existing loop here)
            def _draw_dots(inner_rect):
                for pos in data.DOT_POSITIONS.get(value, []):
                    dot_x = inner_rect.x + pos[0] * inner_rect.width  # Updated to use inner_rect (was x + offset + pos[0] * size)
                    dot_y = inner_rect.y + pos[1] * inner_rect.height  # Updated to use inner_rect (was y + offset + pos[1] * size)
                    pygame.draw.circle(game.screen, (0, 0, 0), (dot_x, dot_y), constants.DOT_RADIUS)
            # Highlight if selected for discard (red border outside black)
            if game.discard_selected[i]:
                outer_rect = pygame.Rect(x + offset - 3, y + offset - 3, size + 6, size + 6)
                pygame.draw.rect(game.screen, (255, 0, 0), outer_rect, 3, border_radius=constants.DIE_BORDER_RADIUS)
            # Draw dots
            inner_content = lambda r: [
                _draw_dots(r),  # Existing pips
                draw_enhancement_visuals(game, r, die)  # Add enhancements/animations
            ]
            draw_rounded_element(game.screen, rect, color_rgb, border_color=(0, 0, 0), border_width=2, radius=constants.DIE_BORDER_RADIUS, inner_content=inner_content)

# In screens.py, update draw_bag_visual to use inner_content with lambda for enhancements (no need for draw_dots_or_icon if small dies have no pips; add if needed)
def draw_bag_visual(game):
    """Draws a brown bag with rounded corners and black border, with dice inside."""
    num_dice = len(game.bag)
    if num_dice > 30:
        columns = 6
    else:
        columns = 5
    rows = math.ceil(num_dice / columns)
    grid_width = columns * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING
    grid_height = rows * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING
    bag_width = grid_width + 2 * constants.BAG_PADDING
    bag_height = grid_height + 2 * constants.BAG_PADDING
    bag_x = game.width - bag_width - 10
    bag_y = 50
    bag_rect = pygame.Rect(bag_x, bag_y, bag_width, bag_height)
    # In draw_game_screen or draw_bag_visual (update the rect draw line)
    bag_color = game.get_bag_color()
    # Draw upside-down triangle at bottom of Z-order
    triangle_points = [
        (bag_x + bag_width // 2, bag_y + 10), # bottom tip
        (bag_x + bag_width // 2 - 15, bag_y - 10), # top left
        (bag_x + bag_width // 2 + 15, bag_y - 10) # top right
    ]
    pygame.draw.polygon(game.screen, bag_color, triangle_points)
    pygame.draw.polygon(game.screen, (0, 0, 0), triangle_points, 2)
    draw_rounded_element(game.screen, bag_rect, bag_color, border_color=(0, 0, 0), border_width=2, radius=constants.BAG_BORDER_RADIUS, inner_content=None)
    sorted_bag = sorted(game.bag, key=lambda d: list(constants.COLORS.keys()).index(d['color']))
    start_x = bag_x + constants.BAG_PADDING
    start_y = bag_y + constants.BAG_PADDING
    index = 0
    current_time = time.time() # For animation
    for row in range(rows):
        y = start_y + row * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
        for col in range(columns):
            if index < num_dice:
                die = sorted_bag[index]
                x = start_x + col * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING)
                rect = pygame.Rect(x, y, constants.SMALL_DIE_SIZE, constants.SMALL_DIE_SIZE)
                color = die['color']
                if color == 'Rainbow':
                    color_index = int(current_time / constants.CYCLE_SPEED) % len(constants.BASE_COLORS)
                    color_rgb = constants.COLORS[constants.BASE_COLORS[color_index]]
                else:
                    color_rgb = constants.COLORS[color]
                inner_content = lambda r: draw_bag_enhancement_visuals(game, r, die)  # Add this; no pips for small dies
                draw_rounded_element(game.screen, rect, color_rgb, border_color=(0, 0, 0), border_width=1, radius=constants.SMALL_DIE_BORDER_RADIUS, inner_content=inner_content)
                index += 1
            else:
                break

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
    """Draws the UI panel with hands, discards, rolls left."""
    panel_x = 50
    panel_y = game.height - constants.BUTTON_HEIGHT - 20 - constants.UI_PANEL_HEIGHT - 10  # Above discard button
    panel_rect = pygame.Rect(panel_x, panel_y, constants.UI_PANEL_WIDTH, constants.UI_PANEL_HEIGHT)
    draw_rounded_element(game.screen, panel_rect, constants.THEME['panel_bg'], border_color=constants.THEME['border'], border_width=2, radius=constants.UI_PANEL_BORDER_RADIUS, inner_content=None)

    # Texts inside
    hands_text = game.tiny_font.render(f"Hands: {game.hands_left}", True, (constants.THEME['text']))
    game.screen.blit(hands_text, (panel_x + 10, panel_y + 10))
    discards_text = game.tiny_font.render(f"Discards: {game.discards_left}", True, (constants.THEME['text']))
    game.screen.blit(discards_text, (panel_x + 10, panel_y + 40))
    rolls_text = game.tiny_font.render(f"Rolls Left: {game.rerolls_left if game.rerolls_left >= 0 else '∞'}", True, (constants.THEME['text']))
    game.screen.blit(rolls_text, (panel_x + 10, panel_y + 70))
    coins_text = game.tiny_font.render(f"Coins: {game.coins}", True, (constants.THEME['text']))
    game.screen.blit(coins_text, (panel_x + 10, panel_y + 100))

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

def draw_text(game):
        """Draws current hand info, score, rerolls, discards, etc."""
        # Current hand type and score
        hand_text = game.small_font.render(game.current_hand_text, True, (constants.THEME['text']))
        game.screen.blit(hand_text, (50, 120))

        # Color modifier with special handling for "(disabled)"
        if " (disabled)" in game.current_modifier_text:
            base_modifier = game.current_modifier_text.replace(" (disabled)", "")
            base_render = game.small_font.render(base_modifier, True, constants.THEME['text'])
            disabled_render = game.small_font.render(" (disabled)", True, (255, 0, 0))  # Red for disabled
            game.screen.blit(base_render, (50, 150))
            game.screen.blit(disabled_render, (50 + base_render.get_width(), 150))  # Append right after base
        else:
            modifier_text = game.small_font.render(game.current_modifier_text, True, (constants.THEME['text']))
            game.screen.blit(modifier_text, (50, 150))

        # Score
        score_text = game.small_font.render(f"Score: {game.round_score}/{int(game.get_blind_target())}", True, (constants.THEME['text']))
        game.screen.blit(score_text, (50, 180))

def draw_charm_die(game, rect, charm, index=None):
    """Draws a charm as a die with icon inside. Grays out if disabled using built-in Pygame transform."""
    # Determine if disabled
    is_disabled = index is not None and index in game.disabled_charms
    
    # Draw die background (white face with border) - gray the background too if disabled for better effect
    bg_color = (128, 128, 128) if is_disabled else constants.DIE_BACKGROUND_COLOR

    # Get charm-specific bg if defined, else fallback to DIE_BACKGROUND_COLOR
    charm_bg = constants.CHARM_BG_COLORS.get(charm['name'], constants.DIE_BACKGROUND_COLOR)

    # Gray if disabled
    bg_color = (128, 128, 128) if is_disabled else charm_bg
    
    # Inner icon rect (padded and scaled)
    def _draw_inner_charm(inner_rect):
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

def draw_tooltip(game, x, y, text):
    lines = wrap_text(game.small_font, text, constants.TOOLTIP_MAX_WIDTH)
    line_height = game.small_font.get_height()
    width = max(game.small_font.size(line)[0] for line in lines) + constants.TOOLTIP_PADDING * 2
    height = len(lines) * line_height + constants.TOOLTIP_PADDING * 2
    if x + width > game.width:
        x = game.width - width
    tooltip_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(game.screen, (100, 100, 100), tooltip_rect)
    for i, line in enumerate(lines):
        desc_surface = game.small_font.render(line, True, (constants.THEME['text']))
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
    popup_y = (game.height - constants.POPUP_HEIGHT) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, constants.POPUP_WIDTH, constants.POPUP_HEIGHT)
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
    game.mute_button_rect = pygame.Rect(popup_x + constants.POPUP_WIDTH - 60, popup_y + constants.POPUP_HEIGHT - 60, 40, 40)  # Adjusted: Inside popup with padding
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
    """Draws the beaten blind popup with a single Continue button and $ animation."""
    popup_rect = pygame.Rect(game.width // 2 - constants.POPUP_WIDTH // 2, 200, constants.POPUP_WIDTH, constants.POPUP_HEIGHT)
    pygame.draw.rect(game.screen, (100, 100, 100), popup_rect)
    pygame.draw.rect(game.screen, (255, 255, 255), popup_rect, 3)  # White border

    # Split message into lines and render with animation for $
    lines = game.popup_message.split('\n')
    for i, line in enumerate(lines):
        text = game.tiny_font.render(line, True, (constants.THEME['text']))
        game.screen.blit(text, (popup_rect.x + (constants.POPUP_WIDTH - text.get_width()) // 2, popup_rect.y + 20 + i * 30))

    # Draw single Continue button
    continue_rect = pygame.Rect(popup_rect.x + (constants.POPUP_WIDTH - constants.BUTTON_WIDTH) // 2, popup_rect.y + constants.POPUP_HEIGHT - 70, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
    pygame.draw.rect(game.screen, (100, 100, 100), continue_rect)
    continue_text = game.tiny_font.render("Continue", True, (constants.THEME['text']))
    game.screen.blit(continue_text, (continue_rect.x + (constants.BUTTON_WIDTH - continue_text.get_width()) // 2, continue_rect.y + 10))

    return continue_rect

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
    restart_text = game.font.render("Restart", True, (constants.THEME['text']))
    game.screen.blit(restart_text, (restart_rect.x + 20, restart_rect.y + 10))
        
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
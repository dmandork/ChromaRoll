# statemachine.py
import os
import pygame
import time
import sys
import copy
import random
import savegame
import math
from screens import draw_splash_screen, draw_init_screen, draw_tutorial_screen, draw_blinds_screen, draw_game_screen, draw_popup, draw_buttons, draw_shop_screen, draw_game_over_screen, draw_pause_menu, draw_custom_button, draw_tooltip, draw_enhancement_visuals  # Import at top of file
from constants import *  # For SPLASH_* constants
from utils import get_easing, draw_rounded_element, wrap_text, resource_path  # Import get_easing to fix "not defined" errors
from data import BOSS_EFFECTS, HAND_TYPES, CHARMS_POOL
from constants import BASE_COLORS, DICE_FACES, NUM_DICE_IN_HAND, DIE_SIZE, HELD_DIE_SCALE, THEME, DEBUG, CHARM_SIZE, CHARM_BOX_WIDTH, CHARM_SPACING, CHARM_BOX_HEIGHT, SPECIAL_COLORS, PACK_BOOST
import constants  # This imports the module, so you can use constants.THEME
import data
from states.shop import ShopState
from states.init import InitState 
from states.base import State, StateMachine

    
class RuneSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.selected_rune_index = -1
        self.selected_die_indices = []  # List for multi-select
        self.random_dice = random.sample(self.game.bag, min(8, len(self.game.bag)))  # 8 random for mod
        self.rune_rects = []  # To store for handle_event
        self.die_rects = []   # To store for handle_event
        self.confirm_rect = None
        self.hold_rect = None
        self.skip_rect = None  # For skip button
        self.continue_rect = None  # New for post-apply
        self.applied_count = 0  # Track how many applied/held
        self.hover_rune_index = -1  # For tooltip
        self.preview_mode = False  # Flag for post-apply preview
        self.preview_message = ""  # For non-die feedback
        self.preview_dies = []  # New: Store enhanced dies for preview

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        if not self.preview_mode:
            # Calculate start_x dynamically for centering
            num_runes = len(self.game.pack_choices)
            total_rune_width = num_runes * constants.CHARM_BOX_WIDTH + (num_runes - 1) * constants.CHARM_SPACING
            start_x = (self.game.width - total_rune_width) // 2

            # Top: Runes (placeholders with wrapped name)
            self.rune_rects = []
            mouse_pos = pygame.mouse.get_pos()  # Get mouse for hover
            current_time = time.time()  # For animations
            for i, rune in enumerate(self.game.pack_choices):
                rune_x = start_x + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
                rune_rect = pygame.Rect(rune_x, 50, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
                
                is_selected = i == self.selected_rune_index  # Assuming single select; change to list check if multi
                is_hover = rune_rect.collidepoint(mouse_pos)
                
                # Animation: Pulse scale if selected
                if is_selected:
                    pulse = 1 + 0.05 * math.sin(current_time * 5)  # Gentle pulse
                    new_w = int(constants.CHARM_BOX_WIDTH * pulse)
                    new_h = int(constants.CHARM_BOX_HEIGHT * pulse)
                    new_rect = pygame.Rect(rune_x - (new_w - constants.CHARM_BOX_WIDTH)//2, 50 - (new_h - constants.CHARM_BOX_HEIGHT)//2, new_w, new_h)
                    pygame.draw.rect(self.game.screen, (200,200,200), new_rect)  # Gray box on scaled rect
                    
                    # Redraw wrapped text centered on new_rect
                    lines = wrap_text(self.game.small_font, rune['name'], new_w - 20)
                    y_offset = new_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
                    for line in lines:
                        text = self.game.small_font.render(line, True, constants.THEME['text'])
                        self.game.screen.blit(text, (new_rect.centerx - text.get_width()//2, y_offset))
                        y_offset += self.game.small_font.get_height()
                    
                    draw_rect = new_rect  # Use for border below
                else:
                    pygame.draw.rect(self.game.screen, (200,200,200), rune_rect)  # Original gray
                    
                    # Original text
                    lines = wrap_text(self.game.small_font, rune['name'], constants.CHARM_BOX_WIDTH - 20)
                    y_offset = rune_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
                    for line in lines:
                        text = self.game.small_font.render(line, True, constants.THEME['text'])
                        self.game.screen.blit(text, (rune_rect.centerx - text.get_width()//2, y_offset))
                        y_offset += self.game.small_font.get_height()
                    
                    draw_rect = rune_rect
                
                # Glow border if hover
                if is_hover:
                    pygame.draw.rect(self.game.screen, (255,255,0), draw_rect, width=3)  # Yellow glow
                
                # Selected border (on top if not hover)
                if is_selected and not is_hover:
                    pygame.draw.rect(self.game.screen, (255,255,0), draw_rect, width=3)  # Yellow border
                
                self.rune_rects.append(rune_rect)  # Append original for clicks

            

            # Bottom: 8 Dice
            num_dice = len(self.random_dice)
            total_die_width = num_dice * constants.DIE_SIZE + (num_dice - 1) * 10  # Assuming 10 spacing
            die_start_x = (self.game.width - total_die_width) // 2
            self.die_rects = []
            for j, die in enumerate(self.random_dice):
                die_x = die_start_x + j * (constants.DIE_SIZE + 10)
                die_rect = pygame.Rect(die_x, self.game.height//2, constants.DIE_SIZE, constants.DIE_SIZE)
                draw_rounded_element(self.game.screen, die_rect, constants.COLORS[die['color']], inner_content=lambda r: self.draw_dots_or_icon(die))  # Use self. if method
                if j in self.selected_die_indices:  # Highlight multi
                    pygame.draw.rect(self.game.screen, (255,255,0), die_rect, width=3)
                self.die_rects.append(die_rect)

            # Confirm button
            self.confirm_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
            draw_custom_button(self.game, self.confirm_rect, "Apply Rune")

            # Hold button (left of confirm)
            self.hold_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2 - 160, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
            draw_custom_button(self.game, self.hold_rect, "Hold Rune")

            # Skip button (right of confirm)
            self.skip_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2 + 160, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
            draw_custom_button(self.game, self.skip_rect, "Skip Pack")

        else:
            # Preview mode: Show updated dice (no runes, no borders)
            title_text = self.game.font.render("Preview Enhanced Dice", True, constants.THEME['text'])
            self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

            # Show enhanced dice (centered, no yellow borders)
            num_preview = len(self.preview_dies)
            total_preview_width = num_preview * constants.DIE_SIZE + (num_preview - 1) * 10
            preview_start_x = (self.game.width - total_preview_width) // 2
            for k, die in enumerate(self.preview_dies):
                die_x = preview_start_x + k * (constants.DIE_SIZE + 10)
                die_rect = pygame.Rect(die_x, self.game.height//2 - 100, constants.DIE_SIZE, constants.DIE_SIZE)  # Higher y for space
                draw_rounded_element(self.game.screen, die_rect, constants.COLORS[die['color']], inner_content=lambda r: self.draw_dots_or_icon(die))
                # Call enhancement visuals if you have a function (e.g., draw_enhancement_visuals(self.game, die_rect, die))

            if self.preview_message:
                msg_text = self.game.small_font.render(self.preview_message, True, (255, 255, 0))
                self.game.screen.blit(msg_text, (self.game.width // 2 - msg_text.get_width() // 2, self.game.height // 2 + 50))

            # Continue button
            self.continue_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
            draw_custom_button(self.game, self.continue_rect, "Continue")

        # Draw tooltip if hovering (only in select mode)
        if not self.preview_mode and self.hover_rune_index != -1:
            mouse_pos = pygame.mouse.get_pos()  # Get current mouse for pos
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, self.game.pack_choices[self.hover_rune_index]['desc'])

    def draw_dots_or_icon(self, die):  # Placeholder method; move to utils/screens if not defined
        # Implement your dot/icon drawing logic here, e.g., for standard dice pips
        pass  # Replace with actual code from your draw functions

    def handle_event(self, event):
        if self.preview_mode:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.continue_rect.collidepoint(mouse_pos):
                    self.preview_mode = False
                    self.preview_message = ""
                    self.preview_dies = []
                    self.random_dice = random.sample(self.game.bag, min(8, len(self.game.bag)))  # Refresh after preview
                    if self.applied_count >= self.game.pack_select_count:
                        self.game.state_machine.change_state(ShopState(self.game))
            return  # Skip other events in preview

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()  # Get mouse_pos here
            # Select rune/die by rect collide
            for i, rune_rect in enumerate(self.rune_rects):
                if rune_rect.collidepoint(mouse_pos):
                    self.selected_rune_index = i
                    self.selected_die_indices = []  # Reset dice on new rune select (optional; to enforce per rune)

            # Die select: Toggle for multi
            for j, die_rect in enumerate(self.die_rects):
                if die_rect.collidepoint(mouse_pos):
                    if self.selected_rune_index == -1:
                        continue  # Skip if no rune selected
                    if j in self.selected_die_indices:
                        self.selected_die_indices.remove(j)
                    else:
                        self.selected_die_indices.append(j)
                    # Limit based on rune
                    if self.selected_rune_index != -1:
                        rune = self.game.pack_choices[self.selected_rune_index]
                        max_dice = rune.get('max_dice', 1)  # Default 1
                        while len(self.selected_die_indices) > max_dice:
                            self.selected_die_indices.pop(0)  # Remove first if over (or pop() for last)

            if self.confirm_rect.collidepoint(mouse_pos) and self.selected_rune_index != -1:
                rune = self.game.pack_choices[self.selected_rune_index]
                dies = [self.random_dice[j] for j in self.selected_die_indices]  # Always list
                self.game.apply_rune_effect(rune, dies)  # Pass list
                self.game.pack_choices.pop(self.selected_rune_index)  # Remove used
                self.applied_count += 1  # Increment count
                self.preview_dies = dies  # Store for preview
                self.preview_mode = True  # Enter preview
                if len(dies) == 0:
                    self.preview_message = "Rune applied (no dice affected)!"  # For non-die

            if self.hold_rect.collidepoint(mouse_pos) and self.selected_rune_index != -1:
                rune = self.game.pack_choices[self.selected_rune_index]
                if None in self.game.rune_tray:  # Room check
                    slot = self.game.rune_tray.index(None)
                    self.game.rune_tray[slot] = rune
                    self.game.pack_choices.pop(self.selected_rune_index)  # Remove from choices
                    self.applied_count += 1  # Count hold as select
                    self.selected_rune_index = -1
                    self.selected_die_indices = []
                    self.random_dice = random.sample(self.game.bag, min(8, len(self.game.bag)))  # Refresh after hold
                    if self.applied_count >= self.game.pack_select_count:
                        self.game.state_machine.change_state(ShopState(self.game))

            if self.skip_rect.collidepoint(mouse_pos):
                self.game.pack_choices = []  # Discard
                self.game.state_machine.change_state(ShopState(self.game))  # Back

        if event.type == pygame.MOUSEMOTION:  # Hover tooltip
            self.hover_rune_index = -1
            for i, rune_rect in enumerate(self.rune_rects):
                if rune_rect.collidepoint(event.pos):
                    self.hover_rune_index = i
                    break  # Only one at a time

class RuneUseState(State):
    def __init__(self, game, rune):
        super().__init__(game)
        self.rune = rune  # Single rune to apply
        self.selected_die_indices = []  # For multi if max_dice > 0
        self.random_dice = random.sample(self.game.bag, min(8, len(self.game.bag)))  # 8 random for mod
        self.die_rects = []   # To store for handle_event
        self.confirm_rect = None
        self.cancel_rect = None  # To cancel back
        self.hover = False  # For rune tooltip

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        # Top: Single rune
        rune_rect = pygame.Rect(self.game.width // 2 - constants.CHARM_BOX_WIDTH // 2, 50, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
        pygame.draw.rect(self.game.screen, (200,200,200), rune_rect)  # Gray box
        
        # Wrap text
        lines = wrap_text(self.game.small_font, self.rune['name'], constants.CHARM_BOX_WIDTH - 20)
        y_offset = rune_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
        for line in lines:
            text = self.game.small_font.render(line, True, constants.THEME['text'])
            self.game.screen.blit(text, (rune_rect.centerx - text.get_width()//2, y_offset))
            y_offset += self.game.small_font.get_height()

        # Bottom: 8 Dice if max_dice > 0
        if self.rune.get('max_dice', 0) > 0:
            num_dice = len(self.random_dice)
            total_die_width = num_dice * constants.DIE_SIZE + (num_dice - 1) * 10
            die_start_x = (self.game.width - total_die_width) // 2
            self.die_rects = []
            for j, die in enumerate(self.random_dice):
                die_x = die_start_x + j * (constants.DIE_SIZE + 10)
                die_rect = pygame.Rect(die_x, self.game.height//2, constants.DIE_SIZE, constants.DIE_SIZE)
                draw_rounded_element(self.game.screen, die_rect, constants.COLORS[die['color']], inner_content=lambda r: self.draw_dots_or_icon(die))
                if j in self.selected_die_indices:
                    pygame.draw.rect(self.game.screen, (255,255,0), die_rect, width=3)
                self.die_rects.append(die_rect)
        else:
            self.die_rects = []  # No dice needed

        # Confirm button
        self.confirm_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        draw_custom_button(self.game, self.confirm_rect, "Apply Rune")

        # Cancel button (left)
        self.cancel_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2 - 160, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
        draw_custom_button(self.game, self.cancel_rect, "Cancel")

        # Tooltip for rune on hover
        mouse_pos = pygame.mouse.get_pos()
        if rune_rect.collidepoint(mouse_pos):
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, self.rune['desc'])

    def draw_dots_or_icon(self, die):  # Placeholder
        pass  # Your pip code

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Die select if needed
            if self.rune.get('max_dice', 0) > 0:
                for j, die_rect in enumerate(self.die_rects):
                    if die_rect.collidepoint(mouse_pos):
                        if j in self.selected_die_indices:
                            self.selected_die_indices.remove(j)
                        else:
                            self.selected_die_indices.append(j)
                        max_dice = self.rune.get('max_dice', 1)
                        while len(self.selected_die_indices) > max_dice:
                            self.selected_die_indices.pop(0)

            if self.confirm_rect.collidepoint(mouse_pos):
                dies = [self.random_dice[j] for j in self.selected_die_indices]
                self.game.apply_rune_effect(self.rune, dies)
                self.game.state_machine.change_state(self.game.previous_state)  # Back to game/shop

            if self.cancel_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(self.game.previous_state)  # Back without apply

class PauseMenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.button_rects = None  # List of (rect, option) tuples

    def enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        from screens import draw_pause_menu
        draw_pause_menu(self.game)
        self.button_rects = self.game.get_pause_button_rects()  # Assuming this method exists and returns rects

    def handle_event(self, event):    
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                print("Escape pressed in Pause - Resuming")  # Debug
                self.game.state_machine.change_state(GameState(self.game))  # Direct resume, no load

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for rect, opt in self.button_rects or []:
                if self.game.mute_button_rect.collidepoint(mouse_pos):
                    self.game.toggle_mute()
                if rect.collidepoint(mouse_pos):
                    if opt == "Return to Game" or event.key == pygame.K_ESCAPE:
                        self.game.is_resuming = True  # Flag
                        self.game.state_machine.change_state(self.game.previous_state)  # Instance
                    elif opt == "Main Menu":
                        savegame.delete_save()
                        self.game.reset_game()
                        self.game.state_machine.change_state(InitState(self.game))
                    elif opt == "Quit":
                        savegame.save_game(self.game)
                        pygame.quit()
                        sys.exit()
                    break

class ConfirmSellState(State):
    def __init__(self, game):
        super().__init__(game)
        self.yes_rect = None
        self.no_rect = None

    def enter(self):
        pass  # Any setup, e.g., confirm index already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        from screens import draw_shop_screen, draw_confirm_sell_popup
        draw_shop_screen(self.game)  # Redraw shop underneath popup
        self.yes_rect, self.no_rect = draw_confirm_sell_popup(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.yes_rect and self.yes_rect.collidepoint(mouse_pos):
                charm = self.game.equipped_charms.pop(self.game.confirm_sell_index)
                sell_val = charm['cost'] // 2
                self.game.coins += sell_val
                # REMOVE this line: data.CHARMS_POOL.append(charm)  # No append—filtering handles availability
                self.game.confirm_sell_index = -1
                self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
            elif self.no_rect and self.no_rect.collidepoint(mouse_pos):
                self.game.confirm_sell_index = -1
                self.game.state_machine.change_state(ShopState(self.game))  # Back to shop

class PackSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.choice_rects = None  # List of rects for choices

    def enter(self):
        pass  # Pack choices already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        from screens import draw_pack_select_screen
        self.choice_rects = draw_pack_select_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for j, choice_rect in enumerate(self.choice_rects or []):
                if choice_rect.collidepoint(mouse_pos):
                    chosen = self.game.pack_choices[j]
                    self.game.hand_multipliers[chosen] += PACK_BOOST
                    self.game.pack_choices = []
                    self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
                    break

class DiceSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.choice_rects = None  # List of (rect, color) tuples

    def enter(self):
        pass  # Pack choices already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        from screens import draw_dice_select_screen
        self.choice_rects = draw_dice_select_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for choice_rect, color in self.choice_rects or []:
                if choice_rect.collidepoint(mouse_pos):
                    # Add new die
                    new_id = f"{color}{len([d for d in self.game.bag if d['color'] == color]) + 1}"
                    new_die = {'id': new_id, 'color': color, 'faces': DICE_FACES[:]}
                    self.game.bag.append(new_die)
                    self.game.full_bag.append(copy.deepcopy(new_die))
                    self.game.pack_choices = []
                    self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
                    break

class DebugMenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.charm_button_rect = None
        self.prism_button_rect = None
        self.rune_button_rect = None
        self.back_button_rect = None

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        title_text = self.game.font.render("Debug Menu", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        button_y = 150
        self.charm_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.charm_button_rect, "Buy Any Charm", is_hover=self.charm_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.prism_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.prism_button_rect, "Apply Any Prism Upgrade", is_hover=self.prism_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.rune_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.rune_button_rect, "Apply Any Rune", is_hover=self.rune_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.back_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.back_button_rect, "Back to Shop", is_hover=self.back_button_rect.collidepoint(mouse_pos))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.charm_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugCharmState(self.game))
            elif self.prism_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugPrismState(self.game))
            elif self.rune_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugRuneSelectState(self.game))
            elif self.back_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(ShopState(self.game))

class DebugCharmState(State):
    def __init__(self, game):
        super().__init__(game)
        self.charm_rects = []
        self.scroll_y = 0
        self.back_rect = None  # New
        self.prev_rect = None
        self.next_rect = None
        self.page = 0
        self.last_wheel_time = 0  # For debounce

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        title_text = self.game.font.render("Debug: Select Charm to Add", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(data.CHARMS_POOL))
        visible_charms = data.CHARMS_POOL[start_idx:end_idx]
        rows = math.ceil(len(visible_charms) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.charm_rects = []
        tooltips_to_draw = []  # Collect for last draw
        for i, charm in enumerate(visible_charms):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            bg_color = constants.CHARM_BG_COLORS.get(charm['name'], (200, 200, 200))
            draw_rounded_element(self.game.screen, rect, bg_color, border_width=2, radius=10)
            name_text = self.game.small_font.render(charm['name'], True, constants.THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, charm['desc']))
            self.charm_rects.append((rect, charm))

        # Scrollbar if needed
        if total_height > self.game.height - 200:  # Viewport height estimate
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(data.CHARMS_POOL):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:  # Debounce: Ignore click if wheel recent
                return
            for rect, charm in self.charm_rects:
                if rect.collidepoint(mouse_pos) and len(self.game.equipped_charms) < self.game.max_charms * 2:
                    self.game.equipped_charms.append(copy.deepcopy(charm))
                    self.game.temp_message = f"Added {charm['name']}!"
                    self.game.state_machine.change_state(DebugMenuState(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)  # Clamp
            self.last_wheel_time = time.time()  # Update for debounce

class DebugPrismState(State):
    def __init__(self, game):
        super().__init__(game)
        self.prism_rects = []
        self.scroll_y = 0
        self.back_rect = None
        self.prev_rect = None
        self.next_rect = None
        self.page = 0
        self.last_wheel_time = 0

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        title_text = self.game.font.render("Debug: Select Prism Upgrade", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(data.HAND_TYPES))
        visible_hts = data.HAND_TYPES[start_idx:end_idx]
        rows = math.ceil(len(visible_hts) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.prism_rects = []
        tooltips_to_draw = []
        for i, ht in enumerate(visible_hts):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            draw_rounded_element(self.game.screen, rect, (180, 140, 100), border_width=2, radius=10)
            name_text = self.game.small_font.render(ht, True, constants.THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, f"Boost {ht} by {constants.PACK_BOOST}x"))
            self.prism_rects.append((rect, ht))

        # Scrollbar if needed
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(data.HAND_TYPES):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:
                return
            for rect, ht in self.prism_rects:
                if rect.collidepoint(mouse_pos):
                    self.game.hand_multipliers[ht] += constants.PACK_BOOST
                    self.game.temp_message = f"Boosted {ht} by {constants.PACK_BOOST}x!"
                    self.game.state_machine.change_state(DebugMenuState(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()

class DebugRuneSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.rune_rects = []
        self.scroll_y = 0
        self.page = 0
        self.prev_rect = None
        self.next_rect = None
        self.back_rect = None  # New
        self.last_wheel_time = 0

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        title_text = self.game.font.render("Debug: Select Rune to Apply", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(data.MYSTIC_RUNES))
        visible_runes = data.MYSTIC_RUNES[start_idx:end_idx]
        rows = math.ceil(len(visible_runes) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.rune_rects = []
        tooltips_to_draw = []  # New collection
        for i, rune in enumerate(visible_runes):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            bg_color = (128, 0, 128)
            draw_rounded_element(self.game.screen, rect, bg_color, border_width=2, radius=10)
            name_text = self.game.small_font.render(rune['name'], True, constants.THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, rune['desc']))
            self.rune_rects.append((rect, rune))

        # Scrollbar
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(data.MYSTIC_RUNES):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:
                return
            for rect, rune in self.rune_rects:
                if rect.collidepoint(mouse_pos):
                    self.game.current_rune = rune
                    self.game.current_rune_slot = -1
                    if rune['max_dice'] == 0:
                        self.game.apply_rune_effect(rune)
                    else:
                        self.game.selected_dice = []
                        self.game.state_machine.change_state(DebugDiceSelectForRune(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()

class DebugDiceSelectForRune(State):
    def __init__(self, game):
        super().__init__(game)
        self.die_rects = []
        self.scroll_y = 0
        self.selected_dice = []  # Allow multi
        self.apply_rect = None  # For apply button
        self.back_rect = None  # New: For cancel/back
        self.last_wheel_time = 0  # For debounce

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        title_text = self.game.font.render(f"Debug: Select up to {self.game.current_rune['max_dice']} Dice for {self.game.current_rune['name']}", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        die_size = 80
        spacing = 10
        cols = 5
        rows = math.ceil(len(self.game.bag) / cols)
        total_height = rows * (die_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.die_rects = []  # Reset
        tooltips_to_draw = []  # New: Collect for last draw
        for i, die in enumerate(self.game.bag):
            col = i % cols
            row = i // cols
            x = spacing + col * (die_size + spacing)
            y = start_y + row * (die_size + spacing)
            rect = pygame.Rect(x, y, die_size, die_size)
            color_rgb = constants.COLORS[die['color']]
            inner_content = lambda r: pygame.draw.circle(self.game.screen, (0, 0, 0), r.center, constants.DOT_RADIUS // 2)
            draw_rounded_element(self.game.screen, rect, color_rgb, border_width=2, radius=10, inner_content=inner_content)
            draw_enhancement_visuals(self.game, rect, die)
            if die in self.selected_dice:
                pygame.draw.rect(self.game.screen, (255, 255, 0), rect, 3)
            if rect.collidepoint(mouse_pos):
                enh_desc = ', '.join(data.ENH_DESC.get(e, e) for e in die['enhancements'])
                tooltips_to_draw.append((x, y + die_size + 10, f"{die['color']} Die - {enh_desc or 'None'}"))
            self.die_rects.append((rect, die))

        # Scrollbar if needed
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Apply button
        self.apply_rect = pygame.Rect(self.game.width // 2 - 150, self.game.height - 50, 300, 40)
        draw_custom_button(self.game, self.apply_rect, "Apply Rune", is_hover=self.apply_rect.collidepoint(mouse_pos))

        # New: Back/Cancel button (left of apply)
        self.back_rect = pygame.Rect(self.game.width // 2 - 450, self.game.height - 50, 300, 40)  # Adjust position as needed
        draw_custom_button(self.game, self.back_rect, "Cancel", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last (on top)
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:  # Debounce
                return
            for rect, die in self.die_rects:
                if rect.collidepoint(mouse_pos):
                    if die in self.selected_dice:
                        self.selected_dice.remove(die)
                    elif len(self.selected_dice) < self.game.current_rune['max_dice']:
                        self.selected_dice.append(die)
                    break
            if self.apply_rect and self.apply_rect.collidepoint(mouse_pos) and self.selected_dice:
                self.game.apply_rune_effect(self.game.current_rune, self.selected_dice)
                self.game.state_machine.change_state(DebugMenuState(self.game))
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))  # Back without apply
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()


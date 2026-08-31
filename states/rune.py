# states/rune.py
import pygame
import time
import math
import random
from states.base import State
from screens import (
    draw_custom_button, draw_tooltip, draw_rounded_element, draw_table_felt,
    draw_gold_plaque, draw_select_die, enhancement_label, _enh_line,
    TABLE_GOLD, TABLE_PLAQUE,
)
from utils import wrap_text
from constants import *  # THEME, CHARM_BOX_WIDTH, CHARM_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT, DIE_SIZE, DOT_RADIUS, COLORS


def _pack_need(game):
    """How many picks this pack allows. Never crash if the attr was never set."""
    n = getattr(game, 'pack_select_count', None)
    if n is None:
        n = getattr(game, 'select_count', 1)
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 1
    return max(1, n)


class RuneSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        print(f"DEBUG: RuneUseState init - tray before: {game.rune_tray}")  # TEMP - confirm no wipe
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
        self.hover_die_index = -1
        self.preview_mode = False  # Flag for post-apply preview
        self.preview_message = ""  # For non-die feedback
        self.preview_dies = []  # New: Store enhanced dies for preview

    def draw(self):
        draw_table_felt(self.game)
        mouse_pos = pygame.mouse.get_pos()  # Moved to top for both modes
        need = _pack_need(self.game)
        left = max(0, need - int(self.applied_count or 0))
        if not self.preview_mode:
            pick_label = f"Pick {need} rune" + ("s" if need != 1 else "")
            if self.applied_count:
                pick_label += f"  ·  {left} left"
            title = self.game.font.render(pick_label, True, TABLE_GOLD)
            self.game.screen.blit(title, (self.game.width // 2 - title.get_width() // 2, 12))
            # Calculate start_x dynamically for centering
            num_runes = len(self.game.pack_choices)
            total_rune_width = num_runes * CHARM_BOX_WIDTH + (num_runes - 1) * CHARM_SPACING
            start_x = (self.game.width - total_rune_width) // 2

            # Top: Runes (placeholders with wrapped name)
            self.rune_rects = []
            current_time = time.time()  # For animations
            for i, rune in enumerate(self.game.pack_choices):
                rune_x = start_x + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
                rune_rect = pygame.Rect(rune_x, 58, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
                
                is_selected = i == self.selected_rune_index  # Assuming single select; change to list check if multi
                is_hover = rune_rect.collidepoint(mouse_pos)
                
                # Animation: Pulse scale if selected
                if is_selected:
                    pulse = 1 + 0.05 * math.sin(current_time * 5)  # Gentle pulse
                    new_w = int(CHARM_BOX_WIDTH * pulse)
                    new_h = int(CHARM_BOX_HEIGHT * pulse)
                    new_rect = pygame.Rect(rune_x - (new_w - CHARM_BOX_WIDTH)//2, 50 - (new_h - CHARM_BOX_HEIGHT)//2, new_w, new_h)
                    pygame.draw.rect(self.game.screen, TABLE_PLAQUE, new_rect, border_radius=12)
                    pygame.draw.rect(self.game.screen, TABLE_GOLD, new_rect, 2, border_radius=12)
                    
                    # Redraw wrapped text centered on new_rect
                    lines = wrap_text(self.game.small_font, rune['name'], new_w - 20)
                    y_offset = new_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
                    for line in lines:
                        text = self.game.small_font.render(line, True, THEME['text'])
                        self.game.screen.blit(text, (new_rect.centerx - text.get_width()//2, y_offset))
                        y_offset += self.game.small_font.get_height()
                    
                    draw_rect = new_rect  # Use for border below
                else:
                    pygame.draw.rect(self.game.screen, TABLE_PLAQUE, rune_rect, border_radius=12)
                    pygame.draw.rect(self.game.screen, TABLE_GOLD, rune_rect, 2, border_radius=12)
                    
                    # Original text
                    lines = wrap_text(self.game.small_font, rune['name'], CHARM_BOX_WIDTH - 20)
                    y_offset = rune_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
                    for line in lines:
                        text = self.game.small_font.render(line, True, THEME['text'])
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

            

            # Bottom: 8 Dice — color, pips, enhancement chips + name
            num_dice = len(self.random_dice)
            total_die_width = num_dice * DIE_SIZE + (num_dice - 1) * 10
            die_start_x = (self.game.width - total_die_width) // 2
            self.die_rects = []
            self.hover_die_index = -1
            for j, die in enumerate(self.random_dice):
                die_x = die_start_x + j * (DIE_SIZE + 10)
                die_rect = pygame.Rect(die_x, self.game.height // 2 - 10, DIE_SIZE, DIE_SIZE)
                draw_select_die(self.game, die_rect, die, selected=(j in self.selected_die_indices))
                if die_rect.collidepoint(mouse_pos):
                    self.hover_die_index = j
                self.die_rects.append(die_rect)

            self.confirm_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
            draw_custom_button(self.game, self.confirm_rect, "Apply Rune", is_hover=self.confirm_rect.collidepoint(mouse_pos))
            self.hold_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2 - 160, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
            draw_custom_button(self.game, self.hold_rect, "Hold Rune", is_hover=self.hold_rect.collidepoint(mouse_pos))
            self.skip_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2 + 160, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
            draw_custom_button(self.game, self.skip_rect, "Skip Pack", is_hover=self.skip_rect.collidepoint(mouse_pos), is_red=True)

        else:
            # Preview mode: Show updated dice (no runes, no borders, no full screen draw to avoid pull)
            title_text = self.game.font.render("Preview Enhanced Dice", True, THEME['text'])
            self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

            # Manual enhanced dice draw (centered, no yellow borders)
            num_preview = len(self.preview_dies)
            if num_preview > 0:
                total_preview_width = num_preview * DIE_SIZE + (num_preview - 1) * 10
                preview_start_x = (self.game.width - total_preview_width) // 2
                for k, die in enumerate(self.preview_dies):
                    die_x = preview_start_x + k * (DIE_SIZE + 10)
                    die_rect = pygame.Rect(die_x, self.game.height//2 - 100, DIE_SIZE, DIE_SIZE)
                    draw_select_die(self.game, die_rect, die, selected=False)
            else:
                no_dice_text = self.game.small_font.render("No dice affected – rune applied!", True, THEME['text'])
                self.game.screen.blit(no_dice_text, (self.game.width // 2 - no_dice_text.get_width() // 2, self.game.height // 2))

            if self.preview_message:
                msg_text = self.game.small_font.render(self.preview_message, True, (255, 255, 0))
                self.game.screen.blit(msg_text, (self.game.width // 2 - msg_text.get_width() // 2, self.game.height // 2 + 50))

            # Continue button
            self.continue_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
            draw_custom_button(self.game, self.continue_rect, "Continue", is_hover=self.continue_rect.collidepoint(mouse_pos))

        # Draw tooltip if hovering (only in select mode)
        if not self.preview_mode and self.hover_rune_index != -1:
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, self.game.pack_choices[self.hover_rune_index]['desc'])
        elif not self.preview_mode and self.hover_die_index != -1:
            die = self.random_dice[self.hover_die_index]
            lines = [f"{die.get('color', '?')} die"]
            tag = enhancement_label(die)
            if tag:
                lines.append(tag)
            for enh in die.get('enhancements') or []:
                lines.append(_enh_line(enh))
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, "\n".join(lines))

    def draw_dots_or_icon(self, die):  # Placeholder method; move to utils/screens if not defined
        # Implement your dot/icon drawing logic here, e.g., for standard dice pips
        pass  # Replace with actual code from your draw functions

    def handle_event(self, event):
        from states.shop import ShopState  # Lazy import
        if self.preview_mode:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.continue_rect.collidepoint(mouse_pos):
                    self.preview_mode = False
                    self.preview_message = ""
                    self.preview_dies = []
                    self.random_dice = random.sample(self.game.bag, min(8, len(self.game.bag)))  # Refresh after preview
                    if self.applied_count >= _pack_need(self.game):
                        from states.shop import resume_shop
                        resume_shop(self.game)
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
                self.selected_rune_index = -1  # Reset after pop to avoid index error
                self.applied_count += 1  # Increment count
                self.preview_dies = dies  # Store for preview
                self.preview_mode = True  # Enter preview
                if len(dies) == 0:
                    self.preview_message = "Rune applied (no dice affected)!"  # For non-die

            if self.hold_rect.collidepoint(mouse_pos) and self.selected_rune_index != -1:
                rune = self.game.pack_choices[self.selected_rune_index]
                if None in self.game.rune_tray:  # Room check
                    slot = self.game.rune_tray.index(None)
                    print(f"DEBUG: Holding {rune['name']} to tray slot {slot}")  # TEMP
                    self.game.rune_tray[slot] = rune
                    self.game.pack_choices.pop(self.selected_rune_index)  # Pop from choices
                    self.selected_rune_index = -1  # Reset
                    self.applied_count += 1  # Increment
                    self.selected_die_indices = []
                    need = _pack_need(self.game)
                    print(f"DEBUG: Hold applied={self.applied_count}, total select={need}, choices left={len(self.game.pack_choices)}")  # TEMP
                    self.game.temp_message = f"Held {rune['name']} to tray! ({self.applied_count}/{need})"  # Progress msg
                    self.game.temp_message_start = time.time()
                    # FIXED: Transition after hold (re-enter only if multi)
                    if self.applied_count < need:
                        # Re-enter with full reset (refreshes UI/choices)
                        new_state = RuneSelectState(self.game)
                        new_state.applied_count = self.applied_count  # Carry over count
                        new_state.selected_rune_index = -1  # Force reset
                        new_state.selected_die_indices = []
                        self.game.state_machine.change_state(new_state)
                    else:
                        from states.shop import resume_shop
                        resume_shop(self.game)
                else:
                    print("DEBUG: Hold failed - tray full")  # TEMP
                    self.game.temp_message = "Tray full - cannot hold rune!"
                    self.game.temp_message_start = time.time()

            if self.skip_rect.collidepoint(mouse_pos):
                self.game.pack_choices = []  # Discard
                from states.shop import resume_shop
                resume_shop(self.game)

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
        self.selected_die_indices = []  # FIXED: Consistent for selection
        self.max_dice = rune.get('max_dice', 0)
        self.random_dice = []
        self.die_rects = []  # To store for handle_event
        self.confirm_rect = None
        self.cancel_rect = None  # To cancel back
        self.hover = False  # For rune tooltip
        self.low_bag_message = ""  # For bag <8

        # Sample dice if needed
        if self.max_dice > 0:
            bag_len = len(self.game.bag)
            print(f"DEBUG: RuneUseState bag_len: {bag_len}, max_dice: {self.max_dice}")  # TEMP
            if bag_len == 0:
                self.low_bag_message = "Bag empty – cannot select dice!"
            else:
                sample_size = min(8, bag_len)
                self.random_dice = random.sample(self.game.bag, sample_size)
                if bag_len < 8:
                    self.low_bag_message = f"Bag low ({bag_len} dice) – limited options."
        else:
            print(f"DEBUG: RuneUseState max_dice=0 – no dice needed for {rune['name']}")  # TEMP

        self.temp_message = f"Select up to {self.max_dice} dice for {rune['name']}"
        self.game.temp_message = self.temp_message
        self.game.show_instruction_popup = True

    def draw(self):
        draw_table_felt(self.game)
        mouse_pos = pygame.mouse.get_pos()
        title = self.game.font.render(self.rune.get('name', 'Rune'), True, TABLE_GOLD)
        self.game.screen.blit(title, (self.game.width // 2 - title.get_width() // 2, 16))
        hint = self.game.tiny_font.render(
            self.temp_message or f"Select up to {self.max_dice} dice", True, THEME['text'])
        self.game.screen.blit(hint, (self.game.width // 2 - hint.get_width() // 2, 62))

        rune_rect = pygame.Rect(self.game.width // 2 - CHARM_BOX_WIDTH // 2, 88, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
        draw_gold_plaque(self.game, rune_rect, fill=TABLE_PLAQUE, radius=12)
        lines = wrap_text(self.game.small_font, self.rune['name'], CHARM_BOX_WIDTH - 20)
        y_offset = rune_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
        for line in lines:
            text = self.game.small_font.render(line, True, THEME['text'])
            self.game.screen.blit(text, (rune_rect.centerx - text.get_width() // 2, y_offset))
            y_offset += self.game.small_font.get_height()

        hover_die = -1
        if self.max_dice > 0:
            if len(self.random_dice) == 0:
                msg_text = self.game.small_font.render(self.low_bag_message or "No dice available", True, (220, 80, 80))
                self.game.screen.blit(msg_text, (self.game.width // 2 - msg_text.get_width() // 2, self.game.height // 2))
                self.die_rects = []
            else:
                num_dice = len(self.random_dice)
                total_die_width = num_dice * DIE_SIZE + (num_dice - 1) * 10
                die_start_x = (self.game.width - total_die_width) // 2
                self.die_rects = []
                for j, die in enumerate(self.random_dice):
                    die_x = die_start_x + j * (DIE_SIZE + 10)
                    die_rect = pygame.Rect(die_x, self.game.height // 2 + 10, DIE_SIZE, DIE_SIZE)
                    draw_select_die(self.game, die_rect, die, selected=(j in self.selected_die_indices))
                    if die_rect.collidepoint(mouse_pos):
                        hover_die = j
                    self.die_rects.append(die_rect)
        else:
            no_dice_text = self.game.small_font.render("No dice needed – press Apply", True, THEME['text'])
            self.game.screen.blit(no_dice_text, (self.game.width // 2 - no_dice_text.get_width() // 2, self.game.height // 2))
            self.die_rects = []

        self.confirm_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
        draw_custom_button(self.game, self.confirm_rect, "Apply Rune",
                           is_hover=self.confirm_rect.collidepoint(mouse_pos))
        self.cancel_rect = pygame.Rect(self.game.width//2 - BUTTON_WIDTH//2 - 160, self.game.height - 100, BUTTON_WIDTH, BUTTON_HEIGHT)
        draw_custom_button(self.game, self.cancel_rect, "Cancel",
                           is_hover=self.cancel_rect.collidepoint(mouse_pos), is_red=True)

        if rune_rect.collidepoint(mouse_pos):
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20,
                         f"{self.rune['name']}: {self.rune['desc']}")
        elif hover_die != -1:
            die = self.random_dice[hover_die]
            lines = [f"{die.get('color', '?')} die"]
            tag = enhancement_label(die)
            if tag:
                lines.append(tag)
            for enh in die.get('enhancements') or []:
                lines.append(_enh_line(enh))
            draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, "\n".join(lines))

    def draw_dots_or_icon(self, die):  # Placeholder – replace with your pip code
        pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Die select if needed
            if self.max_dice > 0 and len(self.random_dice) > 0:
                for j, die_rect in enumerate(self.die_rects):
                    if die_rect.collidepoint(mouse_pos):
                        if j in self.selected_die_indices:
                            self.selected_die_indices.remove(j)
                        else:
                            self.selected_die_indices.append(j)
                        max_dice = self.max_dice
                        while len(self.selected_die_indices) > max_dice:
                            self.selected_die_indices.pop(0)  # Remove oldest
                        print(f"DEBUG: Selected die {j} – indices: {self.selected_die_indices}")  # TEMP
                        return
            # Confirm
            if self.confirm_rect.collidepoint(mouse_pos):
                dies = [self.random_dice[j] for j in self.selected_die_indices]  # Sync to dies
                print(f"DEBUG: Confirm rune {self.rune['name']} with {len(dies)} dice")  # TEMP
                self.game.apply_rune_effect(self.rune, dies)
                # FIXED: Always change_state, set resuming for enter skip
                self.game.last_state_was_rune = True  # Game entry flag
                previous = self.game.previous_state
                if previous is None:
                    from states.game import GameState
                    previous = GameState(self.game)
                self.game.state_machine.change_state(previous)
                self.game.last_state_was_rune = False  # FIXED: Reset after transition
                self.game.from_shop_rune_use = False  # FIXED: Reset after transition
                print("DEBUG: Rune applied, changed state with flags reset")  # TEMP
                return
            # Cancel (same)
            if self.cancel_rect.collidepoint(mouse_pos):
                # FIXED: Always change_state, set resuming
                self.game.last_state_was_rune = True  # FIXED: New flag
                previous = self.game.previous_state
                if previous is None:
                    from states.game import GameState
                    previous = GameState(self.game)
                self.game.state_machine.change_state(previous)
                print("DEBUG: Canceled, changed state to previous")  # TEMP
                return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Cancel back
                self.game.is_resuming = True  # FIXED: Set resuming
                previous = self.game.previous_state
                if previous is None:
                    from states.game import GameState
                    previous = GameState(self.game)
                self.game.state_machine.change_state(previous)
                return
# states/game.py
import pygame
import time
import math
from states.base import State  # Import from base
from states.shop import ShopState  # For transition after popup
from states.pause import PauseMenuState  # For ESC pause (adjust file if different)
from states.rune_use import RuneUseState  # For rune tray clicks (adjust if different)
from screens import draw_game_screen, draw_popup, draw_buttons, draw_tooltip, draw_enhancement_visuals
from constants import DEBUG, NUM_DICE_IN_HAND, THEME, DIE_SIZE, HELD_DIE_SCALE, CHARM_SIZE
from data import ENH_DESC
import savegame

class GameState(State):
    def __init__(self, game):
        super().__init__(game)
        self.reroll_rect = None
        self.discard_rect = None
        self.start_roll_rect = None
        self.score_rect = None
        self.end_turn_rect = None
        self.continue_rect = None  # For popup if shown
        self.hand_die_rects = []  # For 5 in-play dice
        self.bag_die_rects = []   # For bag visuals (upper right)
        self.tray_rects = []  # Store for click

    def enter(self):
        if self.game.is_resuming:
            print("Resuming GameState - Skipping init pull")  # Debug
            self.game.is_resuming = False
            return  # Skip dice pull
        # Init or reset game vars (call new_turn only if no loaded hand/rolls)
        if not self.game.hand or not self.game.rolls or not self.game.has_rolled:
            self.game.new_turn()

    def update(self, dt):
        # Handle animations/timers (e.g., break effects, temp messages)
        if self.game.break_effect_start:
            elapsed = time.time() - self.game.break_effect_start
            if elapsed > self.game.break_effect_duration:
                self.game.break_effect_start = 0  # Reset
                # Clear broken dice or other logic
        if self.game.temp_message_start:
            elapsed = time.time() - self.game.temp_message_start
            if elapsed > self.game.temp_message_duration:
                self.game.temp_message = None  # Fade out complete
        # Add more updates as needed (e.g., color cycling for rainbow)

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics and prevent stacking
        # Modified: Assume draw_game_screen now returns hand_rects, rolls, bag_rects, bag for animations
        hand_rects, rolls, bag_rects, bag = draw_game_screen(self.game)  # Main game elements + return data
        
        # Store rects for hover/clicks in handle_event
        self.hand_die_rects = hand_rects or []
        self.bag_die_rects = bag_rects or []
        
        # Add animations using returned data
        current_time = time.time()
        
        # For hand draw loop (using returned hand_rects and rolls)
        for i, die_rect in enumerate(hand_rects or []):
            if i < len(rolls):
                die, value = rolls[i]
                draw_enhancement_visuals(self.game, die_rect, die)  # Add this after element draw
                
                # Animation: Glow border if enhanced (skip for color/wild only)
                if die.get('enhancements') and any(e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild'] for e in die['enhancements']):
                    glow_color = (255, 255, 0) if math.sin(current_time * 3) > 0 else (255, 215, 0)  # Pulsing yellow
                    pygame.draw.rect(self.game.screen, glow_color, die_rect, 2)
        
        # For bag draw (grid loop, using returned bag_rects and bag)
        for i, small_rect in enumerate(bag_rects or []):
            if i < len(bag):
                die = bag[i]
                # Removed: draw_enhancement_visuals(self.game, small_rect, die)  # No icons in bag
                
                # Removed: If enhanced, subtle scale anim (skip for color/wild only)
                # No borders or pulses in bag

        if self.game.show_popup:
            self.continue_rect = draw_popup(self.game)  # Overlay popup
        else:
            self.reroll_rect, self.discard_rect, self.start_roll_rect, self.score_rect, self.end_turn_rect = draw_buttons(self.game)
        
        # Tooltip hover checks (after all draws)
        mouse_pos = pygame.mouse.get_pos()
        for i, die_rect in enumerate(hand_rects or []):
            if i < len(rolls) and die_rect.collidepoint(mouse_pos):
                die, _ = rolls[i]
                non_color_enh = [e for e in die.get('enhancements', []) if e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']]
                if non_color_enh:  # Only show if has non-color enh
                    enh_desc = ', '.join(ENH_DESC.get(e, e) for e in non_color_enh)
                    draw_tooltip(self.game, die_rect.x, die_rect.y + die_rect.height + 10, enh_desc or "No enhancements")

        for i, small_rect in enumerate(bag_rects or []):
            if i < len(bag) and small_rect.collidepoint(mouse_pos):
                die = bag[i]
                non_color_enh = [e for e in die.get('enhancements', []) if e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']]
                if non_color_enh:  # Only show if has non-color enh
                    enh_desc = ', '.join(ENH_DESC.get(e, e) for e in non_color_enh)
                    draw_tooltip(self.game, small_rect.x, small_rect.y + small_rect.height + 10, enh_desc or "No enhancements")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                
                print("Escape pressed in GameState - Pausing")  # Debug
                savegame.save_game(self.game)  # Save
                self.game.previous_state = self  # Instance
                self.game.state_machine.change_state(PauseMenuState(self.game))

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.game.show_popup:
                if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                    self.game.show_popup = False
                    self.game.advance_blind()
                    self.game.generate_shop()
                    self.game.state_machine.change_state(ShopState(self.game))
                    return

            # Dice clicks
            for i in range(NUM_DICE_IN_HAND):
                total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
                start_x = (self.game.width - total_dice_width) // 2
                x = start_x + i * (DIE_SIZE + 20)
                size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
                offset = (DIE_SIZE - DIE_SIZE * HELD_DIE_SCALE) / 2 if self.game.held[i] else 0
                die_rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
                if die_rect.collidepoint(mouse_pos):
                    if self.game.is_discard_phase:
                        self.game.toggle_discard(i)
                    else:
                        self.game.toggle_hold(i)

            # Button clicks
            if self.reroll_rect and self.reroll_rect.collidepoint(mouse_pos):
                self.game.reroll()
            if self.discard_rect and self.discard_rect.collidepoint(mouse_pos):
                self.game.discard()
            if self.start_roll_rect and self.start_roll_rect.collidepoint(mouse_pos):
                self.game.start_roll_phase()
            if DEBUG and self.score_rect and self.score_rect.collidepoint(mouse_pos):
                self.game.score_and_new_turn()
            if self.end_turn_rect and self.end_turn_rect.collidepoint(mouse_pos):
                self.game.score_and_new_turn()

            # Charm drag start
            for i in range(len(self.game.equipped_charms)):
                x = 50 + i * (CHARM_SIZE + 10)
                y = 10
                rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
                if rect.collidepoint(mouse_pos):
                    self.game.dragging_charm_index = i
                    self.game.dragging_shop = False
                    self.game.drag_offset_x = mouse_pos[0] - x
                    self.game.drag_offset_y = mouse_pos[1] - y
                    break

            # New: Tray click to use rune
            for i, tray_rect in enumerate(self.tray_rects):
                if tray_rect.collidepoint(mouse_pos) and self.game.rune_tray[i]:
                    rune = self.game.rune_tray[i]
                    # Prompt for die if max_dice > 0 (change to RuneUseState similar to Select)
                    self.game.state_machine.change_state(RuneUseState(self.game, rune))  # New state stub
                    self.game.rune_tray[i] = None  # Remove after use

        if event.type == pygame.MOUSEMOTION:
            if self.game.dragging_charm_index != -1:
                pass  # Handled in draw

            # New: Hover tooltips for dice
            mouse_pos = event.pos
            # Hover on 5 in-play dice (hand)
            for i, die_rect in enumerate(self.hand_die_rects):
                if die_rect.collidepoint(mouse_pos):
                    die = self.game.hand[i]  # Assuming self.game.hand is list of dice
                    if 'enhancements' in die and die['enhancements']:
                        desc = ''
                        for enh in die['enhancements']:
                            desc += f"{enh}: {ENH_DESC.get(enh, 'Unknown effect')}\n"
                        draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, desc.strip())
                    return  # Show one at a time; optional—remove if you want multiple

            # Hover on bag dice (upper right)
            for j, bag_rect in enumerate(self.bag_die_rects):
                if bag_rect.collidepoint(mouse_pos):
                    die = self.game.bag[j]  # Or your bag list/index
                    if 'enhancements' in die and die['enhancements']:
                        desc = ''
                        for enh in die['enhancements']:
                            desc += f"{enh}: {ENH_DESC.get(enh, 'Unknown effect')}\n"
                        draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, desc.strip())
                    return

        if event.type == pygame.MOUSEBUTTONUP:
            if self.game.dragging_charm_index != -1:
                mouse_pos = pygame.mouse.get_pos()
                target_index = -1
                for i in range(len(self.game.equipped_charms)):
                    x = 50 + i * (CHARM_SIZE + 10)
                    y = 10
                    rect = pygame.Rect(x, y, CHARM_SIZE, CHARM_SIZE)
                    if rect.collidepoint(mouse_pos):
                        target_index = i
                        break
                if target_index != -1 and target_index != self.game.dragging_charm_index:
                    self.game.equipped_charms[self.game.dragging_charm_index], self.game.equipped_charms[target_index] = self.game.equipped_charms[target_index], self.game.equipped_charms[self.game.dragging_charm_index]
                self.game.dragging_charm_index = -1
                self.game.dragging_shop = False
                # Remap disabled if swapped
                if self.game.dragging_charm_index in self.game.disabled_charms:
                    self.game.disabled_charms.remove(self.game.dragging_charm_index)
                    self.game.disabled_charms.append(target_index)
                elif target_index in self.game.disabled_charms:
                    self.game.disabled_charms.remove(target_index)
                    self.game.disabled_charms.append(self.game.dragging_charm_index)
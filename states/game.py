# states/game.py
import pygame
import time
import math
import random
from states.base import State  # Import from base
from screens import draw_game_screen, draw_popup, draw_buttons, draw_tooltip, draw_enhancement_visuals
from constants import DEBUG, NUM_DICE_IN_HAND, THEME, DIE_SIZE, HELD_DIE_SCALE, CHARM_SIZE, SMALL_DIE_SIZE, SMALL_DIE_SPACING, BAG_PADDING
from data import ENH_DESC
from states.shop import ShopState  # Add if not present
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
        self.hovered_hand_die = None  # Index for hand dice, or None
        self.hovered_bag_die = None   # Index for bag dice, or None
        self.hand_die_rects = []  # For 5 in-play dice
        self.bag_die_rects = []   # For bag visuals (upper right)
        self.tray_rects = []  # Store for click
        self.initial_auto_roll_done = False  # For auto-roll in rolling phase
        game.apply_boss_face_shuffle()  # Apply on resume/load into game state

    def enter(self):
        if self.game.is_resuming:
            print("Resuming GameState - Skipping init pull")  # Debug
            self.game.is_resuming = False
            return  # Skip dice pull
        # Init or reset game vars (call new_turn only if no loaded hand/rolls)
        print("DEBUG: GameState enter - checking conditions")
        if not self.game.hand or not self.game.rolls or not self.game.has_rolled:
            if self.game.turn_initialized and self.game.is_discard_phase:
                print("DEBUG: Resuming discard - skipping pull")
            else:
                self.game.new_turn()
        else:
            self.game.new_turn()  # If has hand but not rolled? Rare, but handle
        self.game.update_advantage_flag()  # Refresh after entering state
        
        # ADD: Force held reset after new_turn/roll
        self.game.held = [False] * NUM_DICE_IN_HAND
        print(f"Debug: Forced held reset in enter - held = {self.game.held}")
        
        # Robust reset for Fate's Favor: Always on new blind entry (after shop/return)
        self.game.used_fates_favor_this_blind = False
        self.game.fates_advantage_index = -1
        self.game.fates_advantage_value = None
        self.game.held_fates_advantage = False
        self.game.selecting_fates_die = False
        print("Debug: Reset Fate's Favor for new blind")

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

        # Trigger advantage roll after auto-roll in rolling phase (roll separate value, no overwrite)
        if not self.game.is_discard_phase and not self.initial_auto_roll_done:
            self.initial_auto_roll_done = True
            # Your auto-roll logic here (e.g., self.game.roll_dice())
            if self.game.has_advantage and self.game.advantage_value is None:
                self.game.original_center_value = self.game.rolls[2][1]  # Save original value
                self.game.advantage_value = random.randint(1, 6)  # Roll separate advantage value
                self.game.held_advantage = False
                print("Debug: Saved original center value:", self.game.original_center_value, "Rolled advantage:", self.game.advantage_value)
        # Add more updates as needed (e.g., color cycling for rainbow)

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics and prevent stacking
        from screens import draw_game_screen
        draw_game_screen(self.game)  # Call without assignment—main elements drawn inside
        # No flip here if it's in main loop; add if needed: pygame.display.flip()

        # Add animations using state data (from update_die_rects and game attrs)
        current_time = time.time()

        # For hand draw loop (using self.game.hand_die_rects and self.game.rolls)
        for i, die_rect in enumerate(self.game.hand_die_rects or []):
            if i < len(self.game.rolls):
                die, value = self.game.rolls[i]
                draw_enhancement_visuals(self.game, die_rect, die)  # Add this after element drawing
        # For bag draw (grid loop, using self.game.bag_die_rects and self.game.bag)
        for i, small_rect in enumerate(self.game.bag_die_rects or []):
            if i < len(self.game.bag):
                die = self.game.bag[i]
                # Removed: draw_enhancement_visuals(self.game, small_rect, die)  # No icons in bag

        if self.game.show_popup:
            self.continue_rect = draw_popup(self.game)  # Overlay popup
        else:
            self.reroll_rect, self.discard_rect, self.start_roll_rect, self.score_rect, self.end_turn_rect = draw_buttons(self.game)

        # Tooltip hover checks (after all draws)
        mouse_pos = pygame.mouse.get_pos()
        for i, die_rect in enumerate(self.game.hand_die_rects or []):
            if i < len(self.game.rolls) and die_rect.collidepoint(mouse_pos):
                die, _ = self.game.rolls[i]
                non_color_enh = [e for e in die.get('enhancements', []) if e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']]
                if non_color_enh:  # Only show if has non-color enh
                    enh_desc = ', '.join(ENH_DESC.get(e, e) for e in non_color_enh)
                    draw_tooltip(self.game, die_rect.x, die_rect.y + die_rect.height + 10, enh_desc or "No enhancements")

        for i, small_rect in enumerate(self.game.bag_die_rects or []):
            if i < len(self.game.bag) and small_rect.collidepoint(mouse_pos):
                die = self.game.bag[i]
                non_color_enh = [e for e in die.get('enhancements', []) if e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']]
                if non_color_enh:  # Only show if has non-color enh
                    enh_desc = ', '.join(ENH_DESC.get(e, e) for e in non_color_enh)
                    draw_tooltip(self.game, small_rect.x, small_rect.y + small_rect.height + 10, enh_desc or "No enhancements")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from states.pause import PauseMenuState  # Lazy import
                print("Escape pressed in GameState - Pausing")  # Debug
                savegame.save_game(self.game)  # Save
                self.game.previous_state = self  # Instance
                self.game.state_machine.change_state(PauseMenuState(self.game))

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()  # Moved to the top to ensure it's always defined
            if self.game.show_popup:
                if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                    from states.shop import ShopState  # Lazy import
                    self.game.show_popup = False
                    self.game.advance_blind()
                    self.game.generate_shop()
                    self.game.state_machine.change_state(ShopState(self.game))
                    return

            # Dice clicks (always check all, including center 3rd die first)
            for i in range(NUM_DICE_IN_HAND):
                total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
                start_x = (self.game.width - total_dice_width) // 2
                x = start_x + i * (DIE_SIZE + 20)
                size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
                offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
                die_rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
                if die_rect.collidepoint(mouse_pos):
                    if self.game.selecting_fates_die:
                        # Activate Fate's Favor advantage on this die
                        self.game.fates_advantage_index = i
                        self.game.fates_advantage_value = random.randint(1, 6)
                        self.game.held_fates_advantage = False  # Start unheld
                        self.game.used_fates_favor_this_blind = True
                        self.game.selecting_fates_die = False
                        if self.game.held[i]:
                            self.game.held[i] = False  # Mutual exclusion
                        self.game.update_hand_text()
                        print(f"Debug: Fate's Favor activated on die {i}, value: {self.game.fates_advantage_value}")
                        break
                    else:
                        if self.game.is_discard_phase:
                            self.game.toggle_discard(i)
                        else:
                            self.game.toggle_hold(i)
                            # ADDED: Exclusion for center die (i==2)
                            if i == 2 and self.game.held[2]:
                                self.game.held_advantage = False  # Unhold advantage if original held
                            print(f"Debug: Toggled die {i} - held[{i}] = {self.game.held[i]}")  # Debug for 3rd die
                        break  # Stop after handling one die click

            # Advantage choice clicks (after main dice, so original center is always checked first)
            if not self.game.is_discard_phase and self.game.has_advantage and self.game.advantage_value is not None:
                if self.game.advantage_die_rect and self.game.advantage_die_rect.collidepoint(mouse_pos):
                    self.game.held_advantage = not self.game.held_advantage  # Toggle advantage
                    if self.game.held_advantage and self.game.held[2]:
                        self.game.held[2] = False  # Unhold original if advantage held
                    print("Debug: Toggled advantage - held_advantage =", self.game.held_advantage, "held[2] =", self.game.held[2])
                    self.game.update_hand_text()  # Refresh preview score
                elif self.game.center_die_rect and self.game.center_die_rect.collidepoint(mouse_pos):
                    self.game.held[2] = not self.game.held[2]  # Toggle original
                    if self.game.held[2] and self.game.held_advantage:
                        self.game.held_advantage = False  # Unhold advantage if original held
                    print("Debug: Toggled original - held[2] =", self.game.held[2], "held_advantage =", self.game.held_advantage)
                    self.game.update_hand_text()  # Refresh preview score

            # Fate's Favor advantage toggle
            if not self.game.is_discard_phase and self.game.fates_advantage_index != -1 and self.game.fates_advantage_value is not None:
                fates_rect = getattr(self.game, 'fates_advantage_die_rect', None)  # Safe access
                if fates_rect is not None and fates_rect.collidepoint(mouse_pos):
                    self.game.held_fates_advantage = not self.game.held_fates_advantage
                    if self.game.held_fates_advantage and self.game.held[self.game.fates_advantage_index]:
                        self.game.held[self.game.fates_advantage_index] = False
                    self.game.update_hand_text()
                    print(f"Debug: Toggled Fate's advantage - held_fates_advantage = {self.game.held_fates_advantage}, held[{self.game.fates_advantage_index}] = {self.game.held[self.game.fates_advantage_index]}")
                # No optional original here—handled in toggle_hold below
            
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
                    charm = self.game.equipped_charms[i]  # Define charm inside rect check
                    if charm['name'] == "Fate's Favor" and i not in self.game.disabled_charms and not self.game.used_fates_favor_this_blind and not self.game.is_discard_phase:
                        self.game.selecting_fates_die = True
                        print("Debug: Entered Fate's Favor selection mode")
                        break  # No drag if activating
                    else:
                        # Existing drag code
                        self.game.dragging_charm_index = i
                        self.game.dragging_shop = False
                        self.game.drag_offset_x = mouse_pos[0] - x
                        self.game.drag_offset_y = mouse_pos[1] - y
                        break  # Break after drag start

            for i, tray_rect in enumerate(self.tray_rects):
                if tray_rect.collidepoint(mouse_pos) and self.game.rune_tray[i]:
                    from states.rune import RuneUseState  # Lazy import
                    rune = self.game.rune_tray[i]
                    # Prompt for die if max_dice > 0 (change to RuneUseState similar to Select)
                    self.game.state_machine.change_state(RuneUseState(self.game, rune))  # New state stub
                    self.game.rune_tray[i] = None  # Remove after use

        if event.type == pygame.MOUSEMOTION:
            if self.game.dragging_charm_index != -1:
                pass  # Handled in draw

            mouse_pos = pygame.mouse.get_pos()  # Moved inside motion for consistency
            self.game.hovered_hand_die = None
            self.game.hovered_bag_die = None

            self.update_die_rects()  # Calc rects here for fresh positions

            # Hover on hand dice
            for i, die_rect in enumerate(self.game.hand_die_rects):
                if die_rect.collidepoint(mouse_pos):
                    self.game.hovered_hand_die = i
                    break

            # Hover on bag dice
            for j, bag_rect in enumerate(self.game.bag_die_rects):
                if bag_rect.collidepoint(mouse_pos):
                    self.game.hovered_bag_die = j
                    break

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

    def update_die_rects(self):
        # Hand dice rects (from your draw_dice logic)
        self.game.hand_die_rects = []
        for i in range(NUM_DICE_IN_HAND):
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
            offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
            rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
            self.game.hand_die_rects.append(rect)

        # ADD: Set Fate's advantage rect if active (for clicking)
        if self.game.fates_advantage_index != -1 and self.game.fates_advantage_value is not None:
            i = self.game.fates_advantage_index
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            adv_y = (self.game.height - DIE_SIZE - 100) - DIE_SIZE - 10
            adv_size = DIE_SIZE * HELD_DIE_SCALE if self.game.held_fates_advantage else DIE_SIZE
            adv_offset = (DIE_SIZE - adv_size) / 2 if self.game.held_fates_advantage else 0
            self.game.fates_advantage_die_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
            print(f"Debug: Set fates_advantage_die_rect = {self.game.fates_advantage_die_rect}")  # Confirm set

        # Bag dice rects (existing)
        self.game.bag_die_rects = []
        columns = 5
        rows = math.ceil(len(self.game.bag) / columns) if self.game.bag else 1
        bag_width = columns * (SMALL_DIE_SIZE + SMALL_DIE_SPACING) - SMALL_DIE_SPACING + BAG_PADDING * 2
        bag_x = self.game.width - bag_width - 20
        bag_y = 50
        for j in range(len(self.game.bag)):
            col = j % columns
            row = j // columns
            small_x = bag_x + BAG_PADDING + col * (SMALL_DIE_SIZE + SMALL_DIE_SPACING)
            small_y = bag_y + BAG_PADDING + row * (SMALL_DIE_SIZE + SMALL_DIE_SPACING)
            rect = pygame.Rect(small_x, small_y, SMALL_DIE_SIZE, SMALL_DIE_SIZE)
            self.game.bag_die_rects.append(rect)
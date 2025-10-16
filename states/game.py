# states/game.py
import pygame
import time
import math
from states.base import State  # Import from base
from screens import draw_game_screen, draw_popup, draw_buttons, draw_tooltip, draw_enhancement_visuals
from constants import DEBUG, NUM_DICE_IN_HAND, THEME, DIE_SIZE, HELD_DIE_SCALE, CHARM_SIZE, SMALL_DIE_SIZE, SMALL_DIE_SPACING, BAG_PADDING
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
        self.hovered_hand_die = None  # Index for hand dice, or None
        self.hovered_bag_die = None   # Index for bag dice, or None
        self.hand_die_rects = []  # For 5 in-play dice
        self.bag_die_rects = []   # For bag visuals (upper right)
        self.tray_rects = []  # Store for click
        game.apply_boss_face_shuffle()  # Apply on resume/load into game state

    def enter(self):
        if self.game.is_resuming:
            print("Resuming GameState - Skipping init pull")  # Debug
            self.game.is_resuming = False
            return  # Skip dice pull
        # Init or reset game vars (call new_turn only if no loaded hand/rolls)
        print("DEBUG: GameState.enter - checking conditions")
        if not self.game.hand or not self.game.rolls or not self.game.has_rolled:
            if self.game.turn_initialized and self.game.is_discard_phase:
                print("DEBUG: Resuming discard - skipping pull")
            else:
                self.game.new_turn()
        else:
            self.game.new_turn()  # If has hand but not rolled? Rare, but handle

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
        from screens import draw_game_screen
        draw_game_screen(self.game)  # Call without assignment—main elements drawn inside
        # No flip here if it's in main loop; add if needed: pygame.display.flip()

        # Add animations using state data (from update_die_rects and game attrs)
        current_time = time.time()

        # For hand draw loop (using self.game.hand_die_rects and self.game.rolls)
        for i, die_rect in enumerate(self.game.hand_die_rects or []):
            if i < len(self.game.rolls):
                die, value = self.game.rolls[i]
                draw_enhancement_visuals(self.game, die_rect, die)  # Add this after element draw
                
                # Animation: Glow border if enhanced (skip for color/wild only)
                # if die.get('enhancements') and any(e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild'] for e in die['enhancements']):
                    # glow_color = (255, 255, 0) if math.sin(current_time * 3) > 0 else (255, 215, 0)  # Pulsing yellow
                    # pygame.draw.rect(self.game.screen, glow_color, die_rect, 2)
        
        # For bag draw (grid loop, using self.game.bag_die_rects and self.game.bag)
        for i, small_rect in enumerate(self.game.bag_die_rects or []):
            if i < len(self.game.bag):
                die = self.game.bag[i]
                # Removed: draw_enhancement_visuals(self.game, small_rect, die)  # No icons in bag
                
                # Removed: If enhanced, subtle scale anim (skip for color/wild only)
                # No borders or pulses in bag

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
            mouse_pos = pygame.mouse.get_pos()
            if self.game.show_popup:
                if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                    from states.shop import ShopState  # Lazy import
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

            mouse_pos = event.pos
            self.game.hovered_hand_die = None
            self.game.hovered_bag_die = None

            self.update_die_rects()  # Calc rects here for fresh positions

            # Hover on hand dice
            for i, die_rect in enumerate(self.game.hand_die_rects):
                if die_rect.collidepoint(mouse_pos):
                    self.game.hovered_hand_die = i
                    #  print(f"Hover detected on hand die {i} at {die_rect}")  # Debug: Confirm rect and trigger
                    break

            # Hover on bag dice
            for j, bag_rect in enumerate(self.game.bag_die_rects):
                if bag_rect.collidepoint(mouse_pos):
                    self.game.hovered_bag_die = j
                    #  print(f"Hover detected on bag die {j} at {bag_rect}")  # Debug
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

    # In class GameState
    def update_die_rects(self):
        # Hand dice rects (from your draw_dice logic)
        #  print("Updating die rects")  # Temp debug—remove later
        self.game.hand_die_rects = []
        for i in range(NUM_DICE_IN_HAND):
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
            offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
            rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
            self.game.hand_die_rects.append(rect)

        # Bag dice rects (from your draw_game_screen bag loop)
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
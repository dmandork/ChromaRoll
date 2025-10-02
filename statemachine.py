# statemachine.py
import os
import pygame
import time
import sys
import copy
import random
import savegame
from screens import draw_splash_screen, draw_init_screen, draw_tutorial_screen, draw_blinds_screen, draw_game_screen, draw_popup, draw_buttons, draw_shop_screen, draw_game_over_screen, draw_pause_menu, draw_custom_button, draw_tooltip  # Import at top of file
from constants import *  # For SPLASH_* constants
from utils import get_easing, draw_rounded_element, wrap_text, resource_path  # Import get_easing to fix "not defined" errors
from data import BOSS_EFFECTS, HAND_TYPES, CHARMS_POOL
from constants import BASE_COLORS, DICE_FACES, NUM_DICE_IN_HAND, DIE_SIZE, HELD_DIE_SCALE, THEME, DEBUG, CHARM_SIZE, CHARM_BOX_WIDTH, CHARM_SPACING, CHARM_BOX_HEIGHT, SPECIAL_COLORS, PACK_BOOST
import constants  # This imports the module, so you can use constants.THEME
import data


class State:
    def __init__(self, game):
        self.game = game  # Reference to ChromaRollGame for shared state (e.g., self.game.coins)

    def enter(self):
        pass  # Optional: Setup when entering (e.g., reset timers)

    def exit(self):
        pass  # Optional: Cleanup when leaving (e.g., stop sounds)

    def update(self, dt):
        pass  # Game logic/timers/animations

    def draw(self):
        pass  # Render the screen

    def handle_event(self, event):
        pass  # Handle inputs/events

class StateMachine:
    def __init__(self, game, initial_state):
        self.game = game
        self.current_state = initial_state
        self.current_state.enter()

    def change_state(self, new_state):
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()

    def update(self, dt):
        self.current_state.update(dt)

    def draw(self):
        self.current_state.draw()

    def handle_event(self, event):
        self.current_state.handle_event(event)

class SplashState(State):
    def __init__(self, game):
        super().__init__(game)
        self.new_game_rect = None
        self.load_game_rect = None
        self.quit_rect = None  # Store rects as instance vars for handle_event access

    def enter(self):
        self.game.splash_start_time = 0
        if not hasattr(self.game, 'splash_total_start') or self.game.splash_total_start == 0:
            self.game.splash_total_start = 0
        self.game.splash_phase = 'pan'

    def update(self, dt):
        # Moved from old run()'s splash block: Timing and phase logic
        current_time = time.time()
        if self.game.splash_start_time == 0:
            self.game.splash_start_time = current_time
        if self.game.splash_total_start == 0:
            self.game.splash_total_start = current_time

        time_elapsed = current_time - self.game.splash_start_time
        total_elapsed = current_time - self.game.splash_total_start

        # Your full panning/zoom/phase code here (copy from screens.py or old run())
        # Example (adapt your full logic):
        image_width, image_height = self.game.splash_image.get_size()
        current_zoom = SPLASH_INITIAL_ZOOM
        visible_height = self.game.height / current_zoom
        focus_y = 0

        if self.game.splash_phase == 'pan':
            progress = min(time_elapsed / SPLASH_DURATION_PAN, 1.0)
            easing_progress = get_easing(progress, SPLASH_EASING)
            start_focus_y = image_height - visible_height / 2
            end_focus_y = visible_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress
            if time_elapsed >= SPLASH_DURATION_PAN:
                self.game.splash_phase = 'hold'
                self.game.splash_start_time = current_time

        elif self.game.splash_phase == 'hold':
            visible_height = self.game.height / SPLASH_INITIAL_ZOOM
            focus_y = visible_height / 2
            if time_elapsed >= SPLASH_DURATION_HOLD:
                self.game.splash_phase = 'zoom_out'
                self.game.splash_start_time = current_time

        elif self.game.splash_phase == 'zoom_out':
            progress = min(time_elapsed / SPLASH_DURATION_ZOOM_OUT, 1.0)
            easing_progress = get_easing(progress, SPLASH_EASING)
            fit_zoom = self.game.height / image_height
            current_zoom = SPLASH_INITIAL_ZOOM - (SPLASH_INITIAL_ZOOM - fit_zoom) * easing_progress
            visible_height = self.game.height / current_zoom
            start_focus_y = (self.game.height / SPLASH_INITIAL_ZOOM) / 2
            end_focus_y = image_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress
            if time_elapsed >= SPLASH_DURATION_ZOOM_OUT:
                self.game.splash_phase = 'done'

        elif self.game.splash_phase == 'done':
            fit_zoom = self.game.height / image_height
            current_zoom = fit_zoom
            visible_height = self.game.height / current_zoom
            focus_y = image_height / 2

        # Add view_y calculation, etc. (your full block)
        # ...

        # Auto-transition if total time up (or button logic in handle_event)
        total_duration = SPLASH_DURATION_PAN + SPLASH_DURATION_HOLD + SPLASH_DURATION_ZOOM_OUT
        if total_elapsed >= total_duration:
            self.game.splash_phase = 'done'  # Ensure 'done'

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        rects = draw_splash_screen(self.game)
        if rects is not None:
            self.new_game_rect, self.load_game_rect, self.quit_rect = rects

    def handle_event(self, event):
        # Moved from old run()'s event blocks for splash
        if event.type == pygame.KEYDOWN:
            if event.key in SPLASH_SKIP_KEYS:
                self.game.splash_phase = 'done'  # Skip

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.game.splash_phase == 'done':
                # Use stored rects from draw()
                if self.new_game_rect and self.new_game_rect.collidepoint(mouse_pos):
                    if os.path.exists('save.json'):  # Direct check instead of load_game return
                        print("Save found, showing prompt")
                        self.game.state_machine.change_state(PromptState(self.game))
                    else:
                        print("No save, starting new")
                        self.game.state_machine.change_state(InitState(self.game))
                    pass
                elif self.quit_rect and self.quit_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
            else:
                self.game.splash_phase = 'done'  # Jump to done on click

class InitState(State):
    def enter(self):
        # New: Re-set temp_message start if message is pending (for timing fix)
        if self.game.temp_message:
            self.game.temp_message_start = time.time()  # Reset timer on enter
            print("DEBUG: Re-set temp_message_start in InitState")  # Confirm (remove after)
        self.game.pouch_offset = 0  # Reset if needed
        self.pouch_rects = None
        self.tutorial_rect = None
        self.left_arrow_rect = None
        self.right_arrow_rect = None  # Store for handle_event

    def update(self, dt):
        pass  # No animations? Leave empty or add if carousel animates

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        self.pouch_rects, self.tutorial_rect, self.left_arrow_rect, self.right_arrow_rect = draw_init_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for idx, rect in enumerate(self.pouch_rects or []):
                if rect.collidepoint(mouse_pos):
                    pouch = data.POUCHES[self.game.pouch_offset + idx]
                    if pouch.get('unlocked', False):
                        self.game.apply_pouch(pouch)
                        self.game.state_machine.change_state(BlindsState(self.game))  # To 'blinds'
                    break
            if self.tutorial_rect and self.tutorial_rect.collidepoint(mouse_pos):
                self.game.tutorial_mode = True
                self.game.tutorial_step = 0
                self.game.state_machine.change_state(TutorialState(self.game))  # To 'tutorial'
            if self.left_arrow_rect and self.left_arrow_rect.collidepoint(mouse_pos):
                self.game.pouch_offset = max(0, self.game.pouch_offset - 4)
            if self.right_arrow_rect and self.right_arrow_rect.collidepoint(mouse_pos):
                if self.pouch_rects and self.game.pouch_offset < len(data.POUCHES) - len(self.pouch_rects):
                    self.game.pouch_offset += 4 

class TutorialState(State):
    def __init__(self, game):
        super().__init__(game)
        self.left_rect = None
        self.right_rect = None
        self.skip_rect = None

    def enter(self):
        self.game.tutorial_step = 0  # Reset to beginning

    def update(self, dt):
        pass  # No ongoing animations? Leave empty

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        self.left_rect, self.right_rect, self.skip_rect = draw_tutorial_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.game.tutorial_step = min(5, self.game.tutorial_step + 1)  # Next, clamp to max
                if self.game.tutorial_step > 5:
                    self.game.tutorial_completed = True
                    self.game.tutorial_mode = False
                    self.game.state_machine.change_state(InitState(self.game))
            elif event.key == pygame.K_BACKSPACE:  # Optional: Key for back
                self.game.tutorial_step = max(0, self.game.tutorial_step - 1)
            elif event.key == pygame.K_ESCAPE:
                self.game.tutorial_completed = True
                self.game.tutorial_mode = False
                self.game.state_machine.change_state(InitState(self.game))  # Skip

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.left_rect and self.left_rect.collidepoint(mouse_pos):
                self.game.tutorial_step = max(0, self.game.tutorial_step - 1)  # Back
            if self.right_rect and self.right_rect.collidepoint(mouse_pos):
                self.game.tutorial_step += 1
                if self.game.tutorial_step > 5:
                    self.game.tutorial_completed = True
                    self.game.tutorial_mode = False
                    self.game.state_machine.change_state(InitState(self.game))
            if self.skip_rect and self.skip_rect.collidepoint(mouse_pos):
                self.game.tutorial_completed = True
                self.game.tutorial_mode = False
                self.game.state_machine.change_state(InitState(self.game))  # Skip

class BlindsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.continue_rect = None
        self.debug_button_rect = None
        self.up_rect = None
        self.down_rect = None
        self.debug_jump_rect = None
        # For item rects in dropdown (since dynamic, recalculate in handle_event)

    def enter(self):
        # Reset any blinds-specific vars (e.g., debug states)
        self.game.debug_boss_dropdown_open = False  # If not already reset
        self.game.debug_boss_scroll_offset = 0
        # Conditional: Generate upcoming boss only if None (fix randomize every entry)
        if self.game.upcoming_boss_effect is None:
            self.game.upcoming_boss_effect = random.choice(BOSS_EFFECTS)

    def update(self, dt):
        pass  # No ongoing updates? Leave empty

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        self.continue_rect, self.debug_button_rect, self.up_rect, self.down_rect, self.debug_jump_rect = draw_blinds_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                # Clear old turn state for new blind
                self.game.hand = []
                self.game.rolls = []
                self.game.held = [False] * constants.NUM_DICE_IN_HAND
                self.game.discard_selected = [False] * constants.NUM_DICE_IN_HAND
                self.game.is_discard_phase = True  # Start with discard
                self.game.has_rolled = False
                self.game.bag[:] = [copy.deepcopy(d) for d in self.game.full_bag]  # Refill bag
                self.game.state_machine.change_state(GameState(self.game))
                return

            if DEBUG:
                if self.debug_button_rect and self.debug_button_rect.collidepoint(mouse_pos):
                    self.game.debug_boss_dropdown_open = not self.game.debug_boss_dropdown_open  # Toggle panel

                if self.game.debug_boss_dropdown_open:
                    if self.up_rect and self.up_rect.collidepoint(mouse_pos):
                        self.game.debug_boss_scroll_offset = max(0, self.game.debug_boss_scroll_offset - 1)
                    if self.down_rect and self.down_rect.collidepoint(mouse_pos):
                        self.game.debug_boss_scroll_offset = min(len(BOSS_EFFECTS) - (300 // 25), self.game.debug_boss_scroll_offset + 1)  # Hardcode as in old code

                    # Click on item: Recalculate item rects (since dynamic)
                    panel_x, panel_y = self.debug_button_rect.x - 300, self.debug_button_rect.y - 300  # Match draw position
                    item_height = 25
                    for i in range(self.game.debug_boss_scroll_offset, min(self.game.debug_boss_scroll_offset + (300 // item_height), len(BOSS_EFFECTS))):
                        item_rect = pygame.Rect(panel_x, panel_y + (i - self.game.debug_boss_scroll_offset) * item_height, 370, item_height)  # Full row clickable
                        if item_rect.collidepoint(mouse_pos):
                            self.game.upcoming_boss_effect = BOSS_EFFECTS[i]
                            self.game.debug_boss_dropdown_open = False  # Close on select
                            break

                if self.debug_jump_rect and self.debug_jump_rect.collidepoint(mouse_pos):
                    self.game.current_blind = 'Boss'
                    self.game.current_boss_effect = self.game.upcoming_boss_effect or random.choice(BOSS_EFFECTS)  # Activate preview or random
                    # Quick reset states (mimic advance_blind)
                    self.game.disabled_charms = []
                    self.game.boss_reroll_count = 0
                    self.game.boss_rainbow_color = None
                    self.game.boss_shuffled_faces = {}
                    # Apply effect setups (copy from advance_blind 'Boss' block)
                    effect_name = self.game.current_boss_effect['name']
                    if effect_name == 'Charm Glitch' and self.game.equipped_charms:
                        self.game.disabled_charms = [random.randint(0, len(self.game.equipped_charms) - 1)]
                    elif effect_name == 'Charm Eclipse':
                        self.game.disabled_charms = list(range(len(self.game.equipped_charms)))
                    elif effect_name == 'Rainbow Restriction':
                        self.game.boss_rainbow_color = random.choice(BASE_COLORS)
                    elif effect_name == 'Face Shuffle':
                        for die in self.game.full_bag:
                            faces = DICE_FACES[:]
                            random.shuffle(faces)
                            self.game.boss_shuffled_faces[die['id']] = faces
                    elif effect_name == 'Charm Tax':
                        tax = len(self.game.equipped_charms) // 2
                        self.game.hands_left = max(0, self.game.hands_left - tax)
                    elif effect_name == 'Hand Trim':
                        self.game.hands_left = max(0, self.game.hands_left - 1)
                    elif effect_name == 'Reroll Ration':
                        self.game.rerolls_left = max(0, self.game.rerolls_left - 1)
                    elif effect_name == 'Discard Drought':
                        self.game.discards_left = max(0, self.game.discards_left - 1)
                    elif effect_name == 'Blind Boost':
                        self.game.discards_left += 1
                    # Reset round elements
                    self.game.round_score = 0
                    self.game.bag[:] = [copy.deepcopy(d) for d in self.game.full_bag]  # Refill
                    self.game.state_machine.change_state(GameState(self.game))  # Jump to 'game'
                    self.game.new_turn()  # Start Boss turn

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
        self.game.screen.fill(constants.THEME['background'])  # Clear relics and prevent stacking
        from screens import draw_game_screen
        draw_game_screen(self.game)  # Main game elements

        if self.game.show_popup:
            self.continue_rect = draw_popup(self.game)  # Overlay popup
        else:
            self.reroll_rect, self.discard_rect, self.start_roll_rect, self.score_rect, self.end_turn_rect = draw_buttons(self.game)

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
                            desc += f"{enh}: {data.ENH_DESC.get(enh, 'Unknown effect')}\n"
                        draw_tooltip(self.game, mouse_pos[0], mouse_pos[1] + 20, desc.strip())
                    return  # Show one at a time; optional—remove if you want multiple

            # Hover on bag dice (upper right)
            for j, bag_rect in enumerate(self.bag_die_rects):
                if bag_rect.collidepoint(mouse_pos):
                    die = self.game.bag[j]  # Or your bag list/index
                    if 'enhancements' in die and die['enhancements']:
                        desc = ''
                        for enh in die['enhancements']:
                            desc += f"{enh}: {data.ENH_DESC.get(enh, 'Unknown effect')}\n"
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

class ShopState(State):
    def __init__(self, game):
        super().__init__(game)
        self.continue_rect = None
        self.sell_rects = None
        self.buy_rects = None
        self.equipped_rects = None
        self.shop_rects = None
        self.pack_rects = None
        self.reroll_rect = None
        self.debug_rect = None  # For debug button
        self.debug_panel_open = False  # Flag for debug panel
        self.scroll_y = 0  # For debug panel scrolling
        self.charm_rects = []  # Store debug panel rects

    def enter(self):
        # Generate shop if empty
        if not self.game.shop_charms:
            self.game.generate_shop()
        self.debug_panel_open = False  # Reset panel
        self.scroll_y = 0  # Reset scroll

    def update(self, dt):
        pass  # Expand for animations if needed

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        # Draw shop, but pass debug_panel_open to skip tooltips when panel is open
        self.continue_rect, self.sell_rects, self.buy_rects, self.equipped_rects, self.shop_rects, self.pack_rects, self.reroll_rect = draw_shop_screen(self.game, skip_tooltips=self.debug_panel_open)
        
        # Debug button (bottom-right to avoid prism packs)
        if constants.DEBUG:
            button_x = self.game.width - constants.DEBUG_BUTTON_SIZE[0] - 50  # Bottom-right
            button_y = self.game.height - constants.DEBUG_BUTTON_SIZE[1] - 50
            self.debug_rect = pygame.Rect(button_x, button_y, *constants.DEBUG_BUTTON_SIZE)
            draw_custom_button(self.game, self.debug_rect, constants.DEBUG_BUTTON_TEXT, 
                              is_hover=self.debug_rect.collidepoint(pygame.mouse.get_pos()))
            
            # Draw debug panel if open
            if self.debug_panel_open:
                self.charm_rects = self.draw_debug_panel()
            else:
                self.charm_rects = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.previous_state = self.game.state_machine.current_state
                self.game.state_machine.change_state(PauseMenuState(self.game))
            elif constants.DEBUG and self.debug_panel_open:
                # Keyboard scrolling
                icons_per_row = 4
                row_height = 100 + 50  # Match draw_debug_panel
                num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
                total_content_height = num_rows * row_height + 70
                max_scroll = max(0, total_content_height - constants.DEBUG_PANEL_HEIGHT)
                if event.key == pygame.K_UP:
                    self.scroll_y = max(0, self.scroll_y - 50)
                elif event.key == pygame.K_DOWN:
                    self.scroll_y = min(self.scroll_y + 50, max_scroll)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle debug button
            if constants.DEBUG and self.debug_rect and self.debug_rect.collidepoint(mouse_pos):
                self.debug_panel_open = not self.debug_panel_open
                print(f"DEBUG: Panel {'opened' if self.debug_panel_open else 'closed'}")
                return
            
            # Handle debug panel interactions
            if constants.DEBUG and self.debug_panel_open:
                for rect, action in self.charm_rects:
                    if rect.collidepoint(mouse_pos):
                        if action == 'close':
                            self.debug_panel_open = False
                            self.game.temp_message = "Debug panel closed"
                            self.game.temp_message_start = time.time()
                        elif action == 'equip_all':
                            for charm in data.CHARMS_POOL:
                                if charm['name'] not in [c['name'] for c in self.game.equipped_charms] and len(self.game.equipped_charms) < self.game.max_charms * 2:
                                    self.game.equipped_charms.append(copy.deepcopy(charm))
                            print("DEBUG: Equipped all available charms!")
                            self.game.temp_message = "Equipped all possible charms!"
                            self.game.temp_message_start = time.time()
                        elif action and len(self.game.equipped_charms) < self.game.max_charms * 2:
                            if any(c['name'] == action['name'] for c in self.game.equipped_charms):
                                print(f"DEBUG: {action['name']} already owned")
                                self.game.temp_message = f"{action['name']} already owned!"
                            else:
                                self.game.equipped_charms.append(copy.deepcopy(action))
                                print(f"DEBUG: Added {action['name']} (free)")
                                self.game.temp_message = f"Added {action['name']}!"
                            self.game.temp_message_start = time.time()
                        else:
                            print("DEBUG: Max charms reached")
                            self.game.temp_message = "No charm slots left!"
                            self.game.temp_message_start = time.time()
                        return
            
            # Handle continue
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                self.game.shop_charms = []  # Clear shop
                self.game.state_machine.change_state(BlindsState(self.game))
                return

            # Handle sell
            for i, sell_rect in enumerate(self.sell_rects or []):
                if sell_rect.collidepoint(mouse_pos):
                    self.game.confirm_sell_index = i
                    self.game.state_machine.change_state(ConfirmSellState(self.game))
                    return

            # Handle buy charms
            for i, buy_rect in enumerate(self.buy_rects or []):
                if buy_rect.collidepoint(mouse_pos):
                    charm = self.game.shop_charms.pop(i)
                    cost = charm['cost']
                    has_debt = any(c['type'] == 'negative_coins' for c in self.game.equipped_charms)
                    min_coins = -5 if has_debt else 0
                    if len(self.game.equipped_charms) < self.game.max_charms and self.game.coins - cost >= min_coins:
                        self.game.equipped_charms.append(charm)
                        self.game.coins -= cost
                        if self.game.current_boss_effect and self.game.current_boss_effect['name'] == 'Charm Eclipse':
                            self.game.disabled_charms = list(range(len(self.game.equipped_charms)))
                    else:
                        self.game.shop_charms.insert(i, charm)
                    return

             # Pack buys
            pack_costs = [3, 5, 7, 3, 5, 9, 4, 7, 9]  # Append rune pack costs
            pack_choices_num = [2, 3, 5, 3, 4, 3, 3, 5, 5]  # Append rune pack choices
            pack_select_num = [1, 1, 1, 1, 1, 1, 1, 1, 2]  # New: Select counts (1 for most, 2 for Super Rune)
            for pack_rect, pack_idx in self.pack_rects or []:
                if pack_rect.collidepoint(mouse_pos):
                    cost = pack_costs[pack_idx]
                    has_debt = any(c['type'] == 'negative_coins' for c in self.game.equipped_charms)
                    min_coins = -5 if has_debt else 0
                    if self.game.coins - cost >= min_coins:
                        self.game.coins -= cost
                        if pack_idx in [0, 1, 2]:
                            self.game.pack_choices = random.sample(data.HAND_TYPES, pack_choices_num[pack_idx])
                            self.game.state_machine.change_state(PackSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                        elif pack_idx in [3, 4, 5]:
                            if pack_idx == 5:
                                self.game.pack_choices = random.sample(constants.SPECIAL_COLORS, pack_choices_num[pack_idx])
                            else:
                                self.game.pack_choices = random.sample(constants.BASE_COLORS, pack_choices_num[pack_idx])
                            self.game.state_machine.change_state(DiceSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                        elif pack_idx in [6, 7, 8]:  # New: Rune packs
                            rune_pack = data.RUNE_PACKS[pack_idx - 6]  # Map to 0-2 index
                            self.game.pack_choices = random.sample(data.MYSTIC_RUNES, pack_choices_num[pack_idx])
                            self.game.pack_select_count = pack_select_num[pack_idx]  # Track how many to select
                            self.game.selected_runes = []  # For multi-select/holding
                            self.game.state_machine.change_state(RuneSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                    return

            # Reroll
            if self.reroll_rect and self.reroll_rect.collidepoint(mouse_pos):
                self.game.reroll_shop()
                return

            # Charm drag start
            for i in range(len(self.game.equipped_charms)):
                x = 50 + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
                y = 150
                rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
                if rect.collidepoint(mouse_pos):
                    self.game.dragging_charm_index = i
                    self.game.dragging_shop = True
                    self.game.drag_offset_x = mouse_pos[0] - x
                    self.game.drag_offset_y = mouse_pos[1] - y
                    break

        if event.type == pygame.MOUSEWHEEL and constants.DEBUG and self.debug_panel_open:
            icons_per_row = 4
            row_height = 100 + 50  # Match draw_debug_panel
            num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
            total_content_height = num_rows * row_height + 70
            scroll_speed = 50
            self.scroll_y -= event.y * scroll_speed
            max_scroll = max(0, total_content_height - constants.DEBUG_PANEL_HEIGHT)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        if event.type == pygame.MOUSEMOTION:
            if self.game.dragging_charm_index != -1:
                pass  # Dragging handled in draw_shop_screen

        if event.type == pygame.MOUSEBUTTONUP:
            if self.game.dragging_charm_index != -1:
                mouse_pos = pygame.mouse.get_pos()
                target_index = -1
                for i in range(len(self.game.equipped_charms)):
                    x = 50 + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
                    y = 150
                    rect = pygame.Rect(x, y, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
                    if rect.collidepoint(mouse_pos):
                        target_index = i
                        break
                if target_index != -1 and target_index != self.game.dragging_charm_index:
                    self.game.equipped_charms[self.game.dragging_charm_index], self.game.equipped_charms[target_index] = \
                        self.game.equipped_charms[target_index], self.game.equipped_charms[self.game.dragging_charm_index]
                self.game.dragging_charm_index = -1
                self.game.dragging_shop = False

    def draw_debug_panel(self):
        """Draws the debug panel with improved spacing and text readability."""
        panel_rect = pygame.Rect(constants.DEBUG_PANEL_X, constants.DEBUG_PANEL_Y, 
                               constants.DEBUG_PANEL_WIDTH, constants.DEBUG_PANEL_HEIGHT)
        pygame.draw.rect(self.game.screen, (0, 0, 0), panel_rect, 3)
        overlay = pygame.Surface((constants.DEBUG_PANEL_WIDTH, constants.DEBUG_PANEL_HEIGHT))
        overlay.fill((40, 40, 40))
        overlay.set_alpha(200)
        self.game.screen.blit(overlay, (constants.DEBUG_PANEL_X, constants.DEBUG_PANEL_Y))
        
        title_text = self.game.font.render("Debug: All Charms (Click to Equip)", True, constants.THEME['text'])
        self.game.screen.blit(title_text, (constants.DEBUG_PANEL_X + 20, constants.DEBUG_PANEL_Y + 20))
        
        icons_per_row = 4
        icon_size = 100
        spacing = 30
        row_height = icon_size + 50
        num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
        total_content_height = num_rows * row_height + 70
        
        start_x = constants.DEBUG_PANEL_X + 20
        start_y = constants.DEBUG_PANEL_Y + 70 - self.scroll_y
        mouse_pos = pygame.mouse.get_pos()
        visible_start_row = max(0, int(self.scroll_y / row_height))
        visible_rows_to_draw = (constants.DEBUG_PANEL_HEIGHT - 70) // row_height + 2
        visible_end_row = min(num_rows, visible_start_row + visible_rows_to_draw)
        
        charm_rects = []
        tooltips_to_draw = []  # Collect tooltips to draw last
        
        for row in range(visible_start_row, visible_end_row):
            for col in range(icons_per_row):
                i = row * icons_per_row + col
                if i >= len(data.CHARMS_POOL):
                    break
                charm = data.CHARMS_POOL[i]
                x = start_x + col * (icon_size + spacing)
                y = start_y + (row - visible_start_row) * row_height
                icon_rect = pygame.Rect(x, y, icon_size, icon_size)
                
                bg_color = constants.CHARM_BG_COLORS.get(charm['name'], (150, 150, 150))
                if charm.get('rarity') == 'Legendary':
                    bg_color = tuple(min(255, c + 50) for c in bg_color)
                elif charm.get('rarity') == 'Common':
                    bg_color = tuple(max(0, c - 30) for c in bg_color)
                draw_rounded_element(self.game.screen, icon_rect, bg_color, radius=10, 
                                   border_color=constants.THEME['border'], border_width=1)
                
                icon_path = self.game.charm_icon_paths.get(charm['name'])
                if icon_path and os.path.exists(icon_path):
                    icon = pygame.image.load(icon_path)
                    icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                    self.game.screen.blit(icon, (x, y))
                else:
                    pygame.draw.circle(self.game.screen, (0, 0, 0), (x + icon_size//2, y + icon_size//2), 10)
                
                if any(c['name'] == charm['name'] for c in self.game.equipped_charms):
                    gray_surf = pygame.Surface((icon_size, icon_size))
                    gray_surf.fill((128, 128, 128))
                    gray_surf.set_alpha(100)
                    self.game.screen.blit(gray_surf, (x, y))
                    owned_text = self.game.tiny_font.render("OWNED", True, (100, 100, 100))
                    self.game.screen.blit(owned_text, (x + 5, y + icon_size - 15))
                
                full_name = f"{charm['name']} ({charm.get('rarity', 'Common')})"
                max_text_width = icon_size - 10
                name_lines = wrap_text(self.game.tiny_font, full_name, max_text_width)
                text_y = y + icon_size + 5
                for line in name_lines[:2]:
                    name_text = self.game.tiny_font.render(line, True, constants.THEME['text'])
                    text_x = x + (icon_size - name_text.get_width()) // 2
                    text_bg_rect = pygame.Rect(text_x - 5, text_y - 2, name_text.get_width() + 10, name_text.get_height() + 4)
                    pygame.draw.rect(self.game.screen, (*constants.THEME['background'], 180), text_bg_rect)
                    self.game.screen.blit(name_text, (text_x, text_y))
                    text_y += self.game.tiny_font.get_height() + 2
                
                cost_text = self.game.tiny_font.render(str(charm['cost']), True, (255, 255, 0))
                badge_rect = pygame.Rect(x + icon_size - 25, y + 5, 20, 15)
                pygame.draw.rect(self.game.screen, (0, 0, 0), badge_rect)
                self.game.screen.blit(cost_text, (badge_rect.x + 2, badge_rect.y + 1))
                
                if icon_rect.collidepoint(mouse_pos):
                    tooltip_text = f"{charm['desc']}\nCost: {charm['cost']} | Type: {charm.get('type', 'Unknown')}"
                    space_above = y - constants.DEBUG_PANEL_Y
                    assumed_tooltip_height = 100
                    tooltip_y = y - assumed_tooltip_height - 5 if space_above > assumed_tooltip_height else y + icon_size + 50
                    tooltip_y = max(constants.DEBUG_PANEL_Y + 10, min(tooltip_y, constants.DEBUG_PANEL_Y + constants.DEBUG_PANEL_HEIGHT - assumed_tooltip_height - 10))
                    # Collect to draw last
                    tooltips_to_draw.append((x, tooltip_y, tooltip_text))
                
                charm_rects.append((icon_rect, charm))
        
        equip_all_rect = pygame.Rect(constants.DEBUG_PANEL_X + 20, constants.DEBUG_PANEL_Y + constants.DEBUG_PANEL_HEIGHT - 50, 150, 30)
        draw_custom_button(self.game, equip_all_rect, "Equip All", is_hover=equip_all_rect.collidepoint(mouse_pos))
        close_rect = pygame.Rect(constants.DEBUG_PANEL_X + constants.DEBUG_PANEL_WIDTH - 100, constants.DEBUG_PANEL_Y + 10, 80, 30)
        draw_custom_button(self.game, close_rect, "Close", is_hover=close_rect.collidepoint(mouse_pos))
        
        # Draw scrollbar
        if total_content_height > constants.DEBUG_PANEL_HEIGHT:
            bar_width = 10
            bar_x = constants.DEBUG_PANEL_X + constants.DEBUG_PANEL_WIDTH - bar_width - 5
            bar_y = constants.DEBUG_PANEL_Y + 30
            bar_height = constants.DEBUG_PANEL_HEIGHT - 60
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))  # Brighter track for visibility
            thumb_height = max(20, (constants.DEBUG_PANEL_HEIGHT - 60) * (constants.DEBUG_PANEL_HEIGHT / total_content_height))
            thumb_y = bar_y + (self.scroll_y / (total_content_height - constants.DEBUG_PANEL_HEIGHT)) * (bar_height - thumb_height)
            thumb_y = max(bar_y, min(thumb_y, bar_y + bar_height - thumb_height))
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, int(thumb_y), bar_width, int(thumb_height)))  # White thumb for contrast
        
        # Draw collected tooltips last (on top)
        for x, tooltip_y, tooltip_text in tooltips_to_draw:
            draw_tooltip(self.game, x, tooltip_y, tooltip_text)
        
        return charm_rects + [(equip_all_rect, 'equip_all'), (close_rect, 'close')]
    
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

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        # Calculate start_x dynamically for centering
        num_runes = len(self.game.pack_choices)
        total_rune_width = num_runes * constants.CHARM_BOX_WIDTH + (num_runes - 1) * constants.CHARM_SPACING
        start_x = (self.game.width - total_rune_width) // 2

        # Top: Runes (placeholders with wrapped name)
        self.rune_rects = []
        for i, rune in enumerate(self.game.pack_choices):
            rune_x = start_x + i * (constants.CHARM_BOX_WIDTH + constants.CHARM_SPACING)
            rune_rect = pygame.Rect(rune_x, 50, constants.CHARM_BOX_WIDTH, constants.CHARM_BOX_HEIGHT)
            pygame.draw.rect(self.game.screen, (200,200,200), rune_rect)  # Gray box
            
            # Wrap text if too long (use your utils.wrap_text; assumes it returns list of lines)
            lines = wrap_text(self.game.small_font, rune['name'], constants.CHARM_BOX_WIDTH - 20)  # Padding 10 each side
            y_offset = rune_rect.centery - (len(lines) * self.game.small_font.get_height() // 2)
            for line in lines:
                text = self.game.small_font.render(line, True, constants.THEME['text'])
                self.game.screen.blit(text, (rune_rect.centerx - text.get_width()//2, y_offset))
                y_offset += self.game.small_font.get_height()
            
            if i == self.selected_rune_index:
                pygame.draw.rect(self.game.screen, (255,255,0), rune_rect, width=3)  # Yellow border
            self.rune_rects.append(rune_rect)

        # Bottom: 8 Dice (refresh shows changes)
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

        # Buttons (hide in preview except continue)
        if not self.preview_mode:
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
            # Continue button in preview
            self.continue_rect = pygame.Rect(self.game.width//2 - constants.BUTTON_WIDTH//2, self.game.height - 100, constants.BUTTON_WIDTH, constants.BUTTON_HEIGHT)
            draw_custom_button(self.game, self.continue_rect, "Continue")

            if self.preview_message:
                msg_text = self.game.small_font.render(self.preview_message, True, (255, 255, 0))
                self.game.screen.blit(msg_text, (self.game.width // 2 - msg_text.get_width() // 2, self.game.height // 2 + 50))

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
                    self.selected_rune_index = -1
                    self.selected_die_indices = []
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
                self.preview_mode = True  # Enter preview after apply
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

class GameOverState(State):
    def __init__(self, game):
        super().__init__(game)
        self.restart_rect = None

    def enter(self):
        pass  # Any reset?

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])  # Clear relics
        from screens import draw_game_over_screen
        self.restart_rect = draw_game_over_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.restart_rect and self.restart_rect.collidepoint(mouse_pos):
                self.game.reset_game()
                self.game.state_machine.change_state(InitState(self.game))  # Change to InitState for pouch select

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

class PromptState(State):
    def __init__(self, game):
        super().__init__(game)
        self.yes_rect = None
        self.no_rect = None

    def enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(constants.THEME['background'])
        # Draw prompt
        prompt_text = self.game.font.render("Resume previous run?", True, constants.THEME['text'])
        self.game.screen.blit(prompt_text, (self.game.width // 2 - prompt_text.get_width() // 2, self.game.height // 2 - 50))

        self.yes_rect = pygame.Rect(self.game.width // 2 - 100 - 20, self.game.height // 2, 100, 40)
        draw_custom_button(self.game, self.yes_rect, "Yes", is_hover=self.yes_rect.collidepoint(pygame.mouse.get_pos()))

        self.no_rect = pygame.Rect(self.game.width // 2 + 20, self.game.height // 2, 100, 40)
        draw_custom_button(self.game, self.no_rect, "No", is_hover=self.no_rect.collidepoint(pygame.mouse.get_pos()))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.yes_rect and self.yes_rect.collidepoint(mouse_pos):
                print("Resuming save")
                save_data = savegame.load_game(self.game)  # Single call
                if save_data:
                    # Resume to saved state (existing code)
                    saved_state = save_data.get('current_state')
                    saved_previous = save_data.get('previous_state')
                    resume_state = saved_previous if saved_state == 'PauseMenuState' else saved_state
                    if resume_state == 'GameState':
                        self.game.state_machine.change_state(GameState(self.game))
                    elif resume_state == 'ShopState':
                        self.game.state_machine.change_state(ShopState(self.game))
                    elif resume_state == 'BlindsState':
                        self.game.state_machine.change_state(BlindsState(self.game))
                    else:
                        self.game.state_machine.change_state(InitState(self.game))  # Fallback
                else:
                    # New: Handle corrupt/missing save
                    self.game.temp_message = "Save file corrupted or missing—starting new game."
                    self.game.temp_message_start = time.time()
                    savegame.delete_save()  # Optional: Clean up corrupt file
                    self.game.reset_game()
                    self.game.state_machine.change_state(InitState(self.game))  # Start fresh
            elif self.no_rect and self.no_rect.collidepoint(mouse_pos):
                print("Deleting save, starting new")
                savegame.delete_save()
                self.game.reset_game()  # Call reset to freshen all vars (bag, coins, etc.)
                self.game.state_machine.change_state(InitState(self.game))
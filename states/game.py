# states/game.py
import pygame
import time
import math
import random
import constants
import utils
from states.base import State  # Import from base
from screens import draw_game_screen, draw_popup, draw_buttons, draw_tooltip, draw_enhancement_visuals, draw_instruction_popup
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
        self.selecting_bag_swap = False  # For Familiar's Foresight mode
        self.swap_use_left = 1  # Per-blind uses (reset in enter)
        self.show_instruction_popup = False

    # In states/game.py, GameState.enter method (add after existing resets, before new_turn call)
    def enter(self):
        print(f"DEBUG: Equipped charms in GameState.enter: {[c['name'] for c in self.game.equipped_charms]}")
        print(f"DEBUG: GameState enter – is_resuming: {self.game.is_resuming}, last_state_was_rune: {self.game.last_state_was_rune}, rolls len: {len(self.game.rolls)}, bag len: {len(self.game.bag)}")  # TEMP
        print(f"DEBUG: GameState.enter() → d20_boon.pending_buff = {self.game.d20_boon.pending_buff if hasattr(self.game, 'd20_boon') and self.game.d20_boon else None}")
                # === D20 RESET - Clear ALL intensified effects for new blind ===
        # BUT PROTECT pending_buff / pending_free_pack so rewards can be applied in advance_blind
        pending_buff_to_keep = None
        pending_free_pack_to_keep = None
        if hasattr(self.game, 'd20_boon') and self.game.d20_boon:
            pending_buff_to_keep = self.game.d20_boon.pending_buff
            pending_free_pack_to_keep = getattr(self.game.d20_boon, 'pending_free_pack', None)

        if not getattr(self.game, 'from_d20_intensify', False):
            self.game.intensified_locked_die_idx = -1
            self.game.roll_harmony_active = False
            self.game.intensified_dimmed_color = None
            self.game.intensified_disabled_type = None
            self.game.intensified_global_color_mult = 1.0
            self.game.intensified_buff = None
            print("DEBUG: D20 flags reset for new blind")
        else:
            self.game.from_d20_intensify = False  # consume the flag (keep effects for this blind)
            print("DEBUG: Came from D20 roll — kept intensified effects")

        # RESTORE the pending reward data (this was the missing piece)
        if pending_buff_to_keep is not None and hasattr(self.game, 'd20_boon') and self.game.d20_boon:
            self.game.d20_boon.pending_buff = pending_buff_to_keep
            self.game.d20_boon.pending_free_pack = pending_free_pack_to_keep
            print("DEBUG: Restored pending_buff for Tier 1 success reward")
        
        """# === APPLY TIER 1 BONUS (isolated path — Prism Pack cannot touch this) ===
        if hasattr(self.game, 'tier1_disabled_hand') and self.game.tier1_disabled_hand:
            disabled = self.game.tier1_disabled_hand
            if not hasattr(self.game, 'hand_multipliers'):
                self.game.hand_multipliers = {}
            self.game.hand_multipliers[disabled] = 2.0
            self.game.temp_message = f"Tier 1 Success! +2× on {disabled} this blind!"
            self.game.temp_message_start = time.time()
            print(f"DEBUG: Applied Tier 1 +2x on '{disabled}' (Prism Pack untouched)")
            # Consume the flag so it only applies once
            del self.game.tier1_disabled_hand """

        # NEW: Carry pending buff to this blind's first hand (e.g., Hue Dimming 2x)
        if hasattr(self.game, 'pending_buff_mult') and self.game.pending_buff_mult != 1.0:
            self.game.temp_intensify_mult = self.game.pending_buff_mult
            print(f"DEBUG: Applied carried buff to first hand: x{self.game.temp_intensify_mult}")  # TEMP
            del self.game.pending_buff_mult  # Consume
        if self.game.from_shop_rune_use:  # Shop entry - force fresh pull
            print("DEBUG: From shop rune – forcing fresh pull")  # TEMP
            self.game.from_shop_rune_use = False
            self.game.has_rolled = False  # Reset to pull
            self.game.new_turn()  # Force dice
            return
        if self.game.is_resuming:
            print("DEBUG: Resuming – skipping init pull")  # Your debug
            self.game.is_resuming = False
            self.game.has_rolled = True
            if len(self.game.rolls) == 0:
                print("DEBUG: Resume empty rolls – forcing pull")  # TEMP
                self.game.new_turn()
            return
        
        # NEW: Marble Mystic - Add Stone enh to random bag die on blind start
        mystic_active = any(charm['type'] == 'enhance_add' and charm.get('enh', 'Stone') == 'Stone' and idx not in self.game.disabled_charms for idx, charm in enumerate(self.game.equipped_charms))
        if mystic_active and self.game.bag:
            random_die = random.choice(self.game.bag).copy()  # Random from bag
            if 'enhancements' not in random_die:
                random_die['enhancements'] = []
            random_die['enhancements'].append('Stone')  # Add enh
            self.game.bag = [d for d in self.game.bag if d['id'] != random_die['id']] + [random_die]  # Replace
            self.game.full_bag = [d for d in self.game.full_bag if d['id'] != random_die['id']] + [random_die]  # Sync template
            self.game.temp_message = f"Marble Mystic: Stone enh added to {random_die['color']} die!"
            self.game.temp_message_start = time.time()
            print(f"DEBUG: Marble Mystic added Stone to {random_die['color']} die (ID: {random_die['id']})")  # TEMP
        else:
            if mystic_active and not self.game.bag:
                self.game.temp_message = "Marble Mystic: Bag empty, skipped enh add."
                self.game.temp_message_start = time.time()

        # FIXED: Fresh entry from blinds – always pull if empty
        if len(self.game.rolls) == 0:
            print("DEBUG: Fresh entry – forcing new_turn/pull")  # TEMP
            self.game.new_turn()
        if not self.game.hand or not self.game.rolls or not self.game.has_rolled:
            if self.game.turn_initialized and self.game.is_discard_phase:
                # print("DEBUG: Resuming discard - skipping pull")
                pass
            else:
                # NEW: Apply Turtle Token here (once per blind entry, before first new_turn)
                # ... your turtle code ...
                print(f"DEBUG: Final hands_left after enter: {self.game.hands_left}")

                self.game.new_turn()

        """# NEW: Carry type-specific buff (e.g., tier 1: +2x for blocked type on first next-blind hand)
        if hasattr(self.game, 'pending_type_mult') and self.game.pending_type_mult:
            self.game.temp_type_mult = self.game.pending_type_mult  # e.g., {'Large Straight': 2.0}
            print(f"DEBUG: Applied carried type buff: {self.game.temp_type_mult}")
            del self.game.pending_type_mult  # Consume """
            
        # FIXED: Removed else: new_turn() – rare case covered by fresh
        self.game.update_advantage_flag()  # Refresh after entering state

        # Turtle Token - Apply net (start - decay) on blind entry
        for idx, charm in enumerate(self.game.equipped_charms):
            if charm['type'] == 'hands_decay' and idx not in self.game.disabled_charms:
                rounds_passed = charm.get('rounds_passed', 0)
                net_bonus = charm['start'] - (rounds_passed * charm['decay'])  # e.g., 5 - (1*1)=4
                if net_bonus > 0:
                    self.game.hands_left += net_bonus
                self.game.hands_left = max(constants.MAX_HANDS, self.game.hands_left)  # NEW: Floor at base 4
                if net_bonus < charm['start']:  # NEW: Msg only if decay applied
                    self.game.temp_message = f"Turtle Token: Hands adjusted to {self.game.hands_left} (passed {rounds_passed})"
                    self.game.temp_message_start = time.time()
                break  # Assume one charm

        
        # NEW: Burglar Bag - +3 hands but lose all discards on blind start
        burglar_active = any(charm['type'] == 'burglar_bonus' and charm.get('lose_discards', False) for charm in self.game.equipped_charms if self.game.equipped_charms.index(charm) not in self.game.disabled_charms)
        if burglar_active:
            self.game.hands_left += 3  # +value (hardcoded; or loop for multi)
            self.game.discards_left = 0  # Lose all
            self.game.temp_message = "Burglar Bag: +3 hands, but no discards this blind!"
            self.game.temp_message_start = time.time()
            print(f"DEBUG: Burglar Bag applied - hands={self.game.hands_left}, discards={self.game.discards_left}")  # TEMP
        
        # Safeguard reset for rolls
        if len(self.game.rolls) != 5:
            self.game.rolls = [(None, 0) for _ in range(5)]

        # ADD: Force held reset after new_turn/roll
        self.game.held = [False] * NUM_DICE_IN_HAND
        # print(f"Debug: Forced held reset in enter - held = {self.game.held}")
        
        # Robust reset for Fate's Favor: Always on new blind entry (after shop/return)
        self.game.used_fates_favor_this_blind = False
        self.game.fates_advantage_index = -1
        self.game.fates_advantage_value = None
        self.game.held_fates_advantage = False
        self.game.selecting_fates_die = False
        # print("Debug: Reset Fate's Favor for new blind")

        self.game.buy_boon_target_index = -1
        self.game.buy_boon_up_rect = None
        self.game.buy_boon_down_rect = None
        self.game.buy_boon_confirm_rect = None

        # Reset Familiar's Foresight per blind
        self.game.selecting_bag_swap = False
        self.game.swap_use_left = 1  # Full use on new blind
        self.game.swap_source_index = -1
        self.game.selecting_bag_die = False 

        self.show_instruction_popup = False 
        

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
        if not self.game.is_discard_phase and self.game.has_advantage and self.game.advantage_value is None:
            self.initial_auto_roll_done = True
            # Your auto-roll logic here (e.g., self.game.roll_dice())
            self.game.original_center_value = self.game.rolls[2][1]  # Save original value
            self.game.advantage_value = random.randint(1, 6)  # Roll separate advantage value
            self.game.held_advantage = False
            # print("Debug: Saved original center value:", self.game.original_center_value, "Rolled advantage:", self.game.advantage_value)

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics and prevent stacking
        from screens import draw_game_screen
        draw_game_screen(self.game)  # Call without assignment—main elements drawn inside
        # No flip here if it's in main loop; add if needed: pygame.display.flip()

        # Calc tray_rects for clicks (match screens.py positions)
        tray_width = 2 * constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING
        tray_x = max(self.game.width - (5 * (constants.SMALL_DIE_SIZE + constants.SMALL_DIE_SPACING) - constants.SMALL_DIE_SPACING + constants.BAG_PADDING * 2) - 20 - tray_width - 10, 10)  # Left of bag
        tray_y = 50  # Match bag_y
        self.tray_rects = []
        for i in range(2):
            slot_rect = pygame.Rect(tray_x + i * (constants.TRAY_SLOT_SIZE + constants.TRAY_SLOT_SPACING), tray_y, constants.TRAY_SLOT_SIZE, constants.TRAY_SLOT_SIZE)
            self.tray_rects.append(slot_rect)
        # print("DEBUG: game tray_rects set:", self.tray_rects)  # TEMP

        # NEW: Draw instruction popup overlay (after main screen, before animations/buttons for layering)
        if self.show_instruction_popup and self.game.temp_message is not None:
            self.cancel_rect = draw_instruction_popup(self.game, self.game.temp_message)
        else:
            self.cancel_rect = None  # Avoid None errors downstream

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

        # After for i, die_rect in enumerate(self.game.hand_die_rects or []): ...
        # NEW: Draw arrows if active
        # NEW: Draw arrows if active
        if self.game.buy_boon_target_index != -1:
            if self.game.buy_boon_up_rect:
                pygame.draw.polygon(self.game.screen, (0, 255, 0), [  # Green up triangle
                    (self.game.buy_boon_up_rect.centerx, self.game.buy_boon_up_rect.top),
                    (self.game.buy_boon_up_rect.left, self.game.buy_boon_up_rect.bottom),
                    (self.game.buy_boon_up_rect.right, self.game.buy_boon_up_rect.bottom)
                ])
            
            if self.game.buy_boon_down_rect:
                pygame.draw.polygon(self.game.screen, (255, 0, 0), [  # Red down triangle
                    (self.game.buy_boon_down_rect.centerx, self.game.buy_boon_down_rect.bottom),
                    (self.game.buy_boon_down_rect.left, self.game.buy_boon_down_rect.top),
                    (self.game.buy_boon_down_rect.right, self.game.buy_boon_down_rect.top)
                ])

            # After down arrow pygame.draw.polygon...
            if self.game.buy_boon_confirm_rect:
                pygame.draw.rect(self.game.screen, (100, 100, 100), self.game.buy_boon_confirm_rect)  # Gray button
                confirm_text = self.game.small_font.render("Confirm", True, (255, 255, 255))
                text_x = self.game.buy_boon_confirm_rect.x + (self.game.buy_boon_confirm_rect.width - confirm_text.get_width()) // 2
                text_y = self.game.buy_boon_confirm_rect.y + (self.game.buy_boon_confirm_rect.height - confirm_text.get_height()) // 2
                self.game.screen.blit(confirm_text, (text_x, text_y))

        # NEW: Draw Disadvantage confirm if active
        if self.game.disadvantage_target_index != -1 and self.game.disadvantage_confirm_rect:
            pygame.draw.rect(self.game.screen, (100, 100, 100), self.game.disadvantage_confirm_rect)
            confirm_text = self.game.small_font.render("Confirm", True, (255, 255, 255))
            text_x = self.game.disadvantage_confirm_rect.x + (self.game.disadvantage_confirm_rect.width - confirm_text.get_width()) // 2
            text_y = self.game.disadvantage_confirm_rect.y + (self.game.disadvantage_confirm_rect.height - confirm_text.get_height()) // 2
            self.game.screen.blit(confirm_text, (text_x, text_y))

        for i, small_rect in enumerate(self.game.bag_die_rects or []):
            if i < len(self.game.bag) and small_rect.collidepoint(mouse_pos):
                die = self.game.bag[i]
                non_color_enh = [e for e in die.get('enhancements', []) if e not in ['Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild']]
                if non_color_enh:  # Only show if has non-color enh
                    enh_desc = ', '.join(ENH_DESC.get(e, e) for e in non_color_enh)  # FIXED: Complete the line
                    draw_tooltip(self.game, small_rect.x, small_rect.y + small_rect.height + 10, enh_desc or "No enhancements")  # FIXED: Complete the tooltip call

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from states.pause import PauseMenuState  # Lazy import
                # print("Escape pressed in GameState - Pausing")  # Debug
                savegame.save_game(self.game)  # Save
                self.game.previous_state = self  # Instance
                self.game.state_machine.change_state(PauseMenuState(self.game))
                # NEW: Cancel swap mode on ESC
                self.game.selecting_bag_swap = False
                self.game.selecting_bag_die = False
                self.game.swap_source_index = -1
                self.game.temp_message = ""
                self.show_instruction_popup = False
                # In if event.key == pygame.K_ESCAPE: (after existing cancels)
                self.game.selecting_buy_boon_die = False
                self.game.buy_boon_target_index = -1
                self.game.buy_boon_up_rect = None
                self.game.buy_boon_down_rect = None
                self.game.selecting_disadvantage_die = False
                self.game.disadvantage_target_index = -1
                self.game.disadvantage_confirm_rect = None
                self.game.selecting_whirlwind_die = False
                self.game.whirlwind_target_index = -1

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()  # Moved to the top to ensure it's always defined
            self.update_die_rects()
            if self.game.show_popup:
                if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                    self.game.show_popup = False  # Existing dismiss
                    
                    # Safeguard - if final boss win and not endless, redirect to prompt before shop
                    if self.game.current_blind == 'Boss' and self.game.current_stake == 8 and not self.game.is_endless:
                        from states.end_prompt import EndPromptState  # type: ignore
                        end_prompt = EndPromptState(self.game)
                        self.game.state_machine.change_state(end_prompt)
                        return  # Stop - no shop transition
                    
                    # Existing post-popup advancement (non-final wins)
                    from states.shop import ShopState  # Lazy import
                    self.game.advance_blind()
                    print(f"DEBUG: advance_blind called post-popup – rolls len: {len(self.game.rolls)}, bag len: {len(self.game.bag)}")  # TEMP
                    self.game.generate_shop()
                    self.game.state_machine.change_state(ShopState(self.game))
                    return

            # NEW: Handle instruction popup clicks (e.g., Cancel)
            if self.show_instruction_popup:
                if self.cancel_rect and self.cancel_rect.collidepoint(mouse_pos):
                    self.show_instruction_popup = False
                    self.game.selecting_bag_swap = False
                    self.game.selecting_bag_die = False
                    self.game.swap_source_index = -1
                    self.game.temp_message = ""
                    return
                
            # NEW: Confirm click
            if self.game.buy_boon_confirm_rect and self.game.buy_boon_confirm_rect.collidepoint(mouse_pos):
                self.game.used_buy_boon_this_turn = True
                self.game.buy_boon_target_index = -1
                self.game.buy_boon_up_rect = None
                self.game.buy_boon_down_rect = None
                self.game.buy_boon_confirm_rect = None
                self.game.temp_message = "Buy Boon confirmed!"
                self.game.temp_message_start = time.time()
                # print("DEBUG: Buy Boon confirmed early; used up")
                return

            # Dice clicks (using visual hand_die_rects[i] for precise hits)
            for i, die_rect in enumerate(self.game.hand_die_rects):
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
                        break
                    else:
                        if self.game.is_discard_phase:
                            self.game.toggle_discard(i)
                        else:
                            self.game.toggle_hold(i)
                            
                            # === ROLL FLOW ADVANTAGE (Tier 4) - dynamic exclusion ===
                            adv_index = getattr(self.game, 'fates_advantage_index', -1)
                            if adv_index != -1 and self.game.has_advantage:
                                if i == adv_index and self.game.held[i]:
                                    self.game.held_advantage = False  # Unhold advantage if original is held
                            
                            # print(f"Debug: Toggled die {i} - held[{i}] = {self.game.held[i]}")  # Debug for 3rd die
                        break  # Stop after handling one die click

            # NEW: Roll Flow advantage selection (roll phase only, first hand)
            if not self.game.is_discard_phase and hasattr(self.game, 'selecting_advantage_die') and self.game.selecting_advantage_die:
                for i in range(NUM_DICE_IN_HAND):
                    die_rect = self.game.hand_die_rects[i]
                    if die_rect.collidepoint(mouse_pos):
                        # Spawn advantage copy above (reuse Amulet logic)
                        self.game.has_advantage = True
                        self.game.advantage_value = random.randint(1, 6)
                        self.game.held_advantage = False  # Start unheld
                        self.game.fates_advantage_index = i  # Reuse for pos (or new flag)
                        self.game.selecting_advantage_die = False  # Exit mode
                        self.game.temp_message = f"Advantage on die {i+1}! Choose to hold."
                        self.game.temp_message_start = time.time()
                        print(f"DEBUG: Selected die {i} for Roll Flow advantage: {self.game.advantage_value}")
                        break

            # Advantage choice clicks (Roll Flow) - recalculate rect on-the-fly so click detection matches visual position
            if not self.game.is_discard_phase and self.game.has_advantage and self.game.advantage_value is not None:
                adv_index = getattr(self.game, 'fates_advantage_index', 2)
                
                # Recalculate start_x exactly like draw_dice does
                total_dice_width = constants.NUM_DICE_IN_HAND * (constants.DIE_SIZE + 20) - 20
                start_x = (self.game.width - total_dice_width) // 2
                
                # Build the exact same rect that was drawn
                x = start_x + adv_index * (constants.DIE_SIZE + 20)
                adv_y = (self.game.height - constants.DIE_SIZE - 100) - constants.DIE_SIZE - 10
                adv_size = constants.DIE_SIZE * constants.HELD_DIE_SCALE if self.game.held_advantage else constants.DIE_SIZE
                adv_offset = (constants.DIE_SIZE - adv_size) / 2 if self.game.held_advantage else 0
                adv_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
                
                if adv_rect.collidepoint(mouse_pos):
                    self.game.held_advantage = not self.game.held_advantage
                    
                    # Mutually exclusive: only one or the other can be held
                    if self.game.held_advantage:
                        self.game.held[adv_index] = False
                    
                    print(f"DEBUG: Toggled advantage on die {adv_index + 1} - held_advantage = {self.game.held_advantage}")
                    self.game.update_hand_text()
                # REMOVED: elif center_die_rect toggle (handled precisely in main loop above)
            
            
            # Fate's Favor advantage toggle
            if not self.game.is_discard_phase and self.game.fates_advantage_index != -1 and self.game.fates_advantage_value is not None:
                fates_rect = getattr(self.game, 'fates_advantage_die_rect', None)  # Safe access
                if fates_rect is not None and fates_rect.collidepoint(mouse_pos):
                    self.game.held_fates_advantage = not self.game.held_fates_advantage
                    if self.game.held_fates_advantage and self.game.held[self.game.fates_advantage_index]:
                        self.game.held[self.game.fates_advantage_index] = False
                    self.game.update_hand_text()
                    # print(f"Debug: Toggled Fate's advantage - held_fates_advantage = {self.game.held_fates_advantage}, held[{self.game.fates_advantage_index}] = {self.game.held[self.game.fates_advantage_index]}")
                # No optional original here—handled in toggle_hold below

            # NEW: UNO Draw 2 - Click equipped charm to gain 2 extra rerolls (once per blind)
            for i, charm_rect in enumerate(self.game.equipped_charm_rects):
                if charm_rect.collidepoint(mouse_pos):
                    charm = self.game.equipped_charms[i]
                    if charm['type'] == 'extra_reroll' and not self.game.used_uno_draw_this_blind and not self.game.is_discard_phase:
                        self.game.rerolls_left += charm['value']  # +2
                        self.game.used_uno_draw_this_blind = True
                        self.game.temp_message = f"UNO Draw 2: +{charm['value']} extra rerolls! (Used up this blind)"
                        self.game.temp_message_start = time.time()
                        print(f"DEBUG: UNO Draw 2 activated - rerolls now {self.game.rerolls_left}")  # TEMP
                    break  # One charm per click

            # Luchador instant sell block (early in MOUSEBUTTONDOWN, after mouse_pos)
            for i, charm in enumerate(self.game.equipped_charms):
                x = 50 + i * (constants.CHARM_SIZE + 10)
                y = 10
                charm_rect = pygame.Rect(x, y, constants.CHARM_SIZE, constants.CHARM_SIZE)
                if charm_rect.collidepoint(mouse_pos) and charm['name'] == 'Luchador Lens':
                    if self.game.current_round == 8:
                        self.game.temp_message = "Cannot disable the final boss!"
                        self.game.temp_message_start = time.time()
                        return
                    # Sell & set flag
                    self.game.coins += charm['cost']
                    del self.game.equipped_charms[i]
                    self.game.luchador_disable_active = True
                    self.game.temp_message = "Luchador Lens sold! Boss will be disabled next boss round."
                    self.game.temp_message_start = time.time()
                    # print(f"DEBUG: Luchador flag set from mid-game")
                    return   
            
            # NEW: Familiar's Foresight swap logic (discard phase only)
            if self.game.is_discard_phase and self.game.selecting_bag_swap:
                mouse_pos = pygame.mouse.get_pos()
                # Check hand die click (for source)
                for i in range(NUM_DICE_IN_HAND):
                    total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
                    start_x = (self.game.width - total_dice_width) // 2
                    x = start_x + i * (DIE_SIZE + 20)
                    size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
                    offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
                    die_rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
                    if die_rect.collidepoint(mouse_pos):
                        self.game.swap_source_index = i
                        self.game.temp_message = "Select bag die to swap with."
                        self.show_instruction_popup = True  # Show popup for bag select
                        # print(f"DEBUG: Selected hand die {i} for swap")
                        return  # Early return to prevent other clicks

            # Separate block for bag selection (after hand picked)
            if self.game.is_discard_phase and hasattr(self.game, 'swap_source_index') and self.game.swap_source_index != -1:
                mouse_pos = pygame.mouse.get_pos()
                # Check bag die click (for target)
                for j, bag_rect in enumerate(self.game.bag_die_rects):
                    if bag_rect.collidepoint(mouse_pos):
                        source_die = self.game.hand[self.game.swap_source_index]
                        target_die = self.game.bag[j]
                        # Swap
                        self.game.hand[self.game.swap_source_index] = target_die
                        self.game.bag[j] = source_die
                        self.game.bag.remove(source_die)  # Re-add to bag end
                        self.game.bag.append(source_die)
                        old_value = self.game.rolls[self.game.swap_source_index][1]  # Keep old value
                        self.game.rolls[self.game.swap_source_index] = (target_die, old_value)  # Sync rolls tuple for draw
                        self.game.swap_use_left -= 1
                        self.game.swap_source_index = -1
                        self.game.selecting_bag_swap = False  # FIXED: Explicit clear
                        self.game.temp_message = f"Swapped! Uses left: {self.game.swap_use_left}"
                        self.show_instruction_popup = False  # Dismiss popup
                        self.game.refresh_bag()
                        self.update_die_rects()
                        self.game.update_hand_text()
                        # print(f"DEBUG: Swapped die {self.game.swap_source_index} with bag {j}; uses left: {self.game.swap_use_left}")
                        return
            
            # NEW: Buy Boon die selection (roll phase only)
            if not self.game.is_discard_phase and self.game.selecting_buy_boon_die:
                mouse_pos = pygame.mouse.get_pos()
                arrow_size = 30  # Define early to avoid unbound
                for i in range(NUM_DICE_IN_HAND):
                    # Use existing hand_die_rects
                    die_rect = self.game.hand_die_rects[i]
                    if die_rect.collidepoint(mouse_pos) and self.game.held[i]:  # Only held dice
                        self.game.buy_boon_target_index = i
                        self.game.temp_message = "Shift die value (up/down arrows)"
                        self.show_instruction_popup = False  # Dismiss select popup
                        self.game.selecting_buy_boon_die = False  # Exit select mode
                        # Calc arrow rects dynamically
                        size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
                        offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
                        up_x = die_rect.x + (die_rect.width - arrow_size) // 2
                        up_y = die_rect.y - arrow_size - 5  # Above die
                        self.game.buy_boon_up_rect = pygame.Rect(up_x, up_y, arrow_size, arrow_size)
                        
                        down_x = up_x
                        down_y = die_rect.y + die_rect.height + 5  # Below die
                        self.game.buy_boon_down_rect = pygame.Rect(down_x, down_y, arrow_size, arrow_size)
                        
                        # In the die selection if (after setting down_rect)
                        confirm_width = 80
                        confirm_height = 30
                        confirm_x = die_rect.x + (die_rect.width - confirm_width) // 2
                        confirm_y = up_y - confirm_height - 10  # Above up arrow
                        self.game.buy_boon_confirm_rect = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)

                        # print(f"DEBUG: Selected die {i} for Buy Boon shifts; shifts left: {self.game.buy_boon_shifts_left}")
                        return  # Early return

            # NEW: Arrow clicks (anytime arrows active)
            if self.game.buy_boon_target_index != -1:
                mouse_pos = pygame.mouse.get_pos()
                if self.game.buy_boon_up_rect and self.game.buy_boon_up_rect.collidepoint(mouse_pos):
                    if self.game.buy_boon_shifts_left > 0 and self.game.coins >= 2:
                        i = self.game.buy_boon_target_index
                        die, value = self.game.rolls[i]
                        new_value = min(6, value + 1)
                        self.game.rolls[i] = (die, new_value)
                        self.game.coins -= 2
                        self.game.buy_boon_shifts_left -= 1
                        self.game.update_hand_text()
                        # print(f"DEBUG: Shifted up die {i} to {new_value}; coins: {self.game.coins}, shifts left: {self.game.buy_boon_shifts_left}")
                        if self.game.buy_boon_shifts_left == 0:
                            self.game.used_buy_boon_this_turn = True
                            self.game.buy_boon_target_index = -1  # Done
                            self.game.buy_boon_up_rect = None
                            self.game.buy_boon_down_rect = None
                    return
                
            # NEW: Disadvantage Dice selection (roll phase only)
            if not self.game.is_discard_phase and self.game.selecting_disadvantage_die:
                mouse_pos = pygame.mouse.get_pos()
                for i in range(NUM_DICE_IN_HAND):
                    die_rect = self.game.hand_die_rects[i]
                    if die_rect.collidepoint(mouse_pos) and self.game.held[i]:  # Only held
                        self.game.disadvantage_target_index = i
                        self.game.temp_message = "Disadvantage applied? (-1 value, +0.5 mult)"
                        self.show_instruction_popup = False
                        self.game.selecting_disadvantage_die = False
                        # Confirm button (below die)
                        confirm_width = 80
                        confirm_height = 30
                        confirm_x = die_rect.x + (die_rect.width - confirm_width) // 2
                        confirm_y = die_rect.y + die_rect.height + 10
                        self.game.disadvantage_confirm_rect = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)
                        # print(f"DEBUG: Selected die {i} for Disadvantage")
                        return

            # NEW: Confirm click
            if self.game.disadvantage_target_index != -1 and self.game.disadvantage_confirm_rect and self.game.disadvantage_confirm_rect.collidepoint(mouse_pos):
                i = self.game.disadvantage_target_index
                _, current_value = self.game.rolls[i]
                new_value = max(1, current_value - 1)
                self.game.rolls[i] = (self.game.rolls[i][0], new_value)  # Update value
                self.game.used_disadvantage_this_turn = True
                self.game.disadvantage_target_index = -1
                self.game.disadvantage_confirm_rect = None
                self.game.temp_message = f"Die disadvantaged to {new_value}! +0.5 mult."
                self.game.temp_message_start = time.time()
                self.game.update_hand_text()
                # print(f"DEBUG: Disadvantage applied to die {i}: {current_value} → {new_value}")
                return
    
            # NEW: Whirlwind Wild selection (roll phase only)
            if not self.game.is_discard_phase and self.game.selecting_whirlwind_die:
                mouse_pos = pygame.mouse.get_pos()
                for i in range(NUM_DICE_IN_HAND):
                    die_rect = self.game.hand_die_rects[i]
                    if die_rect.collidepoint(mouse_pos):
                        # Free reroll this die (no hold check—any die)
                        die, _ = self.game.rolls[i]
                        new_value = random.choice(die['faces'])  # Reroll
                        self.game.rolls[i] = (die, new_value)
                        self.game.used_whirlwind_this_blind = True
                        self.game.selecting_whirlwind_die = False
                        self.game.whirlwind_target_index = -1  # Not needed, but clear
                        self.game.temp_message = f"Free reroll on die {i}! Rolled {new_value}."
                        self.game.temp_message_start = time.time()
                        self.game.update_hand_text()
                        self.game.sfx_channel.play(self.game.roll_sound)  # Optional SFX
                        # print(f"DEBUG: Whirlwind free rerolled die {i} to {new_value}")
                        return

            # NEW: UNO Draw 2 charm click (gain 2 extra rerolls, once per blind)
            # print(f"DEBUG: Mouse click at {mouse_pos} - UNO rect exists? {self.game.uno_charm_rect is not None}")
            if self.game.uno_charm_rect and self.game.uno_charm_rect.collidepoint(mouse_pos):
                print(f"DEBUG: UNO rect HIT! Flag: {self.game.used_uno_this_blind}, Rerolls before: {self.game.rerolls_left}")
                if not self.game.used_uno_this_blind:  # Once-per-blind guard
                    self.game.rerolls_left += 2
                    self.game.used_uno_this_blind = True
                    self.game.temp_message = f"UNO Draw 2! +2 rerolls (now {self.game.rerolls_left})."
                    self.game.temp_message_start = time.time()
                    self.game.update_hand_text()  # Refresh UI counter
                    if hasattr(self.game, 'charm_sound') and self.game.charm_sound:
                        self.game.sfx_channel.play(self.game.charm_sound)  # Optional SFX
                    print(f"DEBUG: UNO effect applied - Rerolls now: {self.game.rerolls_left}, Flag set True")
                    return
                else:
                    # Optional: Flash a "used" hint (or just silent fail)
                    self.game.temp_message = "UNO already used this blind!"
                    self.game.temp_message_start = time.time()
                    print("DEBUG: UNO blocked - flag already True")
                    return
            # else:
                # print("DEBUG: UNO rect MISS or None")  # If here, collision fail

            if self.game.buy_boon_down_rect and self.game.buy_boon_down_rect.collidepoint(mouse_pos):
                if self.game.buy_boon_shifts_left > 0 and self.game.coins >= 2:
                    i = self.game.buy_boon_target_index
                    die, value = self.game.rolls[i]
                    new_value = max(1, value - 1)
                    self.game.rolls[i] = (die, new_value)
                    self.game.coins -= 2
                    self.game.buy_boon_shifts_left -= 1
                    self.game.update_hand_text()
                    # print(f"DEBUG: Shifted down die {i} to {new_value}; coins: {self.game.coins}, shifts left: {self.game.buy_boon_shifts_left}")
                    if self.game.buy_boon_shifts_left == 0:
                        self.game.used_buy_boon_this_turn = True
                        self.game.buy_boon_target_index = -1
                        self.game.buy_boon_up_rect = None
                        self.game.buy_boon_down_rect = None
                return
    
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
                        # print("Debug: Entered Fate's Favor selection mode")
                        break  # No drag if activating
                    # NEW: Familiar's activation
                    elif charm['name'] == "Familiar's Foresight" and i not in self.game.disabled_charms and self.game.is_discard_phase:
                        if self.game.swap_use_left > 0:
                            self.game.selecting_bag_swap = True
                            self.game.temp_message = "Select hand die to swap."
                            self.show_instruction_popup = True
                            # print("DEBUG: Familiar's Foresight activated—select hand die")
                            break
                        else:
                            self.game.temp_message = "No uses left!"
                            self.show_instruction_popup = False  # Ensure no popup
                            # print("DEBUG: Familiar's Foresight no uses—skipped")
                            break
                    # New: Buy Boon
                    elif charm['name'] == "Buy Boon" and i not in self.game.disabled_charms and not self.game.used_buy_boon_this_turn and not self.game.is_discard_phase:
                        if self.game.coins < 4:  # Min for 2 shifts at 2 each
                            self.game.temp_message = "Not enough coins! (Need at least 4)"
                            self.game.temp_message_start = time.time()
                            break
                        self.game.selecting_buy_boon_die = True
                        self.game.temp_message = "Select hand die to shift (2 coins per +/-1, max 2 shifts)"
                        self.show_instruction_popup = True
                        # print("DEBUG: Buy Boon activated—select die")
                        break
                    elif charm['name'] == "Disadvantage Dice" and i not in self.game.disabled_charms and not self.game.used_disadvantage_this_turn and not self.game.is_discard_phase:
                        self.game.selecting_disadvantage_die = True
                        self.game.temp_message = "Select die to disadvantage (-1 value, +0.5 mult)"
                        self.show_instruction_popup = True
                        #print("DEBUG: Disadvantage Dice activated—select die")
                        break
                    elif charm['name'] == "Whirlwind Wild" and i not in self.game.disabled_charms and not self.game.used_whirlwind_this_blind and not self.game.is_discard_phase:
                        # Check for Rainbow charge
                        # print(f"DEBUG: Whirlwind clicked - disabled? {i in self.game.disabled_charms}, used? {self.game.used_whirlwind_this_blind}, discard phase? {self.game.is_discard_phase}")
                        has_rainbow_charge = any(die['color'] == 'Rainbow' for die, _ in self.game.rolls)
                        # print(f"DEBUG: Rainbow charge available? {has_rainbow_charge} (rolls: {[die['color'] for die, _ in self.game.rolls]})")
                        if has_rainbow_charge:
                            self.game.selecting_whirlwind_die = True
                            self.game.temp_message = "Select die for free reroll (Rainbow charge)"
                            self.show_instruction_popup = True
                            # print("DEBUG: Whirlwind Wild activated—select die")
                        else:
                            self.game.temp_message = "No Rainbow charge available!"
                            self.game.temp_message_start = time.time()
                        break

            # NEW: Tray click to use rune
            for i, tray_rect in enumerate(self.tray_rects or []):
                if tray_rect is not None and tray_rect.collidepoint(mouse_pos) and self.game.rune_tray[i]:
                    from states.rune import RuneUseState  # Lazy import
                    rune = self.game.rune_tray[i]
                    self.game.state_machine.change_state(RuneUseState(self.game, rune))  # Transition
                    self.game.previous_state = self
                    # NEW: Rune Recycler - Queue reuse after use (for next shop) - only if not flagged
                    recycler_active = any(charm['type'] == 'rune_reuse' and idx not in self.game.disabled_charms for idx, charm in enumerate(self.game.equipped_charms))
                    if recycler_active and not getattr(self.game, '_recycler_used_this_blind', False):  # FIXED: Per blind flag
                        self.game._recycler_reuse_pending = rune.copy()  # Queue for next shop
                        self.game._recycler_used_this_blind = True  # FIXED: Blind flag (not shop)
                        self.game.temp_message = f"Rune Recycler: {rune['name']} queued for reuse in next shop!"
                        self.game.temp_message_start = time.time()
                    # FIXED: Skip removal if reused rune (persist for Recycler)
                    if not getattr(rune, 'reused', False):
                        self.game.rune_tray[i] = None  # Remove after use
                    break

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
        # Hand dice rects (unchanged)
        self.game.hand_die_rects = []
        for i in range(NUM_DICE_IN_HAND):
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            size = DIE_SIZE * HELD_DIE_SCALE if self.game.held[i] else DIE_SIZE
            offset = (DIE_SIZE - size) / 2 if self.game.held[i] else 0
            rect = pygame.Rect(x + offset, self.game.height - DIE_SIZE - 100 + offset, size, size)
            self.game.hand_die_rects.append(rect)

        # NEW: Set center_die_rect (for consistency, though main loop uses hand_die_rects[2])
        if self.game.hand_die_rects:
            self.game.center_die_rect = self.game.hand_die_rects[2]

        # NEW: Set advantage_die_rect (fresh for clicks)
        if self.game.has_advantage and self.game.advantage_value is not None:
            i = 2
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            adv_y = (self.game.height - DIE_SIZE - 100) - DIE_SIZE - 10
            adv_size = DIE_SIZE * HELD_DIE_SCALE if self.game.held_advantage else DIE_SIZE
            adv_offset = (DIE_SIZE - adv_size) / 2 if self.game.held_advantage else 0
            self.game.advantage_die_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
        else:
            self.game.advantage_die_rect = None

        # Fate's already set here (unchanged)
        if self.game.fates_advantage_index != -1 and self.game.fates_advantage_value is not None:
            i = self.game.fates_advantage_index
            total_dice_width = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
            start_x = (self.game.width - total_dice_width) // 2
            x = start_x + i * (DIE_SIZE + 20)
            adv_y = (self.game.height - DIE_SIZE - 100) - DIE_SIZE - 10
            adv_size = DIE_SIZE * HELD_DIE_SCALE if self.game.held_fates_advantage else DIE_SIZE
            adv_offset = (DIE_SIZE - adv_size) / 2 if self.game.held_fates_advantage else 0
            self.game.fates_advantage_die_rect = pygame.Rect(x + adv_offset, adv_y + adv_offset, adv_size, adv_size)
            # print(f"Debug: Set fates_advantage_die_rect = {self.game.fates_advantage_die_rect}")  # Confirm set

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
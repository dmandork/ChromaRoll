# states/blinds.py
import pygame
import random
import copy
import time
import data  # FIXED: For blind_order and D20_OUTCOMES
from constants import *  # For THEME, BUTTON_WIDTH, BASE_TARGETS, etc.
import constants
from utils import draw_rounded_element, resource_path  # For buttons/UI elements
from screens import draw_blinds_screen, draw_custom_button, draw_play_debug_bar  # For main blinds drawing/buttons
from states.base import State
# Import extracted states if referenced (e.g., for button transitions)
# from states.game import GameState  # If extracted; else from statemachine import GameState
# from states.shop import ShopState  # If extracted and referenced
from data import BOSS_EFFECTS, pick_boss_effect, pick_boss_for_game, intensify_unlocked
from states.game import GameState

from .shop import ShopState

blind_order = ['Small', 'Big', 'Boss']  # FIXED: Define locally


class BlindsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.continue_rect = None
        self.debug_button_rect = None
        self.up_rect = None
        self.down_rect = None
        self.debug_jump_rect = None
        self.intensify_rect = None  # NEW: Single for current blind
        self.debug_force_win_rect = None
        self.debug_rects = []
        # For item rects in dropdown (since dynamic, recalculate in handle_event)
        if DEBUG:
            self.stake_dropdown_open = False
            self.selected_stake = self.game.current_stake
            self.dropdown_rect = None
            self.font_small = pygame.font.Font(None, 20)

    def enter(self):
        print(f"DEBUG: GameState enter – is_resuming: {self.game.is_resuming}, bag len: {len(self.game.bag)}")  # TEMP
        if self.game.is_resuming:
            print("DEBUG: Resuming – skipping init pull")  # Your debug
            self.game.is_resuming = False  # FIXED: Clear after
            return  # Skip new_turn/draw_hand
        # Reset any blinds-specific vars (e.g., debug states)
        self.game.debug_boss_dropdown_open = False  # If not already reset
        self.game.debug_boss_scroll_offset = 0
        if DEBUG:
            self.stake_dropdown_open = False
            self.dropdown_rect = None
        # Conditional: Generate upcoming boss only if None
        if self.game.upcoming_boss_effect is None:
            self.game.upcoming_boss_effect = pick_boss_effect(getattr(self.game, 'current_stake', 1))

        # Rune Relic: Add random rune at blind start (after shop)
        print("DEBUG: Checking for Rune Relic in blinds enter")  # TEMP
        for idx, charm in enumerate(self.game.equipped_charms):
            if charm['type'] == 'random_rune' and idx not in self.game.disabled_charms:
                print("DEBUG: Triggering Rune Relic in blinds")  # TEMP
                rune = random.choice(data.MYSTIC_RUNES).copy()
                if self.game.add_to_rune_tray(rune):
                    self.game.temp_message = f"Added {rune['name']} from Rune Relic!"
                    self.game.temp_message_start = time.time()
                else:
                    self.game.temp_message = "Rune tray full – Rune Relic skipped!"
                    self.game.temp_message_start = time.time()
                break
        print(f"DEBUG: Tray after Relic in blinds: {self.game.rune_tray}")  # TEMP

        # **INSERT: Apply Luchador flag for upcoming boss**
        if self.game.luchador_disable_active and self.game.current_blind != 'Boss':  # Only set for upcoming, not current
            dummy_disabled = {'name': 'DISABLED', 'desc': 'Boss effect disabled by Luchador Lens!', 'difficulty': 'None'}
            self.game.upcoming_boss_effect = dummy_disabled
            print("DEBUG: Luchador flag applied to upcoming boss")

        # NEW: UNO Skip - Skip one boss blind per run (guaranteed, not blind 8)
        skip_active = any(charm['type'] == 'boss_skip' and idx not in self.game.disabled_charms for idx, charm in enumerate(self.game.equipped_charms))
        if skip_active and not self.game.uno_skip_used and self.game.current_blind == 'Boss':
            # FIXED: Advance stake and set to next small blind (instead of 'normal')
            self.game.current_stake += 1
            self.game.current_blind = 'Small'
            self.game.uno_skip_used = True
            self.game.temp_message = "UNO Skip activated! Skipped boss blind. (Used up!)"
            self.game.temp_message_start = time.time()
            print("DEBUG: UNO Skip triggered in Blinds enter - advanced stake, set to Small")  # TEMP
        else:
            if skip_active and self.game.uno_skip_used:
                print("DEBUG: UNO Skip used up, skipping")  # TEMP
            elif skip_active and self.game.current_stake * 3 == 24:  # FIXED: Block final boss (stake 8 = blind 24)
                print("DEBUG: UNO Skip blocked on final boss")  # TEMP

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.blind_rects, self.continue_rect, self.debug_button_rect, self.up_rect, self.down_rect, self.debug_jump_rect, self.intensify_rect = draw_blinds_screen(self.game)  # Unpack 7
        self.debug_force_win_rect = None
        self.debug_rects = []
        debug_open = bool(constants.DEBUG and getattr(self.game, 'debug_play_open', False))
        if constants.DEBUG:
            self.debug_rects = draw_play_debug_bar(self.game)
            # Stake jumper sits next to the DBG tab so it never covers charms.
            tab = self.debug_rects[0][0] if self.debug_rects else pygame.Rect(8, self.game.height - 70, 40, 28)
            self.dropdown_rect = pygame.Rect(tab.right + 8, tab.y, 120, tab.height)

        if debug_open and self.dropdown_rect:
            draw_rounded_element(self.game.screen, self.dropdown_rect, (50, 50, 50), radius=5)
            dropdown_text = f"Stake {self.selected_stake}"
            text_surf = self.font_small.render(dropdown_text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=self.dropdown_rect.center)
            self.game.screen.blit(text_surf, text_rect)
            arrow_x = self.dropdown_rect.right - 15
            arrow_y = self.dropdown_rect.centery
            if self.stake_dropdown_open:
                pygame.draw.polygon(self.game.screen, (255, 255, 255), [(arrow_x-5, arrow_y-3), (arrow_x+5, arrow_y-3), (arrow_x, arrow_y+3)])
            else:
                pygame.draw.polygon(self.game.screen, (255, 255, 255), [(arrow_x-5, arrow_y+3), (arrow_x+5, arrow_y+3), (arrow_x, arrow_y-3)])
            if self.stake_dropdown_open:
                mouse_pos = pygame.mouse.get_pos()
                item_width = self.dropdown_rect.width
                item_height = 25
                y_offset = self.dropdown_rect.y - 5 - 8 * (item_height + 2)
                for stake in range(1, 9):
                    opt_rect = pygame.Rect(self.dropdown_rect.x, y_offset, item_width, item_height)
                    color = (70, 70, 70) if opt_rect.collidepoint(mouse_pos) else (40, 40, 40)
                    draw_rounded_element(self.game.screen, opt_rect, color, radius=3)
                    opt_text = f"Stake {stake}"
                    text_surf = self.font_small.render(opt_text, True, (255, 255, 255))
                    text_rect = text_surf.get_rect(center=opt_rect.center)
                    self.game.screen.blit(text_surf, text_rect)
                    y_offset += item_height + 2

    def handle_event(self, event):
        from states.shop import ShopState  # Lazy import
        from states.init import InitState
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if constants.DEBUG:
                for rect, action in self.debug_rects or []:
                    if rect.collidepoint(mouse_pos):
                        if action == 'toggle':
                            self.game.debug_play_open = not bool(getattr(self.game, 'debug_play_open', False))
                        else:
                            self.game.debug_run_play_action(action)
                        return
            if self.debug_force_win_rect and self.debug_force_win_rect.collidepoint(mouse_pos):
                self.game.debug_force_win(skip_popup=True)
                return
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                # Clear old turn state for new blind
                self.game.hand = []
                self.game.rolls = []
                self.game.held = [False] * NUM_DICE_IN_HAND
                self.game.discard_selected = [False] * NUM_DICE_IN_HAND
                self.game.is_discard_phase = True  # Start with discard
                self.game.has_rolled = False
                self.game.bag[:] = [copy.deepcopy(d) for d in self.game.full_bag]  # Refill bag
                self.game.entering_fresh_blind = True
                if hasattr(self.game, 'd20_boon') and self.game.d20_boon:
                    self.game.d20_boon.begin_next_blind(self.game)
                self.game.state_machine.change_state(GameState(self.game))
                return

            # Intensify: blocked once a d20 has already landed (locked roll / leftover dump).
            if self.intensify_rect and self.intensify_rect.collidepoint(mouse_pos):
                if not intensify_unlocked(getattr(self.game, 'current_stake', 1)):
                    return
                boon = getattr(self.game, 'd20_boon', None)
                if boon is not None and boon.is_locked():
                    return
                from .d20_roll import D20RollState
                self.game.entering_fresh_blind = True
                self.game.state_machine.change_state(D20RollState(self.game, self.game.current_blind))
                return


            if constants.DEBUG and getattr(self.game, 'debug_play_open', False):
                # Existing boss dropdown handling
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
                    visible_items = 300 // item_height  # Panel height // item
                    for i in range(self.game.debug_boss_scroll_offset, min(self.game.debug_boss_scroll_offset + visible_items, len(BOSS_EFFECTS))):
                        item_rect = pygame.Rect(panel_x, panel_y + (i - self.game.debug_boss_scroll_offset) * item_height, 370, item_height)  # Full row clickable
                        if item_rect.collidepoint(mouse_pos):
                            self.game.upcoming_boss_effect = BOSS_EFFECTS[i]
                            self.game.debug_boss_dropdown_open = False  # Close on select
                            break

                # Stake jumper (next to DBG tab; options grow upward)
                if self.dropdown_rect and self.dropdown_rect.collidepoint(mouse_pos):
                    self.stake_dropdown_open = not self.stake_dropdown_open  # Toggle

                if self.stake_dropdown_open and self.dropdown_rect:
                    item_width = self.dropdown_rect.width
                    item_height = 25
                    y_offset = self.dropdown_rect.y - 5 - 8 * (item_height + 2)
                    for stake in range(1, 9):
                        opt_rect = pygame.Rect(self.dropdown_rect.x, y_offset, item_width, item_height)
                        if opt_rect.collidepoint(mouse_pos):
                            self.game.current_stake = stake
                            self.selected_stake = stake
                            self.stake_dropdown_open = False  # Close on select
                            self.game.upcoming_boss_effect = pick_boss_for_game(self.game)
                            break
                        y_offset += item_height + 2

                if self.debug_jump_rect and self.debug_jump_rect.collidepoint(mouse_pos):
                    self.game.current_blind = 'Boss'
                    self.game.current_boss_effect = self.game.upcoming_boss_effect or pick_boss_for_game(self.game)
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
                    elif effect_name == 'Discard Drought':
                        self.game.discards_left = max(0, self.game.discards_left - 1)
                    elif effect_name == 'Blind Boost':
                        self.game.discards_left += 1
                    # Reroll Ration is applied in new_turn (once per hand, −1).
                    # Reset round elements
                    self.game.round_score = 0
                    self.game.bag[:] = [copy.deepcopy(d) for d in self.game.full_bag]  # Refill
                    self.game.state_machine.change_state(GameState(self.game))  # Jump to 'game'
                    self.game.new_turn()  # Start Boss turn

    # Optional: Add this if explicit blind regen is needed beyond setting current_stake
    # def setup_blinds_for_stake(self):
    #     # Regenerate blinds_list or targets based on self.game.current_stake
    #     # E.g., self.game.blinds_list = generate_blinds(self.game.current_stake)  # From data.py
    #     pass
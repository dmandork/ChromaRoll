# states/blinds.py
import pygame
import random
import copy
from constants import *  # For THEME, BUTTON_WIDTH, BASE_TARGETS, etc.
from utils import draw_rounded_element, resource_path  # For buttons/UI elements
from screens import draw_blinds_screen, draw_custom_button  # For main blinds drawing/buttons
from statemachine import State
# Import extracted states if referenced (e.g., for button transitions)
# from states.game import GameState  # If extracted; else from statemachine import GameState
# from states.shop import ShopState  # If extracted and referenced
from data import BOSS_EFFECTS
from statemachine import GameState
from states.shop import ShopState

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
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.continue_rect, self.debug_button_rect, self.up_rect, self.down_rect, self.debug_jump_rect = draw_blinds_screen(self.game)

    def handle_event(self, event):
        from states.init import InitState
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                # Clear old turn state for new blind
                self.game.hand = []
                self.game.rolls = []
                self.game.held = [False] * NUM_DICE_IN_HAND
                self.game.discard_selected = [False] * NUM_DICE_IN_HAND
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
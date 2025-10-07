# states/dice_select.py
import pygame
import copy
from states.base import State
from states.shop import ShopState  # For returning to shop after selection
from screens import draw_dice_select_screen
from constants import THEME, DICE_FACES

class DiceSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.choice_rects = None  # List of (rect, color) tuples

    def enter(self):
        pass  # Pack choices already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
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
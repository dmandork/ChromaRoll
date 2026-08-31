# states/pack_select.py
import pygame
from states.base import State
from states.shop import ShopState  # For returning to shop after selection
from screens import draw_pack_select_screen
from constants import THEME, PACK_BOOST

class PackSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.choice_rects = None  # List of rects for choices

    def enter(self):
        pass  # Pack choices already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.choice_rects, self.skip_rect = draw_pack_select_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if getattr(self, 'skip_rect', None) and self.skip_rect.collidepoint(mouse_pos):
                self.game.pack_choices = []
                from states.shop import resume_shop
                resume_shop(self.game)
                return
            for j, choice_rect in enumerate(self.choice_rects or []):
                if choice_rect.collidepoint(mouse_pos):
                    chosen = self.game.pack_choices[j]
                    self.game.hand_multipliers[chosen] += PACK_BOOST
                    self.game.pack_choices = []
                    from states.shop import resume_shop
                    resume_shop(self.game)  # Back to shop without rerolling stock
                    break
# states/confirm_sell.py
import pygame
from states.base import State
from states.shop import ShopState  # For returning to shop after confirmation
from screens import draw_shop_screen, draw_confirm_sell_popup
from constants import THEME

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
        self.game.screen.fill(THEME['background'])  # Clear relics
        draw_shop_screen(self.game)  # Redraw shop underneath popup
        self.yes_rect, self.no_rect = draw_confirm_sell_popup(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.yes_rect and self.yes_rect.collidepoint(mouse_pos):
                charm = self.game.equipped_charms.pop(self.game.confirm_sell_index)
                sell_val = charm['cost'] // 2
                self.game.coins += sell_val
                self.game.confirm_sell_index = -1
                self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
            elif self.no_rect and self.no_rect.collidepoint(mouse_pos):
                self.game.confirm_sell_index = -1
                self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
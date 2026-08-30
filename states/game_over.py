# states/game_over.py

import pygame
from states.base import State
from states.splash import SplashState
from screens import draw_game_over_screen
from constants import THEME
import savegame

class GameOverState(State):
    def __init__(self, game):
        super().__init__(game)
        self.restart_rect = None

    def enter(self):
        import savegame
        savegame.delete_save()  # Dead run must not Load back into pouch-select / play

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.restart_rect = draw_game_over_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.restart_rect and self.restart_rect.collidepoint(mouse_pos):
                savegame.delete_save()
                self.game.reset_game()
                self.game.state_machine.change_state(SplashState(self.game))

# states/pause.py
import pygame
import sys
from states.base import State
from states.init import InitState  # For main menu
from screens import draw_pause_menu
from constants import THEME
import savegame

class PauseMenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.button_rects = None  # List of (rect, option) tuples
        self.mute_button_rect = None  # Separate for mute if not in button_rects

    def enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        # Assume draw_pause_menu now returns button_rects and mute_button_rect
        self.button_rects, self.mute_button_rect = draw_pause_menu(self.game)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Resume game
                self.game.state_machine.change_state(self.game.previous_state)
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Resume button (e.g., "Return to Game")
            if self.resume_rect and self.resume_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(self.game.previous_state)
                return
            
            # Menu button (e.g., "Quit to Menu")
            if self.menu_rect and self.menu_rect.collidepoint(mouse_pos):
                from states.blinds import BlindsState  # Lazy import
                self.game.state_machine.change_state(BlindsState(self.game))
                return
            
            # Quit button (e.g., "Quit Game")
            if self.quit_rect and self.quit_rect.collidepoint(mouse_pos):
                # Save before quit
                savegame.save_game(self.game)
                pygame.quit()
                sys.exit()

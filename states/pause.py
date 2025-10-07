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
                from states.game import GameState  # Lazy import
                print("Escape pressed in Pause - Resuming")  # Debug
                self.game.state_machine.change_state(GameState(self.game))  # Direct resume, no load

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.mute_button_rect and self.mute_button_rect.collidepoint(mouse_pos):
                self.game.toggle_mute()
            for rect, opt in self.button_rects or []:
                if rect.collidepoint(mouse_pos):
                    if opt == "Return to Game" or event.key == pygame.K_ESCAPE:
                        from states.game import GameState  # Lazy import
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
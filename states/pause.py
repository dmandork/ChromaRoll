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
                # Resume on ESC
                self.game.is_resuming = True  # Set flag to skip GameState reset
                self.game.state_machine.change_state(self.game.previous_state)
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Unpack button_rects for specific checks (assume order: 0=Resume, 1=Main Menu, 2=Quit)
            if self.button_rects:
                # Resume (index 0)
                if len(self.button_rects) > 0 and self.button_rects[0][0].collidepoint(mouse_pos):
                    self.game.is_resuming = True  # Set flag to skip GameState reset
                    self.game.state_machine.change_state(self.game.previous_state)
                    return
                
                # Main Menu (index 1)
                if len(self.button_rects) > 1 and self.button_rects[1][0].collidepoint(mouse_pos):
                    from states.init import InitState  # Or BlindsState if preferred
                    self.game.state_machine.change_state(InitState(self.game))
                    return
                
                # Quit (index 2)
                if len(self.button_rects) > 2 and self.button_rects[2][0].collidepoint(mouse_pos):
                    # Save before quit
                    savegame.save_game(self.game)
                    pygame.quit()
                    sys.exit()
            
            # Mute toggle (on self.mute_button_rect from draw_pause_menu)
            if self.mute_button_rect and self.mute_button_rect.collidepoint(mouse_pos):
                self.game.toggle_mute()
                print(f"DEBUG: Muted: {self.game.mute}")  # For testing
                return
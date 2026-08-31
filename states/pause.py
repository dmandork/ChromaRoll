# states/pause.py
import pygame
import sys
from states.base import State
from states.init import InitState  # For main menu
from screens import draw_pause_menu, draw_table_felt
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
        prev = getattr(self.game, 'previous_state', None)
        drawn = False
        if prev is not None and prev is not self and hasattr(prev, 'draw'):
            try:
                prev.draw()
                drawn = True
            except Exception:
                drawn = False
        if not drawn:
            draw_table_felt(self.game)
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
                for rect, opt in self.button_rects:
                    if not rect.collidepoint(mouse_pos):
                        continue
                    if opt == "Return to Game":
                        self.game.is_resuming = True
                        self.game.state_machine.change_state(self.game.previous_state)
                        return
                    if opt == "Achievements":
                        from states.achievements import AchievementsState
                        self.game.achievements_return = 'pause'
                        self.game.state_machine.change_state(AchievementsState(self.game))
                        return
                    if opt == "Main Menu":
                        from states.splash import SplashState
                        savegame.save_game(self.game)  # keep the run for Load Game
                        self.game.state_machine.change_state(SplashState(self.game))
                        return
                    if opt == "Quit":
                        savegame.save_on_exit(self.game)
                        pygame.quit()
                        sys.exit()
            
            # Mute toggle (on self.mute_button_rect from draw_pause_menu)
            if self.mute_button_rect and self.mute_button_rect.collidepoint(mouse_pos):
                self.game.toggle_mute()
                print(f"DEBUG: Muted: {self.game.mute}")  # For testing
                return
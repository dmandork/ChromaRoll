# states/achievements.py
import pygame
import time
from constants import THEME, DEBUG
from states.base import State
from screens import draw_achievements_screen
import achievements as ach


class AchievementsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.tab = 'quests'
        self.scroll_y = 0
        self.back_rect = None
        self.tab_rects = {}
        self.debug_rects = []

    def enter(self):
        # Menu overlay — do not auto-save over a run.
        ach.attach_progress(self.game)
        self.scroll_y = 0

    def update(self, dt):
        pass

    def draw(self):
        self.back_rect, self.tab_rects, self.debug_rects, self.scroll_y = draw_achievements_screen(
            self.game, tab=self.tab, scroll_y=self.scroll_y, debug=DEBUG)

    def _go_back(self):
        origin = getattr(self.game, 'achievements_return', 'splash')
        if origin == 'pause':
            from states.pause import PauseMenuState
            self.game.state_machine.change_state(PauseMenuState(self.game))
        else:
            from states.splash import SplashState
            self.game.state_machine.change_state(SplashState(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
                return
            if event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 48)
            elif event.key == pygame.K_DOWN:
                self.scroll_y += 48
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - event.y * 40)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self._go_back()
                return
            for name, rect in (self.tab_rects or {}).items():
                if rect.collidepoint(mouse_pos):
                    self.tab = name
                    self.scroll_y = 0
                    return
            for rect, action in self.debug_rects or []:
                if rect.collidepoint(mouse_pos):
                    if action == 'unlock_all':
                        ach.unlock_all(self.game)
                        self.game.temp_message = "All achievements unlocked (debug)"
                        self.game.temp_message_start = time.time()
                    elif action == 'reset':
                        ach.reset_progress(self.game)
                        self.game.temp_message = "Achievement progress reset"
                        self.game.temp_message_start = time.time()
                    return

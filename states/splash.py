# states/splash.py
import os
import pygame
import time
import sys
from constants import *  # Absolute: Assumes run from root
from utils import get_easing, draw_rounded_element, wrap_text, resource_path
from screens import draw_splash_screen
from states.prompt import PromptState  # For transition after splash if needed
from states.init import InitState
from states.base import State

class SplashState(State):
    def __init__(self, game):
        super().__init__(game)
        self.new_game_rect = None
        self.load_game_rect = None
        self.quit_rect = None

    def enter(self):
        self.game.splash_start_time = 0
        if not hasattr(self.game, 'splash_total_start') or self.game.splash_total_start == 0:
            self.game.splash_total_start = 0
        self.game.splash_phase = 'pan'

    def update(self, dt):
        current_time = time.time()
        if self.game.splash_start_time == 0:
            self.game.splash_start_time = current_time
        if self.game.splash_total_start == 0:
            self.game.splash_total_start = current_time

        time_elapsed = current_time - self.game.splash_start_time
        total_elapsed = current_time - self.game.splash_total_start

        image_width, image_height = self.game.splash_image.get_size()
        current_zoom = SPLASH_INITIAL_ZOOM
        visible_height = self.game.height / current_zoom
        focus_y = 0

        if self.game.splash_phase == 'pan':
            progress = min(time_elapsed / SPLASH_DURATION_PAN, 1.0)
            easing_progress = get_easing(progress, SPLASH_EASING)
            start_focus_y = image_height - visible_height / 2
            end_focus_y = visible_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress
            if time_elapsed >= SPLASH_DURATION_PAN:
                self.game.splash_phase = 'hold'
                self.game.splash_start_time = current_time

        elif self.game.splash_phase == 'hold':
            visible_height = self.game.height / SPLASH_INITIAL_ZOOM
            focus_y = visible_height / 2
            if time_elapsed >= SPLASH_DURATION_HOLD:
                self.game.splash_phase = 'zoom_out'
                self.game.splash_start_time = current_time

        elif self.game.splash_phase == 'zoom_out':
            progress = min(time_elapsed / SPLASH_DURATION_ZOOM_OUT, 1.0)
            easing_progress = get_easing(progress, SPLASH_EASING)
            fit_zoom = self.game.height / image_height
            current_zoom = SPLASH_INITIAL_ZOOM - (SPLASH_INITIAL_ZOOM - fit_zoom) * easing_progress
            visible_height = self.game.height / current_zoom
            start_focus_y = (self.game.height / SPLASH_INITIAL_ZOOM) / 2
            end_focus_y = image_height / 2
            focus_y = start_focus_y + (end_focus_y - start_focus_y) * easing_progress
            if time_elapsed >= SPLASH_DURATION_ZOOM_OUT:
                self.game.splash_phase = 'done'

        elif self.game.splash_phase == 'done':
            fit_zoom = self.game.height / image_height
            current_zoom = fit_zoom
            visible_height = self.game.height / current_zoom
            focus_y = image_height / 2

        # Add view_y calculation, etc. (your full block)
        # ...

        # Auto-transition if total time up (or button logic in handle_event)
        total_duration = SPLASH_DURATION_PAN + SPLASH_DURATION_HOLD + SPLASH_DURATION_ZOOM_OUT
        if total_elapsed >= total_duration:
            self.game.splash_phase = 'done'  # Ensure 'done'

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        rects = draw_splash_screen(self.game)
        if rects is not None:
            self.new_game_rect, self.load_game_rect, self.quit_rect = rects

    def handle_event(self, event):
        # Moved from old run()'s event blocks for splash
        if event.type == pygame.KEYDOWN:
            if event.key in SPLASH_SKIP_KEYS:
                self.game.splash_phase = 'done'  # Skip

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.game.splash_phase == 'done':
                # Use stored rects from draw()
                if self.new_game_rect and self.new_game_rect.collidepoint(mouse_pos):
                    if os.path.exists('save.json'):  # Direct check instead of load_game return
                        print("Save found, showing prompt")
                        self.game.state_machine.change_state(PromptState(self.game))
                    else:
                        print("No save, starting new")
                        self.game.state_machine.change_state(InitState(self.game))
                    pass
                elif self.quit_rect and self.quit_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
            else:
                self.game.splash_phase = 'done'  # Jump to done on click
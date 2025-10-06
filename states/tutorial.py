# states/tutorial.py
import pygame
import time  # If used for timers/animations
from constants import *  # For THEME, BUTTON_WIDTH, etc.
from utils import get_easing, draw_rounded_element, wrap_text, resource_path  # If used for UI
from screens import draw_tutorial_screen, draw_custom_button  # For main drawing/buttons
from statemachine import State
# Import referenced states (e.g., InitState for change_state calls)
# If other states like BlindsState are referenced, add them (e.g., from statemachine import BlindsState if not extracted)

class TutorialState(State):
    def __init__(self, game):
        super().__init__(game)
        self.left_rect = None
        self.right_rect = None
        self.skip_rect = None

    def enter(self):
        self.game.tutorial_step = 0  # Reset to beginning

    def update(self, dt):
        pass  # No ongoing animations? Leave empty

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.left_rect, self.right_rect, self.skip_rect = draw_tutorial_screen(self.game)

    def handle_event(self, event):
        from states.init import InitState  # Lazy import here to break cycle
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.game.tutorial_step = min(5, self.game.tutorial_step + 1)  # Next, clamp to max
                if self.game.tutorial_step > 5:
                    self.game.tutorial_completed = True
                    self.game.tutorial_mode = False
                    self.game.state_machine.change_state(InitState(self.game))
            elif event.key == pygame.K_BACKSPACE:  # Optional: Key for back
                self.game.tutorial_step = max(0, self.game.tutorial_step - 1)
            elif event.key == pygame.K_ESCAPE:
                self.game.tutorial_completed = True
                self.game.tutorial_mode = False
                self.game.state_machine.change_state(InitState(self.game))  # Skip

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.left_rect and self.left_rect.collidepoint(mouse_pos):
                self.game.tutorial_step = max(0, self.game.tutorial_step - 1)  # Back
            if self.right_rect and self.right_rect.collidepoint(mouse_pos):
                self.game.tutorial_step += 1
                if self.game.tutorial_step > 5:
                    self.game.tutorial_completed = True
                    self.game.tutorial_mode = False
                    self.game.state_machine.change_state(InitState(self.game))
            if self.skip_rect and self.skip_rect.collidepoint(mouse_pos):
                self.game.tutorial_completed = True
                self.game.tutorial_mode = False
                self.game.state_machine.change_state(InitState(self.game))  # Skip
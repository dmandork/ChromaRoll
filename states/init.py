# states/init.py
import time
import pygame
from constants import *  # For THEME, BUTTON_WIDTH, etc.
from utils import draw_rounded_element, resource_path  # If used for buttons/tooltips
from screens import draw_init_screen, draw_custom_button  # For main drawing and buttons
from states.base import State  # Keep these if not extracted
from states.tutorial import TutorialState  # New location for TutorialState
from states.blinds import BlindsState
# If references other states (e.g., change to GameState), import them
# from states.game import GameState  # Add when extracted; else from statemachine import GameState

class InitState(State):
    def enter(self):
        # New: Re-set temp_message start if message is pending (for timing fix)
        if self.game.temp_message:
            self.game.temp_message_start = time.time()  # Reset timer on enter
            print("DEBUG: Re-set temp_message_start in InitState")  # Confirm (remove after)
        self.game.pouch_offset = 0  # Reset if needed
        self.pouch_rects = None
        self.tutorial_rect = None
        self.left_arrow_rect = None
        self.right_arrow_rect = None  # Store for handle_event

    def update(self, dt):
        pass  # No animations? Leave empty or add if carousel animates

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        self.pouch_rects, self.tutorial_rect, self.left_arrow_rect, self.right_arrow_rect = draw_init_screen(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for idx, rect in enumerate(self.pouch_rects or []):
                if rect.collidepoint(mouse_pos):
                    pouch = data.POUCHES[self.game.pouch_offset + idx]
                    if pouch.get('unlocked', False):
                        self.game.apply_pouch(pouch)
                        self.game.state_machine.change_state(BlindsState(self.game))  # To 'blinds'
                    break
            if self.tutorial_rect and self.tutorial_rect.collidepoint(mouse_pos):
                self.game.tutorial_mode = True
                self.game.tutorial_step = 0
                self.game.state_machine.change_state(TutorialState(self.game))  # To 'tutorial'
            if self.left_arrow_rect and self.left_arrow_rect.collidepoint(mouse_pos):
                self.game.pouch_offset = max(0, self.game.pouch_offset - 4)
            if self.right_arrow_rect and self.right_arrow_rect.collidepoint(mouse_pos):
                if self.pouch_rects and self.game.pouch_offset < len(data.POUCHES) - len(self.pouch_rects):
                    self.game.pouch_offset += 4
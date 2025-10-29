import pygame
import time
import random
from states.base import State
from constants import *  # THEME, etc.
from utils import tint_image, resource_path  # FIXED: Import resource_path
from data import D20_OUTCOMES  # FIXED: Import the outcomes dict

# In states/d20_roll.py, update __init__ for scale
class D20RollState(State):
    def __init__(self, game, blind_type):
        super().__init__(game)
        self.blind_type = blind_type  # 'Small', 'Big', 'Boss'—for context
        self.d20_image = pygame.image.load(resource_path('assets/icons/D20.png')).convert_alpha()  # Blank base
        orig_w, orig_h = self.d20_image.get_size()
        self.d20_image = pygame.transform.smoothscale(self.d20_image, (orig_w // 2, orig_h // 2))  # Shrink by half
        self.d20_rect = self.d20_image.get_rect(center=(game.width // 2, game.height // 2))
        self.roll_start_time = time.time()
        self.roll_duration = 2.0  # Shorten to 2 seconds
        self.roll_result = None  # Final 1-20
        self.outcome = None  # Dict from data.py
        self.font = pygame.font.Font(resource_path(THEME['font_main_path']), 48)  # Big for center number
        self.small_font = pygame.font.Font(resource_path(THEME['font_small_path']), 24)  # For desc
        self.phase = 'rolling'  # 'rolling', 'reveal', 'done'

    def update(self, dt):
        if self.phase == 'rolling':
            elapsed = time.time() - self.roll_start_time
            if elapsed >= self.roll_duration:
                self.roll_result = random.randint(1, 20)
                self.outcome = self.get_outcome(self.roll_result)  # From data.py dict
                self.phase = 'done'  # Direct to done (persistent)
                self.apply_downside()  # Immediate effects (e.g., target change)
        elif self.phase == 'reveal':
            elapsed = time.time() - self.reveal_start_time
            if elapsed >= 2.0:  # Show outcome for 2s, then done
                self.phase = 'done'
                self.apply_downside()  # Immediate effects (e.g., target change)

    def draw(self):
        self.game.screen.fill(THEME['background'])
        # Draw tinted D20 (e.g., gray for now; color later by tier)
        tinted_d20 = tint_image(self.d20_image, (200, 200, 200))  # Example gray
        self.game.screen.blit(tinted_d20, self.d20_rect.topleft)

        # Shuffle/reveal number
        if self.phase == 'rolling':
            # Cycle 1-20 rapidly
            num = random.randint(1, 20)
            text = self.font.render(str(num), True, THEME['text'])
            text_rect = text.get_rect(center=self.d20_rect.center)
            self.game.screen.blit(text, text_rect)
        elif self.phase == 'done':
            text = self.font.render(str(self.roll_result), True, THEME['text'])
            text_rect = text.get_rect(center=self.d20_rect.center)
            self.game.screen.blit(text, text_rect)
            # Show outcome desc below (persistent)
            if self.outcome:
                desc = f"{self.outcome['name']}: {self.outcome['desc']}"
                desc_text = self.small_font.render(desc, True, THEME['text'])
                self.game.screen.blit(desc_text, (self.game.width // 2 - desc_text.get_width() // 2, self.d20_rect.bottom + 20))

        # Done button (after reveal)
        if self.phase == 'done':
            button_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
            pygame.draw.rect(self.game.screen, (100, 100, 100), button_rect)
            button_text = self.small_font.render("Accept & Proceed", True, THEME['text'])
            self.game.screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2, button_rect.centery - button_text.get_height() // 2))
            self.accept_rect = button_rect  # For click

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.phase == 'done':
            if hasattr(self, 'accept_rect') and self.accept_rect.collidepoint(event.pos):
                # Proceed to intensified GameState
                from states.game import GameState
                self.game.state_machine.change_state(GameState(self.game))

    def get_outcome(self, roll):
        # Tier lookup (from data.py - add the dict below)
        for tier in D20_OUTCOMES:
            if tier['min'] <= roll <= tier['max']:
                return tier['outcome']  # Fixed outcome dict

    def apply_downside(self):
        if self.outcome:
            self.game.target_mult = self.outcome['downside']['target_mult']  # e.g., 1.5 for +50%
            # Add other downsides (e.g., self.game.disable_hand = random.choice(HAND_TYPES))
            self.game.intensified_buff = self.outcome['buff']  # Store for win trigger
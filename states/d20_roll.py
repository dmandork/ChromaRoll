import pygame
import time
import random
from states.base import State
from constants import *  # THEME, etc.
from utils import tint_image, resource_path, draw_rounded_element  # FIXED: Import resource_path
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
        self.debug_tier_open = False  # NEW: For dropdown

    def update(self, dt):
        if self.phase == 'rolling':
            elapsed = time.time() - self.roll_start_time
            if elapsed >= self.roll_duration:
                self.roll_result = random.randint(1, 20)
                self.outcome = self.get_outcome(self.roll_result)  # FIXED: Set for desc preview
                self.phase = 'done'  # To done (desc visible, no flags yet)
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

        # Done button (after reveal) - FIXED: Guard hasattr
        self.accept_rect = None  # Reset each draw
        if self.phase == 'done':
            button_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
            pygame.draw.rect(self.game.screen, (100, 100, 100), button_rect)
            button_text = self.small_font.render("Accept & Proceed", True, THEME['text'])
            self.game.screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2, button_rect.centery - button_text.get_height() // 2))
            self.accept_rect = button_rect  # For click

        # NEW: DEBUG Tier Selector (upper left, like blinds dropdown)
        if DEBUG:
            self.debug_tier_rect = pygame.Rect(10, 10, 120, 30)
            draw_rounded_element(self.game.screen, self.debug_tier_rect, (50, 50, 50), radius=5)
            tier_text = self.small_font.render("Test Tier", True, (255, 255, 255))
            self.game.screen.blit(tier_text, (self.debug_tier_rect.centerx - tier_text.get_width() // 2, self.debug_tier_rect.centery - tier_text.get_height() // 2))
            
            # Dropdown options if open (5 tiers)
            if self.debug_tier_open:
                mouse_pos = pygame.mouse.get_pos()  # FIXED: Define here for draw hover
                y_offset = self.debug_tier_rect.bottom + 5
                for tier in range(1, 6):  # 1=worst, 5=best
                    opt_rect = pygame.Rect(10, y_offset, 120, 25)
                    color = (70, 70, 70) if opt_rect.collidepoint(mouse_pos) else (40, 40, 40)
                    draw_rounded_element(self.game.screen, opt_rect, color, radius=3)
                    opt_text = self.small_font.render(f"Tier {tier}", True, (255, 255, 255))
                    self.game.screen.blit(opt_text, (opt_rect.centerx - opt_text.get_width() // 2, opt_rect.centery - opt_text.get_height() // 2))
                    y_offset += 27

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos  # Precise clicks (scoped to mouse events)
            if self.phase == 'done':
                if hasattr(self, 'accept_rect') and self.accept_rect.collidepoint(mouse_pos):
                    # FIXED: Apply flags/buff/temp on accept (delayed)
                    self.outcome = self.get_outcome(self.roll_result)  # Now set outcome
                    self.apply_downside()  # Flags, message, buff—post-commit
                    # NEW: Flag for GameState enter (force pull + buff apply)
                    self.game.from_d20_intensify = True  # Temp flag
                    from states.game import GameState
                    self.game.state_machine.change_state(GameState(self.game))
                    # Clear flag post-transition (in GameState enter, after use)
            
            # FIXED: DEBUG Tier Selector (click button to open; click opt to select/close) - fully nested under MOUSEBUTTONDOWN
            if DEBUG:
                if hasattr(self, 'debug_tier_rect') and self.debug_tier_rect.collidepoint(mouse_pos):
                    self.debug_tier_open = not self.debug_tier_open  # Toggle on button click (stays open)
                    return  # Early exit to ignore other clicks while toggling
                
                if self.debug_tier_open:
                    y_offset = self.debug_tier_rect.bottom + 5
                    for tier in range(1, 6):
                        opt_rect = pygame.Rect(10, y_offset, 120, 25)
                        if opt_rect.collidepoint(mouse_pos):
                            self.roll_result = tier * 4 - 2  # e.g., Tier 1:2 (1-4), Tier 5:18 (17-20)
                            self.outcome = self.get_outcome(self.roll_result)  # Re-apply (for desc)
                            self.debug_tier_open = False  # Close on tier select
                            print(f"DEBUG: Forced Tier {tier} - result: {self.roll_result}, outcome: {self.outcome['name']}")
                            break  # Stop after select
                        y_offset += 27

    def get_outcome(self, roll):
        # Tier lookup (from data.py - add the dict below)
        for tier in D20_OUTCOMES:
            if tier['min'] <= roll <= tier['max']:
                return tier['outcome']  # Fixed outcome dict

    def apply_downside(self):
        if self.outcome:
            # Base target mult
            self.game.target_mult = self.outcome['downside'].get('target_mult', 1.0)
            
            # Fusion twist (assume self.game.fused_color set elsewhere; fallback random)
            fused = getattr(self.game, 'fused_color', None)
            if fused:
                # Override randoms with fused (e.g., dimmed_color = fused)
                if 'dimmed_color' in self.outcome['downside']:
                    self.outcome['downside']['dimmed_color'] = fused
                # Similar for disabled_type/locked_die (e.g., lock a fused-color die)
            
            # Store flags for this blind (use intensified_ prefix to scope)
            self.game.intensified_disabled_type = self.outcome['downside'].get('disabled_type')
            self.game.intensified_dimmed_color = self.outcome['downside'].get('dimmed_color')
            self.game.intensified_locked_die_idx = self.outcome['downside'].get('locked_die_idx', -1)
            self.game.intensified_global_color_mult = self.outcome['downside'].get('global_color_mult', 1.0)
            
            # Store buff for win reward
            self.game.intensified_buff = self.outcome['buff']

            if self.outcome['name'] == 'Roll Harmony':
                self.game.roll_harmony_active = True
                self.game.intensified_locked_die_idx = -1
                print("DEBUG: Roll Harmony flag set on game")
            
            # Temp message for feedback
            self.game.temp_message = f"{self.outcome['name']}: {self.outcome['desc']}"
            self.game.temp_message_start = time.time()

            # NEW: Temp message with color (if any) for return feedback
            msg = f"{self.outcome['name']}: {self.outcome['desc']}"
            if self.game.intensified_disabled_type:
                msg += f" Blocked: {self.game.intensified_disabled_type}"
            elif self.game.intensified_dimmed_color:
                msg += f" Dimmed: {self.game.intensified_dimmed_color} (-20%)"

            # NEW: Roll Flow - Flag for advantage selection on first hand
            if self.outcome['name'] == 'Roll Flow':
                self.game.selecting_advantage_die = True
                msg += " Select die for advantage!"

            self.game.temp_message = msg
            self.game.temp_message_start = time.time()
            
            # FIXED: Log all relevant (disabled + dimmed)
            print(f"DEBUG: Applied {self.outcome['name']} - target_mult: {self.game.target_mult}, disabled: {self.game.intensified_disabled_type}, dimmed_color: {self.game.intensified_dimmed_color}")
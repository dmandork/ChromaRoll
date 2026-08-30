# states/end_prompt.py
import pygame
import copy  # For deepcopy
import random  # For random faces in rolls
from .base import State  # Matches your base.py export
from constants import NUM_DICE_IN_HAND  # Absolute import for held reset

def draw_text_centered(surface, text, font, color, y, x=0, width=0):
    """Raw fallback: Center text horizontally at y, optional x/width bounds."""
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if width > 0:
        text_rect.centerx = x + width // 2
    else:
        text_rect.centerx = surface.get_width() // 2
    text_rect.centery = y
    surface.blit(text_surf, text_rect)

def draw_button(surface, rect, text, color, font):
    """Raw fallback: Draw filled button rect with centered text."""
    # Button bg
    pygame.draw.rect(surface, color, rect, border_radius=5)
    # Border
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=5)
    # Text
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

class EndPromptState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_large = pygame.font.Font(None, 48)  # Or your custom
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Buttons will be set in enter() with dynamic sizing
        self.buttons = {}
        
        # Dynamic summary (stub total_score if not tracked; achievements as 0 for now)
        total_score = getattr(self.game, 'total_score', 0)  # Add tracking in score_and_new_turn if needed
        ach_ids = []
        progress = getattr(self.game, 'progress', None) or {}
        ach_ids = progress.get('new_this_run') or []
        ach_count = len(ach_ids)
        self.summary_text = [
            f"Run Complete! Stake 8 Conquered",
            f"Total Score: {total_score:,}",
            f"Achievements Unlocked This Run: {ach_count}"
        ]

    def enter(self):
        # Optional SFX stubs
        # pygame.mixer.music.pause()
        # victory_sound = pygame.mixer.Sound('assets/sfx/victory.wav')
        # victory_sound.play()
        # Do not write EndPromptState into save.json — Load would then no-op.
        
        # Dynamic button setup using screen dims
        screen_width = self.game.screen.get_width()
        screen_height = self.game.screen.get_height()
        btn_width, btn_height = 250, 60
        y_start = screen_height // 2 + 100  # Increased spacing for buttons
        self.buttons = {
            'endless': {
                'rect': pygame.Rect(screen_width // 2 - btn_width // 2, y_start, btn_width, btn_height),
                'text': 'Continue to Endless Mode',
                'color': (0, 255, 0),
                'hover_color': (0, 200, 0)
            },
            'menu': {
                'rect': pygame.Rect(screen_width // 2 - btn_width // 2, y_start + 80, btn_width, btn_height),
                'text': 'Main Menu',
                'color': (255, 100, 100),
                'hover_color': (200, 50, 50)
            }
        }

    def exit(self):
        # Resume music stub
        # if self.game.is_endless:
        #     pygame.mixer.music.unpause()
        pass

    def update(self, dt):
        pass  # Static

    def handle_event(self, event):  # Note: Your states use handle_event, not handle_events
        mouse_pos = pygame.mouse.get_pos()
        for name, btn in self.buttons.items():
            if btn['rect'].collidepoint(mouse_pos):
                btn['color'] = btn['hover_color']
            else:
                btn['color'] = (0, 255, 0) if name == 'endless' else (255, 100, 100)
        
        if event.type == pygame.QUIT:
            import savegame
            savegame.save_on_exit(self.game)
            return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._to_menu()
            elif event.key == pygame.K_RETURN:
                self._to_endless()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for name, btn in self.buttons.items():
                    if btn['rect'].collidepoint(event.pos):
                        if name == 'endless':
                            self._to_endless()
                        elif name == 'menu':
                            self._to_menu()

    def draw(self):
        surface = self.game.screen  # Use game.screen instead of param to match base.py call
        screen_height = surface.get_height()  # Dynamic, no constants
        surface.fill((20, 20, 40))  # Dark bg
        
        # Title (top, more space)
        draw_text_centered(surface, "Victory!", self.font_large, (255, 215, 0), screen_height // 6)
        draw_text_centered(surface, "You've beaten ChromaRoll!", self.font, (255, 255, 255), screen_height // 6 + 60)
        
        # Summary (middle, increased line spacing)
        y_offset = screen_height // 3
        for line in self.summary_text:
            draw_text_centered(surface, line, self.font_small, (200, 200, 200), y_offset)
            y_offset += 40  # Increased gap to avoid overlap
        
        # Prompt (lower middle, more space)
        draw_text_centered(surface, "Enter Endless Mode?", self.font, (255, 255, 255), y_offset + 60)
        draw_text_centered(surface, "(Infinite stakes await...)", self.font_small, (150, 150, 150), y_offset + 90)

        # Buttons (bottom, centered)
        for btn in self.buttons.values():
            draw_button(surface, btn['rect'], btn['text'], btn['color'], self.font_small)

    def _to_endless(self):
        self.game.is_endless = True
        self.game.extra_rounds = 0
        # Leverage the existing advance_blind method to handle all resets, bag refill, hand/reroll/discard resets,
        # boss effect preview, and set current_stake=9, current_blind='Small' (assuming called after 'Boss')
        # This mimics the normal post-boss progression exactly, ensuring everything is set up correctly.
        self.game.advance_blind()
        # Transition to BlindsState to show the stake 9 layout (small/big/boss), allowing normal proceed to game
        # (where new_turn/rolls init likely happens). This avoids skipping setup and matches "entering stake 9 small blind".
        from .blinds import BlindsState  # type: ignore  # Lazy import
        self.game.state_machine.change_state(BlindsState(self.game))

    def _to_menu(self):
        import savegame
        savegame.delete_save()
        self.game.reset_game()
        from .splash import SplashState
        self.game.state_machine.change_state(SplashState(self.game))
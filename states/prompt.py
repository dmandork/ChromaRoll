# states/prompt.py
import pygame
import time  # For time.time()
import os  # For os.path.exists if needed
import savegame  # Module import for savegame.load_game and savegame.delete_save
from constants import *  # For THEME, BUTTON_WIDTH, etc.
from screens import draw_custom_button, draw_table_felt, draw_gold_plaque, TABLE_GOLD
from screens import draw_confirm_sell_popup  # If used; remove if not needed
# Import unextracted states (they're still in statemachine.py until you move them)
from states.shop import ShopState
from states.init import InitState
from states.blinds import BlindsState
from states.base import State
from states.game import GameState

class PromptState(State):
    def __init__(self, game):
        super().__init__(game)
        self.yes_rect = None
        self.no_rect = None

    def enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self):
        draw_table_felt(self.game)
        plaque = pygame.Rect(self.game.width // 2 - 260, self.game.height // 2 - 120, 520, 220)
        draw_gold_plaque(self.game, plaque, radius=16)
        prompt_text = self.game.font.render("Resume previous run?", True, TABLE_GOLD)
        self.game.screen.blit(prompt_text, (self.game.width // 2 - prompt_text.get_width() // 2, plaque.y + 36))
        self.yes_rect = pygame.Rect(self.game.width // 2 - 150, plaque.bottom - 80, 120, 44)
        draw_custom_button(self.game, self.yes_rect, "Yes",
                           is_hover=self.yes_rect.collidepoint(pygame.mouse.get_pos()),
                           fill_color=THEME.get('yes_button', (0, 150, 0)))
        self.no_rect = pygame.Rect(self.game.width // 2 + 30, plaque.bottom - 80, 120, 44)
        draw_custom_button(self.game, self.no_rect, "No",
                           is_hover=self.no_rect.collidepoint(pygame.mouse.get_pos()), is_red=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.yes_rect and self.yes_rect.collidepoint(mouse_pos):
                print("Resuming save")
                save_data = savegame.load_game(self.game)  # Single call
                if save_data:
                    # Resume to saved state (existing code)
                    saved_state = save_data.get('current_state')
                    saved_previous = save_data.get('previous_state')
                    resume_state = saved_previous if saved_state == 'PauseMenuState' else saved_state
                    if resume_state == 'GameState':
                        self.game.state_machine.change_state(GameState(self.game))
                    elif resume_state == 'ShopState':
                        self.game.state_machine.change_state(ShopState(self.game))
                    elif resume_state == 'BlindsState':
                        self.game.state_machine.change_state(BlindsState(self.game))
                    else:
                        self.game.state_machine.change_state(InitState(self.game))  # Fallback
                else:
                    # New: Handle corrupt/missing save
                    self.game.temp_message = "Save file corrupted or missing—starting new game."
                    self.game.temp_message_start = time.time()
                    savegame.delete_save()  # Optional: Clean up corrupt file
                    self.game.reset_game()
                    self.game.state_machine.change_state(InitState(self.game))  # Start fresh
            elif self.no_rect and self.no_rect.collidepoint(mouse_pos):
                print("Deleting save, starting new")
                savegame.delete_save()
                self.game.reset_game()  # Call reset to freshen all vars (bag, coins, etc.)
                self.game.state_machine.change_state(InitState(self.game))  # Start fresh
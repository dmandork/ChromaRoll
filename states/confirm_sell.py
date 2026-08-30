# states/confirm_sell.py
import pygame
import time
from states.base import State
from states.shop import ShopState  # For returning to shop after confirmation
from screens import draw_shop_screen, draw_confirm_sell_popup
from constants import THEME
from scoring import mortgage_sell_payout
from achievements import notify

class ConfirmSellState(State):
    def __init__(self, game):
        super().__init__(game)
        self.yes_rect = None
        self.no_rect = None

    def enter(self):
        pass  # Any setup, e.g., confirm index already set

    def update(self, dt):
        pass

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        draw_shop_screen(self.game)  # Redraw shop underneath popup
        self.yes_rect, self.no_rect = draw_confirm_sell_popup(self.game)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.yes_rect and self.yes_rect.collidepoint(mouse_pos):
                sell_idx = self.game.confirm_sell_index
                payout, lock_charm, used = mortgage_sell_payout(
                    self.game.equipped_charms,
                    sell_idx,
                    disabled=getattr(self.game, 'disabled_charms', []) or [],
                    already_used=getattr(self.game, 'mortgage_used_this_round', False),
                )
                charm = self.game.equipped_charms.pop(sell_idx)
                self.game.coins += payout
                notify(self.game, 'sell')
                if used:
                    self.game.mortgage_used_this_round = True
                if lock_charm is not None:
                    lock_charm['locked'] = True
                    self.game.temp_message = (
                        f"Mortgage: sold {charm.get('name', 'charm')} for ${payout} (2x). "
                        f"Locked until next shop."
                    )
                    self.game.temp_message_start = time.time()
                elif charm.get('type') == 'sell_double_lock':
                    self.game.temp_message = f"Mortgage cashed out: ${payout} (2x)"
                    self.game.temp_message_start = time.time()
                # **REPLACED: Set Luchador flag (persistent until boss done)**
                if charm['name'] == 'Luchador Lens':
                    if self.game.current_round == 8:  # Final boss exception
                        self.game.temp_message = "Luchador sold, but final boss cannot be disabled."
                        self.game.temp_message_start = time.time()
                    else:
                        self.game.luchador_disable_active = True
                        self.game.temp_message = "Luchador sold! Boss will be disabled next boss round."
                        self.game.temp_message_start = time.time()
                        print("DEBUG: Luchador flag set from shop")
                self.game.confirm_sell_index = -1
                self.game.state_machine.change_state(ShopState(self.game))  # Back to shop
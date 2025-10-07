# states/shop.py
import pygame
import random  # If used for shop generation
import time
import copy
import os
from constants import *  # For THEME, BUTTON_WIDTH, SHOP_REROLL_COST, etc.
from utils import draw_rounded_element, resource_path, wrap_text  # For UI/buttons
from screens import draw_shop_screen, draw_custom_button, draw_tooltip  # For main shop drawing/buttons
from data import CHARMS_POOL  # For charm generation/packs
from states.base import State  # Updated: Import base State here
# Import extracted states if referenced (e.g., for continue/back buttons)
from states.debug import DebugMenuState
from states.pause import PauseMenuState
from states.rune import RuneSelectState, RuneUseState
from states.dice_select import DiceSelectState
from states.pack_select import PackSelectState
from states.confirm_sell import ConfirmSellState

class ShopState(State):
    def __init__(self, game):
        super().__init__(game)
        self.continue_rect = None
        self.sell_rects = None
        self.buy_rects = None
        self.equipped_rects = None
        self.shop_rects = None
        self.pack_rects = None
        self.reroll_rect = None
        self.debug_rect = None  # For debug button
        self.debug_panel_open = False  # Flag for debug panel
        self.scroll_y = 0  # For debug panel scrolling
        self.charm_rects = []  # Store debug panel rects
        self.tray_rects = []  # For tray clicks
        self.debug_button_rect = None  # New for debug menu button

    def enter(self):
        # Generate shop if empty
        if not self.game.shop_charms:
            self.game.generate_shop()
        self.debug_panel_open = False  # Reset panel
        self.scroll_y = 0  # Reset scroll

    def update(self, dt):
        pass  # Expand for animations if needed

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        # Draw shop, but pass debug_panel_open to skip tooltips when panel is open
        self.continue_rect, self.sell_rects, self.buy_rects, self.equipped_rects, self.shop_rects, self.pack_rects, self.reroll_rect = draw_shop_screen(self.game, skip_tooltips=self.debug_panel_open)
        
        # Debug button (bottom-right to avoid prism packs)
        if DEBUG:
            button_x = self.game.width - DEBUG_BUTTON_SIZE[0] - 50  # Bottom-right
            button_y = self.game.height - DEBUG_BUTTON_SIZE[1] - 50
            self.debug_rect = pygame.Rect(button_x, button_y, *DEBUG_BUTTON_SIZE)
            draw_custom_button(self.game, self.debug_rect, DEBUG_BUTTON_TEXT, 
                              is_hover=self.debug_rect.collidepoint(pygame.mouse.get_pos()))
            
            # Draw debug panel if open
            if self.debug_panel_open:
                self.charm_rects = self.draw_debug_panel()
            else:
                self.charm_rects = []

            # Add this: New debug menu button (e.g., next to existing debug button)
            if DEBUG and DEBUG_MENU_IN_SHOP:
                # Position: Below or beside existing debug button (adjust coords as needed)
                self.debug_button_rect = pygame.Rect(button_x, button_y - 60, 150, 50)  # Above existing, example
                draw_custom_button(self.game, self.debug_button_rect, "Debug Menu", is_hover=self.debug_button_rect.collidepoint(pygame.mouse.get_pos()))

    def handle_event(self, event):
        from states.blinds import BlindsState  # Lazy import here - loads only when method runs
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.previous_state = self.game.state_machine.current_state
                self.game.state_machine.change_state(PauseMenuState(self.game))
            elif DEBUG and self.debug_panel_open:
                # Keyboard scrolling
                icons_per_row = 4
                row_height = 100 + 50  # Match draw_debug_panel
                num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
                total_content_height = num_rows * row_height + 70
                max_scroll = max(0, total_content_height - DEBUG_PANEL_HEIGHT)
                if event.key == pygame.K_UP:
                    self.scroll_y = max(0, self.scroll_y - 50)
                elif event.key == pygame.K_DOWN:
                    self.scroll_y = min(self.scroll_y + 50, max_scroll)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle debug button
            if DEBUG and self.debug_rect and self.debug_rect.collidepoint(mouse_pos):
                self.debug_panel_open = not self.debug_panel_open
                print(f"DEBUG: Panel {'opened' if self.debug_panel_open else 'closed'}")
                return
            
            # Handle debug panel interactions
            if DEBUG and self.debug_panel_open:
                for rect, action in self.charm_rects:
                    if rect.collidepoint(mouse_pos):
                        if action == 'close':
                            self.debug_panel_open = False
                            self.game.temp_message = "Debug panel closed"
                            self.game.temp_message_start = time.time()
                        elif action == 'equip_all':
                            for charm in data.CHARMS_POOL:
                                if charm['name'] not in [c['name'] for c in self.game.equipped_charms] and len(self.game.equipped_charms) < self.game.max_charms * 2:
                                    self.game.equipped_charms.append(copy.deepcopy(charm))
                            print("DEBUG: Equipped all available charms!")
                            self.game.temp_message = "Equipped all possible charms!"
                            self.game.temp_message_start = time.time()
                        elif action and len(self.game.equipped_charms) < self.game.max_charms * 2:
                            if any(c['name'] == action['name'] for c in self.game.equipped_charms):
                                print(f"DEBUG: {action['name']} already owned")
                                self.game.temp_message = f"{action['name']} already owned!"
                            else:
                                self.game.equipped_charms.append(copy.deepcopy(action))
                                print(f"DEBUG: Added {action['name']} (free)")
                                self.game.temp_message = f"Added {action['name']}!"
                            self.game.temp_message_start = time.time()
                        else:
                            print("DEBUG: Max charms reached")
                            self.game.temp_message = "No charm slots left!"
                            self.game.temp_message_start = time.time()
                        return
            
            # Add this: Handle new debug menu button click
            if DEBUG and DEBUG_MENU_IN_SHOP and self.debug_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))  # New state below
                return
            
            # Handle continue
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                self.game.shop_charms = []  # Clear shop
                self.game.state_machine.change_state(BlindsState(self.game))
                return

            # Handle sell
            for i, sell_rect in enumerate(self.sell_rects or []):
                if sell_rect.collidepoint(mouse_pos):
                    self.game.confirm_sell_index = i
                    self.game.state_machine.change_state(ConfirmSellState(self.game))
                    return

            # Handle buy charms
            for i, buy_rect in enumerate(self.buy_rects or []):
                if buy_rect.collidepoint(mouse_pos):
                    charm = self.game.shop_charms.pop(i)
                    cost = charm['cost']
                    has_debt = any(c['type'] == 'negative_coins' for c in self.game.equipped_charms)
                    min_coins = -5 if has_debt else 0
                    if len(self.game.equipped_charms) < self.game.max_charms and self.game.coins - cost >= min_coins:
                        self.game.equipped_charms.append(charm)
                        self.game.coins -= cost
                        if self.game.current_boss_effect and self.game.current_boss_effect['name'] == 'Charm Eclipse':
                            self.game.disabled_charms = list(range(len(self.game.equipped_charms)))
                    else:
                        self.game.shop_charms.insert(i, charm)
                    return

             # Pack buys
            pack_costs = [3, 5, 7, 3, 5, 9, 4, 7, 9]  # Append rune pack costs
            pack_choices_num = [2, 3, 5, 3, 4, 3, 3, 5, 5]  # Append rune pack choices
            pack_select_num = [1, 1, 1, 1, 1, 1, 1, 1, 2]  # New: Select counts (1 for most, 2 for Super Rune)
            for pack_rect, pack_idx in self.pack_rects or []:
                if pack_rect.collidepoint(mouse_pos):
                    cost = pack_costs[pack_idx]
                    has_debt = any(c['type'] == 'negative_coins' for c in self.game.equipped_charms)
                    min_coins = -5 if has_debt else 0
                    if self.game.coins - cost >= min_coins:
                        self.game.coins -= cost
                        if pack_idx in [0, 1, 2]:
                            self.game.pack_choices = random.sample(data.HAND_TYPES, pack_choices_num[pack_idx])
                            self.game.state_machine.change_state(PackSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                        elif pack_idx in [3, 4, 5]:
                            if pack_idx == 5:
                                self.game.pack_choices = random.sample(SPECIAL_COLORS, pack_choices_num[pack_idx])
                            else:
                                self.game.pack_choices = random.sample(BASE_COLORS, pack_choices_num[pack_idx])
                            self.game.state_machine.change_state(DiceSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                        elif pack_idx in [6, 7, 8]:  # New: Rune packs
                            rune_pack = data.RUNE_PACKS[pack_idx - 6]  # Map to 0-2 index
                            self.game.pack_choices = random.sample(data.MYSTIC_RUNES, pack_choices_num[pack_idx])
                            self.game.pack_select_count = pack_select_num[pack_idx]  # Track how many to select
                            self.game.selected_runes = []  # For multi-select/holding
                            self.game.state_machine.change_state(RuneSelectState(self.game))
                            self.game.available_packs.remove(pack_idx)
                    return

            # Reroll
            if self.reroll_rect and self.reroll_rect.collidepoint(mouse_pos):
                self.game.reroll_shop()
                return

            # Charm drag start
            for i in range(len(self.game.equipped_charms)):
                x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
                y = 150
                rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
                if rect.collidepoint(mouse_pos):
                    self.game.dragging_charm_index = i
                    self.game.dragging_shop = True
                    self.game.drag_offset_x = mouse_pos[0] - x
                    self.game.drag_offset_y = mouse_pos[1] - y
                    break

            # New: Tray click to use rune
            for i, tray_rect in enumerate(self.tray_rects):
                if tray_rect.collidepoint(mouse_pos) and self.game.rune_tray[i]:
                    rune = self.game.rune_tray[i]
                    self.game.previous_state = self  # Store for back
                    self.game.state_machine.change_state(RuneUseState(self.game, rune))
                    self.game.rune_tray[i] = None  # Remove
                    break

        if event.type == pygame.MOUSEBUTTONUP:
            if self.game.dragging_charm_index != -1:
                mouse_pos = pygame.mouse.get_pos()
                target_index = -1
                for i in range(len(self.game.equipped_charms)):
                    x = 50 + i * (CHARM_BOX_WIDTH + CHARM_SPACING)
                    y = 150
                    rect = pygame.Rect(x, y, CHARM_BOX_WIDTH, CHARM_BOX_HEIGHT)
                    if rect.collidepoint(mouse_pos):
                        target_index = i
                        break
                    if target_index != -1 and target_index != self.game.dragging_charm_index:
                        self.game.equipped_charms[self.game.dragging_charm_index], self.game.equipped_charms[target_index] = \
                            self.game.equipped_charms[target_index], self.game.equipped_charms[self.game.dragging_charm_index]
                    self.game.dragging_charm_index = -1
                    self.game.dragging_shop = False

        if event.type == pygame.MOUSEWHEEL and DEBUG and self.debug_panel_open:
            icons_per_row = 4
            row_height = 100 + 50  # Match draw_debug_panel
            num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
            total_content_height = num_rows * row_height + 70
            scroll_speed = 50
            self.scroll_y -= event.y * scroll_speed
            max_scroll = max(0, total_content_height - DEBUG_PANEL_HEIGHT)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        if event.type == pygame.MOUSEMOTION:
            if self.game.dragging_charm_index != -1:
                pass  # Dragging handled in draw_shop_screen

    def draw_debug_panel(self):
        """Draws the debug panel with improved spacing and text readability."""
        panel_rect = pygame.Rect(DEBUG_PANEL_X, DEBUG_PANEL_Y, 
                               DEBUG_PANEL_WIDTH, DEBUG_PANEL_HEIGHT)
        pygame.draw.rect(self.game.screen, (0, 0, 0), panel_rect, 3)
        overlay = pygame.Surface((DEBUG_PANEL_WIDTH, DEBUG_PANEL_HEIGHT))
        overlay.fill((40, 40, 40))
        overlay.set_alpha(200)
        self.game.screen.blit(overlay, (DEBUG_PANEL_X, DEBUG_PANEL_Y))
        
        title_text = self.game.font.render("Debug: All Charms (Click to Equip)", True, THEME['text'])
        self.game.screen.blit(title_text, (DEBUG_PANEL_X + 20, DEBUG_PANEL_Y + 20))
        
        icons_per_row = 4
        icon_size = 100
        spacing = 30
        row_height = icon_size + 50
        num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
        total_content_height = num_rows * row_height + 70
        
        start_x = DEBUG_PANEL_X + 20
        start_y = DEBUG_PANEL_Y + 70 - self.scroll_y
        mouse_pos = pygame.mouse.get_pos()
        visible_start_row = max(0, int(self.scroll_y / row_height))
        visible_rows_to_draw = (DEBUG_PANEL_HEIGHT - 70) // row_height + 2
        visible_end_row = min(num_rows, visible_start_row + visible_rows_to_draw)
        
        charm_rects = []
        tooltips_to_draw = []  # Collect tooltips to draw last
        
        for row in range(visible_start_row, visible_end_row):
            for col in range(icons_per_row):
                i = row * icons_per_row + col
                if i >= len(data.CHARMS_POOL):
                    break
                charm = data.CHARMS_POOL[i]
                x = start_x + col * (icon_size + spacing)
                y = start_y + (row - visible_start_row) * row_height
                icon_rect = pygame.Rect(x, y, icon_size, icon_size)
                
                bg_color = CHARM_BG_COLORS.get(charm['name'], (150, 150, 150))
                if charm.get('rarity') == 'Legendary':
                    bg_color = tuple(min(255, c + 50) for c in bg_color)
                elif charm.get('rarity') == 'Common':
                    bg_color = tuple(max(0, c - 30) for c in bg_color)
                draw_rounded_element(self.game.screen, icon_rect, bg_color, radius=10, 
                                   border_color=THEME['border'], border_width=1)
                
                icon_path = self.game.charm_icon_paths.get(charm['name'])
                if icon_path and os.path.exists(icon_path):
                    icon = pygame.image.load(icon_path)
                    icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                    self.game.screen.blit(icon, (x, y))
                else:
                    pygame.draw.circle(self.game.screen, (0, 0, 0), (x + icon_size//2, y + icon_size//2), 10)
                
                if any(c['name'] == charm['name'] for c in self.game.equipped_charms):
                    gray_surf = pygame.Surface((icon_size, icon_size))
                    gray_surf.fill((128, 128, 128))
                    gray_surf.set_alpha(100)
                    self.game.screen.blit(gray_surf, (x, y))
                    owned_text = self.game.tiny_font.render("OWNED", True, (100, 100, 100))
                    self.game.screen.blit(owned_text, (x + 5, y + icon_size - 15))
                
                full_name = f"{charm['name']} ({charm.get('rarity', 'Common')})"
                max_text_width = icon_size - 10
                name_lines = wrap_text(self.game.tiny_font, full_name, max_text_width)
                text_y = y + icon_size + 5
                for line in name_lines[:2]:
                    name_text = self.game.tiny_font.render(line, True, THEME['text'])
                    text_x = x + (icon_size - name_text.get_width()) // 2
                    text_bg_rect = pygame.Rect(text_x - 5, text_y - 2, name_text.get_width() + 10, name_text.get_height() + 4)
                    pygame.draw.rect(self.game.screen, (*THEME['background'], 180), text_bg_rect)
                    self.game.screen.blit(name_text, (text_x, text_y))
                    text_y += self.game.tiny_font.get_height() + 2
                
                cost_text = self.game.tiny_font.render(str(charm['cost']), True, (255, 255, 0))
                badge_rect = pygame.Rect(x + icon_size - 25, y + 5, 20, 15)
                pygame.draw.rect(self.game.screen, (0, 0, 0), badge_rect)
                self.game.screen.blit(cost_text, (badge_rect.x + 2, badge_rect.y + 1))
                
                if icon_rect.collidepoint(mouse_pos):
                    tooltip_text = f"{charm['desc']}\nCost: {charm['cost']} | Type: {charm.get('type', 'Unknown')}"
                    space_above = y - DEBUG_PANEL_Y
                    assumed_tooltip_height = 100
                    tooltip_y = y - assumed_tooltip_height - 5 if space_above > assumed_tooltip_height else y + icon_size + 50
                    tooltip_y = max(DEBUG_PANEL_Y + 10, min(tooltip_y, DEBUG_PANEL_Y + DEBUG_PANEL_HEIGHT - assumed_tooltip_height - 10))
                    # Collect to draw last
                    tooltips_to_draw.append((x, tooltip_y, tooltip_text))
                
                charm_rects.append((icon_rect, charm))
        
        equip_all_rect = pygame.Rect(DEBUG_PANEL_X + 20, DEBUG_PANEL_Y + DEBUG_PANEL_HEIGHT - 50, 150, 30)
        draw_custom_button(self.game, equip_all_rect, "Equip All", is_hover=equip_all_rect.collidepoint(mouse_pos))
        close_rect = pygame.Rect(DEBUG_PANEL_X + DEBUG_PANEL_WIDTH - 100, DEBUG_PANEL_Y + 10, 80, 30)
        draw_custom_button(self.game, close_rect, "Close", is_hover=close_rect.collidepoint(mouse_pos))
        
        # Draw scrollbar
        if total_content_height > DEBUG_PANEL_HEIGHT:
            bar_width = 10
            bar_x = DEBUG_PANEL_X + DEBUG_PANEL_WIDTH - bar_width - 5
            bar_y = DEBUG_PANEL_Y + 30
            bar_height = DEBUG_PANEL_HEIGHT - 60
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))  # Brighter track for visibility
            thumb_height = max(20, (DEBUG_PANEL_HEIGHT - 60) * (DEBUG_PANEL_HEIGHT / total_content_height))
            thumb_y = bar_y + (self.scroll_y / (total_content_height - DEBUG_PANEL_HEIGHT)) * (bar_height - thumb_height)
            thumb_y = max(bar_y, min(thumb_y, bar_y + bar_height - thumb_height))
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, int(thumb_y), bar_width, int(thumb_height)))  # White thumb for contrast
        
        # Draw collected tooltips last (on top)
        for x, tooltip_y, tooltip_text in tooltips_to_draw:
            draw_tooltip(self.game, x, tooltip_y, tooltip_text)
        
        return charm_rects + [(equip_all_rect, 'equip_all'), (close_rect, 'close')]
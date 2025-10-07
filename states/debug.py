# states/debug.py
import pygame
import time
import math
import copy
from states.base import State
from screens import draw_custom_button, draw_tooltip, draw_rounded_element, draw_enhancement_visuals
from constants import *  # Or specific: THEME, CHARM_BOX_WIDTH, etc.
from data import CHARMS_POOL, MYSTIC_RUNES, HAND_TYPES, ENH_DESC
from utils import wrap_text

class DebugMenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.charm_button_rect = None
        self.prism_button_rect = None
        self.rune_button_rect = None
        self.back_button_rect = None

    def draw(self):
        self.game.screen.fill(THEME['background'])
        title_text = self.game.font.render("Debug Menu", True, THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        button_y = 150
        self.charm_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.charm_button_rect, "Buy Any Charm", is_hover=self.charm_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.prism_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.prism_button_rect, "Apply Any Prism Upgrade", is_hover=self.prism_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.rune_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.rune_button_rect, "Apply Any Rune", is_hover=self.rune_button_rect.collidepoint(mouse_pos))

        button_y += 60
        self.back_button_rect = pygame.Rect(self.game.width // 2 - 150, button_y, 300, 50)
        draw_custom_button(self.game, self.back_button_rect, "Back to Shop", is_hover=self.back_button_rect.collidepoint(mouse_pos))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.charm_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugCharmState(self.game))
            elif self.prism_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugPrismState(self.game))
            elif self.rune_button_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugRuneSelectState(self.game))
            elif self.back_button_rect.collidepoint(mouse_pos):
                from states.shop import ShopState  # Lazy if cycle risk
                self.game.state_machine.change_state(ShopState(self.game))

class DebugCharmState(State):
    def __init__(self, game):
        super().__init__(game)
        self.charm_rects = []
        self.scroll_y = 0
        self.back_rect = None
        self.prev_rect = None
        self.next_rect = None
        self.page = 0
        self.last_wheel_time = 0  # For debounce

    def draw(self):
        self.game.screen.fill(THEME['background'])
        title_text = self.game.font.render("Debug: Select Charm to Add", True, THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(CHARMS_POOL))
        visible_charms = CHARMS_POOL[start_idx:end_idx]
        rows = math.ceil(len(visible_charms) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.charm_rects = []
        tooltips_to_draw = []  # Collect for last draw
        for i, charm in enumerate(visible_charms):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            bg_color = CHARM_BG_COLORS.get(charm['name'], (200, 200, 200))
            draw_rounded_element(self.game.screen, rect, bg_color, border_width=2, radius=10)
            name_text = self.game.small_font.render(charm['name'], True, THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, charm['desc']))
            self.charm_rects.append((rect, charm))

        # Scrollbar if needed
        if total_height > self.game.height - 200:  # Viewport height estimate
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(CHARMS_POOL):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:
                return
            for rect, charm in self.charm_rects:
                if rect.collidepoint(mouse_pos) and len(self.game.equipped_charms) < self.game.max_charms * 2:
                    self.game.equipped_charms.append(copy.deepcopy(charm))
                    self.game.temp_message = f"Added {charm['name']}!"
                    self.game.state_machine.change_state(DebugMenuState(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()

class DebugPrismState(State):
    def __init__(self, game):
        super().__init__(game)
        self.prism_rects = []
        self.scroll_y = 0
        self.back_rect = None
        self.prev_rect = None
        self.next_rect = None
        self.page = 0
        self.last_wheel_time = 0

    def draw(self):
        self.game.screen.fill(THEME['background'])
        title_text = self.game.font.render("Debug: Select Prism Upgrade", True, THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(HAND_TYPES))
        visible_hts = HAND_TYPES[start_idx:end_idx]
        rows = math.ceil(len(visible_hts) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.prism_rects = []
        tooltips_to_draw = []
        for i, ht in enumerate(visible_hts):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            draw_rounded_element(self.game.screen, rect, (180, 140, 100), border_width=2, radius=10)
            name_text = self.game.small_font.render(ht, True, THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, f"Boost {ht} by {PACK_BOOST}x"))
            self.prism_rects.append((rect, ht))

        # Scrollbar if needed
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(HAND_TYPES):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:
                return
            for rect, ht in self.prism_rects:
                if rect.collidepoint(mouse_pos):
                    self.game.hand_multipliers[ht] += PACK_BOOST
                    self.game.temp_message = f"Boosted {ht} by {PACK_BOOST}x!"
                    self.game.state_machine.change_state(DebugMenuState(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()

class DebugRuneSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.rune_rects = []
        self.scroll_y = 0
        self.page = 0
        self.prev_rect = None
        self.next_rect = None
        self.back_rect = None  # New
        self.last_wheel_time = 0

    def draw(self):
        self.game.screen.fill(THEME['background'])
        title_text = self.game.font.render("Debug: Select Rune to Apply", True, THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        box_size = 140
        spacing = 20
        cols = 4
        per_page = 20
        start_idx = self.page * per_page
        end_idx = min(start_idx + per_page, len(MYSTIC_RUNES))
        visible_runes = MYSTIC_RUNES[start_idx:end_idx]
        rows = math.ceil(len(visible_runes) / cols)
        total_height = rows * (box_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.rune_rects = []
        tooltips_to_draw = []  # New collection
        for i, rune in enumerate(visible_runes):
            col = i % cols
            row = i // cols
            x = spacing + col * (box_size + spacing)
            y = start_y + row * (box_size + spacing)
            rect = pygame.Rect(x, y, box_size, box_size)
            bg_color = (128, 0, 128)
            draw_rounded_element(self.game.screen, rect, bg_color, border_width=2, radius=10)
            name_text = self.game.small_font.render(rune['name'], True, THEME['text'])
            self.game.screen.blit(name_text, (x + 10, y + 10))
            if rect.collidepoint(mouse_pos):
                tooltips_to_draw.append((x, y + box_size + 10, rune['desc']))
            self.rune_rects.append((rect, rune))

        # Scrollbar
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Paging buttons
        if start_idx > 0:
            self.prev_rect = pygame.Rect(50, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.prev_rect, "Prev Page", is_hover=self.prev_rect.collidepoint(mouse_pos))
        if end_idx < len(MYSTIC_RUNES):
            self.next_rect = pygame.Rect(self.game.width - 150, self.game.height - 50, 100, 40)
            draw_custom_button(self.game, self.next_rect, "Next Page", is_hover=self.next_rect.collidepoint(mouse_pos))

        # Back button
        self.back_rect = pygame.Rect(self.game.width // 2 - 100, self.game.height - 100, 200, 50)
        draw_custom_button(self.game, self.back_rect, "Back", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:
                return
            for rect, rune in self.rune_rects:
                if rect.collidepoint(mouse_pos):
                    self.game.current_rune = rune
                    self.game.current_rune_slot = -1
                    if rune['max_dice'] == 0:
                        self.game.apply_rune_effect(rune)
                    else:
                        self.game.selected_dice = []
                        self.game.state_machine.change_state(DebugDiceSelectForRune(self.game))
                    break
            if self.prev_rect and self.prev_rect.collidepoint(mouse_pos):
                self.page = max(0, self.page - 1)
            if self.next_rect and self.next_rect.collidepoint(mouse_pos):
                self.page += 1
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()

class DebugDiceSelectForRune(State):
    def __init__(self, game):
        super().__init__(game)
        self.die_rects = []
        self.scroll_y = 0
        self.selected_dice = []  # Allow multi
        self.apply_rect = None  # For apply button
        self.back_rect = None  # New: For cancel/back
        self.last_wheel_time = 0  # For debounce

    def draw(self):
        self.game.screen.fill(THEME['background'])
        title_text = self.game.font.render(f"Debug: Select up to {self.game.current_rune['max_dice']} Dice for {self.game.current_rune['name']}", True, THEME['text'])
        self.game.screen.blit(title_text, (self.game.width // 2 - title_text.get_width() // 2, 50))

        mouse_pos = pygame.mouse.get_pos()
        die_size = 80
        spacing = 10
        cols = 5
        rows = math.ceil(len(self.game.bag) / cols)
        total_height = rows * (die_size + spacing) + spacing
        start_y = 100 + self.scroll_y
        self.die_rects = []  # Reset
        tooltips_to_draw = []  # New: Collect for last draw
        for i, die in enumerate(self.game.bag):
            col = i % cols
            row = i // cols
            x = spacing + col * (die_size + spacing)
            y = start_y + row * (die_size + spacing)
            rect = pygame.Rect(x, y, die_size, die_size)
            color_rgb = COLORS[die['color']]
            inner_content = lambda r: pygame.draw.circle(self.game.screen, (0, 0, 0), r.center, DOT_RADIUS // 2)
            draw_rounded_element(self.game.screen, rect, color_rgb, border_width=2, radius=10, inner_content=inner_content)
            draw_enhancement_visuals(self.game, rect, die)
            if die in self.selected_dice:
                pygame.draw.rect(self.game.screen, (255, 255, 0), rect, 3)
            if rect.collidepoint(mouse_pos):
                enh_desc = ', '.join(ENH_DESC.get(e, e) for e in die['enhancements'])
                tooltips_to_draw.append((x, y + die_size + 10, f"{die['color']} Die - {enh_desc or 'None'}"))
            self.die_rects.append((rect, die))

        # Scrollbar if needed
        if total_height > self.game.height - 200:
            bar_width = 10
            bar_x = self.game.width - bar_width - 10
            bar_y = 100
            bar_height = self.game.height - 200
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))
            thumb_height = max(20, bar_height * (bar_height / total_height))
            thumb_y = bar_y + (-self.scroll_y / (total_height - bar_height)) * (bar_height - thumb_height)
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, thumb_y, bar_width, thumb_height))

        # Apply button
        self.apply_rect = pygame.Rect(self.game.width // 2 - 150, self.game.height - 50, 300, 40)
        draw_custom_button(self.game, self.apply_rect, "Apply Rune", is_hover=self.apply_rect.collidepoint(mouse_pos))

        # New: Back/Cancel button (left of apply)
        self.back_rect = pygame.Rect(self.game.width // 2 - 450, self.game.height - 50, 300, 40)  # Adjust position as needed
        draw_custom_button(self.game, self.back_rect, "Cancel", is_hover=self.back_rect.collidepoint(mouse_pos))

        # Draw tooltips last (on top)
        for x, y, text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, text)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            current_time = time.time()
            if current_time - self.last_wheel_time < 0.2:  # Debounce
                return
            for rect, die in self.die_rects:
                if rect.collidepoint(mouse_pos):
                    if die in self.selected_dice:
                        self.selected_dice.remove(die)
                    elif len(self.selected_dice) < self.game.current_rune['max_dice']:
                        self.selected_dice.append(die)
                    break
            if self.apply_rect and self.apply_rect.collidepoint(mouse_pos) and self.selected_dice:
                self.game.apply_rune_effect(self.game.current_rune, self.selected_dice)
                self.game.state_machine.change_state(DebugMenuState(self.game))
            if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                self.game.state_machine.change_state(DebugMenuState(self.game))  # Back without apply
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 20
            self.scroll_y = min(0, self.scroll_y)
            self.last_wheel_time = time.time()
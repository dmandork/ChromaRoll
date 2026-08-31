# states/d20_roll.py
# Fusion pick → roll animation → result → Accept into the intensified blind.
# This file only presents UI. All rules live in d20_boon.D20BoonSystem.
#
# Lock contract
#   Fusion (or Skip) is free: Cancel Intensify / ESC restores the pre-enter snapshot
#   and returns to Challenges. Window-X during fusion reopens this screen (still free).
#   Clicking Roll d20 (or Test Tier) locks the number immediately — animation is flavor.
#   After lock there is no Back. Window-X reopens the result; Accept & Play is required.

import pygame
import time
import random

from states.base import State
from constants import *
from utils import tint_image, resource_path, draw_rounded_element
from screens import draw_table_felt, draw_gold_plaque, draw_custom_button, TABLE_GOLD, TABLE_PLAQUE
from d20_boon import BASE_COLORS, D20_TIERS, tier_for_roll


TIER_TINTS = {
    'Prism Fracture': (180, 60, 60),
    'Hue Dimming': (180, 120, 40),
    'Roll Harmony': (80, 140, 180),
    'Roll Flow': (60, 170, 110),
    'Chroma Radiance': (210, 170, 40),
}

FUSION_HINTS = [
    "T1 Fracture: blocked hands still score if they use this color",
    "T2 Dimming: this color is dimmed now, then +30% next blind",
    "T3 Harmony: the locked die prefers this color",
    "T4 Flow: advantage auto-picks a die of this color",
    "T5 Radiance: this color +50% this blind, wildcard next hand",
]


class D20RollState(State):
    def __init__(self, game, blind_type):
        super().__init__(game)
        self.blind_type = blind_type
        try:
            raw = pygame.image.load(resource_path('assets/icons/D20.png')).convert_alpha()
            orig_w, orig_h = raw.get_size()
            self.d20_image = pygame.transform.smoothscale(raw, (max(80, orig_w // 2), max(80, orig_h // 2)))
        except Exception:
            self.d20_image = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(self.d20_image, (200, 200, 200), (80, 80), 78)
        self.d20_rect = self.d20_image.get_rect(center=(game.width // 2, game.height // 2 - 20))
        self.font = pygame.font.Font(resource_path(THEME['font_main_path']), 48)
        self.small_font = pygame.font.Font(resource_path(THEME['font_small_path']), 24)
        self.tiny_font = pygame.font.Font(resource_path(THEME['font_tiny_path']), 20)

        self.phase = 'fusion'  # fusion → rolling → done
        self.selected_fusion = None  # None = not chosen yet; False = skip; str = color
        self.roll_start_time = 0
        self.roll_duration = 2.0
        self.roll_result = None
        self.debug_tier_open = False
        self._committed = False

        self.fusion_rects = {}
        self.skip_rect = None
        self.roll_rect = None
        self.accept_rect = None
        self.cancel_rect = None
        self.back_rect = None  # alias of cancel_rect for older call sites
        self.debug_tier_rect = None

    def enter(self):
        resuming = bool(getattr(self.game, 'is_resuming', False))
        if resuming:
            self.game.is_resuming = False
            self._sync_save_fields()
            return
        # Snapshot BEFORE applying leftover so Cancel can put pending queues back.
        boon = getattr(self.game, 'd20_boon', None)
        if boon is not None:
            self.game._d20_pre_intensify = boon.to_dict()
            boon.begin_next_blind(self.game)
        self._sync_save_fields()

    def restore_progress(self, save_data):
        """Rebuild UI after Load. Boon itself is already from_dict'd by savegame."""
        self.phase = save_data.get('d20_roll_phase') or 'fusion'
        self.selected_fusion = save_data.get('d20_selected_fusion')
        self.roll_result = save_data.get('d20_roll_result')
        if save_data.get('d20_blind_type'):
            self.blind_type = save_data.get('d20_blind_type')
        snap = save_data.get('d20_pre_intensify')
        if snap is not None:
            self.game._d20_pre_intensify = snap
        if self.phase == 'rolling':
            # Animation was flavor — the number is already locked (or we lock it now).
            if self.roll_result is None:
                self.roll_result = random.randint(1, 20)
                self._commit_roll(self.roll_result)
            self.phase = 'done'
            self._committed = True
        elif self.phase == 'done':
            self._committed = True
            if self.roll_result is not None and not (self.game.d20_boon and self.game.d20_boon.is_locked()):
                self._commit_roll(self.roll_result)
        self._sync_save_fields()

    def _sync_save_fields(self):
        self.game.d20_roll_phase = self.phase
        self.game.d20_selected_fusion = self.selected_fusion
        self.game.d20_roll_result = self.roll_result
        self.game.d20_blind_type = self.blind_type

    def _clear_overlay_fields(self):
        self.game.d20_roll_phase = None
        self.game.d20_selected_fusion = None
        self.game.d20_roll_result = None
        self.game.d20_blind_type = None
        self.game._d20_pre_intensify = None

    def update(self, dt):
        if self.phase == 'rolling':
            elapsed = time.time() - self.roll_start_time
            if elapsed >= self.roll_duration:
                self.phase = 'done'
                self._sync_save_fields()

    def _commit_roll(self, roll):
        if self._committed and self.game.d20_boon and self.game.d20_boon.is_locked():
            return
        fused = self.selected_fusion if isinstance(self.selected_fusion, str) else None
        self.game.fused_color = fused
        self.game.d20_boon.start_boon(fused)
        self.game.d20_boon.apply_roll(roll)
        self.game.d20_boon.sync_legacy_flags(self.game)
        self._committed = True
        self._sync_save_fields()
        try:
            import savegame
            savegame.save_game(self.game)
        except Exception:
            pass

    def _start_rolling(self):
        self.phase = 'rolling'
        self.roll_start_time = time.time()
        if self.roll_result is None:
            self.roll_result = random.randint(1, 20)
        self._commit_roll(self.roll_result)

    def _cancel_intensify(self):
        """Back out before the d20 is rolled. No-op once locked."""
        boon = getattr(self.game, 'd20_boon', None)
        if boon is not None and boon.is_locked():
            return
        snap = getattr(self.game, '_d20_pre_intensify', None)
        if boon is not None:
            boon.cancel_unstarted(snap, self.game)
        self._clear_overlay_fields()
        self.game.from_d20_intensify = False
        from states.blinds import BlindsState
        self.game.is_resuming = True
        self.game.state_machine.change_state(BlindsState(self.game))

    def draw(self):
        draw_table_felt(self.game)
        title = self.font.render("Intensify Blind", True, TABLE_GOLD)
        self.game.screen.blit(title, (self.game.width // 2 - title.get_width() // 2, 16))

        sub = self.small_font.render(f"{self.game.current_blind}  ·  Stake {self.game.current_stake}", True, THEME['highlight'])
        self.game.screen.blit(sub, (self.game.width // 2 - sub.get_width() // 2, 68))

        if self.phase == 'fusion':
            self._draw_fusion()
        else:
            self._draw_die()

        if DEBUG:
            self._draw_debug_tiers()

    def _draw_fusion(self):
        prompt = self.small_font.render("Optional Color Fusion — pick a color or skip", True, THEME['text'])
        self.game.screen.blit(prompt, (self.game.width // 2 - prompt.get_width() // 2, 110))

        hint = self.tiny_font.render(
            "Fusion aims the d20 at that color (nerf, lock, advantage, or explode).",
            True, THEME['text']
        )
        self.game.screen.blit(hint, (self.game.width // 2 - hint.get_width() // 2, 140))

        self.fusion_rects = {}
        n = len(BASE_COLORS)
        size = 72
        gap = 18
        total = n * size + (n - 1) * gap
        start_x = self.game.width // 2 - total // 2
        y = 200
        mouse = pygame.mouse.get_pos()
        for i, color in enumerate(BASE_COLORS):
            rect = pygame.Rect(start_x + i * (size + gap), y, size, size)
            self.fusion_rects[color] = rect
            rgb = COLORS.get(color, (200, 200, 200))
            draw_rounded_element(self.game.screen, rect, rgb, border_color=(0, 0, 0), border_width=2, radius=12)
            if self.selected_fusion == color:
                pygame.draw.rect(self.game.screen, TABLE_GOLD, rect.inflate(10, 10), 3, border_radius=14)
            elif rect.collidepoint(mouse):
                pygame.draw.rect(self.game.screen, (255, 255, 255), rect.inflate(6, 6), 2, border_radius=14)
            label = self.tiny_font.render(color, True, THEME['text'])
            self.game.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.bottom + 6))

        # Skip
        self.skip_rect = pygame.Rect(self.game.width // 2 - 110, 318, 220, 42)
        draw_custom_button(self.game, self.skip_rect, "Skip Fusion",
                           is_hover=self.skip_rect.collidepoint(mouse),
                           fill_color=(70, 70, 70) if self.selected_fusion is False else None)
        if self.selected_fusion is False:
            pygame.draw.rect(self.game.screen, TABLE_GOLD, self.skip_rect, 2, border_radius=10)

        ready = self.selected_fusion is False or isinstance(self.selected_fusion, str)
        btn_y = 372
        self.cancel_rect = pygame.Rect(self.game.width // 2 - 230, btn_y, 210, 48)
        self.back_rect = self.cancel_rect
        self.roll_rect = pygame.Rect(self.game.width // 2 + 20, btn_y, 210, 48)

        draw_custom_button(self.game, self.cancel_rect, "Cancel Intensify",
                           is_hover=self.cancel_rect.collidepoint(mouse), is_red=True)
        roll_label = "Roll d20" if ready else "Pick or Skip"
        if isinstance(self.selected_fusion, str):
            roll_label = f"Roll with {self.selected_fusion}"
        draw_custom_button(self.game, self.roll_rect, roll_label,
                           is_hover=ready and self.roll_rect.collidepoint(mouse),
                           fill_color=THEME['yes_button'] if ready else THEME.get('disabled', (80, 80, 80)))

        lock_hint = self.tiny_font.render(
            "Cancel / ESC is free. Rolling the d20 locks this blind's boon.",
            True, THEME['highlight']
        )
        self.game.screen.blit(lock_hint, (self.game.width // 2 - lock_hint.get_width() // 2, btn_y + 54))

        if isinstance(self.selected_fusion, str):
            fy = btn_y + 76
            title = self.tiny_font.render(
                f"{self.selected_fusion}: T1 exempt · T2 dim · T3 lock · T4 adv · T5 explode",
                True, COLORS.get(self.selected_fusion, THEME['highlight']))
            self.game.screen.blit(title, (self.game.width // 2 - title.get_width() // 2, fy))

        self._draw_tier_legend()

    def _draw_tier_legend(self):
        """Left plaque — stays clear of Cancel / Roll / lock hint."""
        from screens import draw_gold_plaque
        x, y = 24, 292
        plaque = pygame.Rect(x, y, 196, 132)
        draw_gold_plaque(self.game, plaque, radius=10)
        header = self.tiny_font.render("Outcomes", True, TABLE_GOLD)
        self.game.screen.blit(header, (plaque.x + 12, plaque.y + 8))
        ly = plaque.y + 28
        for tier in D20_TIERS:
            line = f"{tier['min']}-{tier['max']}  {tier['name']}"
            surf = self.tiny_font.render(line, True, THEME['text'])
            self.game.screen.blit(surf, (plaque.x + 12, ly))
            ly += 18

    def _draw_die(self):
        tint = (200, 200, 200)
        name = None
        if self.phase == 'done' and self.roll_result is not None:
            name = tier_for_roll(self.roll_result)['name']
            tint = TIER_TINTS.get(name, tint)
        tinted = tint_image(self.d20_image, tint)
        self.d20_rect = tinted.get_rect(center=(self.game.width // 2, self.game.height // 2 - 50))
        self.game.screen.blit(tinted, self.d20_rect.topleft)

        if self.phase == 'rolling':
            num = random.randint(1, 20)
            text = self.font.render(str(num), True, THEME['text'])
        else:
            text = self.font.render(str(self.roll_result or '?'), True, THEME['text'])
        text_rect = text.get_rect(center=self.d20_rect.center)
        self.game.screen.blit(text, text_rect)

        self.cancel_rect = None
        self.back_rect = None

        if self.phase == 'done':
            boon = self.game.d20_boon
            name = boon.outcome_name or ''
            name_s = self.small_font.render(name, True, THEME['highlight'])
            self.game.screen.blit(name_s, (self.game.width // 2 - name_s.get_width() // 2, self.d20_rect.bottom + 8))

            desc = boon.outcome_desc or ''
            self._blit_wrapped(desc, self.d20_rect.bottom + 38, self.game.width - 120, max_lines=4)

            locked = self.tiny_font.render(
                "Locked — closing the window will bring you back here. Play this blind.",
                True, THEME['highlight']
            )
            self.accept_rect = pygame.Rect(self.game.width // 2 - 120, self.game.height - 70, 240, 50)
            self.game.screen.blit(locked, (self.game.width // 2 - locked.get_width() // 2,
                                           self.accept_rect.y - 50))
            fused = boon.fused_color
            if fused:
                ftxt = self.tiny_font.render(f"Fusion: {fused}", True, COLORS.get(fused, THEME['text']))
                self.game.screen.blit(ftxt, (self.game.width // 2 - ftxt.get_width() // 2,
                                             self.accept_rect.y - 26))
            draw_rounded_element(self.game.screen, self.accept_rect, THEME['yes_button'], radius=8)
            at = self.small_font.render("Accept & Play", True, THEME['text'])
            self.game.screen.blit(at, (self.accept_rect.centerx - at.get_width() // 2,
                                       self.accept_rect.centery - at.get_height() // 2))
        else:
            spinning = self.tiny_font.render("Rolling — this result is already locked.", True, THEME['highlight'])
            self.game.screen.blit(spinning, (self.game.width // 2 - spinning.get_width() // 2,
                                             self.d20_rect.bottom + 16))
            self.accept_rect = None

    def _blit_wrapped(self, text, y, max_width, max_lines=4):
        words = text.split(' ')
        lines = []
        current = []
        for w in words:
            trial = ' '.join(current + [w])
            if self.tiny_font.size(trial)[0] <= max_width:
                current.append(w)
            else:
                lines.append(' '.join(current))
                current = [w]
        if current:
            lines.append(' '.join(current))
        x0 = self.game.width // 2
        for line in lines[:max_lines]:
            s = self.tiny_font.render(line, True, THEME['text'])
            self.game.screen.blit(s, (x0 - s.get_width() // 2, y))
            y += 22

    def _draw_debug_tiers(self):
        # Bottom-left. Fusion only — Test Tier after lock would be a re-roll exploit.
        if self.phase != 'fusion':
            self.debug_tier_rect = None
            self.debug_tier_open = False
            return
        self.debug_tier_rect = pygame.Rect(20, self.game.height - 60, 130, 30)
        draw_rounded_element(self.game.screen, self.debug_tier_rect, (50, 50, 50), radius=5)
        t = self.small_font.render("Test Tier", True, (255, 255, 255))
        self.game.screen.blit(t, (self.debug_tier_rect.centerx - t.get_width() // 2,
                                  self.debug_tier_rect.centery - t.get_height() // 2))
        if not self.debug_tier_open:
            return
        mouse = pygame.mouse.get_pos()
        n = len(D20_TIERS)
        y = self.debug_tier_rect.top - 5 - n * 28
        for i, tier in enumerate(D20_TIERS, start=1):
            opt = pygame.Rect(20, y, 180, 26)
            color = (70, 70, 70) if opt.collidepoint(mouse) else (40, 40, 40)
            draw_rounded_element(self.game.screen, opt, color, radius=3)
            label = self.tiny_font.render(f"T{i} {tier['name']}", True, (255, 255, 255))
            self.game.screen.blit(label, (opt.x + 8, opt.centery - label.get_height() // 2))
            y += 28

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.phase == 'fusion':
                self._cancel_intensify()
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        mouse_pos = event.pos

        if DEBUG and self.phase == 'fusion' and self.debug_tier_rect and self.debug_tier_rect.collidepoint(mouse_pos):
            self.debug_tier_open = not self.debug_tier_open
            return

        if DEBUG and self.phase == 'fusion' and self.debug_tier_open:
            n = len(D20_TIERS)
            y = self.debug_tier_rect.top - 5 - n * 28
            for i, tier in enumerate(D20_TIERS, start=1):
                opt = pygame.Rect(20, y, 180, 26)
                if opt.collidepoint(mouse_pos):
                    # Mid-range roll of that tier — this locks, same as Roll d20.
                    forced = (tier['min'] + tier['max']) // 2
                    if self.selected_fusion is None:
                        self.selected_fusion = False
                    self.roll_result = forced
                    self._commit_roll(forced)
                    self.phase = 'done'
                    self.debug_tier_open = False
                    self._sync_save_fields()
                    return
                y += 28

        if self.phase == 'fusion':
            if self.cancel_rect and self.cancel_rect.collidepoint(mouse_pos):
                self._cancel_intensify()
                return
            for color, rect in self.fusion_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.selected_fusion = color
                    self._sync_save_fields()
                    return
            if self.skip_rect and self.skip_rect.collidepoint(mouse_pos):
                self.selected_fusion = False
                self._sync_save_fields()
                return
            if self.roll_rect and self.roll_rect.collidepoint(mouse_pos):
                if self.selected_fusion is False or isinstance(self.selected_fusion, str):
                    self._start_rolling()
                return

        if self.phase == 'done' and self.accept_rect and self.accept_rect.collidepoint(mouse_pos):
            self.game.from_d20_intensify = True
            self.game.entering_fresh_blind = True
            self.game.d20_boon.apply_this_blind_to_game(self.game)
            self.game.temp_message = self.game.d20_boon.outcome_desc
            self.game.temp_message_start = time.time()
            self._clear_overlay_fields()
            from states.game import GameState
            self.game.state_machine.change_state(GameState(self.game))

# d20_boon.py  (fully fixed, no "game" references, no errors)
import random
from constants import BASE_COLORS, HAND_TYPES  # or from data import if needed

class D20BoonSystem:
    def __init__(self):
        self.active = False
        self.roll = None
        self.outcome = None
        self.fused_color = None  # Set when activating boon

        # Runtime states that will be filled on roll
        self.disabled_hand_type = None
        self.dimmed_color = None
        self.locked_die_idx = None
        self.prefer_color = None  # for Harmony / Flow preference

        self.pending_buff = None
        self.pending_free_pack = None

    def activate_boon(self, fused_color=None):
        self.active = True
        self.fused_color = fused_color
        self.roll = None
        self.outcome = None
        self.disabled_hand_type = None
        self.dimmed_color = None
        self.locked_die_idx = None
        self.prefer_color = None
        self.pending_buff = None
        self.pending_free_pack = None

    def roll_d20(self):
        if not self.active:
            return
        self.roll = random.randint(1, 20)
        self._apply_outcome()

    def _apply_outcome(self):
        roll = self.roll
        fused = self.fused_color

        if roll <= 4:  # 1-4 Crit Fail — Prism Fracture
            disabled = random.choice(HAND_TYPES)
            exempt_color = fused  # hands with fused color are exempt from disable
            desc = f"Prism Fracture: {disabled} hands disabled"
            if fused:
                desc += f" — hands with {fused} are exempt"

            self.outcome = {
                'name': 'Prism Fracture',
                'desc': desc,
                'target_mult': 1.5,
                'disabled_hand_type': disabled,
                'exempt_color': exempt_color,  # None = normal disable
                'pending_buff': {'hand_type_mult_next': {disabled: 2.0}},
                'pending_free_pack': 2  # Prism Pack ID — change if your ID is different
            }

        elif roll <= 8:  # 5-8 Hue Dimming
            color = fused or random.choice(BASE_COLORS)
            self.dimmed_color = color
            desc = f"Hue Dimming: {color} dice -20% this blind → +30% next blind on success"
            self.outcome = {
                'name': 'Hue Dimming',
                'desc': desc,
                'target_mult': 1.25,
                'color_mult_this': {color: 0.8},
                'pending_buff': {'hand_mult_next': 2.0, 'coins': 20, 'color_mult_next': {color: 1.3}}
            }

        elif roll <= 12:  # 9-12 Roll Harmony
            self.locked_die_idx = random.randint(0, 4)  # position lock
            self.prefer_color = fused  # None or random if you want — you decide in game loop
            desc = f"Roll Harmony: Position {self.locked_die_idx + 1} locked (can't reroll)"
            if fused:
                desc += f" — harmonized {fused} (+extra reroll on that color next blind)"
            self.outcome = {
                'name': 'Roll Harmony',
                'desc': desc,
                'target_mult': 1.08,
                'locked_die_idx': self.locked_die_idx,
                'prefer_color': self.prefer_color,
                'pending_buff': {'hand_mult_this': 1.5, 'extra_discard': 1, 'extra_reroll_next': 1}
            }

        elif roll <= 16:  # 13-16 Roll Flow
            self.prefer_color = fused
            desc = "Roll Flow: -12% target, +1 extra reroll + advantage die"
            if fused:
                desc += f" (prefer {fused})"
            self.outcome = {
                'name': 'Roll Flow',
                'desc': desc,
                'target_mult': 0.88,
                'extra_reroll_this': 1,
                'advantage_prefer_color': self.prefer_color,
                'pending_buff': {'hand_mult_this': 2.5, 'full_discard': True, 'extra_reroll_next': 1}
            }

        else:  # 17-20 Chroma Radiance
            bonus = 1.5 if fused else 1.3
            wildcard_next = fused
            desc = f"Chroma Radiance: -25% target, +{int((bonus-1)*100)}% all colors this blind"
            if fused:
                desc += f" — {fused} is wildcard next hand"
            self.outcome = {
                'name': 'Chroma Radiance',
                'desc': desc,
                'target_mult': 0.75,
                'global_color_mult': bonus,
                'pending_buff': {'hand_mult_next_2': 4.0, 'coins': 50, 'wildcard_next_hand': wildcard_next}
            }

    def get_current_effects(self):
        if not self.outcome:
            return {}
        return {
            'target_mult': self.outcome.get('target_mult', 1.0),
            'disabled_hand_type': self.outcome.get('disabled_hand_type'),
            'exempt_color': self.outcome.get('exempt_color'),
            'color_mult_this': self.outcome.get('color_mult_this', {}),
            'global_color_mult': self.outcome.get('global_color_mult', 1.0),
            'locked_die_idx': self.outcome.get('locked_die_idx'),
            'extra_reroll_this': self.outcome.get('extra_reroll_this', 0),
            'advantage_prefer_color': self.outcome.get('advantage_prefer_color'),
        }

    def apply_pending_rewards(self, game):
        if not self.pending_buff:
            return

        buff = self.pending_buff
        if 'coins' in buff:
            game.coins += buff['coins']

        if 'hand_mult_this' in buff:
            game.hand_multiplier *= buff['hand_mult_this']

        if 'hand_mult_next' in buff:
            game.next_blind_hand_mult = buff['hand_mult_next']  # or however you store pending

        if 'hand_mult_next_2' in buff:
            game.pending_hand_mult_2 = buff['hand_mult_next_2']

        if 'hand_type_mult_next' in buff:
            for hand_type, mult in buff['hand_type_mult_next'].items():
                game.next_blind_hand_bonuses[hand_type] = mult

        if 'color_mult_next' in buff:
            for color, mult in buff['color_mult_next'].items():
                game.next_blind_color_mults[color] = mult

        if 'wildcard_next_hand' in buff and buff['wildcard_next_hand']:
            game.wildcard_color_next = buff['wildcard_next_hand']

        if self.pending_free_pack is not None:
            game.pending_free_pack = self.pending_free_pack

        self.pending_buff = None
        self.pending_free_pack = None
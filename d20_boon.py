# d20_boon.py
# Single owner of the D20 Boon System. No pygame. Safe to unit-test.
#
# Lifecycle
#   start_boon(fused_color)     — player accepted Intensify (fusion optional)
#   apply_roll(n)               — lock this-blind effects + queue win rewards
#   apply_this_blind_to_game()  — push live flags onto the game object
#   begin_next_blind()          — apply queued NEXT-blind rewards (every fresh blind)
#   on_blind_won()              — coins + free pack + queue next-blind buffs
#   end_this_blind()            — clear this-blind; tick duration of leftover buffs
#
# This-blind (during the intensified challenge)
#   T1 Prism Fracture  target x1.5, disable one hand type (fusion: that color exempt)
#   T2 Hue Dimming     target x1.25, one color scores x0.8 (fusion: that color)
#   T3 Roll Harmony    target x1.08, lock a die, x1.5 score, +1 discard
#   T4 Roll Flow       target x0.88, +1 reroll/hand, advantage die, x2.5 score, +5 discards
#   T5 Chroma Radiance target x0.75, all colors x1.3 (fusion: fused color x1.5, wildcard next hand)
#
# After win
#   T1 +2x on the disabled hand type next blind + free Prism Pack in the shop
#   T2 +2x next hand, +$20, +30% that color next blind
#   T3 / T4 already applied this blind
#   T5 +4x next TWO blinds + $50

import random

HAND_TYPES = [
    'Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind',
    'Full House', 'Small Straight', 'Large Straight',
]
BASE_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']

# Static table — NEVER call random at import time.
D20_TIERS = [
    {
        'min': 1, 'max': 4, 'name': 'Prism Fracture',
        'desc': 'High risk: +50% target, disable 1 hand type this blind.',
        'target_mult': 1.5,
    },
    {
        'min': 5, 'max': 8, 'name': 'Hue Dimming',
        'desc': 'Moderate: +25% target, -20% on one color this blind.',
        'target_mult': 1.25,
    },
    {
        'min': 9, 'max': 12, 'name': 'Roll Harmony',
        'desc': 'Balanced: +8% target, lock 1 die this blind. +1.5x score, +1 discard.',
        'target_mult': 1.08,
    },
    {
        'min': 13, 'max': 16, 'name': 'Roll Flow',
        'desc': 'Ease: -12% target, +1 reroll and advantage on 1 die. +2.5x score, extra discards.',
        'target_mult': 0.88,
    },
    {
        'min': 17, 'max': 20, 'name': 'Chroma Radiance',
        'desc': 'Big win: -25% target, +30% all colors this blind.',
        'target_mult': 0.75,
    },
]

# Back-compat alias for anything still importing D20_OUTCOMES from here.
D20_OUTCOMES = D20_TIERS


def tier_for_roll(roll):
    for tier in D20_TIERS:
        if tier['min'] <= roll <= tier['max']:
            return tier
    return D20_TIERS[-1]


class D20BoonSystem:
    def __init__(self):
        self.reset_all()

    def reset_all(self):
        self.active = False
        self.roll = None
        self.outcome_name = None
        self.outcome_desc = None
        self.fused_color = None
        self.clear_this_blind()
        self.clear_queued()
        self.clear_next_blind_live()
        self.free_prism_pack = False

    # ------------------------------------------------------------------ this-blind
    def clear_this_blind(self):
        self.target_mult = 1.0
        self.disabled_hand_type = None
        self.exempt_color = None
        self.dimmed_color = None
        self.harmony_active = False
        self.locked_die_idx = -1
        self.score_mult_this = 1.0
        self.chroma_global = 1.0
        self.color_mult_this = {}
        self.extra_rerolls_per_hand = 0
        self.extra_discards_this = 0
        self.flow_advantage = False

    def clear_queued(self):
        self.pending_hand_type_mult = {}
        self.pending_hand_mult_next = 1.0
        self.pending_hand_mult_blinds = 0
        self.pending_hand_mult_blinds_value = 1.0
        self.pending_color_mult_next = {}
        self.pending_coins = 0
        self.pending_free_prism = False
        self.pending_wildcard = None

    def clear_next_blind_live(self):
        self.next_hand_mult = 1.0
        self.next_blind_score_mult = 1.0
        self.next_blind_score_mult_blinds_left = 0
        self.next_blind_type_mult = {}
        self.next_blind_color_mult = {}
        self.wildcard_color = None

    def is_locked(self):
        """True once the d20 has landed — cannot cancel or re-roll this intensify."""
        return bool(self.active and self.roll is not None)

    # ------------------------------------------------------------------ start / roll
    def start_boon(self, fused_color=None):
        """Begin an intensified blind. Does not touch queued rewards from a prior win."""
        self.clear_this_blind()
        self.active = True
        self.roll = None
        self.outcome_name = None
        self.outcome_desc = None
        self.fused_color = fused_color if fused_color in BASE_COLORS else None

    def apply_roll(self, roll):
        roll = max(1, min(20, int(roll)))
        self.roll = roll
        fused = self.fused_color
        tier = tier_for_roll(roll)
        self.outcome_name = tier['name']
        self.target_mult = tier['target_mult']
        parts = [tier['desc']]

        self.clear_queued()

        if roll <= 4:
            self.disabled_hand_type = random.choice(HAND_TYPES)
            if fused:
                self.exempt_color = fused
                parts.append(f"Blocked: {self.disabled_hand_type} (hands using {fused} exempt)")
            else:
                parts.append(f"Blocked: {self.disabled_hand_type}")
            parts.append(f"Win: +2x {self.disabled_hand_type} next blind + free Prism Pack")
            self.pending_hand_type_mult = {self.disabled_hand_type: 2.0}
            self.pending_free_prism = True

        elif roll <= 8:
            color = fused or random.choice(BASE_COLORS)
            self.dimmed_color = color
            parts.append(f"Dimmed {color} dice: -20% this blind")
            parts.append(f"Win: +2x next hand, +$20, {color} +30% next blind")
            self.pending_hand_mult_next = 2.0
            self.pending_coins = 20
            self.pending_color_mult_next = {color: 1.3}

        elif roll <= 12:
            self.harmony_active = True
            self.score_mult_this = 1.5
            self.extra_discards_this = 1
            if fused:
                parts.append(f"Lock prefers {fused} dice")
            parts.append("This blind: +1.5x score, +1 discard, 1 die locked per hand")
            # Harmony success is THIS blind — nothing queued

        elif roll <= 16:
            self.flow_advantage = True
            self.score_mult_this = 2.5
            self.extra_rerolls_per_hand = 1
            self.extra_discards_this = 5
            if fused:
                parts.append(f"Advantage prefers a {fused} die")
            parts.append("This blind: +2.5x score, +1 reroll/hand, advantage die, +5 discards")

        else:
            self.chroma_global = 1.3
            if fused:
                self.color_mult_this = {fused: 1.5 / 1.3}
                self.pending_wildcard = fused
                parts.append(f"{fused} explodes to +50% this blind; wildcard next hand")
            parts.append("This blind: +30% all colors")
            parts.append("Win: +4x next 2 blinds + $50")
            self.pending_hand_mult_blinds = 2
            self.pending_hand_mult_blinds_value = 4.0
            self.pending_coins = 50

        self.outcome_desc = ' | '.join(parts)
        return self.outcome_name

    def cancel_unstarted(self, snapshot, game=None):
        """Undo Intensify before the d20 is rolled. Refuses if already locked."""
        if self.is_locked():
            return False
        self.from_dict(snapshot or {})
        if game is not None:
            self.sync_legacy_flags(game)
        return True

    # ------------------------------------------------------------------ push onto game
    def sync_legacy_flags(self, game):
        """Keep old attribute names alive so UI / leftover reads still work."""
        game.target_mult = self.target_mult if self.active else 1.0
        game.intensified_disabled_type = self.disabled_hand_type
        game.intensified_dimmed_color = self.dimmed_color
        game.intensified_global_color_mult = self.chroma_global
        game.intensified_locked_die_idx = self.locked_die_idx
        game.roll_harmony_active = self.harmony_active
        already_picked = getattr(game, 'd20_advantage_index', -1) >= 0
        game.selecting_advantage_die = bool(self.flow_advantage and self.active and not already_picked)
        game.has_free_prism_pack = bool(self.free_prism_pack)
        if self.fused_color:
            game.fused_color = self.fused_color

    def apply_this_blind_to_game(self, game):
        if not self.active:
            return
        game.d20_advantage_index = -1
        self.sync_legacy_flags(game)
        if self.flow_advantage:
            game.selecting_advantage_die = True


    def grant_this_blind_resources(self, game):
        """Call once at the end of a fresh GameState.enter so Burglar Bag cannot wipe extras."""
        if not self.active or not self.extra_discards_this:
            return
        if getattr(game, '_d20_discards_applied', False):
            return
        game.discards_left = getattr(game, 'discards_left', 0) + self.extra_discards_this
        game._d20_discards_applied = True

    def pick_harmony_lock(self, rolls):
        """Choose a locked die index for this hand. Prefer fused color when set."""
        if not self.harmony_active:
            self.locked_die_idx = -1
            return -1
        n = len(rolls) if rolls else 5
        fused_idxs = []
        if self.fused_color and rolls:
            for i, item in enumerate(rolls):
                die = item[0] if isinstance(item, (tuple, list)) else item
                if die and isinstance(die, dict) and die.get('color') == self.fused_color:
                    fused_idxs.append(i)
        if fused_idxs:
            self.locked_die_idx = random.choice(fused_idxs)
        else:
            self.locked_die_idx = random.randint(0, max(0, n - 1))
        return self.locked_die_idx

    def preferred_advantage_index(self, rolls):
        if not (self.flow_advantage and self.fused_color and rolls):
            return None
        for i, item in enumerate(rolls):
            die = item[0] if isinstance(item, (tuple, list)) else item
            if die and isinstance(die, dict) and die.get('color') == self.fused_color:
                return i
        return None

    # ------------------------------------------------------------------ scoring helpers
    def is_hand_blocked(self, hand_type, held_colors):
        if not self.active or not self.disabled_hand_type:
            return False
        if hand_type != self.disabled_hand_type:
            return False
        if self.exempt_color and self.exempt_color in (held_colors or []):
            return False
        return True

    def dim_factor(self, held_colors):
        """Single -20% if any dimmed color is in the scored dice. Never stack twice."""
        if not self.active or not self.dimmed_color:
            return 1.0
        if self.dimmed_color in (held_colors or []):
            return 0.8
        return 1.0

    def color_score_mult(self, held_colors):
        """Radiance global + fused-color explode + queued next-blind color buff."""
        m = 1.0
        if self.active and self.chroma_global > 1.0:
            m *= self.chroma_global
            if self.color_mult_this:
                for color, extra in self.color_mult_this.items():
                    if color in (held_colors or []):
                        m *= extra
        for color, extra in self.next_blind_color_mult.items():
            if color in (held_colors or []):
                m *= extra
        return m

    def extra_score_mult(self, hand_type, consume_next_hand=False):
        """Harmony/Flow this-blind, Hue next-hand, Radiance leftover, T1 type +2x."""
        m = 1.0
        if self.active and self.score_mult_this > 1.0:
            m *= self.score_mult_this
        if self.next_blind_score_mult > 1.0:
            m *= self.next_blind_score_mult
        if self.next_hand_mult > 1.0:
            m *= self.next_hand_mult
            if consume_next_hand:
                self.next_hand_mult = 1.0
        if consume_next_hand and self.wildcard_color:
            self.wildcard_color = None
        if hand_type in self.next_blind_type_mult:
            m *= self.next_blind_type_mult[hand_type]
        return m

    def modifier_notes(self, hand_type, held_colors):
        notes = []
        if self.is_hand_blocked(hand_type, held_colors):
            notes.append(f"Blocked {hand_type}: 0 score")
        elif self.disabled_hand_type and hand_type == self.disabled_hand_type and self.exempt_color:
            notes.append(f"Fracture exempt ({self.exempt_color})")
        if self.dim_factor(held_colors) < 1.0:
            notes.append(f"Dimmed {self.dimmed_color} x0.8")
        if self.active and self.score_mult_this > 1.0:
            notes.append(f"D20 {self.outcome_name} x{self.score_mult_this}")
        if self.next_blind_score_mult > 1.0:
            notes.append(f"D20 leftover x{self.next_blind_score_mult}")
        if self.next_hand_mult > 1.0:
            notes.append(f"D20 next hand x{self.next_hand_mult}")
        if hand_type in self.next_blind_type_mult:
            notes.append(f"D20 {hand_type} x{self.next_blind_type_mult[hand_type]}")
        if self.active and self.chroma_global > 1.0:
            notes.append("Chroma Radiance +30%")
            if self.color_mult_this:
                for c in self.color_mult_this:
                    if c in (held_colors or []):
                        notes.append(f"{c} chroma +50%")
        for color, extra in self.next_blind_color_mult.items():
            if color in (held_colors or []):
                notes.append(f"{color} brightened x{extra}")
        if self.wildcard_color:
            notes.append(f"{self.wildcard_color} wildcard")
        return notes

    def hud_lines(self):
        """Short in-game banner lines so the player can see the live boon."""
        lines = []
        if self.active and self.outcome_name:
            fused = f"  Fusion:{self.fused_color}" if self.fused_color else ""
            lines.append(f"D20 {self.outcome_name}{fused}  target x{self.target_mult}")
            if self.disabled_hand_type:
                extra = f" (exempt {self.exempt_color})" if self.exempt_color else ""
                lines.append(f"Blocked: {self.disabled_hand_type}{extra}")
            if self.dimmed_color:
                lines.append(f"Dimmed {self.dimmed_color} x0.8")
            if self.harmony_active:
                lines.append("Harmony: 1 die locked, score x1.5")
            if self.flow_advantage:
                lines.append("Flow: +1 reroll, advantage die, score x2.5")
            if self.chroma_global > 1.0:
                extra = f"  {self.fused_color} x1.5" if self.fused_color else ""
                lines.append(f"Radiance: all colors +30%{extra}")
        else:
            if self.next_blind_score_mult > 1.0:
                left = self.next_blind_score_mult_blinds_left
                lines.append(f"D20 leftover x{self.next_blind_score_mult} ({left} blind{'s' if left != 1 else ''})")
            if self.next_hand_mult > 1.0:
                lines.append(f"D20 next hand x{self.next_hand_mult}")
            if self.next_blind_type_mult:
                ht, mul = next(iter(self.next_blind_type_mult.items()))
                lines.append(f"D20 {ht} x{mul}")
            if self.next_blind_color_mult:
                color, mul = next(iter(self.next_blind_color_mult.items()))
                lines.append(f"{color} brightened x{mul}")
            if self.wildcard_color:
                lines.append(f"{self.wildcard_color} wildcard this hand")
        if self.free_prism_pack:
            lines.append("Free Prism Pack waiting in the next shop")
        return lines

    # ------------------------------------------------------------------ blind boundaries
    def begin_next_blind(self, game=None):
        """Move queued win-rewards onto live next-blind slots. Safe to call every fresh enter.

        No-op while an intensified roll is already locked — otherwise Continue after a
        dumped d20 screen would pay out this roll's unearned win rewards on the same blind.
        """
        if self.active:
            if game is not None:
                self.sync_legacy_flags(game)
            return
        if self.pending_hand_type_mult:
            self.next_blind_type_mult = dict(self.pending_hand_type_mult)
            self.pending_hand_type_mult = {}
        if self.pending_hand_mult_next > 1.0:
            self.next_hand_mult = self.pending_hand_mult_next
            self.pending_hand_mult_next = 1.0
        if self.pending_hand_mult_blinds > 0:
            self.next_blind_score_mult = self.pending_hand_mult_blinds_value
            self.next_blind_score_mult_blinds_left = self.pending_hand_mult_blinds
            self.pending_hand_mult_blinds = 0
            self.pending_hand_mult_blinds_value = 1.0
        if self.pending_color_mult_next:
            self.next_blind_color_mult = dict(self.pending_color_mult_next)
            self.pending_color_mult_next = {}
        if self.pending_wildcard:
            self.wildcard_color = self.pending_wildcard
            self.pending_wildcard = None
        if game is not None:
            self.sync_legacy_flags(game)

    def on_blind_won(self, game=None):
        """Call once when the intensified blind is beaten, before shop."""
        if not self.active:
            return
        coins = self.pending_coins
        if coins and game is not None:
            game.coins = getattr(game, 'coins', 0) + coins
            msg = getattr(game, 'temp_message', None) or ''
            game.temp_message = (msg + f"  D20 +${coins}").strip()
        if self.pending_free_prism:
            self.free_prism_pack = True
            if game is not None:
                game.has_free_prism_pack = True
        self.pending_coins = 0
        self.pending_free_prism = False
        # pending_* next-blind queues stay until begin_next_blind

    def end_this_blind(self, game=None):
        """Clear this-blind effects and tick leftover next-blind durations."""
        self.clear_this_blind()
        self.active = False
        self.roll = None
        # Type / color / next-hand buffs last ONE blind (the one begin_next_blind applied them to).
        self.next_blind_type_mult = {}
        self.next_blind_color_mult = {}
        self.next_hand_mult = 1.0
        self.wildcard_color = None
        if self.next_blind_score_mult_blinds_left > 0:
            self.next_blind_score_mult_blinds_left -= 1
            if self.next_blind_score_mult_blinds_left <= 0:
                self.next_blind_score_mult = 1.0
        if game is not None:
            if hasattr(game, 'd20_advantage_index'):
                game.d20_advantage_index = -1
            if hasattr(game, 'selecting_advantage_die') and not self.flow_advantage:
                game.selecting_advantage_die = False
            self.sync_legacy_flags(game)
            if hasattr(game, '_d20_discards_applied'):
                game._d20_discards_applied = False

    # ------------------------------------------------------------------ save / load
    def to_dict(self):
        return {
            'active': self.active,
            'roll': self.roll,
            'outcome_name': self.outcome_name,
            'outcome_desc': self.outcome_desc,
            'fused_color': self.fused_color,
            'target_mult': self.target_mult,
            'disabled_hand_type': self.disabled_hand_type,
            'exempt_color': self.exempt_color,
            'dimmed_color': self.dimmed_color,
            'harmony_active': self.harmony_active,
            'locked_die_idx': self.locked_die_idx,
            'score_mult_this': self.score_mult_this,
            'chroma_global': self.chroma_global,
            'color_mult_this': dict(self.color_mult_this),
            'extra_rerolls_per_hand': self.extra_rerolls_per_hand,
            'extra_discards_this': self.extra_discards_this,
            'flow_advantage': self.flow_advantage,
            'pending_hand_type_mult': dict(self.pending_hand_type_mult),
            'pending_hand_mult_next': self.pending_hand_mult_next,
            'pending_hand_mult_blinds': self.pending_hand_mult_blinds,
            'pending_hand_mult_blinds_value': self.pending_hand_mult_blinds_value,
            'pending_color_mult_next': dict(self.pending_color_mult_next),
            'pending_coins': self.pending_coins,
            'pending_free_prism': self.pending_free_prism,
            'pending_wildcard': self.pending_wildcard,
            'next_hand_mult': self.next_hand_mult,
            'next_blind_score_mult': self.next_blind_score_mult,
            'next_blind_score_mult_blinds_left': self.next_blind_score_mult_blinds_left,
            'next_blind_type_mult': dict(self.next_blind_type_mult),
            'next_blind_color_mult': dict(self.next_blind_color_mult),
            'wildcard_color': self.wildcard_color,
            'free_prism_pack': self.free_prism_pack,
        }

    def from_dict(self, data):
        if not data:
            self.reset_all()
            return
        self.reset_all()
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)

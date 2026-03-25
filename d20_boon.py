# Updated d20_boon.py -- FULL REWARD DESCRIPTIONS RESTORED
# Matches your RollOutcomesD20.txt EXACTLY: base effect + fusion mod + "Success Reward: [full buff preview]"
# Drop this in, replaces old file. UI will now show COMPLETE info post-roll.
# No other changes needed -- your existing integration (ChromaRoll.py flags/UI) uses outcome['desc'] perfectly.

import random
import time
from data import BASE_COLORS, HAND_TYPES, D20_OUTCOMES  # Loads your data.py table!
# Note: D20_OUTCOMES in data.py has base 'desc' -- we append rewards here.

class D20BoonSystem:
    def __init__(self):
        self.active = False
        self.roll = None
        self.outcome = None
        self.fused_color = None
        self.disabled_hand_type = None
        self.dimmed_color = None
        self.locked_die_idx = None
        self.prefer_color = None
        self.pending_buff = None
        self.pending_free_pack = None

    def activate_boon(self, fused_color=None):
        """Activate before roll. Optional fusion (costs 5 coins in UI if you want)."""
        self.active = True
        self.fused_color = fused_color
        # Reset all
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
            return None
        self.roll = random.randint(1, 20)
        self._apply_outcome()
        return self.roll

    def _apply_outcome(self):
        """Pick from data.py D20_OUTCOMES, apply fusion mods, build FULL desc with rewards."""
        roll = self.roll
        fused = self.fused_color

        # Find matching tier from data.py
        for tier in D20_OUTCOMES:
            if tier['min'] <= roll <= tier['max']:
                base_outcome = tier['outcome'].copy()
                break
        else:
            base_outcome = {'name': 'Unknown Roll', 'desc': 'Error - invalid roll'}

        # Apply fusion + compute effects + FULL desc with rewards
        name = base_outcome['name']
        base_desc = base_outcome['desc']
        downside = base_outcome['downside']
        buff = base_outcome['buff'].copy()

        full_desc_parts = [base_desc]

        if roll <= 4:  # Prism Fracture
            self.disabled_hand_type = random.choice(HAND_TYPES)
            exempt = fused  # Fusion: hands using fused color qualify (exempt from disable)
            if exempt:
                full_desc_parts[0] += f" (hands w/ {exempt} exempt)"
            full_desc_parts.append(f" | Success: +2x {self.disabled_hand_type} next blind + free Prism Pack")
            buff['hand_type_mult_next'] = {self.disabled_hand_type: 2.0}
            self.pending_free_pack = 2  # Prism pack ID (adjust if different)

        elif roll <= 8:  # Hue Dimming
            color = fused or random.choice(BASE_COLORS)
            self.dimmed_color = color
            full_desc_parts[0] += f" ({color} dice)"
            full_desc_parts.append(" | Success: +2x mult next hand +$20 +30% that color next blind")
            buff['hand_mult_next'] = 2.0
            buff['coins'] = 20
            buff['color_mult_next'] = {color: 1.3}

        elif roll <= 12:  # Roll Harmony
            # Lock random/fused color die — DELAY selection until AFTER "Start Roll" click
            self.prefer_color = fused
            self.roll_harmony_active = True
            self.intensified_locked_die_idx = -1     # -1 = not chosen yet
            full_desc_parts[0] += f" (prefer {fused or 'random'} die after Start Roll)"
            full_desc_parts.append(" | Success: +1.5x mult this blind +1 extra discard")
            buff['hand_mult_this'] = 1.5
            buff['extra_discards'] = 1

        elif roll <= 16:  # Roll Flow
            self.prefer_color = fused  # For advantage die pick
            full_desc_parts[0] += f" (advantage prefer {fused or 'random'})"
            full_desc_parts.append(" | Success: +2.5x mult this blind + full discard (5 dice)")
            buff['hand_mult_this'] = 2.5
            buff['extra_discards'] = 5  # Full reset

        else:  # 17-20 Chroma Radiance
            global_bonus = 1.3  # +30% all
            if fused:
                full_desc_parts[0] += f" ({fused} explodes to +50%)"
                # Tech: global 1.3 * fused extra (1.5/1.3 ≈1.15)
                buff['color_mult_this'] = {fused: 1.5 / global_bonus}
            full_desc_parts.append(" | Success: +4x mult next 2 blinds +$50")
            buff['hand_mult_next_2'] = 4.0
            buff['coins'] = 50
            if fused:
                buff['wildcard_next_hand'] = fused

        # Downside effects (target_mult etc from data.py or override)
        self.outcome = {
            'name': name,
            'desc': ' | '.join(full_desc_parts),  # FULL REWARD DESC HERE!
            'target_mult': downside.get('target_mult', 1.0),
            'disabled_hand_type': self.disabled_hand_type,
            'exempt_color': fused if roll <=4 else None,
            'color_mult_this': downside.get('color_mult_this', {}),
            'global_color_mult': downside.get('global_color_mult', 1.0),
            'locked_die_idx': self.locked_die_idx,
            'extra_reroll_this': downside.get('extra_reroll_this', 0),
            'advantage_prefer_color': self.prefer_color if roll <=16 else None,
            **downside  # All other downside keys
        }
        self.pending_buff = buff  # Rewards for apply_pending_rewards(self, game)

    def get_current_effects(self):
        """For blind start: target_mult, disabled, etc."""
        if not self.outcome:
            return {}
        return {
            k: v for k, v in self.outcome.items()
            if k not in ['name', 'desc', 'pending_buff']  # Exclude UI/reward keys
        }

    def apply_pending_rewards(self, game):
        """Call on blind success. Handles ALL doc rewards."""
        if not self.pending_buff:
            return
        buff = self.pending_buff

        # Coins
        if 'coins' in buff:
            game.coins += buff['coins']
            game.temp_message += f" +${buff['coins']}"

        # Mult this blind (retrospective: boost round_score before coins)
        if 'hand_mult_this' in buff:
            game.round_score *= buff['hand_mult_this']
            game.temp_message += f" D20 Success x{buff['hand_mult_this']}"

        # Mult next blind/hand
        if 'hand_mult_next' in buff:
            game.pending_hand_mult = buff['hand_mult_next']  # Your existing pending

        if 'hand_mult_next_2' in buff:
            game.pending_hand_mult_2 = buff['hand_mult_next_2']

        # Hand type next
        if 'hand_type_mult_next' in buff:
            game.next_blind_hand_bonuses.update(buff['hand_type_mult_next'])

        # Color next
        if 'color_mult_next' in buff:
            if not hasattr(game, 'next_blind_color_mults'):
                game.next_blind_color_mults = {}
            game.next_blind_color_mults.update(buff['color_mult_next'])

        # Discards next blind
        if 'extra_discards' in buff:
            game.pending_extra_discards = buff['extra_discards']  # Or +=

        # Wildcard next
        if 'wildcard_next_hand' in buff:
            game.wildcard_color_next = buff['wildcard_next_hand']

        # Free pack
        if self.pending_free_pack is not None:
            game.pending_free_pack = self.pending_free_pack
            game.temp_message += " + Free Prism Pack!"

        # Reset
        self.pending_buff = None
        self.pending_free_pack = None
        self.active = False

        game.temp_message_start = time.time()  # Show success msg
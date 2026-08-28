# d20_boon.py — FIXED & COMPLETE (April 2026 version)
import random
from data import BASE_COLORS, HAND_TYPES, D20_OUTCOMES

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
            return None
        self.roll = random.randint(1, 20)
        self._apply_outcome()
        return self.roll

    def _apply_outcome(self):
        roll = self.roll
        fused = self.fused_color

        # === RESET ALL TIER-SPECIFIC STATE FOR EVERY NEW ROLL ===
        # This fixes old Tier 1 (or any tier) leaking when you re-roll the D20
        self.disabled_hand_type = None
        self.dimmed_color = None
        self.prefer_color = None
        self.pending_free_pack = None

        for tier in D20_OUTCOMES:
            if tier['min'] <= roll <= tier['max']:
                base_outcome = tier['outcome'].copy()
                break
        else:
            base_outcome = {'name': 'Unknown Roll', 'desc': 'Error'}

        name = base_outcome['name']
        base_desc = base_outcome['desc']
        downside = base_outcome.get('downside', {})
        buff = base_outcome.get('buff', {}).copy()

        full_desc_parts = [base_desc]

        if roll <= 4:  # Prism Fracture — Tier 1
            # SINGLE random choice — used for BOTH disabled effect AND success reward
            self.disabled_hand_type = random.choice(HAND_TYPES)
            
            exempt = fused
            if exempt:
                full_desc_parts[0] += f" (hands w/ {exempt} exempt)"
            full_desc_parts.append(f" | Success: +2× {self.disabled_hand_type} next blind + free Prism Pack")

            buff['hand_type_mult_next'] = {self.disabled_hand_type: 2.0}
            self.pending_free_pack = 'prism'

        elif roll <= 8:  # Hue Dimming
            color = fused or random.choice(BASE_COLORS)
            self.dimmed_color = color
            full_desc_parts[0] += f" ({color} dice)"
            full_desc_parts.append(" | Success: +$20 and +30% that color next blind")
            buff['coins'] = 20
            buff['color_mult_next'] = {color: 1.3}

        elif roll <= 12:  # Roll Harmony
            self.prefer_color = fused
            full_desc_parts[0] += f" (prefer {fused or 'random'} die)"
            full_desc_parts.append(" | Success: +1.5× mult this blind +1 extra discard")
            buff['hand_mult_this'] = 1.5
            buff['extra_discards'] = 1

        elif roll <= 16:  # Roll Flow
            self.prefer_color = fused
            full_desc_parts[0] += f" (advantage prefer {fused or 'random'})"
            full_desc_parts.append(" | Success: +2.5× mult this blind + full discard")
            buff['hand_mult_this'] = 2.5
            buff['extra_discards'] = 5

        else:  # Chroma Radiance
            global_bonus = 1.3
            if fused:
                full_desc_parts[0] += f" ({fused} explodes to +50%)"
                buff['color_mult_this'] = {fused: 1.5 / global_bonus}
            full_desc_parts.append(" | Success: +4× mult next 2 blinds +$50")
            buff['hand_mult_next_2'] = 4.0
            buff['coins'] = 50
            if fused:
                buff['wildcard_next_hand'] = fused

        self.outcome = {
            'name': name,
            'desc': ' | '.join(full_desc_parts),
            'target_mult': downside.get('target_mult', 1.0),
            'disabled_hand_type': self.disabled_hand_type,
            'exempt_color': fused if roll <= 4 else None,
            **downside
        }
        self.pending_buff = buff

        print(f"DEBUG: _apply_outcome FINISHED → pending_buff keys = {list(self.pending_buff.keys()) if self.pending_buff else None} | free_pack = {self.pending_free_pack}")
        print(f"DEBUG: _apply_outcome finished — pending_buff = {self.pending_buff} | free_pack = {self.pending_free_pack}")

    def apply_pending_rewards(self, game):
        """Call this ONCE after winning an intensified blind."""
        if not self.pending_buff:
            return
        buff = self.pending_buff

        # Coins
        if 'coins' in buff:
            game.coins += buff['coins']
            if game.temp_message is None:
                game.temp_message = f" +${buff['coins']} (D20)"
            else:
                game.temp_message += f" +${buff['coins']} (D20)"

        # This-blind multipliers (already applied in scoring for most tiers)
        if 'hand_mult_this' in buff:
            game.round_score = int(game.round_score * buff['hand_mult_this'])
            game.temp_message += f" D20 x{buff['hand_mult_this']}"

        # Next-blind general mult
        if 'hand_mult_next' in buff:
            game.pending_buff_mult = buff['hand_mult_next']

        # Next-2-blinds (Tier 5)
        if 'hand_mult_next_2' in buff:
            game.pending_buff_mult = buff['hand_mult_next_2']
            game.intensify_buff_duration = 2

        # === TIER 1 SPECIFIC: +2× on the previously disabled hand type ===
        if 'hand_type_mult_next' in buff:
            if not hasattr(game, 'pending_type_mult'):
                game.pending_type_mult = {}
            game.pending_type_mult.update(buff['hand_type_mult_next'])
            # Also set the flag scoring.py and game.py actually check
            game.tier1_disabled_hand = list(buff['hand_type_mult_next'].keys())[0]
            print(f"DEBUG: Tier 1 queued +2× on {game.tier1_disabled_hand}")

        # Color mult next blind
        if 'color_mult_next' in buff:
            if not hasattr(game, 'next_blind_color_mults'):
                game.next_blind_color_mults = {}
            game.next_blind_color_mults.update(buff['color_mult_next'])

        # Free Prism Pack
        if self.pending_free_pack == 'prism':
            game.has_free_prism_pack = True
            game.pending_free_pack = 'prism'  # for generate_shop
            print("DEBUG: Tier 1 free Prism Pack queued")

        # Clear so we don't apply twice
        self.pending_buff = None
        self.pending_free_pack = None

    def reset_for_new_blind(self):
        """Call from advance_blind and GameState.enter"""
        print("DEBUG: reset_for_new_blind() was called — clearing pending_buff")
        self.active = False
        self.roll = None
        self.outcome = None
        self.pending_buff = None
        self.pending_free_pack = None
        self.disabled_hand_type = None
        self.dimmed_color = None
        self.prefer_color = None
        # Add any new tier-specific variables here in the future
# Headless tests for pouch unlocks + Ghost / Plasma wiring. No pygame window.
import os
import sys
from types import ModuleType

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE = 32
    pg.K_ESCAPE = 27
    pg.K_RETURN = 13
    pg.init = lambda: None
    sys.modules['pygame'] = pg

from scoring import (
    plasma_mix_chips,
    shop_pack_weights,
    dice_pack_choices,
    evaluate_hand,
    randomize_bag_colors,
    _BASE_COLORS,
    _SPECIAL_COLORS,
    _DIE_COLORS,
)
import data


HAND_TYPES = [
    'Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind',
    'Full House', 'Small Straight', 'Large Straight',
]


def die(color, die_id='d'):
    return {'id': die_id, 'color': color, 'faces': [1, 2, 3, 4, 5, 6], 'enhancements': []}


class FakeGame:
    def __init__(self, values=None, colors=None):
        colors = colors or ['Red'] * 5
        values = values or [3, 3, 3, 3, 3]
        self.rolls = [(die(colors[i], f'id{i}'), values[i]) for i in range(5)]
        self.held = [True] * 5
        self.has_advantage = False
        self.held_advantage = False
        self.d20_advantage_index = -1
        self.advantage_value = None
        self.fates_advantage_index = -1
        self.held_fates_advantage = False
        self.fates_advantage_value = None
        self.current_blind = 'Small'
        self.current_boss_effect = None
        self.boss_rainbow_color = None
        self.equipped_charms = []
        self.disabled_charms = []
        self.lucky_triggers = 0
        self.broken_dice = []
        self.confirmed_hands_this_round = 0
        self.hands_left = 4
        self.is_last_hand = False
        self.final_discard_mult = 0
        self.is_final_discard = False
        self.hand_multipliers = {ht: 1.0 for ht in HAND_TYPES}
        self.full_bag = [r[0] for r in self.rolls]
        self.bag = []
        self.coins = 0
        self.extra_coins = 0
        self.discards_left = 3
        self.discards_used_this_round = 0
        self.avoid_streak = 0
        self.stake_milestones = 0
        self.destroyed_dice = []
        self.d20_boon = None
        self.max_charms = 5
        self.score_mult = 1.0
        self.plasma_pouch_active = False


def test_plasma_mix_chip_table():
    assert plasma_mix_chips([]) == 0
    assert plasma_mix_chips(['Red'] * 5) == -40
    assert plasma_mix_chips(['Red', 'Red', 'Blue', 'Blue', 'Red']) == 0
    assert plasma_mix_chips(['Red', 'Blue', 'Green', 'Red', 'Blue']) == 40
    assert plasma_mix_chips(['Red', 'Blue', 'Green', 'Yellow', 'Red']) == 80
    assert plasma_mix_chips(['Red', 'Blue', 'Green', 'Yellow', 'Purple']) == 120
    assert plasma_mix_chips(['Rainbow'] * 5) == 120
    # Rainbow does not break a red mono
    assert plasma_mix_chips(['Red', 'Red', 'Red', 'Rainbow', 'Rainbow']) == -40


def test_plasma_two_pair_mix_bonus():
    g = FakeGame(
        values=[2, 2, 5, 5, 1],
        colors=['Red', 'Blue', 'Green', 'Yellow', 'Purple'],
    )
    ht, base, desc_n, final_n, _c, _m = evaluate_hand(g, is_preview=True)
    g.plasma_pouch_active = True
    ht_p, _b, desc_p, final_p, _c, _m = evaluate_hand(g, is_preview=True)
    assert ht == '2 Pair'
    assert base == 60
    assert final_n == 60
    assert 'Plasma mix +120' in desc_p
    assert final_p == 180  # 60 + 120, no extra mult


def test_plasma_mono_tax():
    g = FakeGame(values=[3, 3, 3, 3, 3], colors=['Red'] * 5)
    _ht, _base, desc_n, final_n, _c, _m = evaluate_hand(g, is_preview=True)
    g.plasma_pouch_active = True
    _ht, _base, desc_p, final_p, _c, _m = evaluate_hand(g, is_preview=True)
    assert final_n == 250 * 4
    assert 'Plasma mono -40' in desc_p
    assert final_p == (250 - 40) * 4
    assert final_p < final_n


def test_evaluate_hand_plasma_averages():
    # Name kept so older test runners still hit a plasma evaluate path.
    g = FakeGame(
        values=[2, 2, 5, 5, 1],
        colors=['Red', 'Blue', 'Green', 'Red', 'Blue'],
    )
    g.plasma_pouch_active = True
    _ht, _base, desc, final, _c, _m = evaluate_hand(g, is_preview=True)
    assert 'Plasma mix +40' in desc
    assert final == 100  # 2 Pair 60 + 40


def test_shop_pack_weights_ghost_boosts_special():
    normal = shop_pack_weights(ghost=False)
    ghost = shop_pack_weights(ghost=True)
    assert len(normal) == 9
    assert len(ghost) == 9
    assert normal[5] == 1.0
    assert ghost[5] == 4.0
    assert ghost[3] == normal[3]


def test_dice_pack_choices_pools():
    assert set(dice_pack_choices(5, ghost=False)) == set(_BASE_COLORS)
    assert set(dice_pack_choices(4, special_only=True)) == set(_SPECIAL_COLORS)
    mixed = dice_pack_choices(9, ghost=True)
    assert set(mixed) == set(_BASE_COLORS) | set(_SPECIAL_COLORS)
    special = dice_pack_choices(4, special_only=True, ghost=True)
    assert set(special) == set(_SPECIAL_COLORS)
    empty = dice_pack_choices(0)
    assert empty == []


def test_ghost_pouch_data_flag():
    ghost = next(p for p in data.POUCHES if p['name'] == 'Ghost Pouch')
    assert ghost['bonus'].get('shop_special_boost') is True
    plasma = next(p for p in data.POUCHES if p['name'] == 'Plasma Pouch')
    assert plasma['bonus'].get('mix_bonus') is True
    assert not plasma['bonus'].get('balance_score')
    assert not plasma['bonus'].get('blind_mult')


def test_erratic_never_picks_black():
    assert 'Black' not in _DIE_COLORS
    assert set(_DIE_COLORS) == set(_BASE_COLORS) | set(_SPECIAL_COLORS)

    class GuardRng:
        def choice(self, seq):
            assert 'Black' not in seq
            assert set(seq) <= set(_DIE_COLORS)
            return 'Glass'

    bag = [{'id': f'd{i}', 'color': 'Red'} for i in range(25)]
    randomize_bag_colors(bag, rng=GuardRng())
    assert all(d['color'] == 'Glass' for d in bag)


if __name__ == '__main__':
    tests = [v for k, v in list(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in tests:
        try:
            fn()
            print('OK', fn.__name__)
        except Exception as e:
            failed += 1
            print('FAIL', fn.__name__, type(e).__name__, e)
    print(f'{len(tests) - failed}/{len(tests)} passed')
    sys.exit(1 if failed else 0)

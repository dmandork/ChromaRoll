# Headless tests for Pass D: Castle Cube, Saving Throw, Space Sphere,
# Monopoly Mortgage, and the two pouch-init bugs. No pygame window.
import os
import sys
from types import ModuleType, SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE = 32
    pg.K_ESCAPE = 27
    pg.K_RETURN = 13
    pg.K_UP = 273
    pg.K_DOWN = 274
    pg.K_LEFT = 276
    pg.K_RIGHT = 275
    pg.QUIT = 12
    pg.MOUSEBUTTONDOWN = 5
    pg.KEYDOWN = 2
    pg.init = lambda: None
    pg.display = SimpleNamespace(
        set_mode=lambda *a, **k: None,
        flip=lambda: None,
        set_caption=lambda *a, **k: None,
    )
    pg.mixer = SimpleNamespace(
        init=lambda *a, **k: None,
        Sound=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None),
        Channel=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None),
    )
    pg.font = SimpleNamespace(
        init=lambda: None,
        Font=lambda *a, **k: None,
        SysFont=lambda *a, **k: None,
    )
    pg.image = SimpleNamespace(load=lambda *a, **k: None)
    pg.draw = SimpleNamespace(
        rect=lambda *a, **k: None,
        circle=lambda *a, **k: None,
        line=lambda *a, **k: None,
    )
    pg.Rect = lambda *a, **k: SimpleNamespace(
        x=0, y=0, width=0, height=0, collidepoint=lambda *a, **k: False
    )
    pg.Surface = lambda *a, **k: SimpleNamespace(
        get_width=lambda: 0,
        get_height=lambda: 0,
        blit=lambda *a, **k: None,
        fill=lambda *a, **k: None,
    )
    sys.modules['pygame'] = pg

from scoring import (
    evaluate_hand,
    glass_breaks,
    rotate_castle_color,
    apply_castle_discards,
    try_space_sphere,
    mortgage_sell_payout,
    pouch_hands_delta,
    pouch_extra_colors,
    _BASE_COLORS,
    _SPECIAL_COLORS,
)

HAND_TYPES = [
    'Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind',
    'Full House', 'Small Straight', 'Large Straight',
]


class SeqRng:
    """Deterministic stand-in for the random module."""

    def __init__(self, randoms=None, ints=None, choices=None):
        self.randoms = list(randoms or [])
        self.ints = list(ints or [])
        self.choices = list(choices or [])

    def random(self):
        return self.randoms.pop(0)

    def randint(self, a, b):
        return self.ints.pop(0)

    def choice(self, seq):
        if self.choices:
            return self.choices.pop(0)
        return seq[0]


def die(color, die_id='d'):
    return {'id': die_id, 'color': color, 'faces': [1, 2, 3, 4, 5, 6], 'enhancements': []}


class FakeGame:
    def __init__(self, charms=None, values=None, colors=None, hold=None):
        colors = colors or ['Red'] * 5
        values = values or [3, 3, 3, 3, 3]
        self.rolls = [(die(colors[i], f'id{i}'), values[i]) for i in range(5)]
        self.held = hold if hold is not None else [True] * 5
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
        self.equipped_charms = charms or []
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


def score_of(game, preview=True):
    hand_type, base, desc, final, chips, _ = evaluate_hand(game, is_preview=preview)
    return hand_type, final, desc, chips


def test_castle_cube_scores_permanent_bonus():
    castle = {
        'name': 'Castle Cube', 'type': 'score_per_discard_color', 'value': 3,
        'active_color': 'Red', 'permanent_bonus': 9,
    }
    g = FakeGame(charms=[castle], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    _, _, desc, chips = score_of(g)
    assert 'Castle Cube +9 (Red)' in desc
    assert chips >= 9


def test_castle_discards_only_matching_color():
    castle = {
        'name': 'Castle Cube', 'type': 'score_per_discard_color', 'value': 3,
        'active_color': 'Red', 'permanent_bonus': 0,
    }
    discarded = [die('Red', 'r1'), die('Blue', 'b1'), die('Red', 'r2')]
    added = apply_castle_discards(castle, discarded)
    assert added == 6
    assert castle['permanent_bonus'] == 6
    added2 = apply_castle_discards(castle, [die('Green', 'g1')])
    assert added2 == 0
    assert castle['permanent_bonus'] == 6


def test_castle_color_rotates_away_from_previous():
    castle = {'name': 'Castle Cube', 'type': 'score_per_discard_color', 'value': 3}
    c1 = rotate_castle_color(castle, rng=SeqRng(choices=['Red']))
    assert c1 == 'Red'
    c2 = rotate_castle_color(castle, rng=SeqRng(choices=['Blue']))
    assert c2 == 'Blue'
    assert c2 != 'Red'
    # Without a scripted choice, never pick the current color
    rotate_castle_color(castle)  # prev Blue; pool is the other four
    assert castle['active_color'] in _BASE_COLORS
    assert castle['active_color'] != 'Blue'


def test_saving_throw_cancels_break():
    g = FakeGame(charms=[{'name': 'Saving Throw', 'type': 'break_save'}])
    # First random() is the break roll (0.0 always "would break"); then save 5 (>3)
    rng = SeqRng(randoms=[0.0], ints=[5])
    assert glass_breaks(g, 1.0, rng=rng) is False
    assert g._last_save_success is True
    assert g._last_save_roll == 5


def test_saving_throw_fail_still_breaks():
    g = FakeGame(charms=[{'name': 'Saving Throw', 'type': 'break_save'}])
    rng = SeqRng(randoms=[0.0], ints=[3])  # 3 is not >3
    assert glass_breaks(g, 1.0, rng=rng) is True
    assert g._last_save_success is False
    assert g._last_save_roll == 3


def test_saving_throw_disabled_does_not_save():
    g = FakeGame(charms=[{'name': 'Saving Throw', 'type': 'break_save'}])
    g.disabled_charms = [0]
    rng = SeqRng(randoms=[0.0], ints=[6])
    assert glass_breaks(g, 1.0, rng=rng) is True
    assert g._last_save_roll is None


def test_no_saving_throw_breaks_on_chance():
    g = FakeGame(charms=[])
    rng = SeqRng(randoms=[0.0])
    assert glass_breaks(g, 1.0, rng=rng) is True
    rng2 = SeqRng(randoms=[0.99])
    assert glass_breaks(g, 0.25, rng=rng2) is False


def test_space_sphere_upgrades_on_hit():
    sphere = {'name': 'Space Sphere', 'type': 'hand_upgrade', 'chance': 0.25}
    g = FakeGame(charms=[sphere])
    rng = SeqRng(randoms=[0.10])  # < 0.25
    assert try_space_sphere(g, 'Pair', rng=rng, boost=0.5) is True
    assert g.hand_multipliers['Pair'] == 1.5
    assert g._space_sphere_hit == 'Pair'


def test_space_sphere_miss_and_nothing():
    sphere = {'name': 'Space Sphere', 'type': 'hand_upgrade', 'chance': 0.25}
    g = FakeGame(charms=[sphere])
    rng = SeqRng(randoms=[0.90])
    assert try_space_sphere(g, 'Pair', rng=rng) is False
    assert g.hand_multipliers['Pair'] == 1.0
    assert try_space_sphere(g, 'Nothing', rng=SeqRng(randoms=[0.0])) is False
    assert try_space_sphere(g, None, rng=SeqRng(randoms=[0.0])) is False


def test_mortgage_doubles_one_sell_then_normal():
    mortgage = {
        'name': 'Monopoly Mortgage', 'type': 'sell_double_lock', 'cost': 4,
        'sell_value': 2, 'value': 2,
    }
    basic = {
        'name': 'Basic Charm', 'type': 'flat_bonus', 'cost': 2, 'sell_value': 4, 'value': 10,
    }
    equipped = [mortgage, basic]
    payout, lock, used = mortgage_sell_payout(equipped, 1)
    assert payout == 8
    assert lock is mortgage
    assert used is True
    # Second sell in the same shop is normal
    payout2, lock2, used2 = mortgage_sell_payout(equipped, 1, already_used=True)
    assert payout2 == 4
    assert lock2 is None
    assert used2 is False


def test_selling_mortgage_itself_doubles_no_lock():
    mortgage = {
        'name': 'Monopoly Mortgage', 'type': 'sell_double_lock', 'cost': 4,
        'sell_value': 2, 'value': 2,
    }
    payout, lock, used = mortgage_sell_payout([mortgage], 0)
    assert payout == 4
    assert lock is None
    assert used is True


def test_pouch_hands_applied_once():
    assert pouch_hands_delta({'bonus': {'hands': 1}}) == 1
    assert pouch_hands_delta({'bonus': {'hands': -1}}) == -1
    assert pouch_hands_delta({'bonus': {}}) == 0
    assert pouch_hands_delta({'name': 'Yellow Pouch', 'bonus': {'coins': 10}}) == 0


def test_black_pouch_no_junk_color():
    rng = SeqRng(choices=['Glass'])
    colors = pouch_extra_colors(
        {'bonus': {'extra_dice': {'random_special': 1}, 'hands': -1, 'charm_slots': 1}},
        rng=rng,
    )
    assert colors == ['Glass']
    assert 'random_special' not in colors
    for c in colors:
        assert c in _SPECIAL_COLORS
    # Named extras still work
    reds = pouch_extra_colors({'bonus': {'extra_dice': {'Red': 2}}})
    assert reds == ['Red', 'Red']


if __name__ == '__main__':
    tests = [v for k, v in list(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f'  ok  {fn.__name__}')
        except Exception as e:
            failed += 1
            print(f' FAIL {fn.__name__}: {e}')
    print(f'{len(tests) - failed}/{len(tests)} passed')
    raise SystemExit(failed)

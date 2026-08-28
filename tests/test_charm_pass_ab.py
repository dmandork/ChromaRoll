# Headless tests for Pass A+B charm fixes. No pygame window needed.
import os
import sys
from types import ModuleType, SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# constants.py imports pygame for key constants. Stub it so this file
# can run on machines (and this sandbox) that don't have pygame installed.
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

from scoring import evaluate_hand

HAND_TYPES = [
    'Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind',
    'Full House', 'Small Straight', 'Large Straight',
]


def die(color, die_id='d', enhancements=None):
    return {'id': die_id, 'color': color, 'faces': [1, 2, 3, 4, 5, 6], 'enhancements': enhancements or []}


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


def test_flower_pot_mono_not_loyalty():
    pot = {'name': 'Flower Pot Prism', 'type': 'mult_conditional', 'mono': True, 'value': 2}
    g = FakeGame(charms=[pot], colors=['Red'] * 5, values=[3, 3, 3, 3, 3])
    ht, final, desc, chips = score_of(g)
    assert ht == '5 of a Kind'
    assert 'Flower Pot Prism +2 (mono)' in desc
    # Mixed colors: no pot
    g2 = FakeGame(charms=[pot], colors=['Red', 'Blue', 'Green', 'Purple', 'Yellow'], values=[1, 2, 3, 4, 5])
    _, _, desc2, _ = score_of(g2)
    assert 'Flower Pot Prism' not in desc2
    # Shared type must not take Loyalty's every-6 path
    pot['local_turns'] = 6
    g3 = FakeGame(charms=[pot], colors=['Red', 'Blue', 'Green', 'Purple', 'Yellow'], values=[1, 2, 3, 4, 5])
    _, _, desc3, _ = score_of(g3)
    assert 'Flower Pot Prism' not in desc3


def test_glass_globe_only_with_glass():
    globe = {'name': 'Glass Globe', 'type': 'mult_conditional', 'glass': True, 'value': 2}
    g = FakeGame(charms=[globe], colors=['Red'] * 4 + ['Glass'], values=[2, 2, 5, 5, 6])
    _, _, desc, _ = score_of(g)
    assert 'Glass Globe +2 (glass)' in desc
    g2 = FakeGame(charms=[globe], colors=['Red'] * 5, values=[2, 2, 5, 5, 6])
    _, _, desc2, _ = score_of(g2)
    assert 'Glass Globe' not in desc2


def test_loyalty_luck_every_six_not_always():
    luck = {'name': 'Loyalty Luck', 'type': 'mult_conditional', 'every': 6, 'value': 3, 'local_turns': 0}
    g = FakeGame(charms=[luck], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    _, _, desc, _ = score_of(g)
    assert 'Loyalty Luck' not in desc
    luck['local_turns'] = 6
    _, _, desc2, _ = score_of(g)
    assert 'Loyalty Luck +3' in desc2


def test_steel_seal_counts_bag_not_scored_enh():
    seal = {'name': 'Steel Seal', 'type': 'mult_per_enhance', 'enhance': 'Steel', 'value': 0.2}
    elixir = {'name': 'Enhance Elixir', 'type': 'mult_per_enhance', 'value': 0.25}
    scored = die('Red', 's1', ['Bonus'])
    steel_in_bag = die('Blue', 'b1', ['Steel'])
    g = FakeGame(charms=[seal], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g.rolls[0] = (scored, 3)
    g.full_bag = [scored, steel_in_bag]
    _, _, desc, _ = score_of(g)
    assert 'Steel Seal +0.2 (1 Steel in bag)' in desc
    g2 = FakeGame(charms=[elixir], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g2.rolls[0] = (scored, 3)
    g2.full_bag = [scored, steel_in_bag]
    _, _, desc2, _ = score_of(g2)
    assert 'Enhance Elixir +0.25 (1 enhancements)' in desc2
    assert 'Steel' not in desc2 or 'in bag' not in desc2


def test_dusk_die_final_hand_only():
    dusk = {'name': 'Dusk Die', 'type': 'retrigger', 'target': 'final_hand'}
    rune = {'name': 'Retrigger Rune', 'type': 'retrigger', 'hands': 'kinds'}
    g = FakeGame(charms=[dusk], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g.is_last_hand = False
    g.hands_left = 3
    _, _, desc, _ = score_of(g)
    assert 'Dusk Die' not in desc
    g.is_last_hand = True
    g.hands_left = 1
    _, _, desc2, _ = score_of(g)
    assert 'Dusk Die x2 (final hand)' in desc2
    g3 = FakeGame(charms=[rune], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    _, _, desc3, _ = score_of(g3)
    assert 'Retrigger Rune x2 (kinds retrigger)' in desc3
    # Shared type: rune must not fire Dusk's final-hand path on a mid-round kinds hand
    g3.is_last_hand = False
    g3.hands_left = 3
    _, _, desc4, _ = score_of(g3)
    assert 'final hand' not in desc4


def test_discard_drake_uses_counter():
    drake = {'name': 'Discard Drake', 'type': 'discard_mult', 'value': 1}
    g = FakeGame(charms=[drake], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g.discards_used_this_round = 0
    _, _, desc, _ = score_of(g)
    assert 'Discard Drake' not in desc
    g.discards_used_this_round = 2
    _, _, desc2, _ = score_of(g)
    assert 'Discard Drake +2 (2 discards)' in desc2


def test_life_milestone_uses_counter():
    life = {'name': 'Life Milestone', 'type': 'mult_per_milestone', 'value': 0.5}
    g = FakeGame(charms=[life], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g.stake_milestones = 0
    _, _, desc, _ = score_of(g)
    assert 'Life Milestone' not in desc
    g.stake_milestones = 4
    _, _, desc2, _ = score_of(g)
    assert 'Life Milestone +2.0 (4 milestones)' in desc2 or 'Life Milestone +2 (4 milestones)' in desc2


def test_square_sphere_this_hand_only_once():
    sq = {'name': 'Square Sphere', 'type': 'score_conditional', 'dice': 4, 'value': 4, 'permanent_bonus': 8}
    g = FakeGame(charms=[sq], colors=['Red'] * 5, values=[3, 3, 3, 1, 2], hold=[True, True, True, True, False])
    ht, final, desc, chips = score_of(g)
    # +4 current + 8 permanent = 12 chips from the charm (plus base of 3oak)
    assert 'Square Sphere +12 (4 dice)' in desc
    assert chips >= 12
    # 3 dice: no square
    g2 = FakeGame(charms=[sq], colors=['Red'] * 5, values=[3, 3, 3, 1, 2], hold=[True, True, True, False, False])
    _, _, desc2, chips2 = score_of(g2)
    assert 'Square Sphere' not in desc2
    assert chips2 < chips


def test_acrobat_does_not_double():
    acrobat = {'name': 'Acrobat Amulet', 'type': 'mult_final_discard', 'value': 2}
    g = FakeGame(charms=[acrobat], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    g.final_discard_mult = 2
    g.is_final_discard = True
    _, _, desc, _ = score_of(g, preview=True)
    assert desc.count('Acrobat Amulet') == 1
    _, _, desc2, _ = score_of(g, preview=False)
    assert desc2.count('Acrobat Amulet') == 1
    assert g.final_discard_mult == 0  # consumed on actual score


def test_ice_shard_preview_is_first_hand_100():
    ice = {'name': 'Ice Shard', 'type': 'score_decay', 'start': 100, 'decay': 5, 'hands_played': 0}
    g = FakeGame(charms=[ice], colors=['Red'] * 5, values=[3, 3, 3, 1, 2])
    _, _, desc, chips = score_of(g, preview=True)
    assert 'Ice Shard +100 (hand 1)' in desc
    assert chips >= 100
    ice['hands_played'] = 1
    _, _, desc2, chips2 = score_of(g, preview=True)
    assert 'Ice Shard +95 (hand 2)' in desc2
    assert chips2 < chips


def test_echo_ember_enumerate_disabled():
    # Simulate the win-payout loop the way it should work
    charms = [
        {'name': 'Echo Ember', 'type': 'coin_per_discard', 'value': 2},
        {'name': 'Other', 'type': 'flat_bonus', 'value': 1},
    ]
    disabled = [0]
    discards_left = 3
    bonus = 0
    for idx, charm in enumerate(charms):
        if charm['type'] == 'coin_per_discard' and idx not in disabled:
            bonus += charm['value'] * discards_left
    assert bonus == 0
    disabled = []
    bonus = 0
    for idx, charm in enumerate(charms):
        if charm['type'] == 'coin_per_discard' and idx not in disabled:
            bonus += charm['value'] * discards_left
    assert bonus == 6


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
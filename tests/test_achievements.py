# tests/test_achievements.py
import os
import sys
from types import SimpleNamespace, ModuleType

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE = 32
    pg.K_ESCAPE = 27
    pg.K_RETURN = 13
    pg.K_UP = 273
    pg.K_DOWN = 274
    pg.init = lambda: None
    sys.modules['pygame'] = pg

import data
import achievements as ach


class FakeGame:
    def __init__(self):
        self._skip_ach_persist = True
        self.progress = ach.default_progress()
        self.unlocks = self.progress
        self.current_stake = 1
        self.equipped_charms = []
        self.hand_multipliers = {ht: 1.0 for ht in data.HAND_TYPES}
        self.bag = []
        self.full_bag = []
        self.lucky_triggers = 0
        self.temp_message = None
        self.temp_message_start = 0
        self.temp_message_duration = 3.0
        self.coins = 0


def test_locked_set_is_45_unique_pool_names():
    names = ach.locked_charm_names()
    pool = {c['name'] for c in data.CHARMS_POOL}
    assert len(names) == len(set(names))
    missing = [n for n in names if n not in pool]
    assert not missing, missing
    assert len(names) == 45
    commons = [c['name'] for c in data.CHARMS_POOL if c['rarity'] == 'Common']
    assert not any(n in names for n in commons)


def test_starter_charms_unlocked_without_progress():
    g = FakeGame()
    assert ach.is_charm_unlocked(g, 'Basic Charm')
    assert ach.is_charm_unlocked(g, 'Joker Die')
    assert not ach.is_charm_unlocked(g, 'Critical Hit')
    assert not ach.is_charm_unlocked(g, 'Castle Cube')
    assert not ach.is_charm_unlocked(g, 'Cloak of Cunning')


def test_shop_hides_rare_at_stake_1_even_if_unlocked():
    g = FakeGame()
    g.progress['unlocked_charms'] = ['Luchador Lens', 'Critical Hit']
    g.current_stake = 1
    pool = [c for c in data.CHARMS_POOL if c['name'] in ('Basic Charm', 'Luchador Lens', 'Critical Hit')]
    out = ach.filter_shop_pool(g, pool)
    names = [c['name'] for c in out]
    assert 'Basic Charm' in names
    assert 'Luchador Lens' not in names  # Rare, stake 1
    assert 'Critical Hit' not in names  # Legendary, stake 1
    g.current_stake = 2
    out2 = ach.filter_shop_pool(g, pool)
    names2 = [c['name'] for c in out2]
    assert 'Luchador Lens' in names2
    assert 'Critical Hit' not in names2
    g.current_stake = 4
    out3 = ach.filter_shop_pool(g, pool)
    names3 = [c['name'] for c in out3]
    assert 'Critical Hit' in names3


def test_locked_charm_never_in_shop():
    g = FakeGame()
    g.current_stake = 8
    pool = [c for c in data.CHARMS_POOL if c['name'] == 'Critical Hit']
    assert ach.filter_shop_pool(g, pool) == []


def test_boxcars_unlocks_critical_hit():
    g = FakeGame()
    newly = ach.evaluate(g, 'score', persist=False, hand_type='5 of a Kind',
                         faces=[6, 6, 6, 6, 6], all_sixes=True, colors=['Red'] * 5)
    ids = [a['id'] for a in newly]
    assert 'boxcars' in ids
    assert 'Critical Hit' in g.progress['unlocked_charms']
    again = ach.evaluate(g, 'score', persist=False, hand_type='5 of a Kind',
                         faces=[6, 6, 6, 6, 6], all_sixes=True)
    assert again == []


def test_close_loss():
    g = FakeGame()
    ach.evaluate(g, 'lose', persist=False, score=80, target=100, close=True)
    assert 'Cloak of Cunning' in g.progress['unlocked_charms']


def test_beat_stake_unlocks_batch():
    g = FakeGame()
    ach.evaluate(g, 'blind_win', persist=False, is_boss=True, stake=2, charm_count=3, coins=10)
    charms = g.progress['unlocked_charms']
    assert 'Luchador Lens' in charms  # s1 caught up
    assert 'Sloth Sigil' in charms
    assert 'Acrobat Amulet' in charms
    assert 'Reroll Recycler Charm' in charms


def test_win_run_life_milestone():
    g = FakeGame()
    ach.evaluate(g, 'run_win', persist=False, stake=8)
    assert 'Life Milestone' in g.progress['unlocked_charms']
    assert g.progress['stats']['max_stake_beaten'] >= 8


def test_sell_two_mortgage():
    g = FakeGame()
    ach.evaluate(g, 'sell', persist=False)
    assert 'Monopoly Mortgage' not in g.progress['unlocked_charms']
    ach.evaluate(g, 'sell', persist=False)
    assert 'Monopoly Mortgage' in g.progress['unlocked_charms']


def test_fiveoak_mono_flower_pot():
    g = FakeGame()
    ach.evaluate(g, 'score', persist=False, hand_type='5 of a Kind',
                 colors=['Blue', 'Blue', 'Blue', 'Blue', 'Rainbow'], mono=True,
                 faces=[2, 2, 2, 2, 2])
    assert 'Flower Pot Prism' in g.progress['unlocked_charms']


def test_unlock_all_and_reset():
    g = FakeGame()
    ach.unlock_all(g, persist=False)
    assert ach.is_charm_unlocked(g, 'Critical Hit')
    assert ach.is_pouch_unlocked(g, 'Ghost Pouch')
    assert ach.is_pouch_unlocked(g, 'Black Pouch')
    assert ach.is_pouch_unlocked(g, 'Plasma Pouch')
    assert ach.is_pouch_unlocked(g, 'Erratic Pouch')
    assert len(g.progress['unlocked_achievements']) == len(ach.ACHIEVEMENTS)
    ach.reset_progress(g, persist=False)
    assert not ach.is_charm_unlocked(g, 'Critical Hit')
    assert not ach.is_pouch_unlocked(g, 'Ghost Pouch')
    assert ach.is_pouch_unlocked(g, 'Red Pouch')
    assert g.progress['unlocked_achievements'] == []


def test_score_payload_all_sixes():
    g = FakeGame()
    dice = [({'color': 'Red'}, 6)] * 5
    p = ach.score_payload(g, '5 of a Kind', dice)
    assert p['all_sixes'] is True
    assert p['all_red'] is True


def test_locked_charms_skip_pouch_names():
    names = ach.locked_charm_names()
    for pouch in ach.LOCKED_POUCHES:
        assert pouch not in names
    assert len(names) == 45


def test_starter_pouches_always_open():
    g = FakeGame()
    for name in ach.STARTER_POUCHES:
        assert ach.is_pouch_unlocked(g, name)
        assert ach.is_pouch_unlocked(g, {'name': name})
    for name in ach.LOCKED_POUCHES:
        assert not ach.is_pouch_unlocked(g, name)


def test_dice_added_unlocks_ghost():
    g = FakeGame()
    for _ in range(9):
        newly = ach.evaluate(g, 'dice_added', persist=False, n=1)
        assert 'pouch_ghost' not in [a['id'] for a in newly]
    newly = ach.evaluate(g, 'dice_added', persist=False, n=1)
    assert 'pouch_ghost' in [a['id'] for a in newly]
    assert 'Ghost Pouch' in g.progress['unlocked_pouches']
    assert 'Ghost Pouch' not in g.progress['unlocked_charms']
    assert ach.is_pouch_unlocked(g, 'Ghost Pouch')


def test_beat_stake_2_unlocks_black_pouch():
    g = FakeGame()
    ach.evaluate(g, 'blind_win', persist=False, is_boss=True, stake=2, charm_count=3, coins=10)
    assert 'Black Pouch' in g.progress['unlocked_pouches']
    assert 'Plasma Pouch' not in g.progress['unlocked_pouches']
    assert ach.is_pouch_unlocked(g, 'Black Pouch')


def test_beat_stake_4_unlocks_plasma_pouch():
    g = FakeGame()
    ach.evaluate(g, 'blind_win', persist=False, is_boss=True, stake=4, charm_count=3, coins=10)
    assert 'Plasma Pouch' in g.progress['unlocked_pouches']
    assert 'Black Pouch' in g.progress['unlocked_pouches']  # catch-up
    assert 'Erratic Pouch' not in g.progress['unlocked_pouches']


def test_win_run_unlocks_erratic_pouch():
    g = FakeGame()
    ach.evaluate(g, 'run_win', persist=False, stake=8)
    assert 'Life Milestone' in g.progress['unlocked_charms']
    assert 'Erratic Pouch' in g.progress['unlocked_pouches']
    assert ach.is_pouch_unlocked(g, 'Erratic Pouch')


def test_pouch_unlock_hint_tracks_dice():
    g = FakeGame()
    g.progress['stats']['dice_added'] = 3
    hint = ach.pouch_unlock_hint(g, 'Ghost Pouch')
    assert '10' in hint
    assert '(3/10)' in hint
    black = ach.pouch_unlock_hint(g, 'Black Pouch')
    assert 'Stake 2' in black


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

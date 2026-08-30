# Headless: Intensify gate + boss pool by stake.
import os
import sys
from types import ModuleType, SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.init = lambda: None
    sys.modules['pygame'] = pg

import data
from data import bosses_for_stake, intensify_unlocked, INTENSIFY_MIN_STAKE, BOSS_EFFECTS


def names(pool):
    return {b['name'] for b in pool}


def test_all_bosses_have_min_stake_and_diff():
    assert len(BOSS_EFFECTS) == 30
    for b in BOSS_EFFECTS:
        assert b['difficulty'] in ('Easy', 'Medium', 'Hard')
        assert b['min_stake'] in (1, 3, 5)


def test_stake_1_is_easy_only():
    n = names(bosses_for_stake(1))
    assert n == names(bosses_for_stake(2))
    assert 'Hold Ban' not in n
    assert 'Charm Eclipse' not in n
    assert 'Reroll Ration' in n
    assert 'Coin Freeze' in n
    assert all(b['difficulty'] == 'Easy' for b in bosses_for_stake(1))


def test_stake_3_adds_medium():
    n = names(bosses_for_stake(3))
    assert 'Hold Limit' in n
    assert 'Discard Delay' in n
    assert 'Charm Eclipse' not in n
    diffs = {b['difficulty'] for b in bosses_for_stake(3)}
    assert diffs == {'Easy', 'Medium'}


def test_stake_5_adds_hard():
    n = names(bosses_for_stake(5))
    assert 'Charm Eclipse' in n
    assert 'Hold Ban' in n
    assert 'Charm Tax' in n
    assert 'Reroll Ration' in n  # easy still in the mix until 7


def test_stake_7_drops_easy():
    n = names(bosses_for_stake(7))
    assert 'Reroll Ration' not in n
    assert 'Hold Ban' in n
    assert 'Hold Limit' in n
    diffs = {b['difficulty'] for b in bosses_for_stake(8)}
    assert 'Easy' not in diffs


def test_endless_is_hard_only():
    assert all(b['difficulty'] == 'Hard' for b in bosses_for_stake(9))
    assert 'Charm Eclipse' in names(bosses_for_stake(12))


def test_intensify_gate():
    assert INTENSIFY_MIN_STAKE == 2
    assert intensify_unlocked(1) is False
    assert intensify_unlocked(2) is True
    assert intensify_unlocked(8) is True


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

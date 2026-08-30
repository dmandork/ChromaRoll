# Headless tests for DEBUG play-bar helpers. No pygame.
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from debug_cheats import (
    PLAY_DEBUG_ACTIONS, close_lose_score, win_notify_kwargs,
    apply_paint, add_steel,
)
import achievements as ach


def test_close_lose_is_80_percent_not_a_win():
    assert close_lose_score(100) == 80
    assert close_lose_score(100) < 100
    assert close_lose_score(0) == 0


def test_win_payload_marks_boss_and_last_hand():
    g = SimpleNamespace(
        current_blind='Boss', current_stake=8,
        current_boss_effect={'name': 'Hold Ban'},
        d20_boon=SimpleNamespace(active=True),
        hands_left=0, equipped_charms=[{'name': 'A'}],
        coins=40, progress={'run': {'rerolls_this_blind': 0}},
        hand_multipliers={'Pair': 1.0},
    )
    kw = win_notify_kwargs(g)
    assert kw['is_boss'] is True
    assert kw['stake'] == 8
    assert kw['hard_boss'] is True
    assert kw['intensified'] is True
    assert kw['last_hand'] is True
    assert kw['no_reroll'] is True
    assert kw['charm_count'] == 1
    assert kw['coins'] == 40


def test_paint_sixes_and_red():
    rolls = [({'color': 'Blue', 'enhancements': []}, 2) for _ in range(5)]
    hand = [{'color': 'Blue'} for _ in range(5)]
    held = [False] * 5
    out, held2 = apply_paint(rolls, hand, held, 'sixes')
    assert all(v == 6 for _d, v in out)
    assert all(held2)
    out2, _ = apply_paint(out, hand, held2, 'red')
    assert all(d['color'] == 'Red' for d, _v in out2)


def test_paint_glass_two():
    rolls = [({'color': 'Yellow', 'enhancements': []}, 3) for _ in range(5)]
    out, held = apply_paint(rolls, [{'color': 'Yellow'}] * 5, [False] * 5, 'glass')
    assert out[0][0]['color'] == 'Glass'
    assert out[1][0]['color'] == 'Glass'
    assert out[2][0]['color'] == 'Yellow'
    assert held[0] and held[1]


def test_steel_stamps_first_die_and_syncs_full_bag():
    d = {'id': 'R1', 'color': 'Red', 'enhancements': []}
    full = [d]
    bag = [d]
    stamped = add_steel(bag, full)
    assert stamped is d
    assert 'Steel' in d['enhancements']
    assert 'Steel' in full[0]['enhancements']


def test_forced_win_payload_unlocks_beat_stake():
    g = SimpleNamespace(
        _skip_ach_persist=True,
        progress=ach.default_progress(),
        current_blind='Boss', current_stake=1,
        current_boss_effect={'name': 'Blind Boost'},
        d20_boon=None, hands_left=2, equipped_charms=[],
        coins=10, hand_multipliers={},
    )
    g.unlocks = g.progress
    ach.evaluate(g, 'blind_win', persist=False, **win_notify_kwargs(g))
    assert 'beat_s1' in g.progress['unlocked_achievements']
    assert 'Luchador Lens' in g.progress['unlocked_charms']


def test_close_lose_unlocks_cloak():
    g = SimpleNamespace(
        _skip_ach_persist=True,
        progress=ach.default_progress(),
        temp_message=None, temp_message_start=0, temp_message_duration=3.0,
    )
    g.unlocks = g.progress
    score = close_lose_score(200)
    ach.evaluate(g, 'lose', persist=False, score=score, target=200, close=True)
    assert 'so_close' in g.progress['unlocked_achievements']
    assert 'Cloak of Cunning' in g.progress['unlocked_charms']


def test_play_bar_covers_the_painful_gates():
    keys = [k for k, _ in PLAY_DEBUG_ACTIONS]
    for need in ('win', 'lose', 'close', 'last', 'coins', 'empty', 'sixes', 'red', 'glass', 'steel'):
        assert need in keys


if __name__ == '__main__':
    tests = [v for k, v in list(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in tests:
        try:
            fn()
            print('OK', fn.__name__)
        except Exception as e:
            failed += 1
            print('FAIL', fn.__name__, e)
    print(f'{len(tests) - failed}/{len(tests)} passed')
    sys.exit(1 if failed else 0)

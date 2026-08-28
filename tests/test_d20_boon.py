# Headless tests for the D20 boon owner. No pygame.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from d20_boon import D20BoonSystem, HAND_TYPES, BASE_COLORS, tier_for_roll


class FakeGame:
    def __init__(self):
        self.coins = 0
        self.discards_left = 3
        self.temp_message = ''
        self.has_free_prism_pack = False
        self.target_mult = 1.0
        self.selecting_advantage_die = False
        self.has_advantage = False


def test_tiers_cover_1_to_20():
    names = [tier_for_roll(n)['name'] for n in range(1, 21)]
    assert names[0] == names[3] == 'Prism Fracture'
    assert names[4] == names[7] == 'Hue Dimming'
    assert names[8] == names[11] == 'Roll Harmony'
    assert names[12] == names[15] == 'Roll Flow'
    assert names[16] == names[19] == 'Chroma Radiance'


def test_t1_same_hand_for_block_and_reward():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(2)
    assert b.disabled_hand_type in HAND_TYPES
    assert b.pending_hand_type_mult == {b.disabled_hand_type: 2.0}
    assert b.pending_free_prism is True
    assert b.target_mult == 1.5
    assert b.is_hand_blocked(b.disabled_hand_type, ['Red']) is True
    assert b.is_hand_blocked('Pair' if b.disabled_hand_type != 'Pair' else '2 Pair', ['Red']) is False


def test_t1_fusion_exempt():
    b = D20BoonSystem()
    b.start_boon('Blue')
    b.apply_roll(3)
    assert b.exempt_color == 'Blue'
    assert b.is_hand_blocked(b.disabled_hand_type, ['Red', 'Green']) is True
    assert b.is_hand_blocked(b.disabled_hand_type, ['Blue', 'Red']) is False


def test_t2_dim_once_and_queue():
    b = D20BoonSystem()
    b.start_boon('Green')
    b.apply_roll(6)
    assert b.dimmed_color == 'Green'
    assert b.dim_factor(['Green', 'Red']) == 0.8
    assert b.dim_factor(['Red']) == 1.0
    assert b.pending_hand_mult_next == 2.0
    assert b.pending_coins == 20
    assert b.pending_color_mult_next == {'Green': 1.3}


def test_t3_this_blind_not_queued():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(10)
    assert b.score_mult_this == 1.5
    assert b.extra_discards_this == 1
    assert b.harmony_active
    assert b.pending_hand_mult_next == 1.0
    g = FakeGame()
    b.grant_this_blind_resources(g)
    assert g.discards_left == 4


def test_t4_flow():
    b = D20BoonSystem()
    b.start_boon('Red')
    b.apply_roll(14)
    assert b.score_mult_this == 2.5
    assert b.flow_advantage
    assert b.extra_rerolls_per_hand == 1
    assert b.target_mult == 0.88
    rolls = [({'color': 'Blue'}, 1), ({'color': 'Red'}, 3), ({'color': 'Green'}, 2)]
    assert b.preferred_advantage_index(rolls) == 1


def test_t5_radiance_and_next_two():
    b = D20BoonSystem()
    b.start_boon('Yellow')
    b.apply_roll(18)
    assert b.chroma_global == 1.3
    assert abs(b.color_score_mult(['Yellow']) - 1.5) < 1e-6
    assert abs(b.color_score_mult(['Red']) - 1.3) < 1e-6
    g = FakeGame()
    b.on_blind_won(g)
    assert g.coins == 50
    b.end_this_blind(g)
    assert b.active is False
    b.begin_next_blind(g)
    assert b.next_blind_score_mult == 4.0
    assert b.next_blind_score_mult_blinds_left == 2
    assert b.wildcard_color == 'Yellow'
    assert b.extra_score_mult('Pair') == 4.0
    b.end_this_blind(g)
    assert b.next_blind_score_mult_blinds_left == 1
    assert b.next_blind_score_mult == 4.0
    b.end_this_blind(g)
    assert b.next_blind_score_mult == 1.0


def test_win_does_not_touch_zero_score():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(10)  # harmony 1.5 this blind
    g = FakeGame()
    g.round_score = 0
    b.on_blind_won(g)
    assert g.round_score == 0  # attribute unused; we never multiply it


def test_t1_reward_applies_next_blind_only():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(1)
    blocked = b.disabled_hand_type
    assert b.extra_score_mult(blocked) == 1.0  # not yet
    g = FakeGame()
    b.on_blind_won(g)
    b.end_this_blind(g)
    b.begin_next_blind(g)
    assert b.extra_score_mult(blocked) == 2.0
    b.end_this_blind(g)
    assert b.extra_score_mult(blocked) == 1.0


def test_save_roundtrip():
    b = D20BoonSystem()
    b.start_boon('Purple')
    b.apply_roll(7)
    d = b.to_dict()
    b2 = D20BoonSystem()
    b2.from_dict(d)
    assert b2.dimmed_color == 'Purple'
    assert b2.fused_color == 'Purple'
    assert b2.pending_coins == 20


def test_hue_next_hand_consumes():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(6)
    g = FakeGame()
    b.on_blind_won(g)
    b.end_this_blind(g)
    b.begin_next_blind(g)
    assert b.next_hand_mult == 2.0
    m = b.extra_score_mult('Pair', consume_next_hand=False)
    assert m == 2.0
    assert b.next_hand_mult == 2.0
    m = b.extra_score_mult('Pair', consume_next_hand=True)
    assert m == 2.0
    assert b.next_hand_mult == 1.0


def test_t5_wildcard_consumes_on_first_score():
    b = D20BoonSystem()
    b.start_boon('Yellow')
    b.apply_roll(18)
    g = FakeGame()
    b.on_blind_won(g)
    b.end_this_blind(g)
    b.begin_next_blind(g)
    assert b.wildcard_color == 'Yellow'
    b.extra_score_mult('Pair', consume_next_hand=False)
    assert b.wildcard_color == 'Yellow'
    b.extra_score_mult('Pair', consume_next_hand=True)
    assert b.wildcard_color is None


def test_leftover_survives_new_intensify():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(18)
    g = FakeGame()
    b.on_blind_won(g)
    b.end_this_blind(g)
    b.begin_next_blind(g)
    assert b.next_blind_score_mult == 4.0
    b.start_boon('Red')
    b.apply_roll(10)  # harmony this-blind, leftover 4x stays live
    assert b.next_blind_score_mult == 4.0
    assert b.score_mult_this == 1.5
    assert abs(b.extra_score_mult('Pair') - 6.0) < 1e-6


def test_free_prism_stays_until_claimed():
    b = D20BoonSystem()
    b.start_boon(None)
    b.apply_roll(2)
    g = FakeGame()
    b.on_blind_won(g)
    assert b.free_prism_pack is True
    b.end_this_blind(g)
    assert b.free_prism_pack is True  # shop still owes the pack


def test_hud_lines_active_and_leftover():
    b = D20BoonSystem()
    b.start_boon('Blue')
    b.apply_roll(3)
    lines = b.hud_lines()
    assert any('Prism Fracture' in x for x in lines)
    assert any('Fusion:Blue' in x for x in lines)
    g = FakeGame()
    b.on_blind_won(g)
    b.end_this_blind(g)
    leftover = b.hud_lines()
    assert any('Free Prism Pack' in x for x in leftover)


def test_harmony_lock_prefers_fusion():
    b = D20BoonSystem()
    b.start_boon('Red')
    b.apply_roll(10)
    rolls = [({'color': 'Blue'}, 1), ({'color': 'Red'}, 3), ({'color': 'Green'}, 2),
             ({'color': 'Yellow'}, 4), ({'color': 'Purple'}, 5)]
    for _ in range(20):
        idx = b.pick_harmony_lock(rolls)
        assert idx == 1  # only Red die


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
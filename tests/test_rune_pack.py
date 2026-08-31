# Rune packs: pick 1 (or 2 for Super), not every option in the pack.
import os
import sys
from types import ModuleType

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.init = lambda: None
    sys.modules['pygame'] = pg

# Mirror shop.py pack tables
PACK_CHOICES_NUM = [2, 3, 5, 3, 4, 3, 3, 5, 5, 1, 5]
PACK_SELECT_NUM = [1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1]


def test_rune_packs_pick_one_or_two_not_the_whole_list():
    # idx 6 Basic Rune, 7 Mega, 8 Super
    assert PACK_SELECT_NUM[6] == 1
    assert PACK_SELECT_NUM[7] == 1
    assert PACK_SELECT_NUM[8] == 2
    assert PACK_CHOICES_NUM[6] == 3
    assert PACK_CHOICES_NUM[7] == 5
    assert PACK_CHOICES_NUM[8] == 5
    for idx in (6, 7, 8):
        assert PACK_SELECT_NUM[idx] < PACK_CHOICES_NUM[idx]


def test_shop_assigns_select_count_not_choices_count():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'states', 'shop.py')).read()
    assert 'pack_select_count = pack_select_num[pack_idx]' in src
    assert 'pack_select_count = pack_choices_num[pack_idx]' not in src


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

# Headless tests for play-screen casino table layout. No pygame window.
import os
import sys
from types import ModuleType, SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeRect:
    def __init__(self, x, y, w=0, h=0):
        if hasattr(x, 'x'):
            self.x, self.y, self.width, self.height = x.x, x.y, x.width, x.height
        else:
            self.x, self.y, self.width, self.height = int(x), int(y), int(w), int(h)
        self.left = self.x
        self.top = self.y
        self.right = self.x + self.width
        self.bottom = self.y + self.height
        self.centerx = self.x + self.width // 2
        self.centery = self.y + self.height // 2

    def inflate(self, dx, dy):
        return FakeRect(self.x - dx // 2, self.y - dy // 2, self.width + dx, self.height + dy)

    def collidepoint(self, *a):
        return False


if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.init = lambda: None
    pg.Rect = FakeRect
    pg.Surface = lambda *a, **k: SimpleNamespace(
        get_width=lambda: 0, get_height=lambda: 0, blit=lambda *a, **k: None,
        fill=lambda *a, **k: None, get_rect=lambda **k: FakeRect(0, 0, 0, 0))
    pg.display = SimpleNamespace(set_mode=lambda *a, **k: None, flip=lambda: None, set_caption=lambda *a: None)
    pg.mixer = SimpleNamespace(init=lambda *a, **k: None)
    pg.draw = SimpleNamespace(
        rect=lambda *a, **k: None, circle=lambda *a, **k: None,
        polygon=lambda *a, **k: None, ellipse=lambda *a, **k: None, line=lambda *a, **k: None)
    pg.font = SimpleNamespace(init=lambda: None, Font=lambda *a, **k: None, SysFont=lambda *a, **k: None)
    pg.image = SimpleNamespace(load=lambda *a, **k: None)
    pg.transform = SimpleNamespace(smoothscale=lambda *a, **k: None, grayscale=lambda s: s)
    pg.SRCALPHA = 16
    sys.modules['pygame'] = pg

import data  # noqa: F401
from screens import (
    play_die_slot, PLAY_CHARM_Y, PLAY_BAG_Y, bag_geometry, TABLE_RAIL,
    _payout_row, _plaque_preview,
)
from constants import DIE_SIZE, NUM_DICE_IN_HAND, INITIAL_WIDTH, INITIAL_HEIGHT, CHARM_SIZE


class FakeGame:
    def __init__(self):
        self.width = INITIAL_WIDTH
        self.height = INITIAL_HEIGHT
        self.bag = [{'id': i, 'color': 'Red'} for i in range(25)]
        self.rolls = []
        self.held = [False] * 5
        self.discard_selected = [False] * 5
        self.equipped_charms = []
        self.current_hand_text = ''
        self.current_modifier_text = ''
        self.is_discard_phase = False


def test_die_slots_match_legacy_formula():
    g = FakeGame()
    total = NUM_DICE_IN_HAND * (DIE_SIZE + 20) - 20
    start_x = (g.width - total) // 2
    for i in range(5):
        slot = play_die_slot(g, i)
        assert slot.x == start_x + i * (DIE_SIZE + 20)
        assert slot.y == g.height - DIE_SIZE - 100
        assert slot.width == DIE_SIZE


def test_charms_and_bag_sit_on_felt():
    g = FakeGame()
    bag, tray = bag_geometry(g)
    assert PLAY_CHARM_Y > TABLE_RAIL
    assert bag.y > TABLE_RAIL
    assert bag.y - 10 >= TABLE_RAIL
    assert bag.right <= g.width - TABLE_RAIL
    assert bag.x > g.width // 2
    for r in tray:
        assert r.y == bag.y
        assert r.x >= TABLE_RAIL


def test_payout_row_counts_dollar_signs():
    assert _payout_row("Hands left: $$$$") == ("Hands left", "$4")
    assert _payout_row("Coins gained: $$$$$$$$$$$$") == ("Coins gained", "$12")
    assert _payout_row("Echo Coins: $3") == ("Echo Coins", "$3")
    assert _payout_row("") is None


def test_plaque_preview_parses_hand_text():
    g = FakeGame()
    g.current_hand_text = "Current Hand: 2 Pair (60 base + 0.0 charms) = 120 total"
    g.current_modifier_text = "Modifiers: None"
    g.is_discard_phase = False
    name, preview, detail = _plaque_preview(g)
    assert name == '2 Pair'
    assert preview == 120
    assert '60 base' in detail
    g.is_discard_phase = True
    name, preview, _ = _plaque_preview(g)
    assert preview is None


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

# Headless tests for stake/blinds layout. No pygame window.
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

    def collidepoint(self, *a):
        return False


if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.init = lambda: None
    pg.Rect = FakeRect
    pg.Surface = lambda *a, **k: SimpleNamespace(
        get_width=lambda: 0, get_height=lambda: 0, blit=lambda *a, **k: None,
        fill=lambda *a, **k: None, get_rect=lambda **k: FakeRect(0, 0, 0, 0),
        copy=lambda: None, set_alpha=lambda *a: None)
    pg.display = SimpleNamespace(set_mode=lambda *a, **k: None, flip=lambda: None, set_caption=lambda *a: None)
    pg.mixer = SimpleNamespace(init=lambda *a, **k: None)
    pg.font = SimpleNamespace(init=lambda: None, Font=lambda *a, **k: None, SysFont=lambda *a, **k: None)
    pg.draw = SimpleNamespace(rect=lambda *a, **k: None, circle=lambda *a, **k: None, polygon=lambda *a, **k: None)
    pg.transform = SimpleNamespace(smoothscale=lambda *a, **k: None, grayscale=lambda s: s)
    pg.SRCALPHA = 16
    sys.modules['pygame'] = pg

import data  # noqa: F401
from screens import blinds_layout, blind_status, PLAY_CHARM_Y, PLAY_BAG_Y, bag_geometry
from constants import CHARM_SIZE, BUTTON_HEIGHT, INITIAL_WIDTH, INITIAL_HEIGHT


class FakeGame:
    def __init__(self, n_dice=25):
        self.width = INITIAL_WIDTH
        self.height = INITIAL_HEIGHT
        self.bag = [{'id': i, 'color': 'Red', 'enhancements': []} for i in range(n_dice)]
        self.current_stake = 3
        self.current_blind = 'Big'
        self.coins = 12
        self.current_pouch = {'name': 'Red Pouch', 'color': 'Red'}
        self.equipped_charms = []
        self.rune_tray = [None, None]


def test_blind_status_order():
    assert blind_status('Small', 'Small') == 'current'
    assert blind_status('Small', 'Big') == 'future'
    assert blind_status('Big', 'Small') == 'past'
    assert blind_status('Boss', 'Big') == 'past'
    assert blind_status('Boss', 'Boss') == 'current'


def test_layout_keeps_play_charm_and_bag():
    g = FakeGame()
    bag, tray = bag_geometry(g)
    layout = blinds_layout(g)
    assert bag.y == PLAY_BAG_Y
    assert bag.right <= g.width
    assert bag.x > g.width // 2  # top-right
    for card in layout['cards']:
        assert card.y >= layout['header_y'] + 60
        assert card.bottom <= layout['continue'].y
        assert card.y >= bag.bottom or card.right < bag.x
    assert layout['intensify'].y == layout['continue'].y
    assert layout['continue'].y == g.height - BUTTON_HEIGHT - 28


def test_header_stays_above_cards_with_or_without_charms():
    g = FakeGame()
    empty = blinds_layout(g)
    g.equipped_charms = [{'name': 'Basic Charm', 'type': 'flat'} for _ in range(5)]
    filled = blinds_layout(g)
    for layout in (empty, filled):
        for card in layout['cards']:
            assert card.y >= layout['header_y'] + layout['header_block'] - 1
    # Charms present → title drops below the charm row, cards follow.
    assert filled['header_y'] >= PLAY_CHARM_Y + CHARM_SIZE
    assert filled['cards'][0].y >= empty['cards'][0].y


def test_cards_are_tall_not_postage():
    g = FakeGame()
    cards = blinds_layout(g)['cards']
    assert len(cards) == 3
    for card in cards:
        assert card.width >= 180
        assert card.height >= 160
    # Small left, Boss right
    assert cards[0].x < cards[1].x < cards[2].x


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

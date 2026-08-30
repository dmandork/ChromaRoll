# Headless tests for Pass C UI layout / tooltip copy. No pygame window.
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

    def collidepoint(self, *a):
        return False

    def inflate(self, *a):
        return self


if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT = 273, 274, 276, 275
    pg.QUIT, pg.MOUSEBUTTONDOWN, pg.KEYDOWN = 12, 5, 2
    pg.init = lambda: None
    pg.Rect = FakeRect
    pg.Surface = lambda *a, **k: SimpleNamespace(
        get_width=lambda: 0, get_height=lambda: 0, blit=lambda *a, **k: None,
        fill=lambda *a, **k: None, get_rect=lambda **k: FakeRect(0, 0, 0, 0),
        copy=lambda: None, set_alpha=lambda *a: None)
    pg.display = SimpleNamespace(set_mode=lambda *a, **k: None, flip=lambda: None, set_caption=lambda *a, **k: None)
    pg.mixer = SimpleNamespace(init=lambda *a, **k: None, Sound=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None), Channel=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None))
    pg.font = SimpleNamespace(init=lambda: None, Font=lambda *a, **k: None, SysFont=lambda *a, **k: None)
    pg.image = SimpleNamespace(load=lambda *a, **k: None)
    pg.draw = SimpleNamespace(rect=lambda *a, **k: None, circle=lambda *a, **k: None, line=lambda *a, **k: None, polygon=lambda *a, **k: None)
    pg.transform = SimpleNamespace(smoothscale=lambda *a, **k: None, grayscale=lambda s: s)
    pg.SRCALPHA = 16
    sys.modules['pygame'] = pg

import data  # load data→constants before screens (avoids circular import)
from screens import (
    charm_tooltip_text, bag_geometry, bag_cells, PLAY_BAG_Y, PLAY_CHARM_Y, WIN_POPUP_WIDTH,
    charm_is_visually_disabled,
)
from constants import BUTTON_WIDTH, BUTTON_HEIGHT, INITIAL_WIDTH, INITIAL_HEIGHT


class FakeGame:
    def __init__(self):
        self.width = INITIAL_WIDTH
        self.height = INITIAL_HEIGHT
        self.bag = [{'id': i, 'color': 'Red', 'enhancements': []} for i in range(25)]
        self.rolls = []
        self.held = []
        self.equipped_charms = []
        self.disabled_charms = []
        self.score_mult = 1.0
        self.discards_used_this_round = 0
        self.discards_left = 3
        self.stake_milestones = 0
        self.final_discard_mult = 0
        self.lucky_triggers = 0
        self.max_charms = 5


def test_no_preview_restates():
    g = FakeGame()
    acrobat = {'name': 'Acrobat Amulet', 'type': 'mult_final_discard', 'value': 2,
               'desc': '+2 mult on final discard of round.'}
    text = charm_tooltip_text(g, acrobat)
    assert 'Preview:' not in text
    assert text.count('+2 mult on final discard') == 1
    cloak = {'name': 'Cloak of Cunning', 'type': 'loss_prevent',
             'desc': 'Saves you from losing the game. One per game.'}
    t2 = charm_tooltip_text(g, cloak)
    assert 'Preview:' not in t2
    forge = {'name': 'Final Forge', 'type': 'final_mult_conditional', 'value': 3,
             'desc': '+3 mult on last hand if it includes an enhancement.'}
    t3 = charm_tooltip_text(g, forge)
    assert t3.count('Preview:') == 0
    assert t3.count('+3 mult on last hand') == 1


def test_live_values_only():
    g = FakeGame()
    g.discards_used_this_round = 2
    drake = {'name': 'Discard Drake', 'type': 'discard_mult', 'value': 1,
             'desc': '+1 mult per discard used this round.'}
    text = charm_tooltip_text(g, drake)
    assert 'Now: +2.0 (2 discards)' in text or 'Now: +2 (2 discards)' in text
    ice = {'name': 'Ice Shard', 'type': 'score_decay', 'start': 100, 'decay': 5,
           'hands_played': 0, 'desc': '+100 score. -5 score per hand played.'}
    t2 = charm_tooltip_text(g, ice)
    assert 'This hand: +100' in t2


def test_bag_geometry_top_right():
    g = FakeGame()
    bag_rect, tray = bag_geometry(g)
    assert bag_rect.y == PLAY_BAG_Y
    assert bag_rect.right <= g.width
    assert bag_rect.x > g.width // 2
    assert len(tray) == 2
    _, _, cells = bag_cells(g)
    assert len(cells) == 25
    # Click cells share the bag's Y origin so hover cannot drift to y=50
    assert all(rect.y >= PLAY_BAG_Y for _d, rect in cells)


def test_intensify_continue_no_overlap():
    btn_y = INITIAL_HEIGHT - BUTTON_HEIGHT - 28
    gap = 24
    total = BUTTON_WIDTH * 2 + gap
    start_x = INITIAL_WIDTH // 2 - total // 2
    intensify = FakeRect(start_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    cont = FakeRect(start_x + BUTTON_WIDTH + gap, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    overlap_x = not (intensify.right <= cont.x or cont.right <= intensify.x)
    overlap_y = not (intensify.bottom <= cont.y or cont.bottom <= intensify.y)
    assert not (overlap_x and overlap_y)
    assert cont.x - intensify.right == gap


def test_win_popup_is_wide():
    assert WIN_POPUP_WIDTH >= 500
    assert PLAY_CHARM_Y >= 20


def test_mortgage_grays_when_locked():
    g = FakeGame()
    mort = {'name': 'Monopoly Mortgage', 'type': 'sell_double_lock', 'cost': 4, 'desc': 'Sell a charm for double coins but lock it for one round.'}
    assert charm_is_visually_disabled(g, mort, index=0) is False
    mort['locked'] = True
    assert charm_is_visually_disabled(g, mort, index=0) is True
    mort['locked'] = False
    g.mortgage_used_this_round = True
    assert charm_is_visually_disabled(g, mort, index=0) is True
    other = {'name': 'Basic Charm', 'type': 'flat_bonus', 'desc': '+10'}
    assert charm_is_visually_disabled(g, other, index=1) is False
    g.disabled_charms = [1]
    assert charm_is_visually_disabled(g, other, index=1) is True
    text = charm_tooltip_text(g, mort, index=0)
    assert 'Used this shop' in text


def test_bag_geometry_origin_for_shop_popup():
    g = FakeGame()
    default, _ = bag_geometry(g)
    moved, _ = bag_geometry(g, origin=(40, 180))
    assert (moved.x, moved.y) == (40, 180)
    assert moved.width == default.width
    assert moved.height == default.height
    _, _, cells = bag_cells(g, origin=(40, 180))
    assert len(cells) == 25
    assert all(rect.x >= 40 and rect.y >= 180 for _d, rect in cells)


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

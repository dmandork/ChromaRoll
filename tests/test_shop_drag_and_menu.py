# tests/test_shop_drag_and_menu.py
# Headless: menu/load contract + shop charm drag (swap, empty slot, park, unstick).
import os
import sys
from types import SimpleNamespace, ModuleType

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


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

    def collidepoint(self, pos):
        if isinstance(pos, (int, float)):
            px, py = pos, 0
        else:
            px, py = pos[0], pos[1]
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height

    def inflate(self, *a):
        return self

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height


class FakeFont:
    def render(self, text, *a, **k):
        return SimpleNamespace(get_width=lambda: len(str(text)) * 8, get_height=lambda: 16,
                               get_rect=lambda **kw: FakeRect(0, 0, 8, 16))

    def size(self, text):
        return (len(str(text)) * 8, 16)


if 'pygame' not in sys.modules:
    pg = ModuleType('pygame')
    pg.K_SPACE, pg.K_ESCAPE, pg.K_RETURN = 32, 27, 13
    pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT = 273, 274, 276, 275
    pg.QUIT, pg.KEYDOWN, pg.KEYUP = 12, 2, 3
    pg.MOUSEBUTTONDOWN, pg.MOUSEBUTTONUP, pg.MOUSEMOTION, pg.MOUSEWHEEL = 5, 6, 4, 7
    pg.VIDEORESIZE = 16
    pg.init = lambda: None
    pg.quit = lambda: None
    pg.error = type('error', (Exception,), {})
    pg.Rect = FakeRect
    pg.Color = lambda *a, **k: (0, 0, 0)
    pg.SRCALPHA = 16
    pg.Surface = lambda *a, **k: SimpleNamespace(
        get_width=lambda: 0, get_height=lambda: 0, blit=lambda *a, **k: None,
        fill=lambda *a, **k: None, get_rect=lambda **k: FakeRect(0, 0, 0, 0),
        copy=lambda: None, set_alpha=lambda *a: None, convert=lambda: None)
    pg.display = SimpleNamespace(
        set_mode=lambda *a, **k: None, flip=lambda: None, set_caption=lambda *a, **k: None)
    pg.mixer = SimpleNamespace(
        init=lambda *a, **k: None,
        Sound=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None),
        Channel=lambda *a, **k: SimpleNamespace(play=lambda *a, **k: None))
    pg.font = SimpleNamespace(init=lambda: None, Font=lambda *a, **k: FakeFont(),
                              SysFont=lambda *a, **k: FakeFont())
    pg.image = SimpleNamespace(load=lambda *a, **k: pg.Surface())
    pg.draw = SimpleNamespace(
        rect=lambda *a, **k: None, circle=lambda *a, **k: None,
        line=lambda *a, **k: None, polygon=lambda *a, **k: None)
    pg.transform = SimpleNamespace(smoothscale=lambda *a, **k: pg.Surface(), grayscale=lambda s: s)
    pg.mouse = SimpleNamespace(get_pos=lambda: (0, 0))
    sys.modules['pygame'] = pg

import data  # load data→constants before shop/screens (avoids circular import)
from states.shop import drop_shop_charm, park_shop_charm, try_buy_shop_charm
from savegame import is_run_save, resolve_run_state, save_on_exit, save_game
import savegame
from states.base import _SKIP_AUTOSAVE, _RUN_AUTOSAVE
import achievements as ach


def _game(n=3, max_c=5):
    g = SimpleNamespace()
    g.equipped_charms = [{'name': f'C{i}'} for i in range(n)]
    g.max_charms = max_c
    g.dragging_charm_index = 0
    g.dragging_shop = True
    g.shop_slot_rects = [FakeRect(i * 10, 0, 10, 10) for i in range(max_c)]
    return g


def test_drop_swaps_occupied():
    g = _game(3)
    drop_shop_charm(g, (25, 5))  # slot 2
    assert [c['name'] for c in g.equipped_charms] == ['C2', 'C1', 'C0']
    assert g.dragging_charm_index == -1
    assert g.dragging_shop is False


def test_drop_on_empty_moves_to_end():
    g = _game(3)
    drop_shop_charm(g, (45, 5))  # slot 4 empty
    assert [c['name'] for c in g.equipped_charms] == ['C1', 'C2', 'C0']
    assert g.dragging_charm_index == -1


def test_drop_on_first_empty_slot():
    g = _game(3)
    drop_shop_charm(g, (35, 5))  # slot 3 is the first empty
    assert [c['name'] for c in g.equipped_charms] == ['C1', 'C2', 'C0']
    assert g.dragging_charm_index == -1


def test_drop_on_own_slot_unsticks():
    g = _game(3)
    drop_shop_charm(g, (5, 5))  # slot 0, same as drag
    assert [c['name'] for c in g.equipped_charms] == ['C0', 'C1', 'C2']
    assert g.dragging_charm_index == -1


def test_drop_miss_unsticks():
    g = _game(5)
    drop_shop_charm(g, (900, 900))
    assert [c['name'] for c in g.equipped_charms] == ['C0', 'C1', 'C2', 'C3', 'C4']
    assert g.dragging_charm_index == -1


def test_fifth_charm_drop_unsticks():
    g = _game(5)
    g.dragging_charm_index = 4
    drop_shop_charm(g, (5, 5))  # swap 4 with 0
    assert [c['name'] for c in g.equipped_charms] == ['C4', 'C1', 'C2', 'C3', 'C0']
    assert g.dragging_charm_index == -1
    assert g.dragging_shop is False


def test_park_full_row_unsticks():
    g = _game(5)
    park_shop_charm(g)
    assert g.dragging_charm_index == -1
    assert [c['name'] for c in g.equipped_charms] == ['C0', 'C1', 'C2', 'C3', 'C4']


def test_park_empty_slot_moves_to_end():
    g = _game(3)
    park_shop_charm(g)
    assert [c['name'] for c in g.equipped_charms] == ['C1', 'C2', 'C0']
    assert g.dragging_charm_index == -1


def test_menu_saves_are_not_runs():
    assert is_run_save({'current_state': 'SplashState'}) is False
    assert is_run_save({'current_state': 'InitState'}) is False
    assert is_run_save({'current_state': 'GameOverState'}) is False
    assert is_run_save({'current_state': 'AchievementsState'}) is False
    assert is_run_save({'current_state': 'EndPromptState'}) is True
    assert is_run_save({'current_state': 'ShopState'}) is True
    assert is_run_save({'current_state': 'GameState'}) is True
    assert is_run_save({'current_state': 'BlindsState'}) is True
    assert is_run_save({'current_state': 'PauseMenuState', 'previous_state': 'GameState'}) is True
    assert is_run_save({'current_state': 'PauseMenuState', 'previous_state': 'SplashState'}) is False
    assert is_run_save({'current_state': 'PackSelectState'}) is True
    assert is_run_save({'current_state': 'DiceSelectState'}) is True
    assert is_run_save({'current_state': 'ConfirmSellState'}) is True
    assert is_run_save({'current_state': 'RuneSelectState'}) is True
    assert is_run_save({'current_state': 'D20RollState'}) is True
    assert is_run_save({'current_state': 'RuneUseState', 'previous_state': 'ShopState'}) is True
    assert is_run_save({'current_state': 'RuneUseState', 'previous_state': 'GameState'}) is True
    assert is_run_save(None) is False


def test_resolve_overlays_to_parent():
    assert resolve_run_state('PackSelectState') == 'ShopState'
    assert resolve_run_state('DiceSelectState') == 'ShopState'
    assert resolve_run_state('ConfirmSellState') == 'ShopState'
    assert resolve_run_state('D20RollState') == 'BlindsState'
    assert resolve_run_state('RuneUseState', 'GameState') == 'GameState'
    assert resolve_run_state('RuneUseState', 'ShopState') == 'ShopState'
    assert resolve_run_state('PauseMenuState', 'ShopState') == 'ShopState'
    assert resolve_run_state('EndPromptState') == 'EndPromptState'
    assert resolve_run_state('GameOverState') is None


def test_skip_autosave_covers_menus():
    for name in ('SplashState', 'PromptState', 'AchievementsState',
                 'GameOverState', 'InitState'):
        assert name in _SKIP_AUTOSAVE
    for name in ('ShopState', 'GameState', 'BlindsState', 'PauseMenuState', 'EndPromptState',
                 'D20RollState'):
        assert name in _RUN_AUTOSAVE
    assert 'InitState' not in _RUN_AUTOSAVE
    assert 'GameOverState' not in _RUN_AUTOSAVE
    assert 'EndPromptState' not in _SKIP_AUTOSAVE


def _fake_game(state_cls):
    g = SimpleNamespace()
    g.state_machine = SimpleNamespace(current_state=state_cls())
    g.previous_state = None
    g.d20_boon = None
    return g


def test_exit_from_splash_does_not_clobber_run():
    import json
    import tempfile
    class SplashState:
        pass
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    try:
        with open(path, 'w') as f:
            json.dump({'current_state': 'ShopState', 'coins': 42, 'shop_charms': [{'name': 'Basic Charm'}]}, f)
        savegame._SAVE_PATH_OVERRIDE = path
        save_on_exit(_fake_game(SplashState))
        with open(path) as f:
            data = json.load(f)
        assert data['current_state'] == 'ShopState'
        assert data['coins'] == 42
    finally:
        savegame._SAVE_PATH_OVERRIDE = None
        try:
            os.remove(path)
        except OSError:
            pass


def test_exit_from_shop_writes_run_save():
    import json
    import tempfile
    class ShopState:
        pass
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    try:
        savegame._SAVE_PATH_OVERRIDE = path
        g = _fake_game(ShopState)
        g.shop_charms = [{'name': 'Basic Charm', 'cost': 2}]
        g.coins = 17
        assert save_on_exit(g) is True
        with open(path) as f:
            data = json.load(f)
        assert data['current_state'] == 'ShopState'
        assert data['resume_state'] == 'ShopState'
        assert data['coins'] == 17
        assert data['shop_charms'][0]['name'] == 'Basic Charm'
        assert is_run_save(data) is True
    finally:
        savegame._SAVE_PATH_OVERRIDE = None
        try:
            os.remove(path)
        except OSError:
            pass


def test_exit_from_pack_select_is_a_run():
    import json
    import tempfile
    class PackSelectState:
        pass
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    try:
        savegame._SAVE_PATH_OVERRIDE = path
        g = _fake_game(PackSelectState)
        g.shop_charms = [{'name': 'Sly Charm'}]
        assert save_on_exit(g) is True
        with open(path) as f:
            data = json.load(f)
        assert data['current_state'] == 'PackSelectState'
        assert data['resume_state'] == 'ShopState'
        assert is_run_save(data) is True
    finally:
        savegame._SAVE_PATH_OVERRIDE = None
        try:
            os.remove(path)
        except OSError:
            pass


def test_exit_from_d20_saves_locked_overlay():
    """Window-X after the d20 lands must keep the overlay so Load cannot dump to blinds."""
    import json
    import tempfile
    class D20RollState:
        def __init__(self):
            self.phase = 'done'
            self.selected_fusion = 'Red'
            self.roll_result = 3
            self.blind_type = 'Small'
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    try:
        savegame._SAVE_PATH_OVERRIDE = path
        g = _fake_game(D20RollState)
        g.coins = 11
        g._d20_pre_intensify = {'active': False, 'pending_coins': 20}
        assert save_on_exit(g) is True
        with open(path) as f:
            data = json.load(f)
        assert data['current_state'] == 'D20RollState'
        assert data['resume_state'] == 'BlindsState'
        assert data['d20_roll_phase'] == 'done'
        assert data['d20_selected_fusion'] == 'Red'
        assert data['d20_roll_result'] == 3
        assert data['d20_blind_type'] == 'Small'
        assert data['d20_pre_intensify']['pending_coins'] == 20
        assert is_run_save(data) is True
    finally:
        savegame._SAVE_PATH_OVERRIDE = None
        try:
            os.remove(path)
        except OSError:
            pass


def _buy_game(n_equipped=0, max_c=5, coins=40, stock=None):
    g = SimpleNamespace()
    g.equipped_charms = [{'name': f'E{i}', 'type': 'basic', 'cost': 2} for i in range(n_equipped)]
    g.max_charms = max_c
    g.coins = coins
    g.shop_charms = stock or [
        {'name': 'Basic Charm', 'type': 'mult', 'cost': 3},
        {'name': 'Sly Charm', 'type': 'mult', 'cost': 4},
        {'name': 'Wily Charm', 'type': 'mult', 'cost': 5},
    ]
    g.disabled_charms = []
    g.current_boss_effect = None
    g.hands_left = 4
    g.temp_message = None
    g.temp_message_start = 0
    g._skip_ach_persist = True
    g.progress = ach.default_progress()
    return g


def test_buy_sixth_slot_with_black_pouch():
    g = _buy_game(n_equipped=5, max_c=6, coins=40)
    assert try_buy_shop_charm(g, 0) == 'ok'
    assert len(g.equipped_charms) == 6
    assert g.shop_charms[0]['name'] == 'Sly Charm'
    assert g.coins == 37


def test_buy_full_slots_puts_charm_back():
    g = _buy_game(n_equipped=6, max_c=6, coins=40)
    assert try_buy_shop_charm(g, 0) == 'full'
    assert len(g.equipped_charms) == 6
    assert g.shop_charms[0]['name'] == 'Basic Charm'
    assert 'slots' in g.temp_message.lower()


def test_buy_stale_index_does_not_crash():
    g = _buy_game(n_equipped=0, max_c=6)
    assert try_buy_shop_charm(g, 3) is None
    assert try_buy_shop_charm(g, -1) is None
    assert len(g.shop_charms) == 3
    try_buy_shop_charm(g, 2)
    assert try_buy_shop_charm(g, 2) is None  # same-frame double click on last tile


def test_buy_broke_puts_charm_back():
    g = _buy_game(n_equipped=0, max_c=6, coins=0)
    assert try_buy_shop_charm(g, 0) == 'broke'
    assert g.shop_charms[0]['name'] == 'Basic Charm'
    assert g.equipped_charms == []


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


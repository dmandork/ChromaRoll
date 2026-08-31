# savegame.py
import json
import os
import sys
import copy
import data  # For restoring pouch by name
import constants
from states.splash import SplashState
from states.prompt import PromptState
from states.init import InitState
from states.shop import ShopState
from states.game import GameState
from states.blinds import BlindsState
from states.game_over import GameOverState
from states.pause import PauseMenuState
from states.end_prompt import EndPromptState

# Tests may point this at a temp file. Production uses the game folder, not cwd.
_SAVE_PATH_OVERRIDE = None

STATE_MAP = {
    'SplashState': SplashState,
    'PromptState': PromptState,
    'InitState': InitState,
    'ShopState': ShopState,
    'GameState': GameState,
    'BlindsState': BlindsState,
    'GameOverState': GameOverState,
    'PauseMenuState': PauseMenuState,
    'EndPromptState': EndPromptState,
}

MENU_STATES = {
    'SplashState', 'PromptState', 'AchievementsState',
    'GameOverState', 'InitState', None,
}

# Screens that are a run but cannot be constructed as Class(game) on Load.
# Resume at the nearest stable parent; the rest of the run data still loads.
OVERLAY_PARENT = {
    'PackSelectState': 'ShopState',
    'DiceSelectState': 'ShopState',
    'RuneSelectState': 'ShopState',
    'ConfirmSellState': 'ShopState',
    'DebugMenuState': 'ShopState',
    'DebugCharmState': 'ShopState',
    'DebugPrismState': 'ShopState',
    'DebugRuneSelectState': 'ShopState',
    'DebugDiceSelectForRune': 'ShopState',
    'D20RollState': 'BlindsState',
    'RuneUseState': None,  # previous_state (shop or play)
}


def save_file_path():
    if _SAVE_PATH_OVERRIDE:
        return _SAVE_PATH_OVERRIDE
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'save.json')


def _copy(val, fallback=None):
    try:
        return copy.deepcopy(val)
    except Exception:
        return fallback if fallback is not None else val


def _list(val):
    try:
        return list(val)
    except Exception:
        return []


def _state_names(game):
    sm = getattr(game, 'state_machine', None)
    cur = None
    if sm is not None and getattr(sm, 'current_state', None) is not None:
        cur = type(sm.current_state).__name__
    prev = getattr(game, 'previous_state', None)
    if prev is not None and not isinstance(prev, str):
        prev = type(prev).__name__
    return cur, prev


def resolve_run_state(current_state, previous_state=None):
    """Map any screen to a STATE_MAP run screen, or None if this is not a run."""
    st = current_state
    prev = previous_state
    if st == 'PauseMenuState':
        st = prev
    if st in OVERLAY_PARENT:
        parent = OVERLAY_PARENT[st]
        st = prev if parent is None else parent
        if st == 'PauseMenuState':
            st = prev
    if st in MENU_STATES or not st:
        return None
    if st in STATE_MAP:
        return st
    if prev in STATE_MAP and prev not in MENU_STATES:
        return prev
    return None


def is_run_save(save_data):
    if not save_data:
        return False
    explicit = save_data.get('resume_state')
    if explicit in STATE_MAP and explicit not in MENU_STATES:
        return True
    return resolve_run_state(
        save_data.get('current_state'),
        save_data.get('previous_state'),
    ) is not None


def save_game(game):
    """Saves the game state to JSON. Never raises — a failed save must not crash quit."""
    path = save_file_path()
    print("Saving to:", os.path.abspath(path))
    current_state_name, previous_state_name = _state_names(game)
    resume_state = resolve_run_state(current_state_name, previous_state_name)
    pouch = getattr(game, 'current_pouch', None)
    pouch_name = pouch.get('name') if isinstance(pouch, dict) else None
    d20 = getattr(game, 'd20_boon', None)
    try:
        d20_data = d20.to_dict() if d20 is not None and hasattr(d20, 'to_dict') else {}
    except Exception:
        d20_data = {}

    def g(name, default=None):
        return getattr(game, name, default)

    save_data = {
        'turn_initialized': g('turn_initialized', False),
        'version': 1,
        'coins': g('coins', 0),
        'extra_coins': g('extra_coins', 0),
        'bag': _copy(g('bag', []), []),
        'full_bag': _copy(g('full_bag', []), []),
        'equipped_charms': _copy(g('equipped_charms', []), []),
        'disabled_charms': _list(g('disabled_charms', [])),
        'current_stake': g('current_stake', 1),
        'current_blind': g('current_blind', 'Small'),
        'round_score': g('round_score', 0),
        'pouch_type': pouch_name,
        'green_pouch_active': g('green_pouch_active', False),
        'ghost_pouch_active': g('ghost_pouch_active', False),
        'plasma_pouch_active': g('plasma_pouch_active', False),
        'pouch_blind_mult': g('pouch_blind_mult', 1.0),
        'hands_left': g('hands_left', constants.MAX_HANDS),
        'rerolls_left': g('rerolls_left', constants.MAX_REROLLS),
        'discards_left': g('discards_left', constants.MAX_DISCARDS),
        'discard_used_this_round': g('discard_used_this_round', False),
        'hand': _copy(g('hand', []), []),
        'rolls': _copy(g('rolls', []), []),
        'held': _list(g('held', [])),
        'discard_selected': _list(g('discard_selected', [])),
        'is_discard_phase': g('is_discard_phase', False),
        'has_rolled': g('has_rolled', False),
        'broken_dice': _list(g('broken_dice', [])),
        'break_effect_start': g('break_effect_start', 0),
        'temp_message': g('temp_message', None),
        'temp_message_start': g('temp_message_start', 0),
        'upcoming_boss_effect': _copy(g('upcoming_boss_effect', None)),
        'current_boss_effect': _copy(g('current_boss_effect', None)),
        'boss_rainbow_color': g('boss_rainbow_color', None),
        'boss_shuffled_faces': _copy(g('boss_shuffled_faces', {}), {}),
        'boss_reroll_count': g('boss_reroll_count', 0),
        'shop_charms': _copy(g('shop_charms', []), []),
        'available_packs': _list(g('available_packs', [])),
        'shop_reroll_cost': g('shop_reroll_cost', 5),
        'current_state': current_state_name,
        'previous_state': previous_state_name,
        'resume_state': resume_state,
        'mute': g('mute', False),
        'rune_tray': _copy(g('rune_tray', [None, None]), [None, None]),
        'confirmed_hands_this_round': g('confirmed_hands_this_round', 0),
        'hands_played_this_round': g('hands_played_this_round', 0),
        'score_mult': g('score_mult', 1.0),
        'dagger_mult': g('dagger_mult', 0.0),
        'pack_choices': _copy(g('pack_choices', []), []),
        'confirm_sell_index': g('confirm_sell_index', -1),
        'turn': g('turn', 0),
        'show_popup': g('show_popup', False),
        'popup_message': g('popup_message', "") or "",
        'effective_interest_max': g('effective_interest_max', constants.INTEREST_MAX),
        'tutorial_step': g('tutorial_step', 0),
        'tutorial_mode': g('tutorial_mode', False),
        'tutorial_completed': g('tutorial_completed', False),
        'unlocks': _copy(g('unlocks', {}), {}),
        'hand_multipliers': _copy(g('hand_multipliers', {}), {}),
        'has_advantage': g('has_advantage', False),
        'advantage_value': g('advantage_value', None),
        'held_advantage': g('held_advantage', False),
        'original_center_value': g('original_center_value', None),
        'used_fates_favor_this_blind': g('used_fates_favor_this_blind', False),
        'fates_advantage_index': g('fates_advantage_index', -1),
        'fates_advantage_value': g('fates_advantage_value', None),
        'held_fates_advantage': g('held_fates_advantage', False),
        'selecting_fates_die': g('selecting_fates_die', False),
        'used_rune_cast_this_shop': g('used_rune_cast_this_shop', False),
        'd20_boon': d20_data,
        'fused_color': g('fused_color', None),
        'has_free_prism_pack': g('has_free_prism_pack', False),
        'target_mult': g('target_mult', 1.0),
        'd20_advantage_index': g('d20_advantage_index', -1),
        'selecting_advantage_die': g('selecting_advantage_die', False),
        '_d20_prism_in_current_shop': g('_d20_prism_in_current_shop', False),
        'grimoire_rune': _copy(g('grimoire_rune', None)),
        'd20_roll_phase': None,
        'd20_selected_fusion': None,
        'd20_roll_result': None,
        'd20_blind_type': None,
        'd20_pre_intensify': _copy(g('_d20_pre_intensify', None)),
        'run_score': g('run_score', 0),
        'best_hand_score': g('best_hand_score', 0),
        'best_hand_type': g('best_hand_type', None),
        'hand_play_counts': _copy(g('hand_play_counts', {}), {}),
        'blind_log': _copy(g('blind_log', []), []),
        'run_started_at': g('run_started_at', None),
        'beaten_bosses': _list(g('beaten_bosses', [])),
    }
    # Prefer live D20 overlay fields so Window-X during the roll reconstructs this screen.
    cur_obj = None
    sm = getattr(game, 'state_machine', None)
    if sm is not None:
        cur_obj = getattr(sm, 'current_state', None)
    if cur_obj is not None and type(cur_obj).__name__ == 'D20RollState':
        save_data['d20_roll_phase'] = getattr(cur_obj, 'phase', None)
        save_data['d20_selected_fusion'] = getattr(cur_obj, 'selected_fusion', None)
        save_data['d20_roll_result'] = getattr(cur_obj, 'roll_result', None)
        save_data['d20_blind_type'] = getattr(cur_obj, 'blind_type', None)
    else:
        save_data['d20_roll_phase'] = g('d20_roll_phase', None)
        save_data['d20_selected_fusion'] = g('d20_selected_fusion', None)
        save_data['d20_roll_result'] = g('d20_roll_result', None)
        save_data['d20_blind_type'] = g('d20_blind_type', None)
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp = path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(save_data, f, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        try:
            if os.path.exists(path + '.tmp'):
                os.remove(path + '.tmp')
        except OSError:
            pass
        return False


def save_on_exit(game):
    """Window X / Quit. Writes a run save; never overwrites a run with a menu screen."""
    cur, prev = _state_names(game)
    if resolve_run_state(cur, prev) is None:
        print("Exit from menu — keeping existing run save")
        return False
    return save_game(game)


def load_game(game):
    """Loads the game state from JSON."""
    path = save_file_path()
    try:
        with open(path, 'r') as f:
            save_data = json.load(f)

        version = save_data.get('version', 0)
        if version > 1:
            print("Warning: Save from newer version—may not load fully.")
        elif version < 1:
            print("Old save detected—attempting load with defaults.")

        if not is_run_save(save_data):
            print("Save is a menu screen, not a run — ignoring")
            return None

        game.turn_initialized = save_data.get('turn_initialized', False)
        game.coins = save_data.get('coins', 0)
        game.extra_coins = save_data.get('extra_coins', 0)
        game.bag = copy.deepcopy(save_data.get('bag', []))
        game.full_bag = copy.deepcopy(save_data.get('full_bag', []))
        game.equipped_charms = copy.deepcopy(save_data.get('equipped_charms', []))
        game.disabled_charms = save_data.get('disabled_charms', [])
        game.current_stake = save_data.get('current_stake', 1)
        game.current_blind = save_data.get('current_blind', 'Small')
        game.round_score = save_data.get('round_score', 0)
        pouch_name = save_data.get('pouch_type')
        game.current_pouch = None
        game.ghost_pouch_active = False
        game.plasma_pouch_active = False
        game.pouch_blind_mult = 1.0
        if pouch_name:
            game.current_pouch = next((p for p in data.POUCHES if p['name'] == pouch_name), None)
            if game.current_pouch:
                bonus = game.current_pouch.get('bonus') or {}
                game.max_charms = 5 + bonus.get('charm_slots', 0)
                game.green_pouch_active = 'Green' in game.current_pouch['name']
                game.ghost_pouch_active = bool(bonus.get('shop_special_boost')) or 'Ghost' in game.current_pouch['name']
                game.plasma_pouch_active = bool(bonus.get('mix_bonus') or bonus.get('balance_score'))
                game.pouch_blind_mult = float(bonus.get('blind_mult') or 1.0)
            else:
                print(f"Warning: Pouch '{pouch_name}' not found in data.POUCHES—using defaults.")
        game.green_pouch_active = save_data.get('green_pouch_active', getattr(game, 'green_pouch_active', False))
        if 'ghost_pouch_active' in save_data:
            game.ghost_pouch_active = bool(save_data.get('ghost_pouch_active'))
        if 'plasma_pouch_active' in save_data:
            game.plasma_pouch_active = bool(save_data.get('plasma_pouch_active'))
        if 'pouch_blind_mult' in save_data:
            try:
                game.pouch_blind_mult = float(save_data.get('pouch_blind_mult') or 1.0)
            except (TypeError, ValueError):
                game.pouch_blind_mult = 1.0
        game.hands_left = save_data.get('hands_left', constants.MAX_HANDS)
        game.rerolls_left = save_data.get('rerolls_left', constants.MAX_REROLLS)
        game.discards_left = save_data.get('discards_left', constants.MAX_DISCARDS)
        game.discard_used_this_round = save_data.get('discard_used_this_round', False)
        game.hand = copy.deepcopy(save_data.get('hand', []))
        game.rolls = copy.deepcopy(save_data.get('rolls', []))
        game.held = save_data.get('held', [False] * constants.NUM_DICE_IN_HAND)
        game.discard_selected = save_data.get('discard_selected', [False] * constants.NUM_DICE_IN_HAND)
        game.is_discard_phase = save_data.get('is_discard_phase', False)
        game.has_rolled = save_data.get('has_rolled', False)
        game.broken_dice = save_data.get('broken_dice', [])
        game.break_effect_start = save_data.get('break_effect_start', 0)
        game.temp_message = save_data.get('temp_message', None)
        game.temp_message_start = save_data.get('temp_message_start', 0)
        game.upcoming_boss_effect = copy.deepcopy(save_data.get('upcoming_boss_effect', None))
        game.current_boss_effect = copy.deepcopy(save_data.get('current_boss_effect', None))
        game.boss_rainbow_color = save_data.get('boss_rainbow_color', None)
        game.boss_shuffled_faces = copy.deepcopy(save_data.get('boss_shuffled_faces', {}))
        game.boss_reroll_count = save_data.get('boss_reroll_count', 0)
        game.shop_charms = copy.deepcopy(save_data.get('shop_charms', []))
        game.available_packs = save_data.get('available_packs', [])
        game.shop_reroll_cost = save_data.get('shop_reroll_cost', 5)
        game.mute = save_data.get('mute', False)
        if hasattr(game, 'apply_mute'):
            game.apply_mute()
        game.hand_multipliers = copy.deepcopy(save_data.get('hand_multipliers', {}))
        game.confirmed_hands_this_round = save_data.get('confirmed_hands_this_round', 0)
        game.hands_played_this_round = save_data.get('hands_played_this_round', 0)
        game.rune_tray = copy.deepcopy(save_data.get('rune_tray', [None, None]))
        for ht in data.HAND_TYPES:
            if ht not in game.hand_multipliers:
                game.hand_multipliers[ht] = 1.0
        game.score_mult = save_data.get('score_mult', 1.0)
        game.dagger_mult = save_data.get('dagger_mult', 0.0)

        game.pack_choices = copy.deepcopy(save_data.get('pack_choices', []))
        game.confirm_sell_index = save_data.get('confirm_sell_index', -1)

        game.turn = save_data.get('turn', 0)
        game.show_popup = save_data.get('show_popup', False)
        game.popup_message = save_data.get('popup_message', "")

        game.effective_interest_max = save_data.get('effective_interest_max', constants.INTEREST_MAX)

        game.tutorial_step = save_data.get('tutorial_step', 0)
        game.tutorial_mode = save_data.get('tutorial_mode', False)
        game.tutorial_completed = save_data.get('tutorial_completed', False)

        import achievements as ach
        ach.attach_progress(game)
        game.unlocks = game.progress

        game.has_advantage = save_data.get('has_advantage', False)
        game.advantage_value = save_data.get('advantage_value', None)
        game.held_advantage = save_data.get('held_advantage', False)
        game.original_center_value = save_data.get('original_center_value', None)

        game.used_fates_favor_this_blind = save_data.get('used_fates_favor_this_blind', False)
        game.fates_advantage_index = save_data.get('fates_advantage_index', -1)
        game.fates_advantage_value = save_data.get('fates_advantage_value', None)
        game.held_fates_advantage = save_data.get('held_fates_advantage', False)
        game.selecting_fates_die = save_data.get('selecting_fates_die', False)

        game.equipped_charms = copy.deepcopy(save_data.get('equipped_charms', []))
        game.disabled_charms = save_data.get('disabled_charms', [])
        print(f"Debug: Loaded equipped_charms = {[c.get('name') for c in game.equipped_charms]}, disabled = {game.disabled_charms}")

        from d20_boon import D20BoonSystem
        if not hasattr(game, 'd20_boon') or game.d20_boon is None:
            game.d20_boon = D20BoonSystem()
        game.d20_boon.from_dict(save_data.get('d20_boon', {}))
        game.fused_color = save_data.get('fused_color', None)
        game.has_free_prism_pack = save_data.get('has_free_prism_pack', False)
        game.target_mult = save_data.get('target_mult', 1.0)
        game.d20_advantage_index = save_data.get('d20_advantage_index', -1)
        game.selecting_advantage_die = save_data.get('selecting_advantage_die', False)
        game._d20_prism_in_current_shop = save_data.get('_d20_prism_in_current_shop', False)
        game.grimoire_rune = copy.deepcopy(save_data.get('grimoire_rune', None))
        game.used_rune_cast_this_shop = save_data.get('used_rune_cast_this_shop', False)
        game.d20_roll_phase = save_data.get('d20_roll_phase')
        game.d20_selected_fusion = save_data.get('d20_selected_fusion')
        game.d20_roll_result = save_data.get('d20_roll_result')
        game.d20_blind_type = save_data.get('d20_blind_type')
        game._d20_pre_intensify = copy.deepcopy(save_data.get('d20_pre_intensify'))
        game.d20_boon.sync_legacy_flags(game)

        game.run_score = save_data.get('run_score', getattr(game, 'run_score', 0) or 0)
        game.best_hand_score = save_data.get('best_hand_score', getattr(game, 'best_hand_score', 0) or 0)
        game.best_hand_type = save_data.get('best_hand_type', getattr(game, 'best_hand_type', None))
        game.hand_play_counts = copy.deepcopy(save_data.get('hand_play_counts') or getattr(game, 'hand_play_counts', {}) or {})
        game.blind_log = copy.deepcopy(save_data.get('blind_log') or [])
        game.run_started_at = save_data.get('run_started_at') or getattr(game, 'run_started_at', None)
        game.beaten_bosses = list(save_data.get('beaten_bosses') or [])
        game._runlog_written = False

        if hasattr(game, 'apply_boss_face_shuffle'):
            game.apply_boss_face_shuffle()

        if hasattr(game, 'update_hand_text'):
            try:
                game.update_hand_text()
            except Exception as e:
                print(f"update_hand_text on load skipped: {e}")

        saved_state = save_data.get('current_state')
        saved_previous = save_data.get('previous_state')
        resume_state = save_data.get('resume_state') or resolve_run_state(saved_state, saved_previous)
        if resume_state not in STATE_MAP or resume_state in MENU_STATES:
            resume_state = 'BlindsState'
        state_class = STATE_MAP[resume_state]

        # Prefer restoring the exact overlay when it only needs Class(game).
        overlay_class = None
        overlay_state = None
        try:
            if saved_state == 'PackSelectState':
                from states.pack_select import PackSelectState
                overlay_class = PackSelectState
            elif saved_state == 'DiceSelectState':
                from states.dice_select import DiceSelectState
                overlay_class = DiceSelectState
            elif saved_state == 'ConfirmSellState':
                from states.confirm_sell import ConfirmSellState
                overlay_class = ConfirmSellState
            elif saved_state == 'RuneSelectState':
                from states.rune import RuneSelectState
                overlay_class = RuneSelectState
            elif saved_state == 'D20RollState':
                from states.d20_roll import D20RollState
                blind = save_data.get('d20_blind_type') or getattr(game, 'current_blind', 'Small')
                st = D20RollState(game, blind)
                st.restore_progress(save_data)
                overlay_state = st
        except Exception as e:
            print(f"Overlay restore skipped: {e}")
            overlay_class = None
            overlay_state = None

        game.is_resuming = True
        if overlay_state is not None:
            game.state_machine.change_state(overlay_state)
        elif overlay_class is not None:
            game.state_machine.change_state(overlay_class(game))
        else:
            game.state_machine.change_state(state_class(game))
        return save_data
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Corrupt save file (kept on disk): {e}")
        return None
    except Exception as e:
        print(f"Unexpected load error: {e}")
        return None


def delete_save():
    """Deletes the save file."""
    path = save_file_path()
    if os.path.exists(path):
        os.remove(path)

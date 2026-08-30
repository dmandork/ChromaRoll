# achievements.py
# Collection + shop appearance. No pygame. Safe to unit-test.
#
# Two gates
#   1. Collection: charm is in progress['unlocked_charms'] (or not in LOCKED).
#   2. Appearance: Rare from Stake 2, Legendary from Stake 4.
#
# Account progress lives in progress.json (survives New Game). save.json may
# copy it but never wipes it.

import json
import os
from collections import defaultdict

PROGRESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'progress.json')

# Uncommons that start locked (build-defining). All Rares + Legendaries are locked too.
LOCKED_UNCOMMONS = (
    'Castle Cube',
    'Space Sphere',
    'Monopoly Mortgage',
    'Steel Seal',
    'Hiker Hex',
    'Lucky Labyrinth',
    'Rune Recycler',
)

STARTER_POUCHES = (
    'Red Pouch', 'Blue Pouch', 'Yellow Pouch', 'Green Pouch',
)
LOCKED_POUCHES = (
    'Black Pouch', 'Ghost Pouch', 'Erratic Pouch', 'Plasma Pouch',
)

ACHIEVEMENTS = [
    # --- custom (play moments) ---
    {'id': 'boxcars', 'name': 'Boxcars', 'desc': 'Score five 6s in one hand.',
     'cond': 'custom', 'key': 'all_sixes', 'unlocks': ['Critical Hit']},
    {'id': 'so_close', 'name': 'So Close', 'desc': 'Lose a blind at 80% or more of the target.',
     'cond': 'custom', 'key': 'close_loss', 'unlocks': ['Cloak of Cunning']},
    {'id': 'one_hue', 'name': 'One Hue', 'desc': 'Score a 5 of a Kind that is also monochrome.',
     'cond': 'custom', 'key': 'fiveoak_mono', 'unlocks': ['Flower Pot Prism']},
    {'id': 'greenhouse', 'name': 'Greenhouse', 'desc': 'Score two or more Glass dice in one hand.',
     'cond': 'custom', 'key': 'glass_pair', 'unlocks': ['Glass Globe']},
    {'id': 'empty_felt', 'name': 'Empty Felt', 'desc': 'Empty the bag during a blind.',
     'cond': 'custom', 'key': 'bag_empty', 'unlocks': ["Familiar's Foresight"]},
    {'id': 'full_rack', 'name': 'Full Rack', 'desc': 'Hold 5 charms at once.',
     'cond': 'custom', 'key': 'five_charms', 'unlocks': ['Wee Widget']},
    {'id': 'travel_light', 'name': 'Travel Light', 'desc': 'Win a blind with 2 or fewer charms equipped.',
     'cond': 'custom', 'key': 'few_charms_win', 'unlocks': ['Stencil Charm']},
    {'id': 'draw_four', 'name': 'Draw Four', 'desc': 'Beat a Hold Ban or Charm Eclipse boss.',
     'cond': 'custom', 'key': 'hard_boss', 'unlocks': ['UNO Skip']},
    {'id': 'last_call', 'name': 'Last Call', 'desc': 'Win a blind on your last hand.',
     'cond': 'custom', 'key': 'last_hand_win', 'unlocks': ['Final Flourish']},
    {'id': 'clean_roll', 'name': 'Clean Roll', 'desc': 'Win a blind without using a reroll.',
     'cond': 'custom', 'key': 'no_reroll_win', 'unlocks': ['UNO Draw 2']},
    {'id': 'dragon_hoard', 'name': 'Dragon Hoard', 'desc': 'Score a hand of only Red dice.',
     'cond': 'custom', 'key': 'all_red', 'unlocks': ["Dragon's Dice"]},
    {'id': 'high_court', 'name': 'High Court', 'desc': 'Score a hand that includes both a 5 and a 6.',
     'cond': 'custom', 'key': 'faces_5_and_6', 'unlocks': ['Triboulet Token']},
    {'id': 'tempered', 'name': 'Tempered', 'desc': 'Have a Steel-enhanced die in your bag.',
     'cond': 'custom', 'key': 'steel_in_bag', 'unlocks': ['Steel Seal']},
    {'id': 'liquidation', 'name': 'Liquidation', 'desc': 'Sell 2 charms in a single shop.',
     'cond': 'custom', 'key': 'sell_two_shop', 'unlocks': ['Monopoly Mortgage']},
    {'id': 'moat', 'name': 'Moat', 'desc': 'Discard 15 dice of one color (lifetime).',
     'cond': 'custom', 'key': 'discard_color_15', 'unlocks': ['Castle Cube']},
    {'id': 'packed', 'name': 'Packed', 'desc': 'Raise any hand type to 2.5x from Prism packs.',
     'cond': 'custom', 'key': 'packed_prism', 'unlocks': ['Space Sphere']},
    {'id': 'gold_loop', 'name': 'Gold Loop', 'desc': 'Score a held Gold or Glass die.',
     'cond': 'custom', 'key': 'held_gold_or_glass', 'unlocks': ['Mime Charm']},
    # --- generic ---
    {'id': 'beat_s1', 'name': 'First Boss', 'desc': 'Beat the Stake 1 boss.',
     'cond': 'beat_stake', 'n': 1, 'unlocks': ['Luchador Lens']},
    {'id': 'beat_s2', 'name': 'Warming Up', 'desc': 'Beat the Stake 2 boss.',
     'cond': 'beat_stake', 'n': 2, 'unlocks': ['Sloth Sigil', 'Reroll Recycler Charm', 'Acrobat Amulet']},
    {'id': 'beat_s3', 'name': 'Ante Climber', 'desc': 'Beat the Stake 3 boss.',
     'cond': 'beat_stake', 'n': 3, 'unlocks': ['Full House Party Charm', 'Turtle Token', 'Discard Drake']},
    {'id': 'beat_s4', 'name': 'Halfway House', 'desc': 'Beat the Stake 4 boss.',
     'cond': 'beat_stake', 'n': 4, 'unlocks': ['Obelisk Orb', "Queen's Quill", 'Burglar Bag']},
    {'id': 'beat_s5', 'name': 'Deep Stakes', 'desc': 'Beat the Stake 5 boss.',
     'cond': 'beat_stake', 'n': 5, 'unlocks': ['Homebrew Hazard', 'Break Buffer', 'Kind Keeper']},
    {'id': 'beat_s6', 'name': 'High Roller', 'desc': 'Beat the Stake 6 boss.',
     'cond': 'beat_stake', 'n': 6, 'unlocks': ['Final Forge', 'Dagger Charm', "Ace's Aura"]},
    {'id': 'win_run', 'name': 'Chroma Champion', 'desc': 'Beat the Stake 8 boss and win a run.',
     'cond': 'win_run', 'unlocks': ['Life Milestone']},
    {'id': 'quads', 'name': 'Quad Squad', 'desc': 'Score 4 of a Kind 3 times.',
     'cond': 'play_hand', 'hand': '4 of a Kind', 'n': 3, 'unlocks': ['Quadruple Threat Charm']},
    {'id': 'shattered', 'name': 'Shattered', 'desc': 'Have Glass dice break 3 times.',
     'cond': 'stat', 'stat': 'glass_breaks', 'n': 3, 'unlocks': ['Fragile Fortune Charm']},
    {'id': 'lucky_streak', 'name': 'Lucky Streak', 'desc': 'Trigger Lucky 6 times.',
     'cond': 'stat', 'stat': 'lucky_triggers', 'n': 6, 'unlocks': ['Lucky Labyrinth']},
    {'id': 'scribe', 'name': 'Scribe', 'desc': 'Use 3 mystic runes.',
     'cond': 'stat', 'stat': 'runes_used', 'n': 3, 'unlocks': ['Rune Recycler']},
    {'id': 'grimoire', 'name': 'Librarian', 'desc': 'Use 8 mystic runes.',
     'cond': 'stat', 'stat': 'runes_used', 'n': 8, 'unlocks': ["Gambler's Grimoire"]},
    {'id': 'intensify_2', 'name': 'Double Down', 'desc': 'Win 2 Intensified blinds.',
     'cond': 'stat', 'stat': 'intensify_wins', 'n': 2, 'unlocks': ["Fate's Favor"]},
    {'id': 'intensify_4', 'name': 'Heat Seeker', 'desc': 'Win 4 Intensified blinds.',
     'cond': 'stat', 'stat': 'intensify_wins', 'n': 4, 'unlocks': ["Sorcerer's Surge"]},
    {'id': 'bankroll', 'name': 'Bankroll', 'desc': 'End a blind holding 40 or more coins.',
     'cond': 'stat', 'stat': 'max_coins_at_blind_end', 'n': 40, 'unlocks': ['Bull Bead']},
    {'id': 'road_work', 'name': 'Road Work', 'desc': 'Score 15 hands (lifetime).',
     'cond': 'stat', 'stat': 'hands_scored', 'n': 15, 'unlocks': ['Hiker Hex']},
    {'id': 'specialist', 'name': 'Specialist', 'desc': 'Score 8 special-color dice (Gold, Silver, Glass, or Rainbow).',
     'cond': 'stat', 'stat': 'special_scored', 'n': 8, 'unlocks': ['Synergy Scroll']},
    {'id': 'kindred', 'name': 'Kindred', 'desc': 'Score 10 hands that are 3, 4, or 5 of a Kind.',
     'cond': 'stat', 'stat': 'kind_hands', 'n': 10, 'unlocks': ['Retrigger Rune']},
    # --- pouches (gated starting bags) ---
    {'id': 'pouch_ghost', 'name': 'Haunting', 'desc': 'Add 10 dice to your bag from shop packs.',
     'cond': 'stat', 'stat': 'dice_added', 'n': 10, 'unlocks': ['Ghost Pouch']},
    {'id': 'pouch_black', 'name': 'Shadow Slot', 'desc': 'Beat the Stake 2 boss.',
     'cond': 'beat_stake', 'n': 2, 'unlocks': ['Black Pouch']},
    {'id': 'pouch_plasma', 'name': 'Equilibrium', 'desc': 'Beat the Stake 4 boss.',
     'cond': 'beat_stake', 'n': 4, 'unlocks': ['Plasma Pouch']},
    {'id': 'pouch_erratic', 'name': 'Chaos Theory', 'desc': 'Beat the Stake 8 boss and win a run.',
     'cond': 'win_run', 'unlocks': ['Erratic Pouch']},
]


def locked_charm_names():
    names = []
    seen = set()
    pouch = set(LOCKED_POUCHES)
    for ach in ACHIEVEMENTS:
        for n in ach.get('unlocks') or []:
            if n in pouch or n in seen:
                continue
            seen.add(n)
            names.append(n)
    return names


def achievement_for_charm(charm_name):
    for ach in ACHIEVEMENTS:
        if charm_name in (ach.get('unlocks') or []):
            return ach
    return None


def default_run():
    return {
        'discards_by_color': {},
        'shop_sells': 0,
        'rerolls_this_blind': 0,
        'charms_at_blind_start': 0,
    }


def default_stats():
    return {
        'max_stake_beaten': 0,
        'runs_won': 0,
        'hands': {},
        'hands_scored': 0,
        'kind_hands': 0,
        'glass_breaks': 0,
        'lucky_triggers': 0,
        'runes_used': 0,
        'intensify_wins': 0,
        'bosses_beaten': 0,
        'max_coins_at_blind_end': 0,
        'special_scored': 0,
        'discards_by_color': {},
        'close_losses': 0,
        'bag_emptied': 0,
        'five_sixes': 0,
        'all_red_hands': 0,
        'max_charms_held': 0,
        'steel_seen': 0,
        'max_prism': 1.0,
        'sells_one_shop_max': 0,
        'dice_added': 0,
    }


def default_progress():
    return {
        'unlocked_achievements': [],
        'unlocked_charms': [],
        'unlocked_pouches': [],
        'stats': default_stats(),
        'run': default_run(),
        'new_this_run': [],
        'unlock_all': False,
    }


def load_progress(path=None):
    path = path or PROGRESS_PATH
    data = default_progress()
    try:
        with open(path, 'r') as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            data.update({k: raw[k] for k in data if k in raw})
            stats = default_stats()
            stats.update(raw.get('stats') or {})
            data['stats'] = stats
            run = default_run()
            run.update(raw.get('run') or {})
            data['run'] = run
            data['unlocked_achievements'] = list(raw.get('unlocked_achievements') or [])
            data['unlocked_charms'] = list(raw.get('unlocked_charms') or [])
            data['unlocked_pouches'] = list(raw.get('unlocked_pouches') or [])
            data['new_this_run'] = list(raw.get('new_this_run') or [])
            data['unlock_all'] = bool(raw.get('unlock_all', False))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return data


def save_progress(progress, path=None):
    path = path or PROGRESS_PATH
    try:
        with open(path, 'w') as f:
            json.dump(progress, f, indent=2)
    except OSError as e:
        print(f"Error saving progress: {e}")


def attach_progress(game, path=None):
    """Load account progress onto the game. Does not wipe on New Game."""
    existing = getattr(game, 'progress', None)
    if isinstance(existing, dict) and 'unlocked_achievements' in existing:
        game.unlocks = existing
        return existing
    progress = load_progress(path)
    game.progress = progress
    game.unlocks = progress
    return progress


def reset_run_stats(game):
    if not getattr(game, 'progress', None):
        attach_progress(game)
    game.progress['run'] = default_run()
    game.progress['new_this_run'] = []


def unlock_all(game, persist=True):
    attach_progress(game)
    game.progress['unlock_all'] = True
    for name in locked_charm_names():
        if name not in game.progress['unlocked_charms']:
            game.progress['unlocked_charms'].append(name)
    for name in LOCKED_POUCHES:
        if name not in game.progress.setdefault('unlocked_pouches', []):
            game.progress['unlocked_pouches'].append(name)
    for ach in ACHIEVEMENTS:
        if ach['id'] not in game.progress['unlocked_achievements']:
            game.progress['unlocked_achievements'].append(ach['id'])
    if persist and not getattr(game, '_skip_ach_persist', False):
        save_progress(game.progress)


def reset_progress(game, persist=True, path=None):
    game.progress = default_progress()
    game.unlocks = game.progress
    if persist and not getattr(game, '_skip_ach_persist', False):
        save_progress(game.progress, path)


def is_charm_unlocked(game, name):
    if name not in set(locked_charm_names()):
        return True
    progress = getattr(game, 'progress', None) or {}
    if progress.get('unlock_all'):
        return True
    return name in (progress.get('unlocked_charms') or [])


def is_pouch_unlocked(game, pouch):
    name = pouch if isinstance(pouch, str) else (pouch or {}).get('name')
    if not name or name in STARTER_POUCHES:
        return True
    if name not in LOCKED_POUCHES:
        return True
    progress = getattr(game, 'progress', None) or {}
    if progress.get('unlock_all'):
        return True
    return name in (progress.get('unlocked_pouches') or [])


def pouch_unlock_hint(game, pouch):
    """Quest text (plus progress for stat pouches) shown on locked carousel tiles."""
    name = pouch if isinstance(pouch, str) else (pouch or {}).get('name')
    a = achievement_for_charm(name) if name else None
    if not a:
        return "Complete a quest to unlock this pouch."
    hint = a.get('desc') or a.get('name') or "Locked"
    if a.get('cond') == 'stat':
        stats = (getattr(game, 'progress', None) or {}).get('stats') or {}
        need = int(a.get('n') or 1)
        have = int(stats.get(a.get('stat'), 0) or 0)
        hint = f"{hint} ({min(have, need)}/{need})"
    return hint


def shop_allows_rarity(rarity, stake):
    if rarity == 'Rare' and stake < 2:
        return False
    if rarity == 'Legendary' and stake < 4:
        return False
    return True


def filter_shop_pool(game, pool):
    """Collection + appearance gates. Empty result is possible; caller should fallback."""
    stake = getattr(game, 'current_stake', 1) or 1
    out = []
    for charm in pool:
        name = charm.get('name')
        if not name:
            continue
        if not is_charm_unlocked(game, name):
            continue
        if not shop_allows_rarity(charm.get('rarity', 'Common'), stake):
            continue
        out.append(charm)
    return out


def _inc(d, key, n=1):
    d[key] = d.get(key, 0) + n


def _update_stats(game, event, payload):
    stats = game.progress['stats']
    run = game.progress['run']
    if event == 'score':
        ht = payload.get('hand_type') or 'Nothing'
        if ht and ht != 'Nothing':
            _inc(stats['hands'], ht)
            stats['hands_scored'] = stats.get('hands_scored', 0) + 1
            if ht in ('3 of a Kind', '4 of a Kind', '5 of a Kind'):
                stats['kind_hands'] = stats.get('kind_hands', 0) + 1
        stats['lucky_triggers'] = stats.get('lucky_triggers', 0) + int(payload.get('lucky', 0) or 0)
        stats['special_scored'] = stats.get('special_scored', 0) + int(payload.get('special_n', 0) or 0)
        if payload.get('all_sixes'):
            stats['five_sixes'] = stats.get('five_sixes', 0) + 1
        if payload.get('all_red'):
            stats['all_red_hands'] = stats.get('all_red_hands', 0) + 1
        prism = float(payload.get('max_prism') or stats.get('max_prism') or 1.0)
        if prism > stats.get('max_prism', 1.0):
            stats['max_prism'] = prism
        if payload.get('steel'):
            stats['steel_seen'] = 1
        n_charms = int(payload.get('charm_count') or 0)
        if n_charms > stats.get('max_charms_held', 0):
            stats['max_charms_held'] = n_charms
    elif event == 'glass_break':
        stats['glass_breaks'] = stats.get('glass_breaks', 0) + 1
    elif event == 'discard':
        for color in payload.get('colors') or []:
            _inc(stats['discards_by_color'], color)
            _inc(run['discards_by_color'], color)
        if payload.get('bag_empty'):
            stats['bag_emptied'] = stats.get('bag_emptied', 0) + 1
    elif event == 'sell':
        run['shop_sells'] = run.get('shop_sells', 0) + 1
        if run['shop_sells'] > stats.get('sells_one_shop_max', 0):
            stats['sells_one_shop_max'] = run['shop_sells']
    elif event == 'shop_open':
        run['shop_sells'] = 0
    elif event == 'reroll':
        run['rerolls_this_blind'] = run.get('rerolls_this_blind', 0) + 1
    elif event == 'rune':
        stats['runes_used'] = stats.get('runes_used', 0) + 1
        if payload.get('steel'):
            stats['steel_seen'] = 1
    elif event == 'dice_added':
        stats['dice_added'] = stats.get('dice_added', 0) + int(payload.get('n') or 1)
    elif event == 'lose':
        score = float(payload.get('score') or 0)
        target = float(payload.get('target') or 0)
        if target > 0 and score >= 0.8 * target:
            stats['close_losses'] = stats.get('close_losses', 0) + 1
    elif event == 'blind_win':
        coins = int(payload.get('coins') or 0)
        if coins > stats.get('max_coins_at_blind_end', 0):
            stats['max_coins_at_blind_end'] = coins
        if payload.get('is_boss'):
            stake = int(payload.get('stake') or 0)
            if stake > stats.get('max_stake_beaten', 0):
                stats['max_stake_beaten'] = stake
            stats['bosses_beaten'] = stats.get('bosses_beaten', 0) + 1
        if payload.get('intensified'):
            stats['intensify_wins'] = stats.get('intensify_wins', 0) + 1
        n_charms = int(payload.get('charm_count') or 0)
        if n_charms > stats.get('max_charms_held', 0):
            stats['max_charms_held'] = n_charms
        prism = float(payload.get('max_prism') or 0)
        if prism > stats.get('max_prism', 1.0):
            stats['max_prism'] = prism
    elif event == 'run_win':
        stats['runs_won'] = stats.get('runs_won', 0) + 1
        stake = int(payload.get('stake') or 8)
        if stake > stats.get('max_stake_beaten', 0):
            stats['max_stake_beaten'] = stake
    elif event == 'equip' or event == 'check':
        n_charms = int(payload.get('charm_count') or 0)
        if n_charms > stats.get('max_charms_held', 0):
            stats['max_charms_held'] = n_charms
        if payload.get('steel'):
            stats['steel_seen'] = 1
        prism = float(payload.get('max_prism') or 0)
        if prism > stats.get('max_prism', 1.0):
            stats['max_prism'] = prism
    return stats, run


def _is_mono(colors):
    base = [c for c in colors if c and c != 'Rainbow']
    if not base:
        return True
    return len(set(base)) == 1


def _custom_met(key, game, event, payload, stats, run):
    if key == 'all_sixes':
        return event == 'score' and bool(payload.get('all_sixes'))
    if key == 'close_loss':
        return event == 'lose' and bool(payload.get('close'))
    if key == 'fiveoak_mono':
        return event == 'score' and payload.get('hand_type') == '5 of a Kind' and bool(payload.get('mono'))
    if key == 'glass_pair':
        return event == 'score' and int(payload.get('glass_n') or 0) >= 2
    if key == 'bag_empty':
        return stats.get('bag_emptied', 0) >= 1
    if key == 'five_charms':
        return stats.get('max_charms_held', 0) >= 5 or int(payload.get('charm_count') or 0) >= 5
    if key == 'few_charms_win':
        return event == 'blind_win' and int(payload.get('charm_count') or 99) <= 2
    if key == 'hard_boss':
        return event == 'blind_win' and bool(payload.get('hard_boss'))
    if key == 'last_hand_win':
        return event == 'blind_win' and bool(payload.get('last_hand'))
    if key == 'no_reroll_win':
        return event == 'blind_win' and bool(payload.get('no_reroll'))
    if key == 'all_red':
        return event == 'score' and bool(payload.get('all_red'))
    if key == 'faces_5_and_6':
        faces = payload.get('faces') or []
        return event == 'score' and (5 in faces) and (6 in faces)
    if key == 'steel_in_bag':
        return stats.get('steel_seen', 0) >= 1 or bool(payload.get('steel'))
    if key == 'sell_two_shop':
        return run.get('shop_sells', 0) >= 2
    if key == 'discard_color_15':
        return any(v >= 15 for v in (stats.get('discards_by_color') or {}).values())
    if key == 'packed_prism':
        return float(stats.get('max_prism') or 1.0) >= 2.5 or float(payload.get('max_prism') or 0) >= 2.5
    if key == 'held_gold_or_glass':
        return event == 'score' and bool(payload.get('held_gold_or_glass'))
    return False


def is_complete(ach, game, event, payload, stats, run):
    cond = ach.get('cond')
    if cond == 'beat_stake':
        return stats.get('max_stake_beaten', 0) >= int(ach.get('n') or 0)
    if cond == 'win_run':
        return stats.get('runs_won', 0) >= 1
    if cond == 'play_hand':
        return (stats.get('hands') or {}).get(ach.get('hand'), 0) >= int(ach.get('n') or 1)
    if cond == 'stat':
        return stats.get(ach.get('stat'), 0) >= int(ach.get('n') or 1)
    if cond == 'custom':
        return _custom_met(ach.get('key'), game, event, payload, stats, run)
    return False


def _toast(game, newly):
    if not newly:
        return
    bits = []
    for ach in newly:
        reward = ', '.join(ach.get('unlocks') or [])
        bits.append(f"{ach['name']}" + (f" — {reward}" if reward else ''))
    game.temp_message = "Unlocked: " + "; ".join(bits)
    game.temp_message_start = __import__('time').time()
    game.temp_message_duration = max(getattr(game, 'temp_message_duration', 3.0), 4.5)


def evaluate(game, event, persist=True, **payload):
    """Update stats and grant any newly completed achievements. Returns list of ach dicts."""
    if not getattr(game, 'progress', None):
        attach_progress(game)
    stats, run = _update_stats(game, event, payload)
    newly = []
    have = set(game.progress.get('unlocked_achievements') or [])
    for ach in ACHIEVEMENTS:
        if ach['id'] in have:
            continue
        if is_complete(ach, game, event, payload, stats, run):
            have.add(ach['id'])
            game.progress['unlocked_achievements'].append(ach['id'])
            game.progress.setdefault('new_this_run', []).append(ach['id'])
            for name in ach.get('unlocks') or []:
                if name in LOCKED_POUCHES:
                    pouches = game.progress.setdefault('unlocked_pouches', [])
                    if name not in pouches:
                        pouches.append(name)
                elif name not in game.progress['unlocked_charms']:
                    game.progress['unlocked_charms'].append(name)
            newly.append(ach)
    if newly and persist and not getattr(game, '_skip_ach_persist', False):
        save_progress(game.progress)
        try:
            _toast(game, newly)
        except Exception:
            pass
    return newly


def notify(game, event, **payload):
    try:
        return evaluate(game, event, **payload)
    except Exception as e:
        print(f"DEBUG: achievement notify failed ({event}): {e}")
        return []


def bag_has_steel(game):
    for die in (getattr(game, 'full_bag', None) or getattr(game, 'bag', None) or []):
        if die and 'Steel' in (die.get('enhancements') or []):
            return True
    return False


def max_prism(game):
    mults = getattr(game, 'hand_multipliers', None) or {}
    if not mults:
        return 1.0
    return float(max(mults.values()) if mults.values() else 1.0)


def score_payload(game, hand_type, held_rolls):
    """Build the score event payload from held (die, value) pairs."""
    held_rolls = [(d, v) for d, v in (held_rolls or []) if d]
    faces = [v for _d, v in held_rolls]
    colors = [d.get('color') for d, _v in held_rolls]
    glass_n = sum(1 for c in colors if c == 'Glass')
    special_n = sum(1 for c in colors if c in ('Gold', 'Silver', 'Glass', 'Rainbow'))
    gold_or_glass = any(
        d.get('color') in ('Gold', 'Glass') for d, _v in held_rolls
    )
    all_red = bool(colors) and all(c == 'Red' for c in colors)
    return {
        'hand_type': hand_type,
        'faces': faces,
        'colors': colors,
        'glass_n': glass_n,
        'special_n': special_n,
        'lucky': getattr(game, 'lucky_triggers', 0) or 0,
        'all_sixes': bool(faces) and all(v == 6 for v in faces) and len(faces) >= 5,
        'all_red': all_red,
        'mono': _is_mono(colors),
        'held_gold_or_glass': gold_or_glass,
        'steel': bag_has_steel(game),
        'max_prism': max_prism(game),
        'charm_count': len(getattr(game, 'equipped_charms', []) or []),
    }

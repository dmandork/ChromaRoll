# Compact run telemetry for balancing. One JSON line per finished run.
# Not a per-turn tape — blinds + bag histograms are enough to see economy/power.
import json
import os
import sys
import time
from collections import Counter
from types import SimpleNamespace


def log_file_path():
    override = os.environ.get('CHROMAROLL_RUNLOG')
    if override:
        return override
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'runs.jsonl')


def crash_log_path():
    override = os.environ.get('CHROMAROLL_CRASHLOG')
    if override:
        return override
    return os.path.join(os.path.dirname(log_file_path()), 'crash.log')


def _pouch_name(game):
    p = getattr(game, 'current_pouch', None) or {}
    if isinstance(p, dict):
        return p.get('name') or 'Unknown'
    return str(p or 'Unknown')


def bag_histogram(bag):
    colors = Counter()
    enh = Counter()
    for die in bag or []:
        if not die:
            continue
        colors[die.get('color') or '?'] += 1
        for e in die.get('enhancements') or []:
            if e not in ('Red', 'Blue', 'Green', 'Purple', 'Yellow', 'Wild'):
                enh[e] += 1
    return {
        'size': sum(colors.values()),
        'colors': dict(colors),
        'enh': dict(enh),
    }


def charm_names(game):
    return [c.get('name') for c in (getattr(game, 'equipped_charms', None) or []) if c]


def hands_played(game):
    counts = getattr(game, 'hand_play_counts', None) or {}
    return {k: int(v) for k, v in counts.items() if v}


def init_run(game):
    game.run_score = 0
    game.best_hand_score = 0
    game.best_hand_type = None
    game.blind_log = []
    game.run_started_at = time.time()
    game._runlog_written = False


def note_scored_hand(game, hand_type, score):
    game.run_score = int(getattr(game, 'run_score', 0) or 0) + int(score or 0)
    if int(score or 0) >= int(getattr(game, 'best_hand_score', 0) or 0):
        game.best_hand_score = int(score or 0)
        game.best_hand_type = hand_type


def record_blind(game):
    bag = getattr(game, 'full_bag', None) or getattr(game, 'bag', []) or []
    hands_left = int(getattr(game, 'hands_left', 0) or 0)
    max_hands = int(getattr(game, 'max_hands', 0) or 0) or int(getattr(game, 'hands_left_initial', 0) or 0)
    used = None
    if max_hands:
        used = max(0, max_hands - hands_left)
    entry = {
        'stake': int(getattr(game, 'current_stake', 0) or 0),
        'blind': getattr(game, 'current_blind', None),
        'target': int(game.get_blind_target()) if hasattr(game, 'get_blind_target') else 0,
        'score': int(getattr(game, 'round_score', 0) or 0),
        'hands_left': hands_left,
        'hands_used': used,
        'coins': int(getattr(game, 'coins', 0) or 0),
        'charms': charm_names(game),
        'bag': bag_histogram(bag),
    }
    log = list(getattr(game, 'blind_log', None) or [])
    log.append(entry)
    game.blind_log = log
    return entry


def build_run_record(game, result):
    bag = getattr(game, 'full_bag', None) or getattr(game, 'bag', []) or []
    debug = False
    try:
        import constants
        debug = bool(getattr(constants, 'DEBUG', False))
    except Exception:
        pass
    return {
        'ended': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'result': result,
        'debug': debug,
        'pouch': _pouch_name(game),
        'stake': int(getattr(game, 'current_stake', 0) or 0),
        'blind': getattr(game, 'current_blind', None),
        'coins': int(getattr(game, 'coins', 0) or 0),
        'run_score': int(getattr(game, 'run_score', 0) or 0),
        'last_blind_score': int(getattr(game, 'round_score', 0) or 0),
        'best': {
            'hand': getattr(game, 'best_hand_type', None),
            'score': int(getattr(game, 'best_hand_score', 0) or 0),
        },
        'hands': hands_played(game),
        'charms': charm_names(game),
        'bag': bag_histogram(bag),
        'blinds': list(getattr(game, 'blind_log', None) or []),
        'bosses': list(getattr(game, 'beaten_bosses', None) or []),
        'seconds': int(max(0, time.time() - float(getattr(game, 'run_started_at', time.time()) or time.time()))),
    }


def _comma(n):
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def finish_lines(record, limit=14):
    """Short labeled lines for the finish plaque. One fact per line."""
    lines = []
    pouch = record.get('pouch') or '?'
    lines.append(f"Pouch     {pouch}")
    lines.append(f"Score     {_comma(record.get('run_score') or 0)}")
    best = record.get('best') or {}
    if best.get('hand'):
        lines.append(f"Best      {best['hand']}   {_comma(best.get('score') or 0)}")
    hands = record.get('hands') or {}
    if hands:
        top = sorted(hands.items(), key=lambda kv: -kv[1])[:4]
        lines.append("Hands     " + "   ".join(f"{n} ×{c}" for n, c in top))
    charms = record.get('charms') or []
    if charms:
        lines.append("Charms    " + " · ".join(charms[:3]))
        if len(charms) > 3:
            lines.append("          " + " · ".join(charms[3:8]))
    bag = record.get('bag') or {}
    colors = bag.get('colors') or {}
    if colors:
        bits = [f"{n} {c}" for c, n in sorted(colors.items(), key=lambda kv: -kv[1])]
        lines.append(f"Bag       {', '.join(bits[:5])}   ({bag.get('size', 0)})")
    enh = bag.get('enh') or {}
    if enh:
        bits = [f"{n} {e}" for e, n in sorted(enh.items(), key=lambda kv: -kv[1])]
        lines.append("Enh       " + " · ".join(bits[:6]))
    return lines[:limit]


def finish_rows(record):
    """(label, value) rows. value is a string or a list of strings (wrapped by the UI)."""
    rows = []
    rows.append(('Pouch', record.get('pouch') or '?'))
    rows.append(('Score', _comma(record.get('run_score') or 0)))
    best = record.get('best') or {}
    if best.get('hand'):
        rows.append(('Best', f"{best['hand']}   {_comma(best.get('score') or 0)}"))
    hands = record.get('hands') or {}
    if hands:
        top = sorted(hands.items(), key=lambda kv: -kv[1])
        rows.append(('Hands', " · ".join(f"{n} ×{c}" for n, c in top)))
    charms = record.get('charms') or []
    if charms:
        rows.append(('Charms', " · ".join(charms)))
    else:
        rows.append(('Charms', 'None'))
    bag = record.get('bag') or {}
    colors = bag.get('colors') or {}
    size = bag.get('size') or 0
    if colors:
        bits = [f"{n} {c}" for c, n in sorted(colors.items(), key=lambda kv: -kv[1])]
        rows.append(('Bag', f"{', '.join(bits)}  ({size})"))
    elif size:
        rows.append(('Bag', f"{size} dice"))
    enh = bag.get('enh') or {}
    if enh:
        bits = [f"{n} {e}" for e, n in sorted(enh.items(), key=lambda kv: -kv[1])]
        rows.append(('Enh', ' · '.join(bits)))
    bosses = record.get('bosses') or []
    if bosses:
        rows.append(('Bosses', " · ".join(str(b) for b in bosses)))
    n_blinds = len(record.get('blinds') or [])
    if n_blinds:
        rows.append(('Blinds', str(n_blinds)))
    sec = int(record.get('seconds') or 0)
    if sec > 0:
        rows.append(('Time', f"{sec // 60}m {sec % 60:02d}s"))
    return rows


def has_run_progress(game):
    """True if this object looks like a started run that hasn't been logged yet."""
    if getattr(game, '_runlog_written', False):
        return False
    if list(getattr(game, 'blind_log', None) or []):
        return True
    if int(getattr(game, 'run_score', 0) or 0):
        return True
    if any(getattr(game, 'equipped_charms', None) or []):
        return True
    if int(getattr(game, 'current_stake', 1) or 1) > 1:
        return True
    pouch = getattr(game, 'current_pouch', None)
    if isinstance(pouch, dict) and pouch.get('name'):
        return True
    if isinstance(pouch, str) and pouch:
        return True
    return False


def _game_from_save_dict(data):
    pouch = data.get('pouch_type') or data.get('pouch')
    if isinstance(pouch, str):
        pouch = {'name': pouch}
    return SimpleNamespace(
        current_pouch=pouch or {},
        current_stake=data.get('current_stake', 1),
        current_blind=data.get('current_blind'),
        coins=data.get('coins', 0),
        run_score=data.get('run_score', 0),
        round_score=data.get('round_score', 0),
        best_hand_type=data.get('best_hand_type'),
        best_hand_score=data.get('best_hand_score', 0),
        hand_play_counts=data.get('hand_play_counts') or {},
        equipped_charms=data.get('equipped_charms') or [],
        full_bag=data.get('full_bag') or data.get('bag') or [],
        bag=data.get('bag') or [],
        run_started_at=data.get('run_started_at') or time.time(),
        blind_log=data.get('blind_log') or [],
        _runlog_written=False,
    )


def abandon_current_run(game):
    """Flush the in-progress run to runs.jsonl before New Game wipes it.

    Uses live game state if it looks like a run; otherwise hydrates from save.json.
    `ended` is stamped at write time (now). Already-logged wins/losses are skipped.
    """
    if getattr(game, '_runlog_written', False):
        return None
    if has_run_progress(game):
        return append_run(game, 'abandon')
    try:
        import savegame
        path = savegame.save_file_path()
        if not os.path.exists(path):
            return None
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        if not savegame.is_run_save(data):
            return None
        dummy = _game_from_save_dict(data)
        if not has_run_progress(dummy):
            return None
        return append_run(dummy, 'abandon')
    except Exception:
        return None


def append_run(game, result):
    if getattr(game, '_runlog_written', False):
        return None
    record = build_run_record(game, result)
    game.last_run_record = record
    path = log_file_path()
    try:
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=True) + '\n')
        game._runlog_written = True
    except Exception:
        pass
    return record


def write_crash(game, exc=None):
    """Append traceback + run snapshot to crash.log, and a runs.jsonl line with result=crash."""
    import traceback
    if exc is None:
        tb = traceback.format_exc()
    else:
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    lines = [
        time.strftime('%Y-%m-%dT%H:%M:%S'),
        f"stake={getattr(game, 'current_stake', None) if game is not None else None} "
        f"blind={getattr(game, 'current_blind', None) if game is not None else None}",
        f"pouch={_pouch_name(game) if game is not None else '?'}",
        'charms=' + (', '.join(charm_names(game)) if game is not None else ''),
        tb.rstrip(),
        '-' * 40,
        '',
    ]
    path = crash_log_path()
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))
    except Exception:
        pass
    if game is None:
        return None
    try:
        rec = append_run(game, 'crash')
    except Exception:
        rec = None
    try:
        import savegame
        savegame.save_on_exit(game)
    except Exception:
        pass
    return rec

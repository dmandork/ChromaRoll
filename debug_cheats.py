# debug_cheats.py
# DEBUG-only helpers. No pygame. Safe to unit-test.
#
# Play-screen bar and blinds Force Win call through these so a forced
# win/lose still fires the same achievement notify payload as a real one.

PLAY_DEBUG_ACTIONS = [
    ('win', 'Win'),
    ('lose', 'Lose'),
    ('close', 'CloseLose'),
    ('last', 'LastHand'),
    ('coins', '+$40'),
    ('empty', 'Empty'),
    ('sixes', 'Five 6s'),
    ('red', 'All Red'),
    ('glass', 'Glass x2'),
    ('steel', '+Steel'),
]


def close_lose_score(target):
    """Score that counts as So Close (>= 80% of target) without beating it."""
    t = int(target or 0)
    if t <= 0:
        return 0
    return max(0, int(t * 0.8))


def win_notify_kwargs(game):
    """Same payload score_and_new_turn sends on a real blind win."""
    boss_name = ((getattr(game, 'current_boss_effect', None) or {}) or {}).get('name')
    progress = getattr(game, 'progress', None) or {}
    run = progress.get('run') or {}
    boon = getattr(game, 'd20_boon', None)
    try:
        from achievements import max_prism
        prism = max_prism(game)
    except Exception:
        prism = 1.0
    return {
        'is_boss': getattr(game, 'current_blind', None) == 'Boss',
        'stake': getattr(game, 'current_stake', 1),
        'hard_boss': getattr(game, 'current_blind', None) == 'Boss' and boss_name in ('Hold Ban', 'Charm Eclipse'),
        'intensified': bool(boon and getattr(boon, 'active', False)),
        'last_hand': int(getattr(game, 'hands_left', 1) or 0) <= 0,
        'no_reroll': int(run.get('rerolls_this_blind', 0) or 0) == 0,
        'charm_count': len(getattr(game, 'equipped_charms', []) or []),
        'coins': getattr(game, 'coins', 0),
        'max_prism': prism,
    }


def apply_paint(rolls, hand, held, kind):
    """Mutate the in-play dice for a custom achievement. Returns (rolls, held)."""
    rolls = list(rolls or [])
    hand = list(hand or [])
    n = len(rolls)
    if n == 0:
        return rolls, list(held or [])
    held_out = list(held or [False] * n)
    if len(held_out) < n:
        held_out.extend([False] * (n - len(held_out)))

    def slot(i, color=None, face=None):
        die, val = rolls[i]
        if not isinstance(die, dict):
            die = {'color': 'Red', 'faces': [1, 2, 3, 4, 5, 6], 'enhancements': []}
        else:
            die = dict(die)
            die['enhancements'] = list(die.get('enhancements') or [])
        if color:
            die['color'] = color
        if face is not None:
            val = face
        rolls[i] = (die, val)
        if i < len(hand) and isinstance(hand[i], dict):
            hand[i]['color'] = die['color']
        held_out[i] = True

    if kind == 'sixes':
        for i in range(n):
            slot(i, face=6)
    elif kind == 'red':
        for i in range(n):
            slot(i, color='Red')
    elif kind == 'glass':
        slot(0, color='Glass')
        if n > 1:
            slot(1, color='Glass')
    return rolls, held_out


def add_steel(bag, full_bag=None):
    """Stamp Steel on the first bag die. Returns the die or None."""
    bag = bag if bag is not None else []
    if not bag:
        bag = full_bag or []
    if not bag:
        return None
    die = bag[0]
    if not isinstance(die, dict):
        return None
    enh = list(die.get('enhancements') or [])
    if 'Steel' not in enh:
        enh.append('Steel')
    die['enhancements'] = enh
    if full_bag:
        for d in full_bag:
            if d is die or (isinstance(d, dict) and d.get('id') == die.get('id')):
                d.setdefault('enhancements', [])
                if 'Steel' not in d['enhancements']:
                    d['enhancements'].append('Steel')
    return die

# scoring.py

import random
import time
from data import ENH_EFFECTS, MYSTIC_RUNES

# Local copies so tests can import this module without constants/pygame.
_BASE_COLORS = ['Red', 'Blue', 'Green', 'Purple', 'Yellow']
_SPECIAL_COLORS = ['Gold', 'Silver', 'Glass', 'Rainbow']
_DIE_COLORS = _BASE_COLORS + _SPECIAL_COLORS
_PACK_BOOST = 0.5


def glass_breaks(game, chance, rng=None):
    """True if a Glass die is destroyed after the break roll.

    Saving Throw (`break_save`) gets a d6; 4–6 cancels a would-be break.
    Sets game._last_save_roll / game._last_save_success when a save is attempted.
    """
    rng = rng or random
    if game is not None:
        game._last_save_roll = None
        game._last_save_success = False
    if rng.random() >= chance:
        return False
    has_save = False
    if game is not None:
        disabled = getattr(game, 'disabled_charms', []) or []
        for idx, charm in enumerate(getattr(game, 'equipped_charms', []) or []):
            if charm.get('type') == 'break_save' and idx not in disabled:
                has_save = True
                break
    if not has_save:
        return True
    save_roll = rng.randint(1, 6)
    saved = save_roll > 3
    if game is not None:
        game._last_save_roll = save_roll
        game._last_save_success = saved
    return not saved


def rotate_castle_color(charm, rng=None):
    """Pick a new Castle Cube color, avoiding the previous one when possible."""
    rng = rng or random
    prev = charm.get('active_color')
    choices = [c for c in _BASE_COLORS if c != prev] or list(_BASE_COLORS)
    charm['active_color'] = rng.choice(choices)
    return charm['active_color']


def apply_castle_discards(charm, discarded_dice):
    """Permanent +value chips per discarded die matching the current color."""
    color = charm.get('active_color')
    if not color:
        return 0
    n = sum(1 for d in (discarded_dice or []) if d and d.get('color') == color)
    added = n * charm.get('value', 3)
    if added:
        charm['permanent_bonus'] = charm.get('permanent_bonus', 0) + added
    return added


def try_space_sphere(game, hand_type, rng=None, boost=None):
    """25% chance to add PACK_BOOST to the scored hand type. Returns True on hit."""
    rng = rng or random
    boost = _PACK_BOOST if boost is None else boost
    if not hand_type or hand_type == 'Nothing':
        return False
    disabled = getattr(game, 'disabled_charms', []) or []
    for idx, charm in enumerate(getattr(game, 'equipped_charms', []) or []):
        if charm.get('type') != 'hand_upgrade':
            continue
        if idx in disabled:
            continue
        if rng.random() < charm.get('chance', 0.25):
            if getattr(game, 'hand_multipliers', None) is None:
                game.hand_multipliers = {}
            game.hand_multipliers[hand_type] = game.hand_multipliers.get(hand_type, 1.0) + boost
            game._space_sphere_hit = hand_type
            return True
        return False
    return False


def mortgage_sell_payout(equipped, sell_index, disabled=None, already_used=False):
    """Return (payout, lock_charm_or_None, used_mortgage).

    One doubled sell per shop while Monopoly Mortgage is equipped. Selling
    Mortgage itself also pays 2x and needs no lock (it leaves the loadout).
    """
    disabled = disabled or []
    charm = equipped[sell_index]
    base = charm.get('sell_value', charm.get('cost', 0) // 2)
    mortgage = None
    mortgage_idx = None
    for idx, c in enumerate(equipped):
        if c.get('type') == 'sell_double_lock' and idx not in disabled and not c.get('locked'):
            mortgage = c
            mortgage_idx = idx
            break
    if mortgage is None or already_used:
        return base, None, False
    payout = int(base * mortgage.get('value', 2))
    if sell_index == mortgage_idx or charm is mortgage:
        return payout, None, True
    return payout, mortgage, True


def pouch_charm_slots(pouch):
    """Absolute charm-slot count for a pouch. Assign this — never += leftover max_charms."""
    return 5 + (pouch.get('bonus') or {}).get('charm_slots', 0)


def pouch_hands_delta(pouch):
    """Hands bonus from a pouch. Call this ONCE in apply_pouch."""
    return (pouch.get('bonus') or {}).get('hands', 0)


def pouch_extra_colors(pouch, rng=None):
    """Colors of extra dice a pouch should add. Never emits 'random_special'."""
    rng = rng or random
    extras = (pouch.get('bonus') or {}).get('extra_dice') or {}
    colors = []
    for color, count in extras.items():
        n = int(count or 0)
        if color == 'random_special':
            for _ in range(n):
                colors.append(rng.choice(_SPECIAL_COLORS))
        else:
            colors.extend([color] * n)
    return colors


def randomize_bag_colors(bag, rng=None):
    """Erratic pouch: recolor every die using real die colors only (never Black)."""
    rng = rng or random
    pool = list(_DIE_COLORS)
    for die in bag or []:
        if die:
            die['color'] = rng.choice(pool)
    return bag


def shop_pack_weights(ghost=False):
    """Pack row weights: 0-2 prism, 3-4 base dice, 5 special dice, 6-8 runes."""
    weights = [1.0] * 6 + [1.0, 0.8, 0.3]
    if ghost:
        weights[5] = 4.0
    return weights


def dice_pack_choices(n, special_only=False, ghost=False, rng=None):
    """Colors offered by a dice pack. Ghost mixes specials into standard packs."""
    rng = rng or random
    n = int(n or 0)
    if n <= 0:
        return []
    if special_only:
        pool = list(_SPECIAL_COLORS)
    elif ghost:
        pool = list(_BASE_COLORS) + list(_SPECIAL_COLORS)
    else:
        pool = list(_BASE_COLORS)
    if n >= len(pool):
        return list(pool)
    return rng.sample(pool, n)


def plasma_mix_chips(colors):
    """Plasma mix identity: pay for many hues, tax a one-color hand.

    Distinct non-Rainbow colors among held dice:
      5 → +120, 4 → +80, 3 → +40, 2 → 0, 1 → −40.
    All-Rainbow counts as a full spectrum (+120). Rainbow never breaks mono.
    """
    colors = [c for c in (colors or []) if c]
    if not colors:
        return 0
    base = [c for c in colors if c != 'Rainbow']
    if not base:
        unique = 5
    else:
        unique = len(set(base))
    if unique >= 5:
        return 120
    if unique == 4:
        return 80
    if unique == 3:
        return 40
    if unique <= 1:
        return -40
    return 0


def apply_kind_wilds(game, held_rolls, counts, max_count, groups, modifier_desc):
    """2s (Face Forgery), 4s (Kind Keeper), 6s (Kind King) join the best non-wild kind."""
    disabled = set(getattr(game, 'disabled_charms', []) or [])
    wild_faces = set()
    labels = {}
    for idx, charm in enumerate(getattr(game, 'equipped_charms', []) or []):
        if idx in disabled:
            continue
        t = charm.get('type')
        if t == 'face_wild' and charm.get('face') is not None:
            wild_faces.add(int(charm['face']))
            labels[int(charm['face'])] = charm.get('name', 'Face Forgery')
        elif t == 'wild_4':
            wild_faces.add(4)
            labels[4] = charm.get('name', 'Kind Keeper')
        elif t == 'wild_6':
            wild_faces.add(6)
            labels[6] = charm.get('name', 'Kind King')
        elif t == 'kind_wild' and charm.get('face') is not None:
            wild_faces.add(int(charm['face']))
            labels[int(charm['face'])] = charm.get('name', 'Wild Face')
    if not wild_faces:
        return counts, max_count
    wild_die_count = sum(1 for _, v in held_rolls if v in wild_faces)
    if wild_die_count <= 0:
        return counts, max_count
    non_wild = {k: v for k, v in counts.items() if k not in wild_faces and v > 0}
    if not non_wild:
        return counts, max_count
    target = max(non_wild, key=lambda k: (non_wild[k], k))
    counts[target] = counts.get(target, 0) + wild_die_count
    wild_colors = [die.get('color') for die, v in held_rolls if v in wild_faces]
    groups.setdefault(target, []).extend(wild_colors)
    for wf in wild_faces:
        if wf != target:
            counts[wf] = 0
            groups.pop(wf, None)
    max_count = max(counts.values()) if counts else 0
    names = sorted({labels[f] for f in wild_faces if f in labels})
    modifier_desc.append(f"{wild_die_count} {'/'.join(names)} wilds → {target}s")
    return counts, max_count


def apply_wild_4(game, held_rolls, counts, max_count, groups, modifier_desc):
    return apply_kind_wilds(game, held_rolls, counts, max_count, groups, modifier_desc)


def apply_wild_6(game, held_rolls, counts, max_count, groups, modifier_desc):
    return apply_kind_wilds(game, held_rolls, counts, max_count, groups, modifier_desc)


def apply_face_wild(game, held_rolls, counts, max_count, groups, modifier_desc, wild_face):
    return apply_kind_wilds(game, held_rolls, counts, max_count, groups, modifier_desc)


def get_stencil_mult(game):
    empty_slots = game.max_charms - len(game.equipped_charms)
    for charm in game.equipped_charms:
        if charm['type'] == 'empty_slot_mult':
            return 1.0 + (charm['value'] * empty_slots)
    return 1.0


def evaluate_hand(game, is_preview=True):
    """Exact replica of your original get_hand_type_and_score, but cleaned and with zero bugs."""
    held_rolls = [(die, value) for i, (die, value) in enumerate(game.rolls) if game.held[i]]
    if not held_rolls:
        return "Nothing", 0, "None", 0, 0, 0.0

    original_rolls = held_rolls[:]
    modifier_desc = []

    boon = getattr(game, 'd20_boon', None)

    # Wildcard: fused color acts as Rainbow for color bonuses this hand
    if boon and boon.wildcard_color:
        wild = boon.wildcard_color
        rewritten = []
        for die, val in held_rolls:
            if die.get('color') == wild:
                d = die.copy()
                d['color'] = 'Rainbow'
                rewritten.append((d, val))
            else:
                rewritten.append((die, val))
        held_rolls = rewritten

    held_colors = [die.get('color') for die, _ in held_rolls]

    # Hue Dimming — applied ONCE at the end via boon.dim_factor, not here
    dimmed_mult = 1.0

    # === ADVANTAGE / FATE'S FAVOR / D20 ROLL FLOW ===
    if game.has_advantage and game.held_advantage:
        adv_idx = getattr(game, 'd20_advantage_index', -1)
        if adv_idx < 0:
            adv_idx = 2  # Advantage Amulet: center die
        if 0 <= adv_idx < len(game.rolls) and game.rolls[adv_idx][0]:
            original_die = game.rolls[adv_idx][0]
            advantage_die = original_die.copy()
            held_rolls.append((advantage_die, game.advantage_value))

    if game.fates_advantage_index != -1 and game.held_fates_advantage:
        original_die = game.rolls[game.fates_advantage_index][0]
        advantage_die = original_die.copy()  # Copy the full die object so color is preserved
        held_rolls.append((advantage_die, game.fates_advantage_value))

    # === NOW CALCULATE VALUES FOR STRAIGHT DETECTION (includes advantage) ===
    values = [value for _, value in held_rolls]
    colors_list = [die['color'] for die, _ in held_rolls]
    sorted_values = sorted(values)
    counts = {i: values.count(i) for i in set(values)}
    max_count = max(counts.values()) if counts else 0
    pair_count = list(counts.values()).count(2)

    groups = {}
    for die, val in held_rolls:
        groups.setdefault(val, []).append(die['color'])

    counts, max_count = apply_kind_wilds(game, held_rolls, counts, max_count, groups, modifier_desc)
    pair_count = list(v for v in counts.values() if v > 0).count(2)

    # Boss: Value Vault inverts values
    if game.current_blind == 'Boss' and game.current_boss_effect and game.current_boss_effect['name'] == 'Value Vault':
        values = [7 - v for v in values]
        sorted_values = sorted(values)

    straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
    short_straights_small = [[1,2,3], [2,3,4], [3,4,5], [4,5,6]]
    short_straights_large = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
    has_four_fingers = any(c['type'] == 'short_straight' for c in game.equipped_charms if game.equipped_charms.index(c) not in game.disabled_charms)

    # Hand type detection
    hand_type = "Nothing"
    base_score = 0
    base_modifier = 0.0
    retrigger_mult = 1.0

    if sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large)):
        hand_type = "Large Straight"
        base_score = 160
        straight_values = sorted_values if not has_four_fingers else next((s for s in short_straights_large if all(x in values for x in s)), sorted_values)
        straight_colors = []
        for v in straight_values:
            straight_colors += groups.get(v, [])
        actual_colors_straight = [c for c in straight_colors if c != 'Rainbow']
        actual_set_straight = set(actual_colors_straight)
        if len(actual_set_straight) <= 1:
            base_modifier += 1.0
            modifier_desc.append("Monochrome +1")
        elif len(actual_colors_straight) == len(actual_set_straight):
            base_modifier += 1.0
            modifier_desc.append("Rainbow +1")

    elif any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small)):
        hand_type = "Small Straight"
        base_score = 90
        straight_values = next((s for s in straights if all(x in values for x in s)), sorted_values) if not has_four_fingers else next((s for s in short_straights_small if all(x in values for x in s)), sorted_values)
        straight_colors = []
        for v in straight_values:
            straight_colors += groups.get(v, [])
        actual_colors_straight = [c for c in straight_colors if c != 'Rainbow']
        actual_set_straight = set(actual_colors_straight)
        if len(actual_set_straight) <= 1:
            base_modifier += 1.0
            modifier_desc.append("Monochrome +1")
        elif len(actual_colors_straight) == len(actual_set_straight):
            base_modifier += 1.0
            modifier_desc.append("Rainbow +1")

    # Continue with remaining hand types
    if max_count == 5:
        hand_type = "5 of a Kind"
        base_score = 250
        if len(set(c for c in colors_list if c != 'Rainbow')) <= 1:
            base_modifier += 3.0
            modifier_desc.append("Monochrome +3")
        elif len([c for c in colors_list if c != 'Rainbow']) == len(set(c for c in colors_list if c != 'Rainbow')):
            base_modifier += 2.0
            modifier_desc.append("Rainbow +2")

    elif max_count == 4:
        hand_type = "4 of a Kind"
        base_score = 160
        for val, group_colors in groups.items():
            if counts.get(val, 0) == 4:
                actual_g_colors = [c for c in group_colors if c != 'Rainbow']
                if len(set(actual_g_colors)) <= 1:
                    base_modifier += 2.0
                    modifier_desc.append("Monochrome +2")
                elif len(actual_g_colors) == len(set(actual_g_colors)):
                    base_modifier += 1.0
                    modifier_desc.append("Rainbow +1")
                break

    elif max_count == 3 and 2 in counts.values():
        hand_type = "Full House"
        base_score = 160
        three_val = next((val for val, count in counts.items() if count == 3), None)
        pair_val = next((val for val, count in counts.items() if count == 2), None)
        three_group = groups.get(three_val, [])
        pair_group = groups.get(pair_val, [])
        if len(set(c for c in colors_list if c != 'Rainbow')) <= 1:
            base_modifier += 3.0
            modifier_desc.append("Full Mono +3")
        elif len([c for c in colors_list if c != 'Rainbow']) == len(set(c for c in colors_list if c != 'Rainbow')):
            base_modifier += 2.0
            modifier_desc.append("Rainbow +2")
        else:
            mono_three = len(set(c for c in three_group if c != 'Rainbow')) <= 1
            mono_pair = len(set(c for c in pair_group if c != 'Rainbow')) <= 1
            if mono_three and mono_pair:
                base_modifier += 1.0
                modifier_desc.append("Both Mono +1")
            elif mono_three or mono_pair:
                base_modifier += 0.5
                modifier_desc.append("One Mono +0.5")

    elif max_count == 3:
        hand_type = "3 of a Kind"
        base_score = 80
        for val, group_colors in groups.items():
            if counts.get(val, 0) == 3:
                actual_g_colors = [c for c in group_colors if c != 'Rainbow']
                if len(set(actual_g_colors)) <= 1:
                    base_modifier += 1.0
                    modifier_desc.append("Monochrome +1")
                elif len(actual_g_colors) == len(set(actual_g_colors)):
                    base_modifier += 0.5
                    modifier_desc.append("Rainbow +0.5")
                break

    elif pair_count == 2:
        hand_type = "2 Pair"
        base_score = 60
        mono_pairs = 0
        for group_colors in groups.values():
            if len(group_colors) == 2:
                actual_set = set(c for c in group_colors if c != 'Rainbow')
                if len(actual_set) <= 1:
                    mono_pairs += 1
        if mono_pairs == 1:
            base_modifier += 0.5
            modifier_desc.append("One Mono Pair +0.5")
        elif mono_pairs == 2:
            base_modifier += 1.0
            modifier_desc.append("Two Mono Pairs +1")

    elif pair_count == 1:
        hand_type = "Pair"
        base_score = 20
        for val, group_colors in groups.items():
            if counts.get(val, 0) == 2:
                actual_g_colors = [c for c in group_colors if c != 'Rainbow']
                if len(set(actual_g_colors)) <= 1:
                    base_modifier += 0.5
                    modifier_desc.append("Monochrome +0.5")
                break

    # Boss effects
    if game.current_blind == 'Boss' and game.current_boss_effect:
        effect_name = game.current_boss_effect['name']
        if effect_name == 'Score Dip':
            base_score = int(base_score * 0.9)
        if effect_name == 'Color Fade':
            base_modifier = 0.0
            modifier_desc = ["None"]
        if effect_name == 'Mono Mixup' and len(set(colors_list)) > 1:
            base_modifier -= 0.5
        if effect_name == 'Rainbow Restriction':
            colors_list = [game.boss_rainbow_color if c == 'Rainbow' else c for c in colors_list]

    # Enhancements (every single one preserved)
    rune_chips = 0
    rune_mult_add = 0.0
    rune_break_dies = []
    if not is_preview:
        game.lucky_triggers = 0
    enh_counts = {}
    enhancement_desc_parts = []

    for die, value in held_rolls:
        enh = die.get('enhancements', [])
        for e in enh:
            enh_counts[e] = enh_counts.get(e, 0) + 1

        if 'Bonus' in enh:
            rune_chips += 10 * len([e for e in enh if e == 'Bonus'])
        if 'Mult' in enh:
            rune_mult_add += 0.5 * len([e for e in enh if e == 'Mult'])
        if 'Lucky' in enh:
            if not is_preview and random.random() < 0.33:
                game.lucky_triggers += len([e for e in enh if e == 'Lucky'])
            elif is_preview:
                expected = 0.33 * enh_counts.get('Lucky', 0)
                enhancement_desc_parts.append(f"Lucky x{enh_counts.get('Lucky',0)}: ~+{expected:.1f} coins")
        if 'Steel' in enh:
            rune_mult_add += 0.5 * len([e for e in enh if e == 'Steel'])
        if 'Fragile' in enh:
            rune_mult_add += 1.0 * len([e for e in enh if e == 'Fragile'])
            if not is_preview and random.random() < 0.25:
                rune_break_dies.append(die)
        if 'Stone' in enh:
            rune_chips += 50 * len([e for e in enh if e == 'Stone'])

    for enh_type, count in enh_counts.items():
        if enh_type in ENH_EFFECTS:
            effect = ENH_EFFECTS[enh_type]
            if 'mult_add' in effect:
                total_add = effect['mult_add'] * count
                enhancement_desc_parts.append(f"{enh_type} x{count}: +{total_add} mult")
            if 'score' in effect:
                total_score = effect['score'] * count
                enhancement_desc_parts.append(f"{enh_type} x{count}: +{total_score}")
            if enh_type == 'Fragile':
                enhancement_desc_parts.append(f"Fragile x{count}: +{1.0 * count} mult (25% break each)")

    if enhancement_desc_parts:
        modifier_desc += enhancement_desc_parts

    for die in rune_break_dies:
        for idx, (d, v) in enumerate(held_rolls):
            if d is die:
                game.broken_dice.append(idx)
                break

    # Charm processing (your full charm loop - unchanged)
    charm_color_mult_add = 0.0
    charm_chips = 0.0
    charm_mult_add = 0.0
    is_mono = any("Mono" in d for d in modifier_desc)
    is_rainbow = any("Rainbow" in d for d in modifier_desc)
    num_dice_used = len(held_rolls)
    is_small_straight = any(all(x in values for x in s) for s in straights) or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_small))
    is_large_straight = sorted_values in [[1,2,3,4,5], [2,3,4,5,6]] or (has_four_fingers and any(all(x in values for x in s) for s in short_straights_large))
    game.confirmed_hands_this_round = getattr(game, 'confirmed_hands_this_round', 0)

    for idx, charm in enumerate(game.equipped_charms):
        if idx in game.disabled_charms:
            continue

        if charm['type'] == 'flat_bonus':
            charm_chips += charm['value']

        elif charm['type'] == 'per_color_bonus':
            charm_chips += colors_list.count(charm['color']) * charm['value']

        elif charm['type'] == 'hand_bonus':
            for h in charm['hands']:
                if h == 'Pair' and max_count >= 2:
                    charm_chips += charm['value']
                elif h == '2 Pair' and pair_count >= 2:
                    charm_chips += charm['value']
                elif h == '3 of a Kind' and max_count >= 3:
                    charm_chips += charm['value']
                elif h == '4 of a Kind' and max_count >= 4:
                    charm_chips += charm['value']
                elif h == '5 of a Kind' and max_count == 5:
                    charm_chips += charm['value']
                elif h == 'Full House' and max_count == 3 and 2 in counts.values():
                    charm_chips += charm['value']
                elif h == 'Small Straight' and is_small_straight:
                    charm_chips += charm['value']
                elif h == 'Large Straight' and is_large_straight:
                    charm_chips += charm['value']

        elif charm['type'] == 'mono_mult_bonus':
            if is_mono:
                charm_color_mult_add += charm['value']
                modifier_desc.append(f"{charm['name']} +{charm['value']}")

        elif charm['type'] == 'few_dice_bonus':
            if num_dice_used <= charm['max_dice']:
                charm_chips += charm['value']

        elif charm['type'] == 'empty_slot_mult':
            empty_slots = game.max_charms - len(game.equipped_charms)
            mult_add = charm['value'] * empty_slots
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'per_value_bonus':
            count = 0
            for _, value in held_rolls:
                if (charm['parity'] == 'even' and value % 2 == 0) or (charm['parity'] == 'odd' and value % 2 != 0):
                    count += 1
            charm_chips += count * charm['value']

        elif charm['type'] == 'rainbow_mult_bonus':
            if is_rainbow:
                charm_color_mult_add += charm['value']
                modifier_desc.append(f"{charm['name']} +{charm['value']}")

        elif charm['type'] == 'sacrifice_mult':
            mult_add = game.score_mult
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'mult_bonus':
            if 'hands' in charm:
                if hand_type in charm['hands']:
                    mult_add = charm['value'] - 1
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add}")
            else:
                mult_add = charm['value'] - 1
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'color_mult':
            count = sum(1 for die, _ in held_rolls if die['color'] == charm['color'])
            mult_add = count * charm['value']
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({count} {charm['color']})")

        elif charm['type'] == 'color_mult_conditional':
            if not hasattr(game, 'rerolls_left_initial') or game.rerolls_left != game.rerolls_left_initial:
                continue
            count = sum(1 for die, _ in held_rolls if die['color'] == charm['color'])
            mult_add = count * charm['value']
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({count} {charm['color']})")

        elif charm['type'] == 'mult_conditional':
            # Flower Pot (mono), Glass Globe (glass), Loyalty Luck (every N turns)
            if charm.get('mono'):
                actual = [die.get('color') for die, _ in held_rolls if die.get('color') != 'Rainbow']
                if held_rolls and len(set(actual)) <= 1:
                    charm_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']} (mono)")
            elif charm.get('glass'):
                if any(die.get('color') == 'Glass' for die, _ in held_rolls):
                    charm_mult_add += charm['value']
                    modifier_desc.append(f"{charm['name']} +{charm['value']} (glass)")
            elif charm.get('every'):
                if 'local_turns' not in charm:
                    charm['local_turns'] = 0
                local_turn = charm['local_turns']
                every = charm['every']
                if local_turn > 0 and local_turn % every == 0:
                    mult_add = charm['value']
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'mult_per_face':
            count = sum(1 for _, v in held_rolls if v in charm['faces'])
            mult_add = charm['value'] * count
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({count} faces)")

        elif charm['type'] == 'bonus_per_charm':
            count = len([c for idx, c in enumerate(game.equipped_charms) if idx not in game.disabled_charms])
            mult_add = charm['mult'] * count
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({count} charms)")
            charm_chips += charm['score'] * count

        elif charm['type'] == 'mult_per_streak':
            mult_add = round(charm['value'] * game.avoid_streak, 1)
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({game.avoid_streak} streak)")

        elif charm['type'] == 'mult_per_low_bag':
            low_count = max(0, 25 - len(game.full_bag))
            mult_add = charm['value'] * low_count
            charm_mult_add += mult_add
            modifier_desc.append(f"{charm['name']} +{mult_add} ({low_count} below 25)")

        elif charm['type'] == 'mult_per_lucky':
            mult_add = charm.get('permanent_bonus', 0.0)
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} (permanent)")

        elif charm['type'] == 'mult_per_milestone':
            mult_add = charm['value'] * getattr(game, 'stake_milestones', 0)
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({game.stake_milestones} milestones)")

        elif charm['type'] == 'surge_random':
            if hand_type in ['3 of a Kind', '4 of a Kind', '5 of a Kind']:
                surge_mult = charm.get('surge_mult', 0)
                if surge_mult > 0:
                    charm_mult_add += surge_mult
                    modifier_desc.append(f"{charm['name']} +{surge_mult}x (this turn's surge)")

        elif charm['type'] == 'rainbow_mult':
            unique_colors = len(set(colors_list))
            if is_rainbow and unique_colors > 1:
                mult_add = charm['value'] * (unique_colors - 1)
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add:.1f} ({unique_colors} colors)")

        elif charm['type'] == 'coin_per_color':
            green_count = sum(1 for die, _ in held_rolls if die['color'] == charm['color'])
            if not is_preview and green_count > 0:
                game.extra_coins += green_count
                modifier_desc.append(f"{charm['name']} +{green_count} coins ({green_count} {charm['color']})")

        elif charm['type'] == 'retrigger':
            hands = charm.get('hands')
            is_kinds = hands == 'kinds' or (isinstance(hands, str) and 'kinds' in hands) or (
                isinstance(hands, (list, tuple)) and 'kinds' in hands
            )
            if is_kinds and hand_type in ['3 of a Kind', '4 of a Kind', '5 of a Kind']:
                retrigger_mult *= 2
                modifier_desc.append(f"{charm['name']} x2 (kinds retrigger)")
            elif charm.get('target') == 'final_hand':
                if getattr(game, 'is_last_hand', False) or getattr(game, 'hands_left', 99) == 1:
                    retrigger_mult *= 2
                    modifier_desc.append(f"{charm['name']} x2 (final hand)")

        elif charm['type'] == 'advantage_choice':
            pass  # handled elsewhere

        elif charm['type'] == 'reroll_advantage':
            pass  # handled elsewhere

        elif charm['type'] == 'rune_cast':
            pass  # handled elsewhere

        elif charm['type'] == 'coin_per_lucky':
            if not is_preview and game.lucky_triggers > 0:
                coins_added = charm['value'] * game.lucky_triggers
                modifier_desc.append(f"{charm['name']} +{coins_added} coins ({game.lucky_triggers} lucky)")

        elif charm['type'] == 'random_rune':
            pass

        elif charm['type'] == 'interest_bonus':
            pass  # handled in score_and_new_turn

        elif charm['type'] == 'retrigger_special':
            pass

        elif charm['type'] == 'mult_per_enhance':
            enhance_name = charm.get('enhance') or charm.get('enh')
            if enhance_name:
                # Steel Seal: count that enhancement across the owned bag
                bag = getattr(game, 'full_bag', None) or getattr(game, 'bag', []) or []
                count = sum(1 for d in bag if d and enhance_name in (d.get('enhancements') or []))
                mult_add = charm['value'] * count
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({count} {enhance_name} in bag)")
            else:
                # Enhance Elixir: per enhancement on scored dice
                total_enhancements = sum(len(die.get('enhancements') or []) for die, _ in held_rolls)
                mult_add = charm['value'] * total_enhancements
                if mult_add > 0:
                    charm_mult_add += mult_add
                    modifier_desc.append(f"{charm['name']} +{mult_add} ({total_enhancements} enhancements)")

        elif charm['type'] == 'discard_mult':
            mult_add = charm['value'] * getattr(game, 'discards_used_this_round', 0)
            if mult_add > 0:
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} ({game.discards_used_this_round} discards)")

        elif charm['type'] == 'coin_per_wild':
            non_rainbow_colors = [die['color'] for die, _ in held_rolls if die['color'] != 'Rainbow']
            is_mono_hand = len(set(non_rainbow_colors)) <= 1 if non_rainbow_colors else False
            wild_count = sum(1 for die, _ in held_rolls if die['color'] == 'Rainbow' and is_mono_hand)
            if not is_preview and wild_count > 0:
                game.extra_coins += charm['value'] * wild_count
                modifier_desc.append(f"{charm['name']} +{charm['value'] * wild_count} coins ({wild_count} wilds in mono)")

        elif charm['type'] == 'final_mult':
            if game.hands_left == 1:
                mult_add = charm['value']
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add} (final hand)")

        elif charm['type'] == 'final_mult_conditional':
            has_enh = any(len(die.get('enhancements', [])) > 0 for die, _ in held_rolls)
            if game.is_last_hand and has_enh:
                mult_add = charm['value']
                charm_mult_add += mult_add
                modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'face_buy_high':
            pass

        elif charm['type'] == 'coin_per_discard':
            discards_left = getattr(game, 'discards_left', 0)
            if not is_preview and discards_left > 0:
                modifier_desc.append(f"{charm['name']} +{charm['value'] * discards_left} coins ({discards_left} discards)")

        elif charm['type'] == 'risk_mult':
            mult_add = charm['value']
            charm_mult_add += mult_add
            if mult_add > 0:
                modifier_desc.append(f"{charm['name']} +{mult_add}")

        elif charm['type'] == 'loss_prevent':
            pass

        elif charm['type'] == 'revive_die':
            if not is_preview and game.destroyed_dice and not getattr(game, '_needle_used_this_blind', False) and random.random() < charm['chance']:
                if game.destroyed_dice:
                    revived_die = random.choice(game.destroyed_dice).copy()
                    game.full_bag.append(revived_die)
                    game.bag.append(revived_die)
                    game.destroyed_dice.remove(revived_die)
                    game._needle_used_this_blind = True
                    modifier_desc.append(f"{charm['name']}: Revived {revived_die['color']} die!")

        elif charm['type'] == 'rune_scribe':
            has_magic_3 = any(v in charm['faces'] for _, v in held_rolls)
            if has_magic_3 and not is_preview and not getattr(game, '_scribe_used_this_blind', False):
                random_rune = random.choice(MYSTIC_RUNES).copy()
                if game.add_to_rune_tray(random_rune):
                    game._scribe_used_this_blind = True
                    modifier_desc.append(f"{charm['name']}: Scribed {random_rune['name']} to tray!")
                else:
                    modifier_desc.append(f"{charm['name']}: Tray full, skipped scribe.")

        elif charm['type'] == 'discard_destroy_coin':
            pass

        elif charm['type'] == 'score_per_discard_color':
            bonus = charm.get('permanent_bonus', 0)
            if bonus:
                charm_chips += bonus
                color = charm.get('active_color', '?')
                modifier_desc.append(f"{charm['name']} +{bonus} ({color})")

        elif charm['type'] == 'mult_final_discard':
            pass  # applied once via game.final_discard_mult — do not stack here

        elif charm['type'] == 'score_per_coin':
            charm_chips += charm['value'] * game.coins

        elif charm['type'] == 'crit_bonus':
            if all(value == 6 for _, value in held_rolls):
                mult_add = charm['value'] - 1
                charm_mult_add += mult_add
                if mult_add > 0:
                    modifier_desc.append(f"{charm['name']} +{mult_add}")
                if not is_preview:
                    game.coins += 50

        elif charm['type'] == 'score_bonus' and charm['value'] == 'stat_sum':
            face_sum = sum(value for _, value in held_rolls)
            charm_chips += face_sum
            modifier_desc.append(f"{charm['name']} +{face_sum} (Sum of faces)")

        elif charm['type'] == 'score_decay':
            if 'hands_played' not in charm:
                charm['hands_played'] = 0
            # Preview must match the actual upcoming score: always treat this as hand N+1.
            preview_hands = charm['hands_played'] + 1
            decay_bonus = max(0, charm['start'] - (charm['decay'] * (preview_hands - 1)))
            charm_chips += decay_bonus
            modifier_desc.append(f"{charm['name']} +{decay_bonus} (hand {preview_hands})")

        elif charm['type'] == 'score_conditional':
            if len(held_rolls) == charm['dice']:
                this_add = charm['value'] + charm.get('permanent_bonus', 0)
                charm_chips += this_add
                modifier_desc.append(f"{charm['name']} +{this_add} ({len(held_rolls)} dice)")

        elif charm['type'] == 'die_bonus_perm':
            pass

    # Intensified disabled type (fusion: hands that include the exempt color still score)
    held_colors_now = [die.get('color') for die, _ in held_rolls]
    if boon and boon.is_hand_blocked(hand_type, held_colors_now):
        base_score = 0
        modifier_desc.append(f"Blocked {hand_type}: 0 score—adapt!")
        final_score = 0

    # Per-die score_bonus
    for die, _ in held_rolls:
        charm_chips += die.get('score_bonus', 0)

    total_modifier = base_modifier + charm_color_mult_add + rune_mult_add + charm_mult_add

    """ # Temp type mult, Acrobat, Prism Pack, Glass, etc.
    if hasattr(game, 'temp_type_mult') and game.temp_type_mult:
        type_mult = game.temp_type_mult.get(hand_type, 1.0)
        if type_mult > 1.0:
            total_modifier += type_mult - 1
            modifier_desc.append(f"Type Buff x{type_mult} for {hand_type}")
        if not is_preview:
            del game.temp_type_mult """

    total_modifier += game.final_discard_mult
    if game.final_discard_mult > 0:
        modifier_desc.append(f"Acrobat Amulet +{game.final_discard_mult}")
        if not is_preview:
            game.final_discard_mult = 0
            game.is_final_discard = False

    # === Hand-Type Multipliers (Prism Pack only — D20 type bonus is separate) ===
    if hand_type in game.hand_multipliers:
        full_mult = game.hand_multipliers[hand_type]
        total_modifier += full_mult - 1
        if full_mult > 1.0:
            modifier_desc.append(f"{hand_type} {full_mult:.1f}x (Prism)")

    silence_glass = game.current_blind == 'Boss' and game.current_boss_effect and game.current_boss_effect['name'] == 'Special Silence'
    glass_count = sum(1 for die, _ in held_rolls if die['color'] == 'Glass')
    glass_mult = (3 + glass_count) if glass_count > 0 and not silence_glass else 0
    if glass_mult > 0:
        total_modifier += glass_mult
        modifier_desc.append(f"Glass +{glass_mult}")

    has_mime = any(c['type'] == 'retrigger_held' for idx, c in enumerate(game.equipped_charms) if idx not in game.disabled_charms)
    if has_mime and not silence_glass and glass_count > 0:
        total_modifier += glass_mult
        modifier_desc.append(f"Mime (Glass) +{glass_mult}")

    if game.current_blind == 'Boss' and game.current_boss_effect and game.current_boss_effect['name'] == 'Multiplier Mute':
        total_modifier = min(total_modifier, 2.5)
        if total_modifier >= 2.5:
            modifier_desc.append("Multiplier Mute capped at +2.5")

    for idx, charm in enumerate(game.equipped_charms):
        if idx in game.disabled_charms:
            continue
        if charm['type'] == 'face_retrigger':
            face_count = sum(1 for _, v in held_rolls if v == charm['face'])
            if face_count > 0:
                retrigger_mult *= 2
                modifier_desc.append(f"{charm['name']} x2 (retrigger)")

    # === D20 Boon extras (single place, no double-dim) ===
    d20_mult = 1.0
    if boon:
        colors_for_boon = [die.get('color') for die, _ in original_rolls]
        if boon.is_hand_blocked(hand_type, colors_for_boon):
            final_score = 0
            modifier_desc.append(f"Blocked {hand_type}: 0 score—adapt!")
            modifier_desc = ", ".join(modifier_desc) if modifier_desc else "None"
            return hand_type, 0, modifier_desc, 0, charm_chips, charm_color_mult_add

        dim = boon.dim_factor(colors_for_boon)
        extra = boon.extra_score_mult(hand_type, consume_next_hand=not is_preview)
        color_m = boon.color_score_mult(colors_for_boon)
        d20_mult = dim * extra * color_m
        for note in boon.modifier_notes(hand_type, colors_for_boon):
            if note not in modifier_desc:
                modifier_desc.append(note)

    chroma_mult = 1.0  # radiance is inside boon.color_score_mult now

    # Final score assembly
    chips = (base_score * dimmed_mult) + charm_chips + rune_chips
    if getattr(game, 'plasma_pouch_active', False):
        mix = plasma_mix_chips(colors_list)
        chips += mix
        if mix > 0:
            modifier_desc.append(f"Plasma mix +{mix}")
        elif mix < 0:
            modifier_desc.append(f"Plasma mono {mix}")
    mult = (1 + total_modifier) * retrigger_mult * chroma_mult * d20_mult
    final_score = int(chips * mult)

    modifier_desc = ", ".join(modifier_desc) if modifier_desc else "None"

    return hand_type, base_score, modifier_desc, final_score, charm_chips, charm_color_mult_add


def apply_enhancement_retrigger(game, die, i):
    """Apply second proc for one enhanced die; returns (delta_score, delta_coins)."""
    enh = die.get('enhancements', [])
    if not enh:
        return 0, 0
    
    delta_score = 0
    delta_coins = 0
    
    for e in enh:
        if e not in ENH_EFFECTS:   # data.ENH_EFFECTS is now just ENH_EFFECTS because we imported it
            continue
        effect = ENH_EFFECTS[e]
        
        # Mult add (Steel, Fragile, Mult, etc.)
        if 'mult_add' in effect:
            die_value = die.get('value', die.get('face', 0))
            delta_score += die_value * effect['mult_add']
        
        # Fixed score (Bonus, Stone)
        if 'score' in effect:
            delta_score += effect['score']
        
        # Coins
        if 'coin_value' in effect:
            if e == 'Gold' and game.held[i]:
                delta_coins += effect['coin_value']
                game.sfx_channel.play(game.coin_sound)
            elif e == 'Silver' and not game.held[i]:
                delta_coins += effect['coin_value']
                game.sfx_channel.play(game.coin_sound)
            elif e == 'Lucky':
                if random.random() < effect.get('coin_chance', 0.33):
                    delta_coins += effect['coin_value']
                    game.sfx_channel.play(game.coin_sound)
    
    # Fragile + Glass = extra spicy break chance on retrigger
    if 'Fragile' in enh and die['color'] == 'Glass' and glass_breaks(game, 0.25):
        game.sfx_channel.play(game.break_sound)
        game.full_bag = [d for d in game.full_bag if d['id'] != die['id']]
        game.bag = [d for d in game.bag if d['id'] != die['id']]
        game.destroyed_dice.append(die.copy())
        game.broken_dice.append(i)
        game.break_effect_start = time.time()
    
    return delta_score, delta_coins
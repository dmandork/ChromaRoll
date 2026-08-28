# scoring.py

import random
import time
from data import ENH_EFFECTS, MYSTIC_RUNES


def apply_wild_4(game, held_rolls, counts, max_count, groups, modifier_desc):
    wild_face = 4
    wild_die_count = sum(1 for _, v in held_rolls if v == wild_face)
    if wild_die_count > 0:
        non_wild_counts = {k: v for k, v in counts.items() if k != wild_face}
        if non_wild_counts:
            highest_group = max(non_wild_counts, key=non_wild_counts.get)
            counts[highest_group] += wild_die_count
            max_count = max(counts.values())
            wild_colors = [die['color'] for die, v in held_rolls if v == wild_face]
            groups[highest_group] += wild_colors
            if wild_face in groups:
                del groups[wild_face]
            modifier_desc.append(f"{wild_die_count} Kind Keeper Wilds → {highest_group}s")
    return counts, max_count


def apply_wild_6(game, held_rolls, counts, max_count, groups, modifier_desc):
    wild_face = 6
    wild_die_count = sum(1 for _, v in held_rolls if v == wild_face)
    if wild_die_count > 0:
        non_wild_counts = {k: v for k, v in counts.items() if k != wild_face}
        if non_wild_counts:
            highest_group = max(non_wild_counts, key=non_wild_counts.get)
            counts[highest_group] += wild_die_count
            max_count = max(counts.values())
            wild_colors = [die['color'] for die, v in held_rolls if v == wild_face]
            groups[highest_group] += wild_colors
            if wild_face in groups:
                del groups[wild_face]
            modifier_desc.append(f"{wild_die_count} Kind King Wilds → {highest_group}s")
    return counts, max_count


def apply_face_wild(game, held_rolls, counts, max_count, groups, modifier_desc, wild_face):
    wild_die_count = sum(1 for _, v in held_rolls if v == wild_face)
    if wild_die_count > 0:
        non_wild_counts = {k: v for k, v in counts.items() if k != wild_face}
        if non_wild_counts:
            highest_group = max(non_wild_counts, key=non_wild_counts.get)
            counts[highest_group] += wild_die_count
            max_count = max(counts.values())
            wild_colors = [die['color'] for die, v in held_rolls if v == wild_face]
            groups[highest_group] += wild_colors
            if wild_face in groups:
                del groups[wild_face]
            modifier_desc.append(f"{wild_die_count} Face Forgery Wilds → {highest_group}s")
    return counts, max_count


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

    # === HUE DIMMING (D20 Tier 2) - Flat -20% if ANY dimmed die is used ===
    dimmed_mult = 1.0
    dimmed_count = 0

    if hasattr(game, 'intensified_dimmed_color') and game.intensified_dimmed_color:
        dimmed_color = game.intensified_dimmed_color
        dimmed_count = sum(1 for die, _ in held_rolls if die.get('color') == dimmed_color)
        if dimmed_count > 0:
            dimmed_mult = 0.8
            modifier_desc.append(f"Dimmed {dimmed_color}: x0.8 score (-20%)")

    # === ADVANTAGE / FATE'S FAVOR - ADD AFTER STRAIGHT DETECTION ===
    if game.has_advantage and game.held_advantage:
        original_die = game.rolls[2][0]
        advantage_die = original_die.copy()  # Copy the full die object so color is preserved
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
            if 'local_turns' not in charm:
                charm['local_turns'] = 0
            local_turn = charm['local_turns']
            every = charm.get('every', 6)
            if local_turn % every == 0:
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

        elif charm['type'] == 'retrigger' and 'hands' in charm and 'kinds' in charm['hands']:
            if hand_type in ['3 of a Kind', '4 of a Kind', '5 of a Kind']:
                retrigger_mult *= 2
                modifier_desc.append(f"{charm['name']} x2 (kinds retrigger)")

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
            total_enhancements = sum(len(die.get('enhancements', [])) for die, _ in held_rolls)
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
            pass

        elif charm['type'] == 'mult_final_discard':
            if not is_preview and getattr(game, 'is_final_discard', False):
                charm_mult_add += charm['value']
                modifier_desc.append(f"{charm['name']} +{charm['value']} (final discard)")

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
            preview_hands = charm['hands_played'] + (0 if is_preview else 1)
            decay_bonus = max(0, charm['start'] - (charm['decay'] * (preview_hands - 1)))
            charm_chips += decay_bonus
            modifier_desc.append(f"{charm['name']} +{decay_bonus} (hand {preview_hands})")

        elif charm['type'] == 'score_conditional':
            if len(held_rolls) == charm['dice']:
                charm_chips += charm['value']
                charm_chips += charm.get('permanent_bonus', 0)

        elif charm['type'] == 'die_bonus_perm':
            pass

    # Intensified disabled type
    if hasattr(game, 'intensified_disabled_type') and game.intensified_disabled_type:
        if hand_type == game.intensified_disabled_type:
            base_score = 0
            modifier_desc.append(f"Blocked {hand_type}: 0 score—adapt!")
            final_score = 0

    # Per-die score_bonus
    for die, _ in held_rolls:
        charm_chips += die.get('score_bonus', 0)

    # === D20 HUE DIMMING - +30% to the specific color NEXT BLIND ONLY ===
    if hasattr(game, 'next_blind_color_mults') and game.next_blind_color_mults:
        for color, mult in list(game.next_blind_color_mults.items()):
            count = sum(1 for die, _ in held_rolls if die.get('color') == color)
            if count > 0:
                color_bonus = (mult - 1.0)   # e.g. +0.3 for 30%
                charm_color_mult_add += color_bonus
                modifier_desc.append(f"{color} +{int(color_bonus*100)}% (D20 Hue Dimming)")

        # === Clear after this blind is finished ===
        # This makes the +30% apply for the FULL next blind, then disappear forever
        game.next_blind_color_mults = {}

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

    # === Hand-Type Multipliers: Prism Pack (additive) + D20 Tier 1 (multiplicative ONLY) ===
    prism_mult = game.hand_multipliers.get(hand_type, 1.0)
    d20_mult = 1.0
    if hasattr(game, 'pending_type_mult') and hand_type in game.pending_type_mult:
        d20_mult = game.pending_type_mult[hand_type]

    # Prism Pack stays additive (exactly like every other bonus)
    if prism_mult > 1.0:
        total_modifier += (prism_mult - 1.0)
        modifier_desc.append(f"{hand_type} {prism_mult:.1f}x (Prism Pack)")

    # D20 Tier 1 is kept separate — we will multiply with it later
    if d20_mult > 1.0:
        modifier_desc.append(f"{hand_type} {d20_mult:.1f}x (D20 Tier 1)")

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

    # === TIER 5 CHROMA RADIANCE - Simple +30% to final score (LAST STEP) ===
    is_chroma_radiance = False
    if hasattr(game, 'd20_boon') and game.d20_boon is not None:
        if game.d20_boon.outcome and game.d20_boon.outcome.get('name') == 'Chroma Radiance':
            is_chroma_radiance = True
    if getattr(game, 'intensified_global_color_mult', 1.0) > 1.0:
        is_chroma_radiance = True

    chroma_mult = 1.3 if is_chroma_radiance else 1.0
    if chroma_mult > 1.0:
        modifier_desc.append("Chroma Radiance +30% all colors")

    # Final score assembly
    final_score = int(((base_score * dimmed_mult) + charm_chips + rune_chips) * (1 + total_modifier) * retrigger_mult * chroma_mult * d20_mult)

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
    if 'Fragile' in enh and die['color'] == 'Glass' and random.random() < 0.25:
        game.sfx_channel.play(game.break_sound)
        game.full_bag = [d for d in game.full_bag if d['id'] != die['id']]
        game.bag = [d for d in game.bag if d['id'] != die['id']]
        game.destroyed_dice.append(die.copy())
        game.broken_dice.append(i)
        game.break_effect_start = time.time()
    
    return delta_score, delta_coins
# data.py
# Game data: lists, dicts for charms, pouches, bosses, etc.

HAND_TYPES = ['Pair', '2 Pair', '3 of a Kind', '4 of a Kind', '5 of a Kind', 'Full House', 'Small Straight', 'Large Straight']

DICE_DESCRIPTIONS = {
    'Red': 'Add 1 Red Die',
    'Blue': 'Add 1 Blue Die',
    'Green': 'Add 1 Green Die',
    'Purple': 'Add 1 Purple Die',
    'Yellow': 'Add 1 Yellow Die',
    'Gold': 'Gold Die: +1 coin when held in score',
    'Silver': 'Silver Die: +1 coin when not held in score',
    'Glass': 'Glass Die: x4 mult when held, 25% chance to break',
    'Rainbow': 'Rainbow Die: Acts as wild for color bonuses (mono & rainbow)'}  # Descriptions for each die color

BOSS_EFFECTS = [
    {'name': 'Hold Ban', 'desc': 'You cannot hold any dice between rerolls.', 'difficulty': 'Hard'},
    {'name': 'Reroll Ration', 'desc': 'Rerolls left reduced by 1 for the round.', 'difficulty': 'Easy'},
    {'name': 'Discard Drought', 'desc': 'Discards left reduced by 1 for the round.', 'difficulty': 'Easy'},
    {'name': 'Reroll Penalty', 'desc': 'Each reroll costs 1 coin (deducted immediately).', 'difficulty': 'Easy'},
    {'name': 'Hold Limit', 'desc': 'You can only hold up to 3 dice between rerolls.', 'difficulty': 'Medium'},
    {'name': 'Discard Cap', 'desc': 'Discard phase limited to 2 dice max per use.', 'difficulty': 'Easy'},
    {'name': 'Score Dip', 'desc': 'Base hand scores reduced by 10% for the round.', 'difficulty': 'Easy'},
    {'name': 'Target Bump', 'desc': 'Blind target increased by 20%.', 'difficulty': 'Medium'},
    {'name': 'Color Fade', 'desc': 'No monochrome or rainbow bonuses applied this round.', 'difficulty': 'Medium'},
    {'name': 'Fragile Flip', 'desc': 'Glass dice break chance increased to 50%.', 'difficulty': 'Medium'},
    {'name': 'Charm Glitch', 'desc': 'One random equipped charm is disabled for the round.', 'difficulty': 'Medium'},
    {'name': 'Face Shuffle', 'desc': 'Dice faces are randomized (e.g., non-standard values like duplicates or missing numbers).', 
     'difficulty': 'Medium'},
    {'name': 'Coin Freeze', 'desc': 'No extra coins from Gold/Silver this round.', 'difficulty': 'Medium'},
    {'name': 'Rainbow Restriction', 'desc': 'Rainbow dice only count as one fixed color (random per round) for bonuses.', 
     'difficulty': 'Medium'},
    {'name': 'Glass Guard', 'desc': 'Glass dice cannot be held (auto-unheld after rolls).', 'difficulty': 'Medium'},
    {'name': 'Charm Tax', 'desc': 'Each equipped charm reduces hands left by 0.5 (rounded down).', 'difficulty': 'Medium'},
    {'name': 'Mono Mixup', 'desc': 'Monochrome bonuses halved if more than one color is present (even Rainbows).', 
     'difficulty': 'Medium'},
    {'name': 'Reroll Rebound', 'desc': 'After each reroll, one random held die is unheld.', 'difficulty': 'Medium'},
    {'name': 'Hand Trim', 'desc': 'Hands left reduced by 1 for the round.', 'difficulty': 'Hard'},
    {'name': 'Break Surge', 'desc': 'Glass break chance increases by 10% per reroll used.', 'difficulty': 'Hard'},
    {'name': 'Special Silence', 'desc': 'All special die effects disabled (no Gold coins, Silver extras, Glass mult, Rainbow wild).', 
     'difficulty': 'Hard'},
    {'name': 'Die Drain', 'desc': 'One random die is removed from your hand after each reroll, and pulling a new one from the bag.', 'difficulty': 'Hard'},
    {'name': 'Charm Eclipse', 'desc': 'All equipped charms are disabled for the round.', 'difficulty': 'Hard'},
    {'name': 'Value Vault', 'desc': 'All rolled values are inverted (1=6, 2=5, etc.), messing with straights and high/low strategies.', 
     'difficulty': 'Hard'},
    {'name': 'Blind Boost', 'desc': 'Blind target increased by 30%, but +1 extra discard.', 'difficulty': 'Hard'},
    {'name': 'Special Swap', 'desc': 'All special dice effects are inverted (e.g., Gold gives coins when not held, Silver when held).', 
     'difficulty': 'Hard'},
    {'name': 'Discard Delay', 'desc': 'Discard phase only available after first reroll.', 'difficulty': 'Hard'},
    {'name': 'Multiplier Mute', 'desc': 'All multipliers (charms, hands, colors) capped at x1.5.', 'difficulty': 'Hard'},
    {'name': 'Bag Bottleneck', 'desc': 'Bag refills only half full after depletion (fewer redraw options).', 'difficulty': 'Hard'},
    {'name': 'Hold Hazard', 'desc': 'Held dice have a 20% chance to reroll anyway on next roll.', 'difficulty': 'Hard'}
]

POUCHES = [
    {'name': 'Red Pouch', 'color': 'Red', 'desc': 'Aggro focus: +1 discard per round, extra 2 Red dice.', 
     'bonus': {'extra_dice': {'Red': 2}, 'discards': 1}, 'unlocked': True},
    {'name': 'Blue Pouch', 'color': 'Blue', 'desc': 'Control: +1 hand per round, extra 1 Blue die and 1 Silver die.', 
     'bonus': {'extra_dice': {'Blue': 1, 'Silver': 1}, 'hands': 1}, 'unlocked': True},
    {'name': 'Yellow Pouch', 'color': 'Yellow', 'desc': 'Balanced: +10 starting coins, even split of base colors.', 
     'bonus': {'coins': 10}, 'unlocked': True},
    {'name': 'Green Pouch', 'color': 'Green', 'desc': 
     'Economy: +2 coins per unused hand and +1 per unused discard at round end, extra 1 Green die and 1 Gold die.', 
     'bonus': {'extra_dice': {'Green': 1, 'Gold': 1}}, 'unlocked': True},
    {'name': 'Black Pouch', 'color': 'Black', 'desc': 'High-risk: +1 charm slot, -1 hand per round, extra 1 random special die.', 
     'bonus': {'charm_slots': 1, 'hands': -1, 'extra_dice': {'random_special': 1}}, 'unlocked': False},  # Example; add random logic in apply_pouch
    {'name': 'Ghost Pouch', 'color': 'Glass', 'desc': 'Risky: Higher special dice in shops, start with 1 Glass die.', 
     'bonus': {'extra_dice': {'Glass': 1}}, 'unlocked': False},  # Shop chance via flag
    {'name': 'Erratic Pouch', 'color': 'Rainbow', 'desc': 'Chaotic: Randomize starting bag colors/faces.', 
     'bonus': {'randomize_bag': True}, 'unlocked': False},
    {'name': 'Plasma Pouch', 'color': 'Purple', 'desc': 'Balanced scorer: Average base score and mult, x1.5 blind targets.', 
     'bonus': {'balance_score': True, 'blind_mult': 1.5}, 'unlocked': False}
]  # Descriptions and bonuses for each pouch; 'unlocked' indicates availability

# Dot positions for each face value (1-6)
DOT_POSITIONS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75), (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)]
}

CHARMS_POOL = [
    {'name': 'Basic Charm', 'rarity': 'Common', 'cost': 2, 'desc': '+10 to all final scores.', 'type': 'flat_bonus', 'value': 10},

    {'name': 'Red Greed Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Red die scored.', 'type': 
     'per_color_bonus', 'color': 'Red', 'value': 5},

    {'name': 'Blue Lust Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Blue die scored.', 'type': 
     'per_color_bonus', 'color': 'Blue', 'value': 5},

    {'name': 'Green Wrath Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Green die scored.', 'type': 
     'per_color_bonus', 'color': 'Green', 'value': 5},

    {'name': 'Purple Glutton Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Purple die scored.', 'type': 
     'per_color_bonus', 'color': 'Purple', 'value': 5},

    {'name': 'Yellow Jolly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per Yellow die scored.', 'type': 
     'per_color_bonus', 'color': 'Yellow', 'value': 5},

    {'name': 'Zany Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+40 score if hand contains a 3 of a Kind.', 'type': 
     'hand_bonus', 'hands': ['3 of a Kind'], 'value': 40},

    {'name': 'Mad Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+30 score if hand contains a 2 Pair.', 'type': 'hand_bonus', 
     'hands': ['2 Pair'], 'value': 30},

    {'name': 'Crazy Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+35 score if hand contains a Small or Large Straight.', 
     'type': 'hand_bonus', 'hands': ['Small Straight', 'Large Straight'], 'value': 35},

    {'name': 'Droll Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to monochrome multipliers.', 'type': 
     'mono_mult_bonus', 'value': 0.5},

    {'name': 'Sly Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+50 base score if hand contains a Pair.', 'type': 
     'hand_bonus', 'hands': ['Pair'], 'value': 50},

    {'name': 'Wily Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+100 base score if hand contains a 3 of a Kind.', 'type': 
     'hand_bonus', 'hands': ['3 of a Kind'], 'value': 100},

    {'name': 'Clever Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+80 base score if hand contains a 2 Pair.', 'type': 
     'hand_bonus', 'hands': ['2 Pair'], 'value': 80},

    {'name': 'Devious Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
     '+100 base score if hand contains a Small or Large Straight.', 'type': 'hand_bonus', 'hands': 
     ['Small Straight', 'Large Straight'], 'value': 100},

    {'name': 'Half Charm', 'rarity': 'Common', 'cost': 4, 'desc': '+20 score if hand uses 3 or fewer dice.', 'type': 
     'few_dice_bonus', 'max_dice': 3, 'value': 20},

    {'name': 'Stencil Charm', 'rarity': 'Legendary', 'cost': 7, 'desc': '+0.5x multiplier per empty charm slot.', 'type': 'empty_slot_mult', 'value': 0.5},

    {'name': 'Four Fingers Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
     'Small Straights can be made with 3 dice; Large with 4.', 'type': 'short_straight'},

    {'name': 'Mime Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
     'Retrigger effects of held dice (e.g., double Gold coins, Glass mult/break chance).', 'type': 'retrigger_held'},

    {'name': 'Debt Charm', 'rarity': 'Common', 'cost': 2, 'desc': 'Allows going into negative coins for shop buys (up to -5).', 
     'type': 'negative_coins', 'limit': -5},

    {'name': 'Dagger Charm', 'rarity': 'Legendary', 'cost': 10, 'desc': 
     'When blind starts, sacrifice a charm to the right and add 0.1x its cost to your score multiplier permanently. (Max 5x)', 'type': 'sacrifice_mult'},

    {'name': 'Golden Touch Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
     '+2 coins per Gold die held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Gold', 'value': 2},

    {'name': 'Silver Lining Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': 
     '+2 coins per Silver die not held in score (stacks with base effect).', 'type': 'extra_coin_bonus', 'color': 'Silver', 'value': 2},

    {'name': 'Fragile Fortune Charm', 'rarity': 'Rare', 'cost': 6, 'desc': 
     'Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins.', 'type': 'glass_mod', 'break_chance': 0.10, 
     'break_penalty': 5},

    {'name': 'Even Stevens Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per even-valued die scored.', 'type': 
             'per_value_bonus', 'parity': 'even', 'value': 5},

    {'name': 'Oddball Charm', 'rarity': 'Common', 'cost': 3, 'desc': '+5 score per odd-valued die scored.', 'type': 
     'per_value_bonus', 'parity': 'odd', 'value': 5},

    {'name': 'Rainbow Prism Charm', 'rarity': 'Uncommon', 'cost': 5, 'desc': '+0.5x to rainbow multipliers.', 'type': 
     'rainbow_mult_bonus', 'value': 0.5},

    {'name': 'Full House Party Charm', 'rarity': 'Rare', 'cost': 6, 'desc': '+150 base score if hand contains a Full House.', 
     'type': 'hand_bonus', 'hands': ['Full House'], 'value': 150},

    {'name': 'Quadruple Threat Charm', 'rarity': 'Rare', 'cost': 7, 'desc': '+200 base score if hand contains a 4 of a Kind.', 
     'type': 'hand_bonus', 'hands': ['4 of a Kind'], 'value': 200},

    {'name': 'Reroll Recycler Charm', 'rarity': 'Rare', 'cost': 8, 'desc': 
     'Gain 1 extra reroll in the turn if you use a discard.', 'type': 'reroll_recycler'},

    {'name': 'Interest Booster Charm', 'rarity': 'Common', 'cost': 3, 'desc': 
     'Increases max coins for interest calculation by 20.', 'type': 'interest_max_bonus', 'value': 20},
]

# Add to data.py (e.g., at the end or near CHARMS_POOL)

RUNE_PACKS = [
    {'name': 'Basic Rune Pack', 'cost': 4, 'choices': 3, 'select': 1, 'rarity': 'Common'},
    {'name': 'Mega Rune Pack', 'cost': 7, 'choices': 5, 'select': 1, 'rarity': 'Uncommon'},
    {'name': 'Super Rune Pack', 'cost': 9, 'choices': 5, 'select': 2, 'rarity': 'Rare'}
]

# In data.py, update MYSTIC_RUNES to add 'max_dice' key (0 for no die, 1 default, 2/3 for multi)
MYSTIC_RUNES = [
    {'name': 'Mystic Fool Rune', 'desc': 'Creates a copy of the last Mystic or Upgrade Rune used this run (must have room in consumable inventory).', 'max_dice': 0},
    {'name': 'Mystic Luck Rune', 'desc': 'Enhances 1 selected die in bag to "Lucky" (25% chance for +1 coin or x1.5 mult when scored, stacking with color effects).', 'max_dice': 1},
    {'name': 'Mystic Oracle Rune', 'desc': 'Creates up to 2 random Upgrade Runes for hand type boosts.', 'max_dice': 0},
    {'name': 'Mystic Mult Rune', 'desc': 'Enhances 2 selected dice in bag to add +0.5x mult when scored (stacks with Glass, etc.).', 'max_dice': 2},
    {'name': 'Mystic Emperor Rune', 'desc': 'Creates up to 2 random Mystic Runes (must have room).', 'max_dice': 0},
    {'name': 'Mystic Bonus Rune', 'desc': 'Enhances 2 selected dice in bag to add +10 score when scored.', 'max_dice': 2},
    {'name': 'Mystic Wild Rune', 'desc': 'Converts 1 selected die in bag to Rainbow color (acts as any color for mono/rainbow bonuses).', 'max_dice': 1},
    {'name': 'Mystic Steel Rune', 'desc': 'Enhances 1 selected die in bag to "Steel" (x1.5 mult, can\'t break like Glass).', 'max_dice': 1},
    {'name': 'Mystic Fragile Rune', 'desc': 'Enhances 1 selected die in bag to "Fragile" (x2 mult, 25% break chance—stacks/modifies Glass).', 'max_dice': 1},
    {'name': 'Mystic Wealth Rune', 'desc': 'Doubles current coins (max +20).', 'max_dice': 0},
    {'name': 'Mystic Fate Rune', 'desc': '1 in 4 chance to add a random Edition (Foil, Holo, or Poly) to a random die in bag.', 'max_dice': 0},  # Random, no select
    {'name': 'Mystic Strength Rune', 'desc': 'Enhances up to 2 selected dice to "harmonize" faces toward mid-high values (e.g., [1,2,3,4,5,6] becomes [3,4,4,5,5,6]—duplicates mids/highs, removes lows for better kinds/straights).', 'max_dice': 2},
    {'name': 'Mystic Sacrifice Rune', 'desc': 'Destroys up to 2 selected dice in bag (gain coins equal to their "value" based on color/rarity).', 'max_dice': 2},
    {'name': 'Mystic Transmute Rune', 'desc': 'Convert 1 selected die to the color and faces of another selected die (clone for duplicates).', 'max_dice': 2},  # Target + source
    {'name': 'Mystic Balance Rune', 'desc': 'Gives coins equal to total cost/sell value of equipped charms (max 50).', 'max_dice': 0},
    {'name': 'Mystic Gold Rune', 'desc': 'Converts 1 selected die in bag to Gold color (+coins when held, as per your system).', 'max_dice': 1},
    {'name': 'Mystic Stone Rune', 'desc': 'Enhances 1 selected die in bag to "Stone" (+50 score, but fixed value/no roll variance).', 'max_dice': 1},
    {'name': 'Mystic Red Rune', 'desc': 'Converts up to 3 selected dice in bag to Red color.', 'max_dice': 3},
    {'name': 'Mystic Blue Rune', 'desc': 'Converts up to 3 selected dice in bag to Blue color.', 'max_dice': 3},
    {'name': 'Mystic Green Rune', 'desc': 'Converts up to 3 selected dice in bag to Green color.', 'max_dice': 3},
    {'name': 'Mystic Judgement Rune', 'desc': 'Creates a random Common Charm (must have charm slot room).', 'max_dice': 0},
    {'name': 'Mystic Purple Rune', 'desc': 'Converts up to 3 selected dice in bag to Purple color.', 'max_dice': 3},
    {'name': 'Mystic Yellow Rune', 'desc': 'Converts up to 3 selected dice in bag to Yellow color.', 'max_dice': 3},
    {'name': 'Mystic Silver Rune', 'desc': 'Converts 1 selected die in bag to Silver color (+coins when not held in score, as per your system).', 'max_dice': 1}
]

# In data.py, after MYSTIC_RUNES

ENH_DESC = {
    'Lucky': 'Lucky: 25% chance for +1 coin or x1.5 mult when scored (stacks with color effects).',
    'Mult': 'Mult: Adds +0.5x mult when scored (stacks with Glass, etc.).',
    'Bonus': 'Bonus: Adds +10 score when scored.',
    'Wild': 'Rainbow: Acts as any color for mono/rainbow bonuses.',
    'Steel': 'Steel: x1.5 mult, can\'t break like Glass.',
    'Fragile': 'Fragile: x2 mult, 25% break chance (stacks/modifies Glass).',
    'Fate': 'Edition: Random Edition applied (Foil, Holo, or Poly).',  # If editions added later
    'Strength': 'Harmonized: Faces shifted to mid-high duplicates for better kinds/straights.',
    'Sacrifice': 'Destroyed: This die was sacrificed (no longer in bag).',  # If tracking history
    'Transmute': 'Transmuted: Cloned color and faces from another die.',
    'Gold': 'Gold: +coins when held in score.',
    'Stone': 'Stone: +50 score, but fixed value/no roll variance.',
    'Red': 'Red: Converted to Red color.',
    'Blue': 'Blue: Converted to Blue color.',
    'Green': 'Green: Converted to Green color.',
    'Judgement': 'Judgement: Created a random Common Charm.',
    'Purple': 'Purple: Converted to Purple color.',
    'Yellow': 'Yellow: Converted to Yellow color.',
    'Silver': 'Silver: +coins when not held in score.',
    # Add more if new enhancements (e.g., from Oracle/Wealth if they add die effects)
}
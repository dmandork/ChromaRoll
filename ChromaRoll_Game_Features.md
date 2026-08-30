# ChromaRoll — Complete Game Features Reference

_Generated from the live codebase (Passes A–D). This is a player-and-designer reference, not a marketing sheet. Numbers, costs, and effect text match `data.py`, `d20_boon.py`, `scoring.py`, and the current shop/play UI._

**Snapshot**

| | |
|---|---|
| Genre | Roguelike dice-poker (Balatro × Yahtzee) |
| Engine | Python / Pygame, 1024×600, 60 FPS |
| Charms in pool | 105 (Common 31 / Uncommon 36 / Rare 24 / Legendary 14) |
| Pouches | 8 (4 unlocked by default, 4 gated) |
| Boss effects | 30 |
| Mystic runes | 24 |
| Stakes | 8 (+ optional Endless) |
| Blinds per stake | Small → Big → Boss |
| Base hands / discards / rerolls | 4 / 3 / 2 |
| Starting bag | 25 dice (5 of each base color) |
| Charm slots | 5 (Black Pouch +1) |
| Rune tray | 2 slots |

## Table of contents

1. [What the game is](#1-what-the-game-is)
2. [A single run](#2-a-single-run)
3. [Scoring](#3-scoring)
4. [Screens](#4-screens)
5. [Dice](#5-dice)
6. [Pouches (starting bags)](#6-pouches-starting-bags)
7. [Charms](#7-charms)
8. [Shop packs](#8-shop-packs)
9. [Mystic runes and enhancements](#9-mystic-runes-and-enhancements)
10. [Boss effects](#10-boss-effects)
11. [D20 Boon System](#11-d20-boon-system)
12. [Economy](#12-economy)
13. [Save, pause, debug](#13-save-pause-debug)
14. [Glossary](#14-glossary)
15. [Work in progress](#15-work-in-progress)

---

## 1. What the game is

ChromaRoll is a single-player roguelike. Each **run** you pick a starting pouch, then fight through eight **stakes**. A stake is three **blinds** — Small, Big, then Boss — each with a score target. You form poker-style hands with five colored dice, hold and reroll, spend discards, and score. **Charms** modify scoring and economy. **Runes** enhance individual dice. **Prism packs** permanently boost a hand type. Optional **D20 Intensify** on a blind raises the target in exchange for a boon.

Beat the Stake 8 boss to win the run. You are then offered Endless Mode (escalating targets) or a return to the main menu.

Inspiration is openly Balatro (charms ≈ jokers, blinds, shop, packs) mixed with Yahtzee (five dice, holds, kinds and straights) plus a color layer (mono / rainbow bonuses, special dice).

## 2. A single run

### Loop

```
Splash → (optional Tutorial) → Pouch select
     → Blinds screen (preview boss, optional Intensify)
     → Play the blind (discard → roll/hold/reroll → score, repeat)
     → Win popup (coins, interest, leftover hands/discards)
     → Shop (charms, packs, sell, BAG toggle, Continue)
     → next blind / next stake
     → Stake 8 Boss win → End prompt (Endless or Menu)
```

Lose a blind with no Cloak of Cunning → Game Over. Cloak destroys itself and repeats the blind once per run.

### Resources each blind

| Resource | Base | Notes |
|---|---|---|
| Hands | 4 | Each score spends one. Hit the target before they run out. |
| Discards | 3 | Spend during the discard phase to replace dice from the bag. |
| Rerolls | 2 | After the first roll. Held dice keep their face. |
| Charm slots | 5 | Shop will not buy past the cap unless Debt Charm is covering coins. |
| Rune tray | 2 | Consumable mystic runes waiting to be applied. |

Pouch bonuses, Turtle Token, Burglar Bag, UNO Draw 2, Reroll Recycler, and D20 tiers modify these.

### Blinds and targets

Targets scale by stake (forgiving early, aggressive late). Small / Big / Boss use different base values, then stake scaling, then D20 `target_mult` if you Intensified. Endless (stake > 8) adds +15% per stake past 8.

The upcoming boss effect is rolled when you enter the blinds screen and previewed on the Boss box.

---

## 3. Scoring

A scored hand is **held dice only**. Unheld dice in the five-slot window are ignored for the hand type.

### Hand types

| Hand | Base chips | Detection |
|---|---|---|
| Nothing | 0 | No pair or better. Space Sphere will not upgrade this. |
| Pair | 20 | Two matching faces. |
| 2 Pair | 60 | Two different pairs. |
| 3 of a Kind | 80 | Three matching faces. |
| Full House | 160 | Three of a kind + a pair. |
| 4 of a Kind | 160 | Four matching faces. |
| 5 of a Kind | 250 | All five match. |
| Small Straight | (straight table) | Four sequential faces (1-2-3-4, 2-3-4-5, 3-4-5-6). Four Fingers: three sequential. |
| Large Straight | (straight table) | 1-2-3-4-5 or 2-3-4-5-6. Four Fingers: four sequential. |

### Color bonuses (the chroma layer)

Rainbow dice are wild for color. They do not break mono by themselves.

- **Monochrome** — remaining non-rainbow colors are a single color (or none). Adds a hand-type-scaled modifier (Pair +0.5 up to 5oak/Full House +3).
- **Rainbow (all-different)** — remaining non-rainbow colors are all unique. Similar modifier table.
- Full House can also get “Both Mono”, “One Mono”, or full mono/rainbow.

Charms such as Droll Charm, Rainbow Prism Charm, Flower Pot Prism, and Bardic Blade stack on top of this.

### Final score (simplified)

```
chips  = base_hand + charm_chips + rune Bonus/Stone + Hiker Hex + Square/Castle/Ice/Bull/Stat…
mult   = 1 + color_mods + charm_mults + prism_pack(hand_type) + Glass + Acrobat + D20 leftover
score  = chips × mult   (then D20 this-blind score_mult, if any)
```

Glass held in the hand adds a large mult and then rolls a **break chance** (25% base). Saving Throw can cancel a would-be break (d6, 4–6 lives). Fragile Fortune, Break Buffer, Fragile Flip, Break Surge, Special Silence, and Mime all modify this.

Prism packs permanently add +0.5x to a chosen hand type (`hand_multipliers`). Space Sphere has a 25% chance to do the same to the hand you just scored.

---

## 4. Screens

### Splash

Animated title pan/hold/zoom on the splash art. Buttons: **New Game**, **Load Game**, **Quit**. Space / Esc / Enter skip the animation. New Game goes to pouch select (or tutorial if not completed). Load restores `save.json` into the saved state (shop, blinds, play, etc.).

### Tutorial

Six steps (0–5) covering dice, holds, discards, scoring, shop, and blinds. Left / Right / Skip. Completing or skipping sets `tutorial_completed` and continues to pouch select.

### Pouch select (Init)

Choose one of eight pouches. Locked pouches (Black, Ghost, Erratic, Plasma) show but cannot be selected until unlocks exist. Confirming calls `apply_pouch` (hands/discards/coins/extra dice applied **once**) and goes to the blinds screen.

### Blinds

Three boxes: Small, Big, Boss. Current blind is highlighted. Each shows its score target. Boss shows the upcoming effect. **Intensify** (D20) sits beside **Continue** with a 24px gap (Pass C). Intensify opens the D20 roll screen. Continue / selecting the current blind enters play. Debug (if on): stake dropdown, jump-to-boss.

### Play (game)

Left column, top-down (Pass C layout):

1. Equipped charms (clickable — Fate’s Favor, Buy Boon, Disadvantage, Whirlwind, UNO Draw 2, Luchador, Familiar’s Foresight).
2. HUD: hand type preview, modifiers, score vs target, D20 leftover lines.
3. Five hand dice along the bottom. Click to hold (roll phase) or mark for discard (discard phase).
4. Buttons: Discard / Start Roll / Reroll / Score, depending on phase.

Top-right: **dice bag** (always visible here) and the two-slot **rune tray**. Hover a bag die with enhancements or Hiker Hex bonus for a tooltip. Hover a charm for name + desc + live values (no duplicated “Preview:” lines).

Win popup (520px wide) lists remaining-hand coins, remaining-discard coins, interest, extras (Gold/Silver/Echo/unused hands), rune gains, D20 reward line.

### D20 roll

Shown after Intensify. Optional **color fusion** (click a base color). Roll animation 1–20. Result names the tier, this-blind downside, and win reward. **Accept & Play** starts the blind with the boon active. Debug-only **Test Tier** is bottom-left so it does not cover the title.

### Shop

Reached only after beating a blind (never skipped on Intensify — the free Prism Pack from Prism Fracture is injected into **this** shop as pack index 10).

- Top-left: Shop title, coins, **Reroll (5)**, **BAG** toggle.
- Top-right: Continue, rune tray.
- Equipped charms row with Sell buttons. Mortgage, when spent, is **grayed out with a LOCKED overlay**; tooltip says “Used this shop — next shop”. Sell still works (cashing Mortgage itself out pays 2×).
- Lower panel: up to three shop charms (Buy) and pack tiles (Prism / Dice / Special Dice / Rune / Reused Rune / FREE D20 Prism).
- **BAG button**: toggles a centered overlay of the current bag (count + every die, hover for color/enhancements). Click BAG again or click outside the panel to close. Clicks on shop items are blocked while the overlay is open so you cannot accidentally buy through it.
- Hand multipliers list (hidden while the bag overlay is open).

Rerolling the shop costs 5 coins and rolls a new charm row. Debt Charm allows purchases down to −20 coins.

### Pack select

Opened by buying a pack. Prism: pick 1 hand type from N options; that type gains +0.5x forever this run. Dice packs: pick a color die to add to the bag. Special dice packs: Gold / Silver / Glass / Rainbow. Rune packs: pick 1 or 2 mystic runes into the tray (skip allowed). Super Rune Pack lets you pick 2 of 5.

### Rune use / dice select

Click a tray rune to enter rune-use. Runes with `max_dice` > 0 then ask you to click that many bag dice. Confirm applies the enhancement or conversion and consumes the rune. Rune Recycler can put a used rune back into the next shop as a free pack (index 9) once per shop cycle.

### Confirm sell

Yes / No over the shop. Default sell value is `cost // 2` (Gift Glyph can raise `sell_value`). Monopoly Mortgage doubles the **next** sell this shop, then locks. Selling Luchador Lens flags the next non-final boss as disabled.

### Pause

Esc from play/shop/blinds. Resume, save, mute, quit to menu. Previous state is restored on Resume.

### Game Over

Shown when hands run out without hitting the target and Cloak does not save you. Return to menu / (load if a save exists).

### End prompt

Stake 8 boss beaten. Summary (total score, achievements stub). **Continue to Endless Mode** or **Main Menu**. Endless keeps climbing stakes with +15% target per extra stake.

### Debug (shop / blinds)

When `DEBUG` is on: infinite coins, unlimited rerolls, charm search to equip any charm, prism boosts, rune inject, stake jumper, force boss effect, Test Tier on D20. This is how you verify individual charms without a full run.

---

## 5. Dice

Every die has `id`, `color`, `faces` (usually 1–6), `enhancements[]`, and optional `score_bonus` (Hiker Hex).

### Base colors (starting bag: 5 each)

| Color | Role |
|---|---|
| Red | Offense identity. Greedy Gambler / Dragon’s Dice / Red Greed. |
| Blue | Control identity. Sloth Sigil (no-reroll). |
| Green | Economy / nature. Envy Echo, Druid’s Dream. |
| Purple | Gluttony identity. |
| Yellow | Jolly / prism identity. |

### Special colors

| Color | When scored / held | Break? |
|---|---|---|
| Gold | +1 coin if **held** when you score (Golden Touch stacks). | No |
| Silver | +1 coin if **not held** when you score (Silver Lining stacks). | No |
| Glass | Large mult if held; 25% chance to be destroyed after scoring. | Yes |
| Rainbow | Wild for mono and rainbow color bonuses. Wild Warden pays when it wilds a mono. Whirlwind Wild spends a Rainbow as a free reroll charge. | No |

Coin Freeze / Special Silence / Special Swap boss effects invert or mute Gold/Silver/Glass/Rainbow.

Destroyed dice go to `destroyed_dice` so Necromancer’s Needle can revive one (50% once per blind).

---

## 6. Pouches (starting bags)

Four starter pouches are always available. Four more are quest-gated
(`progress.json` → `unlocked_pouches`). Locked tiles on the select carousel
are muted with a LOCKED badge; hover / click shows the quest.

| Pouch | Unlock | Bonus |
|---|---|---|
| **Red Pouch** | Starter | +1 discard/round, +2 Red dice (bag 27). |
| **Blue Pouch** | Starter | +1 hand/round (5 total, **not** 6 — Pass D fix), +1 Blue, +1 Silver. |
| **Yellow Pouch** | Starter | +10 starting coins. Standard 25 dice. |
| **Green Pouch** | Starter | +1 Green, +1 Gold. Extra coins at round end for leftover hands (+2) and discards (+1) via `green_pouch_active`. |
| **Black Pouch** | Beat Stake 2 boss | +1 charm slot, −1 hand (3 total, **not** 2 — Pass D fix), +1 random special die (Gold/Silver/Glass/Rainbow — never a junk `random_special` color). |
| **Ghost Pouch** | Add 10 dice from shop packs (lifetime) | +1 Glass. Special dice packs are 4× more likely in the shop. Standard dice packs mix specials into the offer. |
| **Erratic Pouch** | Win a run (Stake 8) | Randomizes every starting die’s color across the 9 real die colors (5 base + Gold/Silver/Glass/Rainbow). Never the Black pouch-tile color. `full_bag` stays in sync with `bag`. |
| **Plasma Pouch** | Beat Stake 4 boss | Mix scorer: +40 / +80 / +120 chips for 3 / 4 / 5 colors in the scored hand. −40 if every die is one color. Rainbow does not break mono (all-Rainbow counts as a full mix). No extra blind tax. |

DEBUG Achievements → Unlock All grants the four locked pouches. Reset clears them.
Existing accounts that already beat Stake 2 / 4 / won a run catch up on the next achievement event.


---

## 7. Charms

Charms are the build. Shop offers three you do not already own, weighted Common 60% / Uncommon 30% / Rare 10% / Legendary ramps with stake. Default sell value is half cost. Max 5 equipped (6 with Black Pouch).

Hovering a charm shows **name + description + live values only** (Pass C). Mortgage adds “Next sell: 2x coins” or “Used this shop — next shop”. Castle Cube shows current color and permanent chips. Ice Shard / Discard Drake / Steel Seal / Loyalty / Acrobat / Luchador / Gift Glyph / Life Milestone all show live numbers.

Boss Charm Glitch disables one random equipped charm for the blind. Charm Eclipse disables all. Disabled charms are gray. Monopoly Mortgage is also gray while locked even if the boss did not disable it.

Click-activated charms (play screen, on the charm icon): Fate’s Favor, Buy Boon, Disadvantage Dice, Whirlwind Wild, UNO Draw 2, Luchador Lens (sell-to-disable), Familiar’s Foresight (discard-phase bag swap).

### How to read the tables

- **Cost** is the shop price in coins.
- **Type** is the internal `type` string scoring and hooks key off. Several charms share a type (Pass A split those with extra flags: `mono` / `glass` / `every`, `enhance`, `target`).
- Effect text is the in-game description.

### Common charms

| Charm | Cost | Type | Effect |
|---|---|---|---|
| Basic Charm | 2 | `flat_bonus` | +10 to all final scores. |
| Red Greed Charm | 3 | `per_color_bonus` | +5 score per Red die scored. |
| Blue Lust Charm | 3 | `per_color_bonus` | +5 score per Blue die scored. |
| Green Wrath Charm | 3 | `per_color_bonus` | +5 score per Green die scored. |
| Purple Glutton Charm | 3 | `per_color_bonus` | +5 score per Purple die scored. |
| Yellow Jolly Charm | 3 | `per_color_bonus` | +5 score per Yellow die scored. |
| Zany Charm | 4 | `hand_bonus` | +40 score if hand contains a 3 of a Kind. |
| Mad Charm | 4 | `hand_bonus` | +30 score if hand contains a 2 Pair. |
| Crazy Charm | 4 | `hand_bonus` | +35 score if hand contains a Small or Large Straight. |
| Sly Charm | 3 | `hand_bonus` | +50 base score if hand contains a Pair. |
| Wily Charm | 4 | `hand_bonus` | +100 base score if hand contains a 3 of a Kind. |
| Half Charm | 4 | `few_dice_bonus` | +20 score if hand uses 3 or fewer dice. |
| Debt Charm | 2 | `negative_coins` | Allows going into negative coins for shop buys (up to -20). |
| Even Stevens Charm | 3 | `per_value_bonus` | +5 score per even-valued die scored. |
| Oddball Charm | 3 | `per_value_bonus` | +5 score per odd-valued die scored. |
| Interest Booster Charm | 3 | `interest_max_bonus` | Increases max coins for interest calculation by 20. |
| Luck's Locket | 4 | `coin_per_lucky` | +3 coins if a lucky enhancement triggers. |
| Envy Echo | 3 | `color_mult` | +0.5 mult for Green dice scored. |
| Gluttony Glyph | 3 | `color_mult` | +0.5 mult for Purple dice scored. |
| Interest Idol | 4 | `interest_bonus` | +1 coin per 10 coins held at round end. |
| Wild Warden | 3 | `coin_per_wild` | Rainbow dice gain +1 coin when wilding a mono. |
| Buy Boon | 3 | `face_buy_high` | Pay 2 coins per +/-1 shift to a die face once per turn (max 2 shifts). |
| Disadvantage Dice | 3 | `risk_mult` | -1 to one die face, but +0.5 mult overall. |
| Saving Throw | 4 | `break_save` | Avoid break on Glass dice with a successful "save" (roll >3). |
| Greedy Gambler | 3 | `color_mult` | +0.5 mult for Red dice scored. |
| Economy Echo | 4 | `coin_gen` | +1 coin per unused hand at round end. |
| Whirlwind Wild | 3 | `rainbow_double` | Rainbows in hand grant free reroll on one die (once per blind). |
| Joker Die | 2 | `mult_bonus` | +4 mult. |
| Square Sphere | 3 | `score_conditional` | +4 score if hand uses exactly 4 dice. (permanent scaling throughout the game) |
| Cloud Cube | 3 | `coin_per_face` | Earn 1 coin per 6 dice in bag at end of round. |
| Reserved Relic | 3 | `coin_chance` | Each high face (4-6) held has 1 in 2 chance for 1 coin. |

### Uncommon charms

| Charm | Cost | Type | Effect |
|---|---|---|---|
| Droll Charm | 5 | `mono_mult_bonus` | +0.5 mult to monochrome bonuses. |
| Clever Charm | 5 | `hand_bonus` | +80 base score if hand contains a 2 Pair. |
| Devious Charm | 5 | `hand_bonus` | +100 base score if hand contains a Small or Large Straight. |
| Four Fingers Charm | 5 | `short_straight` | Small Straights can be made with 3 dice; Large with 4. |
| Golden Touch Charm | 5 | `extra_coin_bonus` | +2 coins per Gold die held in score (stacks with base effect). |
| Silver Lining Charm | 5 | `extra_coin_bonus` | +2 coins per Silver die not held in score (stacks with base effect). |
| Rainbow Prism Charm | 5 | `rainbow_mult_bonus` | +0.5 mult to rainbow bonuses. |
| Advantage Amulet | 5 | `advantage_choice` | After discard phase, roll a duplicate for the center die; choose which to hold during rolling phase. |
| Rune Relic | 6 | `random_rune` | Enhance a die with a random rune effect at the start of each blind. |
| Yellow Prism | 4 | `color_mult` | +0.5 mult for Yellow dice scored. |
| Face Forgery | 4 | `face_wild` | Treat 2s as wild for kinds if scored. |
| Enhance Elixir | 5 | `mult_per_enhance` | +0.25 mult per enhancement on scored dice. |
| Echo Ember | 4 | `coin_per_discard` | +2 coins per unused discard. |
| Triple Threat | 4 | `mult_bonus` | +0.5 mult for Three of a Kind. |
| Stat Roller | 4 | `score_bonus` | Adds the sum of all dice faces in the hand to the base score (e.g., 6,6,6,3,1 = +22). |
| Discard Dynamo | 5 | `discard_mult` | +0.5 mult per discard used. |
| Rune Recycler | 4 | `rune_reuse` | Reuse one rune per shop. |
| Kind King | 5 | `wild_6` | Kings (6s) count as wild for kinds. |
| Bardic Blade | 5 | `rainbow_mult` | +0.5 mult per color in rainbow hand. |
| Druid's Dream | 5 | `coin_per_color` | +coins equal to greens in hand (nature bond). |
| Spellbook Scribe | 5 | `rune_scribe` | Scribe a rune to your tray if scored with a magic number "3". |
| Necromancer's Needle | 4 | `revive_die` | 50% chance to revive a random dice that was destroyed this run. |
| Steel Seal | 6 | `mult_per_enhance` | +0.2 mult per Steel-enhanced die in bag. |
| Dusk Die | 4 | `retrigger` | Retrigger all scored dice in final hand of round. |
| Loyalty Luck | 5 | `mult_conditional` | +3 mult every 6 turns played. |
| Marble Mystic | 5 | `enhance_add` | Add a Stone enhancement to a random die when blind selected. |
| Space Sphere | 5 | `hand_upgrade` | 25% chance to upgrade the specific hand type played. |
| Ice Shard | 4 | `score_decay` | +100 score. -5 score per hand played. |
| Hiker Hex | 5 | `die_bonus_perm` | Each scored die permanently gains +4 score value. |
| Rocket Rune | 5 | `coin_scaling` | Earn 1 coin at round end. Gains +2 when boss defeated. |
| Gift Glyph | 4 | `sell_bonus` | Adds 1 coin sell value to all charms and runes at round end. |
| Erosion Edge | 4 | `mult_per_low_bag` | +2 mult per die below 25 in bag. |
| Lucky Labyrinth | 5 | `mult_per_lucky` | +0.2 mult per successful lucky trigger. |
| Trading Token | 4 | `discard_destroy_coin` | If first discard is 1 die, destroy it for 3 coins. |
| Castle Cube | 5 | `score_per_discard_color` | +3 score per discarded color die. Color changes per round. |
| Monopoly Mortgage | 4 | `sell_double_lock` | Sell a charm for double coins but lock it for one round. |

### Rare charms

| Charm | Cost | Type | Effect |
|---|---|---|---|
| Mime Charm | 6 | `retrigger_held` | Retrigger effects of held dice (e.g., double Gold coins, Glass mult/break chance). |
| Fragile Fortune Charm | 6 | `glass_mod` | Reduces Glass die break chance to 10%, but if it breaks, lose 5 coins. |
| Full House Party Charm | 6 | `hand_bonus` | +150 base score if hand contains a Full House. |
| Quadruple Threat Charm | 7 | `hand_bonus` | +200 base score if hand contains a 4 of a Kind. |
| Reroll Recycler Charm | 8 | `reroll_recycler` | Gain 1 extra reroll in the turn if you use a discard. |
| Fate's Favor | 6 | `reroll_advantage` | Once per round, reroll a die with advantage (roll twice, choose). |
| Sloth Sigil | 5 | `color_mult_conditional` | +0.5 mult for Blue dice scored if no rerolls used. |
| Queen's Quill | 6 | `mult_per_face` | Queens (5s) give +0.5 mult per one in hand. |
| Synergy Scroll | 7 | `retrigger_special` | Retrigger enhancements on special colors. |
| Discard Drake | 6 | `discard_mult` | +1 mult per discard used this round. |
| Kind Keeper | 5 | `wild_4` | 4s count as wild for three/four of a kinds. |
| Homebrew Hazard | 7 | `random_event` | Random encounter: 1/6 chance for bonus charm. |
| Break Buffer | 6 | `break_reduce` | Glass dice break only on 1,2,3 (33% chance if low value). |
| Dragon's Dice | 7 | `color_risk_mult` | If all reds, +1 mult but risk burn (10% break on all dice). |
| Familiar's Foresight | 6 | `bag_swap` | Once per blind, in the discard phase swap 1 dice of your choice with any dice in your bag. |
| Flower Pot Prism | 8 | `mult_conditional` | +2 mult if scored dice are all one color. |
| Glass Globe | 6 | `mult_conditional` | +2 mult if hand contains Glass dice. |
| Obelisk Orb | 8 | `mult_per_streak` | +0.2 mult per consecutive hand without your most-played type. |
| Burglar Bag | 6 | `burglar_bonus` | When blind selected, +3 hands but lose all discards. |
| Luchador Lens | 6 | `boss_disable` | Sell this to disable current boss effect. |
| Turtle Token | 5 | `hands_decay` | +5 hands. Reduces by 1 each round. |
| Bull Bead | 7 | `score_per_coin` | +2 score bonus per coin held (based on current coins). |
| Acrobat Amulet | 6 | `mult_final_discard` | +2 mult on final discard of round. |
| UNO Skip | 6 | `boss_skip` | Skip one boss effect per run. |

### Legendary charms

| Charm | Cost | Type | Effect |
|---|---|---|---|
| Stencil Charm | 7 | `empty_slot_mult` | +0.5 mult per empty charm slot. |
| Dagger Charm | 10 | `sacrifice_mult` | When blind starts, sacrifice a charm to the right and add 0.1 mult per its cost permanently. (Max +5 mult) |
| Gambler's Grimoire | 9 | `rune_cast` | Cast a random mystic rune effect for free once per shop. |
| Ace's Aura | 8 | `face_retrigger` | Aces (1s) retrigger scoring once. |
| Final Forge | 10 | `final_mult_conditional` | +3 mult on last hand if it includes an enhancement. |
| Critical Hit | 9 | `crit_bonus` | If all dice 6, +6 mult and +50 coins. |
| Retrigger Rune | 10 | `retrigger` | Retrigger scoring on kinds. |
| Final Flourish | 10 | `final_mult` | +2 mult on last hand of round. |
| Sorcerer's Surge | 10 | `surge_random` | Random +2x to +5x mult on kinds (rolled once per turn). |
| Cloak of Cunning | 9 | `loss_prevent` | Saves you from losing the game. The charm is destroyed if you lose a blind and you must repeat the blind. One per game. |
| Triboulet Token | 10 | `mult_per_face` | Scored dice with faces 5 or 6 give +1 mult. |
| Wee Widget | 10 | `bonus_per_charm` | +2 mult and +20 score per charm equipped. |
| UNO Draw 2 | 9 | `extra_reroll` | Gain 2 extra rerolls once per blind. |
| Life Milestone | 9 | `mult_per_milestone` | +0.5 mult per stake milestone reached. |

### Charm notes that the one-line desc does not spell out

- **Castle Cube** — Picks a base color each blind. Discarded dice of that color permanently add +3 chips to the charm. Color rotates next blind. Tooltip shows color + total.
- **Saving Throw** — When Glass would break, roll a d6. 4–6 the die lives. Mime retriggers also get a save.
- **Space Sphere** — After scoring a real hand (not Nothing), 25% to add +0.5x to that hand type (same as a Prism).
- **Monopoly Mortgage** — Next sell this shop pays 2× sell value, then Mortgage grays out / LOCKED until the next shop. Selling Mortgage itself also pays 2× and leaves.
- **Cloak of Cunning** — Once per **run**, not per blind. Destroyed on use; you replay the lost blind.
- **Square Sphere** — Permanent bonus grows **after** the hand is scored, so this hand gets `value + previous permanent` only once.
- **Ice Shard** — Preview matches the upcoming hand: first score +100, then +95, +90…
- **Acrobat Amulet** — Arms when you spend your last discard, then +2 mult on the **next** score, consumed.
- **Loyalty Luck** — +3 mult every 6 scored turns (`local_turns`).
- **Steel Seal** — Counts Steel enhancements in the **whole bag**, not just scored dice. Enhance Elixir (same type, no `enhance` key) counts enhancements on scored dice.
- **Flower Pot / Glass Globe / Loyalty Luck** — Share `mult_conditional`; branched on `mono` / `glass` / `every`.
- **Dusk Die / Retrigger Rune** — Share `retrigger`; branched on `target: final_hand` vs `hands: kinds`.
- **Trading Token** — First discard of a turn, exactly 1 die: that die is destroyed (the replacement stays), +3 coins.
- **Echo Ember** — Pays on blind **win** for unused discards, $2 each. Disabled Echo pays 0.
- **Luchador Lens** — Sell it. Cannot disable the Stake 8 boss.
- **UNO Skip** — Skips one Boss blind per run, not Stake 8.
- **Dagger Charm** — Sacrifices the charm to its **right** in the equipped row when a blind starts. Drag order matters.
- **Turtle Token vs Burglar Bag** — Turtle adds decaying hands on blind enter; Burglar adds +3 hands and zeroes discards. Together they are swingy.

---

## 8. Shop packs

| Pack | Shop index | Cost | You pick |
|---|---|---|---|
| Basic Prism | 0 | 3 | 1 of 2 hand types, +0.5x |
| Standard Prism | 1 | 5 | 1 of 3 hand types, +0.5x |
| Premium Prism | 2 | 7 | 1 of 5 hand types, +0.5x |
| Dice Pack (3) | 3 | 3 | 1 of 3 base-color dice added to the bag |
| Dice Pack (4) | 4 | 5 | 1 of 4 base-color dice |
| Special Dice Pack | 5 | 9 | 1 of 3 specials (Gold / Silver / Glass / Rainbow) |
| Basic Rune Pack | 6 | 4 | 1 of 3 mystic runes |
| Mega Rune Pack | 7 | 7 | 1 of 5 mystic runes |
| Super Rune Pack | 8 | 9 | **2 of 5** mystic runes |
| Reused Rune | 9 | 0 | Free; injected by Rune Recycler |
| FREE Prism Pack | 10 | 0 | D20 Prism Fracture win reward; current shop, gold border |

Two packs are rolled per shop (weights lower on Super Rune). A third appears with a Voucher Tag if that tag is ever active.

Gambler’s Grimoire adds a free random rune drawn **below** the pack row once per shop.

---

## 9. Mystic runes and enhancements

Tray holds two runes. Click to use. `max_dice` is how many bag dice you must target (0 = instant).

| Rune | Dice | Effect |
|---|---|---|
| Mystic Fool Rune | 0 | Creates a copy of the last Mystic or Upgrade Rune used this run (must have room in consumable inventory). |
| Mystic Luck Rune | 1 | Enhances 1 selected die in bag to "Lucky" (33% chance for +1 coin). |
| Mystic Oracle Rune | 0 | Creates up to 2 random Upgrade Runes for hand type boosts. |
| Mystic Mult Rune | 2 | Enhances 2 selected dice in bag to add +0.5x mult when scored (stacks with Glass, etc.). |
| Mystic Emperor Rune | 0 | Creates up to 2 random Mystic Runes (must have room). |
| Mystic Bonus Rune | 2 | Enhances 2 selected dice in bag to add +10 score when scored. |
| Mystic Wild Rune | 1 | Converts 1 selected die in bag to Rainbow color (acts as any color for mono/rainbow bonuses). |
| Mystic Steel Rune | 1 | Enhances 1 selected die in bag to "Steel" (x1.5 mult, can't break like Glass). |
| Mystic Fragile Rune | 1 | Enhances 1 selected die in bag to "Fragile" (x2 mult, 25% break chance—stacks/modifies Glass). |
| Mystic Wealth Rune | 0 | Adds coins equal to current coins, up to a maximum gain of 20. |
| Mystic Fate Rune | 0 | 1 in 4 chance to add a random Edition (Foil, Holo, or Poly) to a random die in bag. |
| Mystic Strength Rune | 2 | Enhances up to 2 selected dice to "harmonize" faces toward mid-high values (e.g., [1,2,3,4,5,6] becomes [3,4,4,5,5,6]—duplicates mids/highs, removes lows for better kinds/straights). |
| Mystic Sacrifice Rune | 2 | Destroys up to 2 selected dice in bag (gain coins equal to their "value" based on color/rarity). |
| Mystic Transmute Rune | 2 | Convert 1 selected die to the color and faces of another selected die (clone for duplicates). |
| Mystic Balance Rune | 0 | Gives coins equal to total cost/sell value of equipped charms (max 50). |
| Mystic Gold Rune | 1 | Converts 1 selected die in bag to Gold color (+coins when held, as per your system). |
| Mystic Stone Rune | 1 | Enhances 1 selected die in bag to "Stone" (+50 score, but fixed value/no roll variance). |
| Mystic Red Rune | 3 | Converts up to 3 selected dice in bag to Red color. |
| Mystic Blue Rune | 3 | Converts up to 3 selected dice in bag to Blue color. |
| Mystic Green Rune | 3 | Converts up to 3 selected dice in bag to Green color. |
| Mystic Judgement Rune | 0 | Creates a random Common Charm (must have charm slot room). |
| Mystic Purple Rune | 3 | Converts up to 3 selected dice in bag to Purple color. |
| Mystic Yellow Rune | 3 | Converts up to 3 selected dice in bag to Yellow color. |
| Mystic Silver Rune | 1 | Converts 1 selected die in bag to Silver color (+coins when not held in score, as per your system). |

### Enhancement tags on dice

| Tag | Scoring / other |
|---|---|
| Lucky | 33% +1 coin when scored. Luck’s Locket / Lucky Labyrinth scale off triggers. |
| Mult | +0.5 mult when scored. |
| Bonus | +10 chips when scored. |
| Steel | +0.5 mult, does not break. Steel Seal counts these in the bag. |
| Fragile | ×2 mult, 25% extra break chance (spicy with Glass). |
| Stone | +50 chips, no roll variance (Marble Mystic applies this on blind start). |
| Gold / Silver / Wild | Color conversions — see special dice. |
| Strength | Faces nudged toward mid-high duplicates. |
| Fate | 1/4 edition (Foil / Holo / Poly) — edition scoring is thin. |
| Sacrifice / Transmute / Judgement | Applied at rune time, not as a lingering score tag. |

Synergy Scroll retriggers enhancements on held special-color dice when you score. Mime retriggers held Gold coins and Glass mult/break.

---

## 10. Boss effects

One is rolled as `upcoming_boss_effect` and applied when the Boss blind starts. Luchador (sold) replaces a non-final boss with a dummy “DISABLED”. UNO Skip jumps past a non-final boss blind entirely.

| Effect | Difficulty | What it does |
|---|---|---|
| Hold Ban | Hard | You cannot hold any dice between rerolls. |
| Reroll Ration | Easy | Rerolls left reduced by 1 for the round. |
| Discard Drought | Easy | Discards left reduced by 1 for the round. |
| Reroll Penalty | Easy | Each reroll costs 1 coin (deducted immediately). |
| Hold Limit | Medium | You can only hold up to 3 dice between rerolls. |
| Discard Cap | Easy | Discard phase limited to 2 dice max per use. |
| Score Dip | Easy | Base hand scores reduced by 10% for the round. |
| Target Bump | Medium | Blind target increased by 20%. |
| Color Fade | Medium | No monochrome or rainbow bonuses applied this round. |
| Fragile Flip | Medium | Glass dice break chance increased to 50%. |
| Charm Glitch | Medium | One random equipped charm is disabled for the round. |
| Face Shuffle | Medium | Dice faces are randomized (e.g., non-standard values like duplicates or missing numbers). |
| Coin Freeze | Medium | No extra coins from Gold/Silver this round. |
| Rainbow Restriction | Medium | Rainbow dice only count as one fixed color (random per round) for bonuses. |
| Glass Guard | Medium | Glass dice cannot be held (auto-unheld after rolls). |
| Charm Tax | Medium | Each equipped charm reduces hands left by 0.5 (rounded down). |
| Mono Mixup | Medium | Monochrome bonuses halved if more than one color is present (even Rainbows). |
| Reroll Rebound | Medium | After each reroll, one random held die is unheld. |
| Hand Trim | Hard | Hands left reduced by 1 for the round. |
| Break Surge | Hard | Glass break chance increases by 10% per reroll used. |
| Special Silence | Hard | All special die effects disabled (no Gold coins, Silver extras, Glass mult, Rainbow wild). |
| Die Drain | Hard | One random die is removed from your hand after each reroll, and pulling a new one from the bag. |
| Charm Eclipse | Hard | All equipped charms are disabled for the round. |
| Value Vault | Hard | All rolled values are inverted (1=6, 2=5, etc.), messing with straights and high/low strategies. |
| Blind Boost | Hard | Blind target increased by 30%, but +1 extra discard. |
| Special Swap | Hard | All special dice effects are inverted (e.g., Gold gives coins when not held, Silver when held). |
| Discard Delay | Hard | Discard phase only available after first reroll. |
| Multiplier Mute | Hard | All multipliers (charms, hands, colors) capped at x1.5. |
| Bag Bottleneck | Hard | Bag refills only half full after depletion (fewer redraw options). |
| Hold Hazard | Hard | Held dice have a 20% chance to reroll anyway on next roll. |

Stake 8 boss cannot be Luchador-disabled or UNO-skipped. Special final-boss variants (stacked effects, multi-phase) are still planned.

---

## 11. D20 Boon System

On the blinds screen, **Intensify** is optional. You may fuse a base color first (targets that color for exemption / dim / wildcard). Then a d20 is rolled.

Shop always appears after a win, even if you Intensified. Prism Fracture’s free pack is pack index 10 in the **current** shop.

| Roll | Tier | This-blind downside | On win |
|---|---|---|---|
| 1–4 | **Prism Fracture** | Target ×1.5. One hand type scores 0 (fusion: that color is exempt). | Next blind: +2x on the disabled type. Free Prism Pack this shop. |
| 5–8 | **Hue Dimming** | Target ×1.25. One color scores ×0.8 (fusion picks the color). | +2x next hand, +$20, +30% that color next blind. |
| 9–12 | **Roll Harmony** | Target ×1.08. One die locked. +1.5x score, +1 discard this blind. | Already paid this blind. |
| 13–16 | **Roll Flow** | Target ×0.88. +1 reroll/hand, advantage die, +2.5x score, extra discards. Fusion auto-picks a fused-color die for advantage. | Already paid this blind. |
| 17–20 | **Chroma Radiance** | Target ×0.75. All colors ×1.3 (fusion: fused color ×1.5, wildcard next hand). | +4x for the next **two** blinds + $50. |

Leftover buffs (Radiance ×4, Fracture type-boost, Hue next-hand) tick down in `begin_next_blind` / `end_this_blind`. They survive a new Intensify instead of being wiped.

---

## 12. Economy

| Source | When |
|---|---|
| Remaining hands | Blind win |
| Remaining discards | Blind win (plus Echo Ember $2 each) |
| Interest | `min(coins, 50 + Interest Booster) // 10`, plus Interest Idol |
| Gold / Silver / charm extras | On score or win popup |
| Lucky | 33% +1, plus Luck’s Locket |
| Green Pouch | +2 per leftover hand, +1 per leftover discard |
| Cloud Cube / Rocket Rune / Economy Echo / Gift Glyph | Round end |
| Trading Token / Wild Warden / Druid’s Dream / Reserved Relic | Situational |
| D20 | Hue +$20, Radiance +$50 |

Shop: charms, packs, 5-coin reroll. Sell default = half cost. Mortgage 2× once per shop. Gift Glyph raises everyone’s `sell_value` at round end.

---

## 13. Save, pause, debug

- **Save** (`save.json`) stores bag, charms, multipliers, blinds, shop, D20 boon, tray, mute, tutorial, unlocks. Esc → Pause auto-saves.
- **Load** from splash restores the saved state machine screen.
- **Mute** toggle top-right (speaker icons).
- **Debug** (`constants.DEBUG = True` by default in this repo): infinite coins, unlimited rerolls, charm injector, prism injector, rune injector, stake jumper, boss picker, D20 Test Tier.

---

## 14. Glossary

| Term | Meaning |
|---|---|
| **Run** | One attempt, pouch to Stake 8 (or Endless). |
| **Stake** | Ante. 1–8 for a standard win. Three blinds each. |
| **Blind** | One scoring encounter: Small, Big, or Boss. |
| **Hand** (resource) | One chance to score. Base 4 per blind. |
| **Hand** (poker) | The poker-like combination of held faces. |
| **Discard** | Replace 1–5 dice (boss Cap: 2) from the bag. Base 3 per blind. |
| **Reroll** | Re-roll unheld dice. Base 2 after the opening roll. |
| **Hold** | Lock a die’s face across rerolls. |
| **Bag** | All dice you own. Play screen always shows it; shop shows it behind the BAG toggle. |
| **Charm** | Equipped modifier. Joker-equivalent. |
| **Pouch** | Starting bag / resource kit. |
| **Rune** | Consumable enhancement from a pack or charm. Lives in the 2-slot tray. |
| **Enhancement** | Tag on a die (Lucky, Steel, Fragile…). |
| **Prism** | Pack that permanently +0.5x a hand type. |
| **Mult** | Additive multiplier stacked onto 1.0, then applied to chips. |
| **Chips / score** | Base + charm chips, then × mult. |
| **Mono** | All scored (non-rainbow) dice one color. |
| **Rainbow (bonus)** | All scored (non-rainbow) dice different colors. Distinct from Rainbow **dice**. |
| **Wild** | Rainbow die counting as any color. |
| **Break** | Glass (or Fragile) die destroyed after scoring. |
| **Save** | Saving Throw d6 > 3 cancels a break. |
| **Intensify** | Optional D20 risk on a blind. |
| **Fusion** | Optional color chosen before the D20, biasing that tier. |
| **Boon** | The D20 outcome (this-blind curse + win reward). |
| **Disabled charm** | Gray; skipped by scoring. Boss Glitch/Eclipse, or Mortgage lock. |
| **Sell value** | Coins gained when you sell. Half cost unless Gift Glyph / Mortgage. |
| **Interest** | End-of-blind coins from current money. |
| **Endless** | Post–Stake 8 continuation with +15%/stake targets. |
| **Cloak** | Once-per-run loss save; replay the blind. |

---

## 15. Work in progress

### Done in recent passes

| Pass | What landed |
|---|---|
| D20 boon | Full 5-tier system, fusion, free Prism in the current shop, no shop-skip. |
| A | Shared charm `type` strings no longer collide (Flower Pot vs Loyalty, Steel Seal vs Elixir, Dusk vs Retrigger Rune). Silent counters (`discards_used_this_round`, `stake_milestones`) now increment. |
| B | Cloak once-per-run, Square Sphere single apply, Acrobat consume, Ice Shard preview, Echo Ember enumerate, Trading Token, recycler crash, Castle-adjacent discard hooks. |
| C | Play HUD column, Intensify/Continue side-by-side, tooltip helper (no repeated Preview lines), bag click/visual alignment, win popup width, D20 Test Tier moved. |
| D | Castle Cube, Saving Throw, Space Sphere, Monopoly Mortgage. Blue/Black pouch hands applied once. Black Pouch no junk `random_special` die. |
| Shop bag (this drop) | BAG toggle overlay in shop. Mortgage grays + LOCKED while spent. |
| E | Achievements screen, 39 quests, 45 locked charms. Collection + shop appearance gates. |
| Pouches | Ghost / Black / Plasma / Erratic quest-gated. Ghost shop weighting + mixed packs. Plasma mix chips (+40/80/120 for 3/4/5 colors, −40 mono). |

### Known incomplete / next

| Item | Status |
|---|---|
| **Endless polish** | Flag and +15% scaling exist. No unique bosses, no high-score table. |
| **Final boss variants** | Stake 8 uses a normal boss effect. No multi-phase / stacked finale. |
| **Tutorial expansions** | Six steps exist; Prism / Rune / D20 are thin. |
| **Editions (Foil/Holo/Poly)** | Mystic Fate Rune can tag them; scoring support is thin. |
| **Buy Boon / Disadvantage / Whirlwind** | UI + handlers exist; they need a dedicated playtest pass, not a stub fill. |
| **Mime + Glass / Dagger drag / Turtle + Burglar** | High-risk interactions called out in the Project Bible; worth a focused test run. |
| **Color-blind options / Android / Steam** | Roadmapped in the PRD, not started. |

### Design debts (not bugs, not started)

- Balance pass across all 105 charms (costs vs. power, especially Legendaries and permanent scalers: Ice Shard, Square Sphere, Castle Cube, Hiker Hex, Lucky Labyrinth, Bull Bead).
- Interest and leftover-hand coin economy vs. late-stake targets.
- Charm slot of 5 vs. Wee Widget / Stencil / Dagger tension.
- House-rule bag heat / wagers (deferred).

---

## Appendix A — File map

| File | Role |
|---|---|
| `ChromaRoll.py` | Game object, discard/score/advance_blind, shop gen, pouch apply, Cloak, glass break. |
| `scoring.py` | `evaluate_hand` plus Pass D helpers (`glass_breaks`, Castle, Space Sphere, Mortgage payout, pouch extras). |
| `d20_boon.py` | D20 state machine. No pygame. |
| `data.py` | Charms, pouches, bosses, runes, enhancements, hand types. |
| `screens.py` | All drawing, tooltips, bag geometry, shop BAG overlay. |
| `constants.py` | Layout, theme, DEBUG flags. |
| `savegame.py` | JSON save/load. |
| `states/*.py` | One screen each: splash, init, blinds, game, shop, d20_roll, pack_select, rune, pause, tutorial, end_prompt, game_over, debug. |
| `tests/` | Headless: `test_d20_boon.py`, `test_charm_pass_ab.py`, `test_charm_pass_d.py`, `test_ui_pass_c.py`. |

## Appendix B — Resolution and controls

- Window: 1024×600.
- Mouse: primary input. Click dice, charms, buttons, bag, tray.
- Esc: pause (saves).
- Splash skip: Space / Esc / Enter.
- Debug shop panel: Up / Down to scroll the charm list.
- No keyboard dice holds. Touch/Android is planned, not implemented.

_End of reference. When you change a charm, pouch, or screen, update this file in the same drop._

# states/shop.py
import pygame
import random  # If used for shop generation
import time
import math
import copy
import os
from constants import *  # For THEME, BUTTON_WIDTH, SHOP_REROLL_COST, etc.
from utils import draw_rounded_element, resource_path, wrap_text  # For UI/buttons
from screens import draw_shop_screen, draw_custom_button, draw_tooltip  # For main shop drawing/buttons
from data import CHARMS_POOL  # For charm generation/packs
import data
from scoring import dice_pack_choices

from states.base import State
from states.rune import RuneUseState, RuneSelectState  # FIXED: Lazy import at top of handle_event (for IDE/Pylance)

def drop_shop_charm(game, mouse_pos):
    """Drop a dragged equipped charm onto a slot (swap, or park in an empty slot)."""
    drag = getattr(game, 'dragging_charm_index', -1)
    if drag is None or drag < 0:
        return
    charms = game.equipped_charms
    if drag >= len(charms):
        game.dragging_charm_index = -1
        game.dragging_shop = False
        return
    slots = getattr(game, 'shop_slot_rects', None) or []
    target = -1
    for i, rect in enumerate(slots):
        if rect.collidepoint(mouse_pos):
            target = i
            break
    n = len(charms)
    if 0 <= target < n and target != drag:
        charms[drag], charms[target] = charms[target], charms[drag]
    elif target >= n:
        charm = charms.pop(drag)
        charms.append(charm)
    game.dragging_charm_index = -1
    game.dragging_shop = False


def park_shop_charm(game):
    """ESC / right-click: put the held charm in the first empty slot, or unstick if full."""
    drag = getattr(game, 'dragging_charm_index', -1)
    if drag is None or drag < 0:
        return
    charms = game.equipped_charms
    max_c = getattr(game, 'max_charms', 5)
    if 0 <= drag < len(charms) and len(charms) < max_c and drag != len(charms) - 1:
        charm = charms.pop(drag)
        charms.append(charm)
    game.dragging_charm_index = -1
    game.dragging_shop = False


def try_buy_shop_charm(game, index):
    """Buy shop_charms[index]. Safe if the rect list is stale or longer than stock.

    Returns 'ok', 'prism', 'full', 'broke', or None if index is invalid.
    """
    shop = getattr(game, 'shop_charms', None)
    if not shop or index < 0 or index >= len(shop):
        return None
    raw = shop[index]
    if raw.get('is_free_prism', False):
        shop.pop(index)
        return 'prism'
    charm = copy.deepcopy(shop.pop(index))
    cost = int(charm.get('cost') or 0)
    disabled = getattr(game, 'disabled_charms', None) or []
    debt_active = any(
        c.get('type') == 'negative_coins' and idx not in disabled
        for idx, c in enumerate(getattr(game, 'equipped_charms', None) or [])
    )
    debt_limit = -20 if debt_active else 0
    max_c = getattr(game, 'max_charms', 5) or 5
    equipped = game.equipped_charms
    if len(equipped) >= max_c:
        shop.insert(index, charm)
        game.temp_message = "No charm slots left!"
        game.temp_message_start = time.time()
        return 'full'
    if game.coins - cost < debt_limit:
        shop.insert(index, charm)
        game.temp_message = "Not enough coins!"
        game.temp_message_start = time.time()
        return 'broke'
    equipped.append(charm)
    from achievements import notify
    notify(game, 'check', charm_count=len(equipped))
    if charm.get('name') == 'Loyalty Luck':
        charm['local_turns'] = 1
    elif charm.get('name') == 'Turtle Token':
        game.hands_left += charm['start']
        charm['rounds_passed'] = 0
        game.temp_message = f"Turtle Token: +{charm['start']} hands (decays -1 per round)!"
        game.temp_message_start = time.time()
    game.coins -= cost
    boss = getattr(game, 'current_boss_effect', None)
    if boss and boss.get('name') == 'Charm Eclipse':
        game.disabled_charms = list(range(len(equipped)))
    if charm.get('name') != 'Turtle Token':
        game.temp_message = f"Bought {charm['name']} for {charm['cost']} coins."
        game.temp_message_start = time.time()
    return 'ok'


def resume_shop(game):
    """Return to the current shop without rerolling stock / Homebrew."""
    game.is_resuming = True
    game.state_machine.change_state(ShopState(game))


class ShopState(State):
    def __init__(self, game):
        super().__init__(game)
        self.continue_rect = None
        self.sell_rects = None
        self.buy_rects = None
        self.equipped_rects = None
        self.shop_rects = None
        self.pack_rects = None
        self.reroll_rect = None
        self.debug_rect = None  # For debug button
        self.debug_panel_open = False  # Flag for debug panel
        self.scroll_y = 0  # For debug panel scrolling
        self.charm_rects = []  # Store debug panel rects
        self.tray_rects = []  # For tray clicks
        self.debug_button_rect = None  # New for debug menu button

    def enter(self):
        resuming = bool(getattr(self.game, 'is_resuming', False))
        if resuming:
            self.game.is_resuming = False
        # Generate shop if empty — never on resume/load (that wiped a saved shop).
        if not resuming and not self.game.shop_charms:
            self.game.generate_shop()
        self.debug_panel_open = False  # Reset panel
        self.scroll_y = 0  # Reset scroll
        # Fallback calc for debug_button_rect (if draw not run yet)
        if DEBUG and DEBUG_MENU_IN_SHOP:
            button_x = self.game.width - 150 - 50  # Above existing debug_rect (adjust if needed)
            button_y = self.game.height - 50 - 60  # Above existing
            self.debug_button_rect = pygame.Rect(button_x, button_y, 150, 50)
        self.game.shop_bag_open = False
        if resuming:
            return
        # ADD: Reset for Gambler's Grimoire on new shop
        self.game.used_rune_cast_this_shop = False
        # print("Debug: Reset Gambler's Grimoire for new shop")
        # NEW: Homebrew Hazard random event if equipped
        has_homebrew = any(charm['type'] == 'random_event' and idx not in self.game.disabled_charms 
                for idx, charm in enumerate(self.game.equipped_charms))
        if has_homebrew and random.random() < 1/6:
            # Success: +1 bonus charm (free common/rare pick)
            available_pool = [c for c in data.CHARMS_POOL 
                            if c['rarity'] in ['Common', 'Uncommon', 'Rare'] and  # Limit to non-legendary for balance
                            c['name'] not in [e['name'] for e in self.game.equipped_charms]]
            if available_pool:
                bonus_charm = copy.deepcopy(random.choice(available_pool))
                bonus_charm['cost'] = 0  # Free (copy only — never the catalog)
                self.game.shop_charms.append(bonus_charm)
                self.game.temp_message = f"Homebrew success! Free {bonus_charm['name']} added to shop."
                self.game.temp_message_start = time.time()
                # print(f"DEBUG: Homebrew added free {bonus_charm['name']} to shop")
            else:
                self.game.temp_message = "Homebrew success... but no charms available!"
                self.game.temp_message_start = time.time()
        # NEW: Add pending Recycler rune to this shop's choices (if queued from prior use)
        if hasattr(self.game, '_recycler_reuse_pending'):
            pending_rune = self.game._recycler_reuse_pending
            pending_rune['cost'] = 0
            pending_rune['reused'] = True
            self.game.pack_choices.append(pending_rune)
            self.game.available_packs.append(9)  # Special index
            delattr(self.game, '_recycler_reuse_pending')  # Clear pending
            self.game.temp_message = f"Rune Recycler: {pending_rune['name']} available in shop!"
            self.game.temp_message_start = time.time()

        # Free Prism Pack is added in generate_shop as pack index 10 (pack row), not as a charm.

    def update(self, dt):
        pass  # Expand for animations if needed

    def draw(self):
        self.game.screen.fill(THEME['background'])  # Clear relics
        # Draw shop, but pass debug_panel_open to skip tooltips when panel is open
        self.continue_rect, self.sell_rects, self.buy_rects, self.equipped_rects, self.shop_rects, self.pack_rects, self.reroll_rect, self.tray_rects = draw_shop_screen(self.game, skip_tooltips=self.debug_panel_open)  # FIXED: Unpack 8th as self.tray_rects
        
        # Calc bag_width for tray pos (match screens.py)
        columns = 5
        rows = math.ceil(len(self.game.bag) / columns) if self.game.bag else 1
        bag_width = columns * (SMALL_DIE_SIZE + SMALL_DIE_SPACING) - SMALL_DIE_SPACING + BAG_PADDING * 2

        # Calc tray_rects for clicks (match screens.py) - FIXED: No recalc, use from unpack
        # print("DEBUG: shop self.tray_rects from unpack:", self.tray_rects)  # TEMP - confirm new rects

        # Debug button (bottom-right to avoid prism packs)
        if DEBUG:
            button_x = self.game.width - DEBUG_BUTTON_SIZE[0] - 50  # Bottom-right
            button_y = self.game.height - DEBUG_BUTTON_SIZE[1] - 50
            self.debug_rect = pygame.Rect(button_x, button_y, *DEBUG_BUTTON_SIZE)
            draw_custom_button(self.game, self.debug_rect, DEBUG_BUTTON_TEXT, 
                            is_hover=self.debug_rect.collidepoint(pygame.mouse.get_pos()))
            
            # Draw debug panel if open
            if self.debug_panel_open:
                self.charm_rects = self.draw_debug_panel()
            else:
                self.charm_rects = []

            # Add this: New debug menu button (e.g., next to existing debug button)
            if DEBUG and DEBUG_MENU_IN_SHOP:
                # Position: Below or beside existing debug button (adjust coords as needed)
                self.debug_button_rect = pygame.Rect(button_x, button_y - 60, 150, 50)  # Above existing, example
                draw_custom_button(self.game, self.debug_button_rect, "Debug Menu", is_hover=self.debug_button_rect.collidepoint(pygame.mouse.get_pos()))

    def handle_event(self, event):
        from states.blinds import BlindsState  # Lazy import here - loads only when method runs
        from states.rune import RuneUseState  # FIXED: Lazy import at top of handle_event (for IDE/Pylance)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if getattr(self.game, 'dragging_charm_index', -1) != -1:
                    park_shop_charm(self.game)
                    return
                from states.pause import PauseMenuState  # Lazy import
                import savegame
                savegame.save_game(self.game)  # Save
                self.game.previous_state = self  # ADD: Set to current ShopState instance
                self.game.state_machine.change_state(PauseMenuState(self.game))
            elif DEBUG and self.debug_panel_open:
                # Keyboard scrolling
                icons_per_row = 4
                row_height = 100 + 50  # Match draw_debug_panel
                num_rows = (len(CHARMS_POOL) + icons_per_row - 1) // icons_per_row
                total_content_height = num_rows * row_height + 70
                max_scroll = max(0, total_content_height - DEBUG_PANEL_HEIGHT)
                if event.key == pygame.K_UP:
                    self.scroll_y = max(0, self.scroll_y - 50)
                elif event.key == pygame.K_DOWN:
                    self.scroll_y = min(self.scroll_y + 50, max_scroll)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle debug button
            if DEBUG and self.debug_rect and self.debug_rect.collidepoint(mouse_pos):
                self.debug_panel_open = not self.debug_panel_open
                # print(f"DEBUG: Panel {'opened' if self.debug_panel_open else 'closed'}")
                return
            
            # Handle debug panel interactions
            if DEBUG and self.debug_panel_open:
                for rect, action in self.charm_rects:
                    if rect.collidepoint(mouse_pos):
                        if action == 'close':
                            self.debug_panel_open = False
                            self.game.temp_message = "Debug panel closed"
                            self.game.temp_message_start = time.time()
                        elif action == 'equip_all':
                            for charm in CHARMS_POOL:
                                if charm['name'] not in [c['name'] for c in self.game.equipped_charms] and len(self.game.equipped_charms) < self.game.max_charms * 2:
                                    self.game.equipped_charms.append(copy.deepcopy(charm))
                            from achievements import notify
                            notify(self.game, 'check', charm_count=len(self.game.equipped_charms))
                            # print("DEBUG: Equipped all available charms!")
                            self.game.temp_message = "Equipped all possible charms!"
                            self.game.temp_message_start = time.time()
                        elif action and len(self.game.equipped_charms) < self.game.max_charms * 2:
                            if any(c['name'] == action['name'] for c in self.game.equipped_charms):
                                # print(f"DEBUG: {action['name']} already owned")
                                self.game.temp_message = f"{action['name']} already owned!"
                            else:
                                self.game.equipped_charms.append(copy.deepcopy(action))
                                from achievements import notify
                                notify(self.game, 'check', charm_count=len(self.game.equipped_charms))
                                # print(f"DEBUG: Added {action['name']} (free)")
                                self.game.temp_message = f"Added {action['name']}!"
                            self.game.temp_message_start = time.time()
                        else:
                            # print("DEBUG: Max charms reached")
                            self.game.temp_message = "No charm slots left!"
                            self.game.temp_message_start = time.time()
                        return
            
            # Handle new debug menu button click
            if DEBUG and DEBUG_MENU_IN_SHOP and self.debug_button_rect.collidepoint(mouse_pos):
                from states.debug import DebugMenuState  # Lazy import
                self.game.state_machine.change_state(DebugMenuState(self.game))  # New state below
                return

            toggle = getattr(self.game, 'shop_bag_toggle_rect', None)
            if toggle and toggle.collidepoint(mouse_pos):
                self.game.shop_bag_open = not getattr(self.game, 'shop_bag_open', False)
                return
            if getattr(self.game, 'shop_bag_open', False):
                panel = getattr(self.game, 'shop_bag_panel_rect', None)
                if panel and panel.collidepoint(mouse_pos):
                    return
                self.game.shop_bag_open = False
                return

            # Handle continue to blinds
            if self.continue_rect and self.continue_rect.collidepoint(mouse_pos):
                self.game.shop_charms = []  # Clear shop
                self.game._d20_prism_in_current_shop = False
                if 10 in getattr(self.game, 'available_packs', []):
                    self.game.available_packs = [p for p in self.game.available_packs if p != 10]
                n = NUM_DICE_IN_HAND
                self.game.rolls = []
                self.game.hand = []
                self.game.held = [False] * n
                self.game.discard_selected = [False] * n
                self.game.has_rolled = False
                from states.blinds import BlindsState
                self.game.state_machine.change_state(BlindsState(self.game))
                return

            # Handle sell
            for i, sell_rect in enumerate(self.sell_rects or []):
                if sell_rect.collidepoint(mouse_pos):
                    from states.confirm_sell import ConfirmSellState  # Lazy import
                    self.game.confirm_sell_index = i
                    # **INSERT: Pre-set flag if Luchador (before transition)**
                    charm = self.game.equipped_charms[i] if i < len(self.game.equipped_charms) else self.shop_items[i]  # Adjust based on your sell source
                    if charm['name'] == 'Luchador Lens':
                        self.game.pending_luchador_disable = True
                        # print("DEBUG: Luchador sell flagged from shop")
                    self.game.state_machine.change_state(ConfirmSellState(self.game))
                    return

            # Handle buy charms — shop tiles (1:1 with stock), not the leftover
            # Grimoire Buy rect that used to be appended onto buy_rects.
            buy_index = None
            for i, shop_rect in enumerate(self.shop_rects or []):
                if shop_rect.collidepoint(mouse_pos):
                    buy_index = i
                    break
            if buy_index is None:
                for i, buy_rect in enumerate(self.buy_rects or []):
                    if buy_rect.collidepoint(mouse_pos):
                        buy_index = i
                        break
            if buy_index is not None:
                result = try_buy_shop_charm(self.game, buy_index)
                if result is None:
                    pass  # leftover rect (Grimoire); pack handler owns it
                elif result == 'prism':
                    from states.pack_select import PackSelectState
                    self.game.pack_choices = random.sample(data.HAND_TYPES, 5)
                    self.game.temp_message = "Free Prism Pack opened! (Tier 1 Success Reward)"
                    self.game.temp_message_start = time.time()
                    self.game.state_machine.change_state(PackSelectState(self.game))
                    return
                else:
                    return

            # Pack buys
            pack_costs = [3, 5, 7, 3, 5, 9, 4, 7, 9, 0, 0]
            pack_choices_num = [2, 3, 5, 3, 4, 3, 3, 5, 5, 1, 5]
            pack_select_num = [1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1]

            for pack_rect, pack_idx in self.pack_rects or []:
                if pack_rect.collidepoint(mouse_pos):
                    
                    # NEW: Handle free Grimoire rune buy (index -1)
                    if pack_idx == -1:
                        grimoire_rune = getattr(self.game, 'grimoire_rune', None)
                        if grimoire_rune:
                            max_c = getattr(self.game, 'max_charms', 5) or 5
                            if len(self.game.equipped_charms) < max_c:
                                self.game.equipped_charms.append(grimoire_rune)
                                self.game.grimoire_rune = None
                                if hasattr(self.game, '_grimoire_drawn'):
                                    del self.game._grimoire_drawn
                                from achievements import notify
                                notify(self.game, 'check', charm_count=len(self.game.equipped_charms))
                            else:
                                self.game.temp_message = "No charm slots left!"
                                self.game.temp_message_start = time.time()
                        return

                    # NEW: Handle Rune Recycler reused rune (index 9)
                    elif pack_idx == 9:
                        reused_rune = self.game.pack_choices[-1] if self.game.pack_choices else None
                        if reused_rune and self.game.rune_tray.count(None) > 0:
                            self.game.add_to_rune_tray(reused_rune)
                            self.game.pack_choices.pop()
                            if 9 in self.game.available_packs:
                                self.game.available_packs.remove(9)
                            self.game.temp_message = f"Reused {reused_rune['name']} to tray!"
                            if hasattr(self.game, '_recycler_used_this_shop'):
                                delattr(self.game, '_recycler_used_this_shop')
                        else:
                            self.game.temp_message = "Tray full—reused rune discarded."
                            if hasattr(self.game, '_recycler_used_this_shop'):
                                delattr(self.game, '_recycler_used_this_shop')
                        self.game.temp_message_start = time.time()
                        return

                    # FREE Prism Pack from D20 Prism Fracture (pack index 10)
                    elif pack_idx == 10:
                        from states.pack_select import PackSelectState
                        self.game.pack_choices = random.sample(data.HAND_TYPES, 5)
                        if 10 in self.game.available_packs:
                            self.game.available_packs.remove(10)
                        self.game.has_free_prism_pack = False
                        self.game._d20_prism_in_current_shop = False
                        if hasattr(self.game, 'd20_boon') and self.game.d20_boon:
                            self.game.d20_boon.free_prism_pack = False
                        self.game.temp_message = "Free Prism Pack opened! (D20 Prism Fracture)"
                        self.game.temp_message_start = time.time()
                        self.game.state_machine.change_state(PackSelectState(self.game))
                        return

                    # === SPECIAL: Free Prism Pack from Tier 1 ===
                    #if charm.get('is_free_prism', False):
                    #    print("DEBUG: Free Prism Pack from Tier 1 claimed!")
                    #    self.game.shop_charms.pop(i)
                        
                        # Use the SAME logic as your normal premium packs
                    #    from states.pack_select import PackSelectState
                    #    self.game.pack_choices = random.sample(data.HAND_TYPES, 5)  # Adjust 5 if your Prism pack uses different count
                        
                    #    self.game.state_machine.change_state(PackSelectState(self.game))
                        
                    #    self.game.temp_message = "Free Prism Pack opened! (Tier 1 Success Reward)"
                    #    self.game.temp_message_start = time.time()
                    #    return

                    # === Normal paid pack buying (your original logic) ===
                    if pack_idx != -1:  # Skip cost check for Grimoire
                        cost = pack_costs[pack_idx]
                        has_debt = any(c['type'] == 'negative_coins' for c in self.game.equipped_charms)
                        min_coins = -5 if has_debt else 0
                        if self.game.coins - cost >= min_coins:
                            self.game.coins -= cost
                            if pack_idx in [0, 1, 2]:
                                from states.pack_select import PackSelectState
                                self.game.pack_choices = random.sample(data.HAND_TYPES, pack_choices_num[pack_idx])
                                self.game.state_machine.change_state(PackSelectState(self.game))
                                if pack_idx in self.game.available_packs:
                                    self.game.available_packs.remove(pack_idx)
                            elif pack_idx in [3, 4, 5]:
                                from states.dice_select import DiceSelectState
                                n = pack_choices_num[pack_idx]
                                ghost = bool(getattr(self.game, 'ghost_pouch_active', False))
                                if pack_idx == 5:
                                    self.game.pack_choices = dice_pack_choices(n, special_only=True, ghost=ghost)
                                else:
                                    self.game.pack_choices = dice_pack_choices(n, special_only=False, ghost=ghost)
                                self.game.state_machine.change_state(DiceSelectState(self.game))
                                if pack_idx in self.game.available_packs:
                                    self.game.available_packs.remove(pack_idx)
                            elif pack_idx in [6, 7, 8]:  # Rune packs
                                from states.rune import RuneSelectState
                                self.game.pack_choices = random.sample(data.MYSTIC_RUNES, pack_choices_num[pack_idx])
                                self.game.pack_select_count = pack_choices_num[pack_idx]
                                self.game.selected_runes = []
                                self.game.state_machine.change_state(RuneSelectState(self.game))
                                if pack_idx in self.game.available_packs:
                                    self.game.available_packs.remove(pack_idx)
                        return   # Exit after normal pack buy
                    
            # Reroll
            if self.reroll_rect and self.reroll_rect.collidepoint(mouse_pos):
                self.game.reroll_shop()
                return

            # Right-click parks a stuck / dragged charm into an empty slot
            if getattr(event, 'button', 1) == 3:
                if getattr(self.game, 'dragging_charm_index', -1) != -1:
                    park_shop_charm(self.game)
                return

            # Charm drag start — use the same slot rects draw_shop_screen painted
            if getattr(event, 'button', 1) == 1:
                slots = getattr(self.game, 'shop_slot_rects', None) or []
                n = len(self.game.equipped_charms)
                for i, rect in enumerate(slots):
                    if i >= n:
                        break
                    if not rect.collidepoint(mouse_pos):
                        continue
                    if any(s.collidepoint(mouse_pos) for s in (self.sell_rects or [])):
                        break
                    self.game.dragging_charm_index = i
                    self.game.dragging_shop = True
                    self.game.drag_offset_x = mouse_pos[0] - rect.x
                    self.game.drag_offset_y = mouse_pos[1] - rect.y
                    return

            # Tray click to use rune
            for i, tray_rect in enumerate(self.tray_rects or []):
                if tray_rect is not None and tray_rect.collidepoint(mouse_pos) and self.game.rune_tray[i]:
                    from states.rune import RuneUseState  # Lazy import
                    rune = self.game.rune_tray[i]
                    self.game.state_machine.change_state(RuneUseState(self.game, rune))  # Transition
                    self.game.previous_state = self
                    recycler_active = any(charm['type'] == 'rune_reuse' and idx not in self.game.disabled_charms for idx, charm in enumerate(self.game.equipped_charms))
                    if recycler_active and not getattr(self.game, '_recycler_used_this_blind', False):
                        self.game._recycler_reuse_pending = rune.copy()
                        self.game._recycler_used_this_blind = True
                        self.game.temp_message = f"Rune Recycler: {rune['name']} queued for reuse in next shop!"
                        self.game.temp_message_start = time.time()
                    if not getattr(rune, 'reused', False):
                        self.game.rune_tray[i] = None
                    break

        if event.type == pygame.MOUSEBUTTONUP:
            if getattr(self.game, 'dragging_charm_index', -1) == -1:
                pass
            elif getattr(event, 'button', 1) == 3:
                park_shop_charm(self.game)
            else:
                drop_shop_charm(self.game, pygame.mouse.get_pos())

        if event.type == pygame.MOUSEWHEEL and DEBUG and self.debug_panel_open:
            icons_per_row = 4
            row_height = 100 + 50  # Match draw_debug_panel
            num_rows = (len(data.CHARMS_POOL) + icons_per_row - 1) // icons_per_row
            total_content_height = num_rows * row_height + 70
            scroll_speed = 50
            self.scroll_y -= event.y * scroll_speed
            max_scroll = max(0, total_content_height - DEBUG_PANEL_HEIGHT)
            self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        if event.type == pygame.MOUSEMOTION:
            if self.game.dragging_charm_index != -1:
                pass  # Dragging handled in draw_shop_screen

    def draw_debug_panel(self):
        """Draws the debug panel with improved spacing and text readability."""
        panel_rect = pygame.Rect(DEBUG_PANEL_X, DEBUG_PANEL_Y, 
                               DEBUG_PANEL_WIDTH, DEBUG_PANEL_HEIGHT)
        pygame.draw.rect(self.game.screen, (0, 0, 0), panel_rect, 3)
        overlay = pygame.Surface((DEBUG_PANEL_WIDTH, DEBUG_PANEL_HEIGHT))
        overlay.fill((40, 40, 40))
        overlay.set_alpha(200)
        self.game.screen.blit(overlay, (DEBUG_PANEL_X, DEBUG_PANEL_Y))
        
        title_text = self.game.font.render("Debug: All Charms (Click to Equip)", True, THEME['text'])
        self.game.screen.blit(title_text, (DEBUG_PANEL_X + 20, DEBUG_PANEL_Y + 20))
        
        icons_per_row = 4
        icon_size = 100
        spacing = 30
        row_height = icon_size + 50
        num_rows = (len(CHARMS_POOL) + icons_per_row - 1) // icons_per_row
        total_content_height = num_rows * row_height + 70
        
        start_x = DEBUG_PANEL_X + 20
        start_y = DEBUG_PANEL_Y + 70 - self.scroll_y
        mouse_pos = pygame.mouse.get_pos()
        visible_start_row = max(0, int(self.scroll_y / row_height))
        visible_rows_to_draw = (DEBUG_PANEL_HEIGHT - 70) // row_height + 2
        visible_end_row = min(num_rows, visible_start_row + visible_rows_to_draw)
        
        charm_rects = []
        tooltips_to_draw = []  # Collect tooltips to draw last
        
        for row in range(visible_start_row, visible_end_row):
            for col in range(icons_per_row):
                i = row * icons_per_row + col
                if i >= len(CHARMS_POOL):
                    break
                charm = CHARMS_POOL[i]
                x = start_x + col * (icon_size + spacing)
                y = start_y + (row - visible_start_row) * row_height
                icon_rect = pygame.Rect(x, y, icon_size, icon_size)
                
                bg_color = CHARM_BG_COLORS.get(charm['name'], (150, 150, 150))
                if charm.get('rarity') == 'Legendary':
                    bg_color = tuple(min(255, c + 50) for c in bg_color)
                elif charm.get('rarity') == 'Common':
                    bg_color = tuple(max(0, c - 30) for c in bg_color)
                draw_rounded_element(self.game.screen, icon_rect, bg_color, radius=10, 
                                   border_color=THEME['border'], border_width=1)
                
                icon_path = self.game.charm_icon_paths.get(charm['name'])
                if icon_path and os.path.exists(icon_path):
                    icon = pygame.image.load(icon_path)
                    icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                    self.game.screen.blit(icon, (x, y))
                else:
                    pygame.draw.circle(self.game.screen, (0, 0, 0), (x + icon_size//2, y + icon_size//2), 10)
                
                if any(c['name'] == charm['name'] for c in self.game.equipped_charms):
                    gray_surf = pygame.Surface((icon_size, icon_size))
                    gray_surf.fill((128, 128, 128))
                    gray_surf.set_alpha(100)
                    self.game.screen.blit(gray_surf, (x, y))
                    owned_text = self.game.tiny_font.render("OWNED", True, (100, 100, 100))
                    self.game.screen.blit(owned_text, (x + 5, y + icon_size - 15))
                
                full_name = f"{charm['name']} ({charm.get('rarity', 'Common')})"
                max_text_width = icon_size - 10
                name_lines = wrap_text(self.game.tiny_font, full_name, max_text_width)
                text_y = y + icon_size + 5
                for line in name_lines[:2]:
                    name_text = self.game.tiny_font.render(line, True, THEME['text'])
                    text_x = x + (icon_size - name_text.get_width()) // 2
                    text_bg_rect = pygame.Rect(text_x - 5, text_y - 2, name_text.get_width() + 10, name_text.get_height() + 4)
                    pygame.draw.rect(self.game.screen, (*THEME['background'], 180), text_bg_rect)
                    self.game.screen.blit(name_text, (text_x, text_y))
                    text_y += self.game.tiny_font.get_height() + 2
                
                cost_text = self.game.tiny_font.render(str(charm['cost']), True, (255, 255, 0))
                badge_rect = pygame.Rect(x + icon_size - 25, y + 5, 20, 15)
                pygame.draw.rect(self.game.screen, (0, 0, 0), badge_rect)
                self.game.screen.blit(cost_text, (badge_rect.x + 2, badge_rect.y + 1))
                
                if icon_rect.collidepoint(mouse_pos):
                    tooltip_text = f"{charm['desc']}\nCost: {charm['cost']} | Type: {charm.get('type', 'Unknown')}"
                    space_above = y - DEBUG_PANEL_Y
                    assumed_tooltip_height = 100
                    tooltip_y = y - assumed_tooltip_height - 5 if space_above > assumed_tooltip_height else y + icon_size + 50
                    tooltip_y = max(DEBUG_PANEL_Y + 10, min(tooltip_y, DEBUG_PANEL_Y + DEBUG_PANEL_HEIGHT - assumed_tooltip_height - 10))
                    # Collect to draw last
                    tooltips_to_draw.append((x, tooltip_y, tooltip_text))
                
                charm_rects.append((icon_rect, charm))
        
        equip_all_rect = pygame.Rect(DEBUG_PANEL_X + 20, DEBUG_PANEL_Y + DEBUG_PANEL_HEIGHT - 50, 150, 30)
        draw_custom_button(self.game, equip_all_rect, "Equip All", is_hover=equip_all_rect.collidepoint(mouse_pos))
        close_rect = pygame.Rect(DEBUG_PANEL_X + DEBUG_PANEL_WIDTH - 100, DEBUG_PANEL_Y + 10, 80, 30)
        draw_custom_button(self.game, close_rect, "Close", is_hover=close_rect.collidepoint(mouse_pos))
        
        # Draw scrollbar
        if total_content_height > DEBUG_PANEL_HEIGHT:
            bar_width = 10
            bar_x = DEBUG_PANEL_X + DEBUG_PANEL_WIDTH - bar_width - 5
            bar_y = DEBUG_PANEL_Y + 30
            bar_height = DEBUG_PANEL_HEIGHT - 60
            pygame.draw.rect(self.game.screen, (150, 150, 150), (bar_x, bar_y, bar_width, bar_height))  # Brighter track for visibility
            thumb_height = max(20, (DEBUG_PANEL_HEIGHT - 60) * (DEBUG_PANEL_HEIGHT / total_content_height))
            thumb_y = bar_y + (self.scroll_y / (total_content_height - DEBUG_PANEL_HEIGHT)) * (bar_height - thumb_height)
            thumb_y = max(bar_y, min(thumb_y, bar_y + bar_height - thumb_height))
            pygame.draw.rect(self.game.screen, (255, 255, 255), (bar_x, int(thumb_y), bar_width, int(thumb_height)))  # White thumb for contrast
        
        # Draw collected tooltips last (on top)
        for x, y, tooltip_text in tooltips_to_draw:
            draw_tooltip(self.game, x, y, tooltip_text)
        
        return charm_rects + [(equip_all_rect, 'equip_all'), (close_rect, 'close')]
# states/base.py
import pygame

# Menu screens must not overwrite a run save. That's why Load looked like a no-op
# (Splash/Init/GameOver auto-saved over the shop/blinds/play file).
_SKIP_AUTOSAVE = {
    'SplashState', 'PromptState', 'AchievementsState',
    'GameOverState', 'InitState',
}

# Only persist screens Load can actually resume. Overlay states (packs, runes)
# keep the previous shop/play save instead of writing an un-resumable name.
_RUN_AUTOSAVE = {
    'ShopState', 'GameState', 'BlindsState', 'PauseMenuState', 'EndPromptState',
    'D20RollState',
}

class State:
    def __init__(self, game):
        self.game = game
        self.prev_state = None

    def enter(self):
        import savegame  # Lazy import to avoid cycles
        if type(self).__name__ not in _SKIP_AUTOSAVE:
            savegame.save_game(self.game)

    def exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass

class StateMachine:
    def __init__(self, game, initial_state):
        self.game = game
        self.current_state = initial_state
        self.current_state.enter()

    def change_state(self, new_state):
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()
        # Persist run screens even when a subclass overrides enter() without super().
        name = type(self.current_state).__name__
        if name in _RUN_AUTOSAVE:
            import savegame
            savegame.save_game(self.game)

    def update(self, dt):
        self.current_state.update(dt)

    def draw(self):
        self.current_state.draw()

    def handle_event(self, event):
        self.current_state.handle_event(event)
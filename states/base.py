# states/base.py
import pygame

class State:
    def __init__(self, game):
        self.game = game
        self.prev_state = None

    def enter(self):
        import savegame  # Lazy import to avoid cycles
        savegame.save_game(self.game)  # Auto-save on every state entry

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

    def update(self, dt):
        self.current_state.update(dt)

    def draw(self):
        self.current_state.draw()

    def handle_event(self, event):
        self.current_state.handle_event(event)
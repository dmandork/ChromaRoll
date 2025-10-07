# states/base.py
class State:
    def __init__(self, game):
        self.game = game  # Reference to ChromaRollGame for shared state (e.g., self.game.coins)

    def enter(self):
        pass  # Optional: Setup when entering (e.g., reset timers)

    def exit(self):
        pass  # Optional: Cleanup when leaving (e.g., stop sounds)

    def update(self, dt):
        pass  # Game logic/timers/animations

    def draw(self):
        pass  # Render the screen

    def handle_event(self, event):
        pass  # Handle inputs/events

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
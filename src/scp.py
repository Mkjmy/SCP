# scp.py

import mechanics
import random

class SCP:
    """
    Base class for all SCP entities.
    Modularly built using 'Mechanics' from the Primitive Engine.
    """
    
    # Behavior States
    STATE_CONTAINED = "contained" # In its cell, quiet
    STATE_ACTIVE = "active"       # Acting within its cell or near it
    STATE_BREACHED = "breached"   # Out of its cell, hunting/wandering

    def __init__(self, scp_id, name, object_class, initial_room):
        self.id = scp_id
        self.name = name
        self.object_class = object_class # e.g., 'Safe', 'Euclid', 'Keter'
        self.current_room = initial_room
        self.containment_room = initial_room # The specific room where it belongs
        
        self.state = self.STATE_CONTAINED
        self.is_contained = True # Legacy support, maps to state
        
        self.activity_level = 0.5 # 0.0 to 1.0, how often it acts when it can
        self.description = "A mysterious anomaly."
        self.mechanics = []

    def set_state(self, new_state):
        self.state = new_state
        self.is_contained = (new_state == self.STATE_CONTAINED)

    def add_mechanic(self, mechanic_key, params=None):
        """Adds a mechanic to this SCP using its registry key."""
        mechanic_class = mechanics.get_mechanic_class(mechanic_key)
        if mechanic_class:
            mechanic_instance = mechanic_class(self, params)
            self.mechanics.append(mechanic_instance)
        else:
            print(f"Error: Mechanic key '{mechanic_key}' not found in registry.")

    def trigger_event(self, event_name, **kwargs):
        """Dispatches an event to all attached mechanics and returns any results."""
        # Check for activity based on activity_level for turn-based events
        if event_name in ["tick", "turn_start", "player_move"]:
            if random.random() > self.activity_level:
                return [] # Skip this action

        results = []
        for mechanic in self.mechanics:
            res = mechanic.on_event(event_name, **kwargs)
            if res:
                results.append(res)
        return results

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_status(self):
        """Returns a basic status string for the SCP."""
        mechanic_names = [m.__class__.__name__.replace('Mechanic', '') for m in self.mechanics]
        return (
            f"SCP ID: {self.id}\n"
            f"Name: {self.name}\n"
            f"Object Class: {self.object_class}\n"
            f"Current Room: {self.current_room}\n"
            f"Contained: {self.is_contained}\n"
            f"Mechanics: {', '.join(mechanic_names)}\n"
            f"Description: {self.description}"
        )

    # --- Standard event hooks (now dispatch to mechanics) ---

    def on_player_perceive(self, player, game_state):
        return self.trigger_event("player_perceive", player=player, game_state=game_state)

    def on_memory_tick(self, player, game_state):
        return self.trigger_event("memory_tick", player=player, game_state=game_state)

    def on_player_move(self, player, direction, game_state):
        return self.trigger_event("player_move", player=player, direction=direction, game_state=game_state)

    def on_turn_start(self, player, game_state):
        return self.trigger_event("turn_start", player=player, game_state=game_state)

    def on_tick(self, player, game_state):
        return self.trigger_event("tick", player=player, game_state=game_state)

    def on_player_near(self, player, game_state):
        return self.trigger_event("player_near", player=player, game_state=game_state)

    def on_player_attack(self, player, game_state):
        return self.trigger_event("player_attack", player=player, game_state=game_state)

    def on_player_run(self, player, game_state):
        return self.trigger_event("player_run", player=player, game_state=game_state)

    def on_player_talk(self, player, game_state):
        return self.trigger_event("player_talk", player=player, game_state=game_state)

    def on_atmosphere_check(self, player, game_state):
        return self.trigger_event("atmosphere_check", player=player, game_state=game_state)

    def on_observe_description(self, player, description):
        results = self.trigger_event("observe_description", player=player, description=description)
        # For description, we might want to use the last modification or a chain
        # If any mechanic redacted it, return that.
        for res in results:
            if res != description:
                return res
        return description

    def on_breach(self, game_state):
        self.is_contained = False
        print(f"{self.name} ({self.id}) has breached containment!")

    def on_contain(self, game_state):
        self.is_contained = True
        print(f"{self.name} ({self.id}) has been re-contained.")

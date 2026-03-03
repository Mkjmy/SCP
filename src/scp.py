# scp.py

import mechanics

class SCP:
    """
    Base class for all SCP entities.
    Modularly built using 'Mechanics' from the Primitive Engine.
    """
    def __init__(self, scp_id, name, object_class, initial_room):
        self.id = scp_id
        self.name = name
        self.object_class = object_class # e.g., 'Safe', 'Euclid', 'Keter'
        self.current_room = initial_room
        self.is_contained = True # True if in its containment cell, False if breached
        self.description = "A mysterious anomaly." # Default description
        self.mechanics = [] # List of BaseMechanic-derived objects

    def add_mechanic(self, mechanic_class_name, params=None):
        """Adds a mechanic to this SCP by class name."""
        try:
            # Assuming mechanics are in the 'mechanics' module
            mechanic_class = getattr(mechanics, f"{mechanic_class_name}Mechanic")
            mechanic_instance = mechanic_class(self, params)
            self.mechanics.append(mechanic_instance)
        except AttributeError:
            print(f"Error: Mechanic '{mechanic_class_name}' not found in mechanics module.")

    def trigger_event(self, event_name, **kwargs):
        """Dispatches an event to all attached mechanics and returns any results."""
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

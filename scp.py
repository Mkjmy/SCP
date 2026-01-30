# scp.py

class SCP:
    """
    Base class for all SCP entities.
    Provides common properties and placeholder methods for unique abilities.
    """
    def __init__(self, scp_id, name, object_class, initial_room):
        self.id = scp_id
        self.name = name
        self.object_class = object_class # e.g., 'Safe', 'Euclid', 'Keter'
        self.current_room = initial_room
        self.is_contained = True # True if in its containment cell, False if breached
        self.description = "A mysterious anomaly." # Default description

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_status(self):
        """Returns a basic status string for the SCP."""
        return (
            f"SCP ID: {self.id}\n"
            f"Name: {self.name}\n"
            f"Object Class: {self.object_class}\n"
            f"Current Room: {self.current_room}\n"
            f"Contained: {self.is_contained}\n"
            f"Description: {self.description}"
        )

    # --- Placeholder methods for game events (to be overridden by specific SCPs) ---

    def on_player_enter_room(self, player_location, game_state):
        """Called when the player enters the same room as this SCP."""
        pass

    def on_player_observe(self, player_is_observing, game_state):
        """
        Called when the player's observation status changes or is checked.
        `player_is_observing` is a boolean.
        """
        pass

    def on_turn_start(self, game_state):
        """Called at the beginning of each game turn."""
        pass

    def on_turn_end(self, game_state):
        """Called at the end of each game turn."""
        pass

    def on_breach(self, game_state):
        """Called when the SCP breaches containment."""
        self.is_contained = False
        print(f"{self.name} ({self.id}) has breached containment!")

    def on_contain(self, game_state):
        """Called when the SCP is re-contained."""
        self.is_contained = True
        print(f"{self.name} ({self.id}) has been re-contained.")

    # Add more event hooks as needed for different SCP behaviors

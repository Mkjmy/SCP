# mechanics.py

class BaseMechanic:
    """Base class for all SCP mechanics."""
    def __init__(self, scp, params=None):
        self.scp = scp
        self.params = params or {}

    def on_event(self, event_name, **kwargs):
        """Dispatches an event to the appropriate handler."""
        handler = getattr(self, f"on_{event_name}", None)
        if callable(handler):
            return handler(**kwargs)
        return None

    # --- Primitive Primitives (Utility methods for all mechanics) ---

    def damage_player(self, player, amount, reason=None):
        player.health -= amount
        msg = f"You took {amount} damage from {self.scp.name}."
        if reason: msg += f" ({reason})"
        return msg

    def drain_sanity(self, player, amount, reason=None):
        return player.change_sanity(-amount)

    def change_morale(self, player, amount):
        return player.change_morale(amount)

# --- 1. Perception Layer ---
# ... (rest of classes will be updated and registered below)

class PerceptionMechanic(BaseMechanic):
    """
    Handles how the SCP is perceived and how it perceives others.
    Primitives: Line of sight, Attention, Awareness, Memory, Cognitohazard, etc.
    """
    def on_player_perceive(self, player, game_state):
        """Called when the player might perceive this SCP."""
        # Cognitohazard effect
        if self.params.get("cognitohazard"):
            effect = self.params.get("cognitohazard_effect", "confusion")
            return self.apply_effect(player, effect)
        
        # Antimeme effect
        if self.params.get("antimeme"):
            player.perception["memory_persistence"][self.scp.id] = 0
            return "You see something... but you've already forgotten what it was."
        
        return None

    def on_memory_tick(self, player, game_state):
        """Called every tick to handle memory persistence."""
        if self.params.get("antimeme"):
            if self.scp.id in player.perception.get("memory", {}):
                del player.perception["memory"][self.scp.id]
                return f"Information about {self.scp.name} has vanished from your mind."
        return None

    def apply_effect(self, player, effect_type):
        # Placeholder for applying effects to player
        return f"The sight of {self.scp.name} causes {effect_type}!"

# --- 2. Reality Layer ---

class RealityMechanic(BaseMechanic):
    """
    Handles reality bending and rule modification.
    Primitives: Reality stability, Reality bending, Probability, Time, Dimensions.
    """
    def modify_rule(self, player, rule_name, new_value):
        """Changes a global or local rule without hardcoding."""
        player.active_rules[rule_name] = new_value
        return f"Reality shifts: {rule_name} is now {new_value}."

    def on_turn_start(self, player, game_state):
        if self.params.get("reality_bending"):
            # Example: modify gravity or movement cost
            rule = self.params.get("rule_to_bend", "stamina_cost_multiplier")
            value = self.params.get("bend_value", 2.0)
            return self.modify_rule(player, rule, value)
        return None

# --- 3. Spatial Concepts ---

class SpatialMechanic(BaseMechanic):
    """
    Handles non-Euclidean space and topology.
    Primitives: Non-Euclidean, Teleport, Pocket dimension, Room mutation.
    """
    def on_player_move(self, player, direction, game_state):
        if self.params.get("non_euclidean"):
            # Example: moving North leads to a random room
            if direction == self.params.get("trigger_direction", "north"):
                target_room = self.params.get("target_room", "pocket_dimension")
                player.location = target_room
                return f"The hallway warps. You find yourself in {target_room}."
        return None

# --- 4. Cognitive / Psychological ---

class CognitiveMechanic(BaseMechanic):
    """
    Handles mental states and influence.
    Primitives: Fear, Obsession, Compulsion, Rage, Influence radius.
    """
    def apply_mind_state(self, player, state):
        if state not in player.mind_states:
            player.mind_states.add(state)
            return f"You are now feeling {state}."
        return None

    def on_player_near(self, player, game_state):
        if self.params.get("fear_aura"):
            radius = self.params.get("radius", 1)
            # Logic to check distance would go here
            return self.apply_mind_state(player, "terrified")
        return None

# --- 5. Biological / Physical ---

class BioPhysicalMechanic(BaseMechanic):
    """
    Handles biological effects.
    Primitives: Infection, Mutation, Regeneration, Decay.
    """
    def on_tick(self, player, game_state):
        if self.params.get("infection"):
            if self.scp.current_room == player.location:
                return self.damage_player(player, self.params.get("decay_rate", 1), reason="corrosive infection")
        return None

# --- 6. Information Mechanics ---

class InformationMechanic(BaseMechanic):
    """
    Handles knowledge and visibility.
    Primitives: Knowledge gate, Redacted state, Access level.
    """
    def redact_output(self, text, clearance_level, required_level):
        if clearance_level < required_level:
            return "[REDACTED]"
        return text

    def on_observe_description(self, player, description):
        if self.params.get("infohazard") and player.clearance_level < self.params.get("required_clearance", 4):
            return self.redact_output(description, player.clearance_level, self.params.get("required_clearance", 4))
        return description

# --- 7. Narrative Layer (Meta) ---

class NarrativeMechanic(BaseMechanic):
    """
    Handles atmosphere, story branches, and meta-narrative.
    Primitives: Atmosphere, Plot armor, Author override, Narrative awareness.
    """
    def _handle_interaction(self, player, interaction_type):
        story_key = f"story_{interaction_type}"
        if story_key in self.params:
            outcome = self.params[story_key]
            # Handle optional effects
            if isinstance(outcome, dict):
                msg = outcome.get("message", "")
                if outcome.get("kill"):
                    player.health = 0
                elif "damage" in outcome:
                    self.damage_player(player, outcome["damage"])
                return msg
            return outcome
        return None

    def on_player_attack(self, player, game_state):
        return self._handle_interaction(player, "attack")

    def on_player_run(self, player, game_state):
        return self._handle_interaction(player, "run")

    def on_player_talk(self, player, game_state):
        return self._handle_interaction(player, "talk")

    def on_atmosphere_check(self, player, game_state):
        if self.params.get("atmosphere_shift"):
            mood = self.params.get("mood", "minimal")
            return f"The air grows heavy. Current atmosphere: {mood}"
        return None

# --- Registry System ---

MECHANIC_REGISTRY = {
    "perception": PerceptionMechanic,
    "reality": RealityMechanic,
    "spatial": SpatialMechanic,
    "cognitive": CognitiveMechanic,
    "biophysical": BioPhysicalMechanic,
    "information": InformationMechanic,
    "narrative": NarrativeMechanic
}

def get_mechanic_class(name):
    """Returns the mechanic class mapped to the given name."""
    return MECHANIC_REGISTRY.get(name.lower())

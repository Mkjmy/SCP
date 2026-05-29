# story_manager.py
import json
import os

class StoryManager:
    def __init__(self, storyline_file):
        self.storyline_file = storyline_file
        self.data = self.load_storyline()
        self.active_events = []
        self.completed_events = set()
        self.turn_counter = 0
        self.facility_code = "GREEN" # Possible: GREEN, YELLOW, RED

    def load_storyline(self):
        if not os.path.exists(self.storyline_file):
            return {}
        with open(self.storyline_file, 'r') as f:
            return json.load(f)

    def check_events(self, current_turn, player, npc_manager, scp_manager):
        """Checks if any events should trigger this turn."""
        self.turn_counter = current_turn
        triggered_data = {"messages": [], "event": None}
        
        for chapter_id, chapter_data in self.data.items():
            for event in chapter_data.get("events", []):
                event_id = event.get("id")
                if event_id in self.completed_events:
                    continue
                
                if current_turn == event.get("trigger_turn"):
                    # Handle state changes immediately
                    if event.get("type") == "UPDATE_CODE":
                        self.facility_code = event.get("code", "GREEN")
                        triggered_data["messages"].append(f"--- SYSTEM NOTIFICATION: SECURITY LEVEL {self.facility_code} ---")
                        self.completed_events.add(event_id)
                        continue

                    # Check for NPCs to spawn
                    if "spawns" in event:
                        triggered_data["spawns"] = event["spawns"]

                    # If it's a CHOICE, we return the whole event to main_loop for processing
                    if event.get("type") == "CHOICE":
                        triggered_data["event"] = event
                        return triggered_data 
                    
                    res = self.execute_event(event, player, npc_manager, scp_manager)
                    if res: triggered_data["messages"].append(res)
                    self.completed_events.add(event_id)
        
        return triggered_data

    def execute_choice(self, event, choice_id, player, npc_manager):
        """Executes the results of a player choosing an option in an event."""
        chosen_option = next((opt for opt in event.get("options", []) if opt["id"] == choice_id), None)
        if not chosen_option: return "Invalid choice."

        msg = chosen_option.get("log", "Event completed.")
        effects = chosen_option.get("effect", {})

        # Apply Effects
        if "morale" in effects: player.change_morale(effects["morale"])
        if "health" in effects: player.health += effects["health"]
        if "stamina" in effects: player.stamina += effects["stamina"]
        if "sanity" in effects: player.change_sanity(effects.get("sanity", 0))

        # New Social/Anatomy Effects
        if "inventory" in effects:
            player.inventory.append(effects["inventory"])
            msg += f"\n[Obtained: {effects['inventory']}]"

        if "injury" in effects:
            part, severity = effects["injury"].split(":")
            # Use 'neck' as a proxy for 'spine' or 'skull' if exact part is missing
            injury_res = player.apply_injury(part if part in player.body_parts else 'spine', severity)
            msg += f"\n{injury_res}"

        if "loyalty" in effects:
            # We'll assume player.loyalty exists or just store in discovered_intel
            player.discovered_intel.append(f"Loyalty: {effects['loyalty']}")
            msg += f"\nYour status with the Foundation has shifted: {effects['loyalty']}"

        # Log the social/narrative result
        self.completed_events.add(event.get("id"))
        return f"Selection: {chosen_option.get('text')}\n\nResult: {msg}"


    def execute_event(self, event, player, npc_manager, scp_manager):
        """Executes non-choice events."""
        event_type = event.get("type")
        if event_type == "MESSAGE":
            # Store message to be shown in main loop
            return event.get("message")
        return None

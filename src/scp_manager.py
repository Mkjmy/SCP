# scp_manager.py
import importlib
import json
import random
from scp import SCP # Import the base SCP class

class SCPManager:
    def __init__(self, map_data):
        self.map_data = map_data
        self._scps = {} # {scp_id: SCP_instance}

    def load_scps_from_definitions(self, definitions_file):
        """
        Loads SCP definitions from a new hierarchical JSON structure.
        The JSON maps zone_id to a dictionary containing 'entity' and 'structure'.
        """
        try:
            with open(definitions_file, 'r') as f:
                zone_defs = json.load(f)
        except FileNotFoundError:
            print(f"Error: SCP definitions file '{definitions_file}' not found.")
            return

        for zone_id, zone_data in zone_defs.items():
            entity_data = zone_data.get("entity")
            if not entity_data:
                print(f"Warning: Zone {zone_id} is missing 'entity' data. Skipping.")
                continue

            scp_id = entity_data.get("id", zone_id)

            try:
                # Instantiate the base SCP class
                # Note: In a procedural map, initial_room will be assigned by the map generator
                scp_instance = SCP(
                    scp_id=scp_id,
                    name=entity_data.get("name", scp_id),
                    object_class=entity_data.get("object_class", "Euclid"),
                    initial_room="pending_assignment"
                )
                scp_instance.description = entity_data.get("description", scp_instance.description)
                scp_instance.activity_level = entity_data.get("activity_level", 0.5)
                
                # Load mechanics
                mechanic_defs = entity_data.get("mechanics", [])
                for mech_def in mechanic_defs:
                    mech_type = mech_def.get("type")
                    mech_params = mech_def.get("params", {})
                    if mech_type:
                        scp_instance.add_mechanic(mech_type, mech_params)

                self._scps[scp_id] = scp_instance
                # print(f"Loaded {scp_instance.name} ({scp_id}) with {len(scp_instance.mechanics)} mechanics.")

            except Exception as e:
                print(f"Error loading SCP {scp_id} from {zone_id}: {e}")

    def get_scp_by_id(self, scp_id):
        return self._scps.get(scp_id)

    def get_scps_in_room(self, room_id):
        return [scp for scp in self._scps.values() if scp.current_room == room_id]

    def move_scp(self, scp_id, target_room_id):
        scp = self._scps.get(scp_id)
        if scp and target_room_id in self.map_data:
            print(f"Moving {scp.name} from {scp.current_room} to {target_room_id}")
            scp.current_room = target_room_id
            return True
        print(f"Failed to move SCP {scp_id} to {target_room_id}.")
        return False

    def trigger_event(self, event_name, **kwargs):
        """Dispatches an event to all active SCPs."""
        for scp in self._scps.values():
            event_method = getattr(scp, event_name, None)
            if callable(event_method):
                event_method(**kwargs)

    def get_scp_locations_for_display(self):
        """
        Returns a dictionary mapping room_id to a list of SCP IDs or markers for display.
        Example: {"room_id": ["SCP-173", "SCP-049"]} or {"room_id": ["173", "049"]}
        """
        display_locations = {}
        for scp_id, scp_instance in self._scps.items():
            room_id = scp_instance.current_room
            marker = scp_instance.id.split('_')[1] # e.g., '173' from 'scp_173'
            
            if room_id not in display_locations:
                display_locations[room_id] = []
            display_locations[room_id].append(marker)
        return display_locations


# For testing purposes (will be integrated into main.py later)
if __name__ == "__main__":
    from map_visualizer import load_map_data, generate_ascii_map

    # 1. Load map data
    map_data = load_map_data()
    if not map_data:
        print("Could not load map data. Exiting SCPManager test.")
    else:
        # 2. Create SCPManager instance
        scp_manager = SCPManager(map_data)

        # 3. Create a dummy SCP definitions file for testing
        dummy_scp_definitions = {
            "scp_173": {
                "class_name": "SCP173", # This class will be created later
                "name": "SCP-173 The Sculpture",
                "object_class": "Keter",
                "initial_room": "hallway_a",
                "description": "A statue that moves when not observed."
            },
            "scp_049": {
                "class_name": "SCP049", # This class will be created later
                "name": "SCP-049 The Plague Doctor",
                "object_class": "Euclid",
                "initial_room": "control_room",
                "description": "A humanoid entity resembling a medieval plague doctor."
            }
        }
        with open("scp_definitions.json", "w") as f:
            json.dump(dummy_scp_definitions, f, indent=2)
        print("Created dummy scp_definitions.json")

        # 4. Load SCPs
        scp_manager.load_scps_from_definitions("scp_definitions.json")
        
        print("\n--- Initial SCP Status ---")
        for scp_id, scp in scp_manager._scps.items():
            print(f"- {scp.name} ({scp.id}) in {scp.current_room}")

        # 5. Display initial map with SCPs (using map_visualizer)
        print("\n--- Initial Map with SCPs ---")
        scp_display_locations = scp_manager.get_scp_locations_for_display()
        # For map_visualizer, we need to map the SCP ID to a short marker
        # This will need to be refined: map_visualizer expects single-char roles for NPCs
        # For SCPs, perhaps just use the number (e.g., '173', '049')
        # We need to adapt the visualizer to handle this if it expects single chars.
        
        # Current map_visualizer expects a list of single characters.
        # Let's adapt scp_display_locations to match for now:
        # Example: {"hallway_a": ["173"], "control_room": ["049"]}
        
        # The visualizer will need to be flexible for NPC chars vs SCP numbers.
        # For testing, let's just make sure it passes something it can display.
        # If the visualizer can't handle multiple characters, we might need a custom draw for SCPs.
        
        # Let's temporarily pass the raw SCP ID (e.g., "173") as a marker
        # This will mean my modified draw_text in map_visualizer will display "[173]"
        ascii_map = generate_ascii_map(map_data, scp_display_locations)
        print(ascii_map)

        # 6. Simulate movement for an SCP
        print("\n--- Simulating SCP Movement ---")
        scp_id_to_move = "scp_173"
        target_room = "hallway_b"
        scp_manager.move_scp(scp_id_to_move, target_room)

        print("\n--- SCP Status After Movement ---")
        for scp_id, scp in scp_manager._scps.items():
            print(f"- {scp.name} ({scp.id}) in {scp.current_room}")

        # 7. Display map after movement
        print("\n--- Map After Movement ---")
        scp_display_locations_after_move = scp_manager.get_scp_locations_for_display()
        ascii_map_after_move = generate_ascii_map(map_data, scp_display_locations_after_move)
        print(ascii_map_after_move)

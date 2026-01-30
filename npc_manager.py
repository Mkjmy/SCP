import random
import datetime
from character import Character, generate_character # Assuming character.py is in the same directory

class NPCManager:
    def __init__(self, map_data):
        self.map_data = map_data
        self._npcs = {} # {npc_id: {"character": Character_obj, "current_room": "room_id", "last_moved_at": datetime_obj}}
        self._next_npc_id = 1

    def spawn_npc(self, role, initial_room_id):
        if initial_room_id not in self.map_data:
            print(f"Warning: Attempted to spawn NPC in non-existent room: {initial_room_id}")
            return None

        npc_character = generate_character(role)
        npc_id = f"npc_{self._next_npc_id:03d}"
        self._next_npc_id += 1

        self._npcs[npc_id] = {
            "character": npc_character,
            "current_room": initial_room_id,
            "last_moved_at": datetime.datetime.now()
        }
        print(f"Spawned {npc_character.name} ({role}) with ID {npc_id} in {initial_room_id}")
        return npc_id

    def move_npc(self, npc_id):
        if npc_id not in self._npcs:
            print(f"Warning: NPC with ID {npc_id} not found for movement.")
            return False

        npc_info = self._npcs[npc_id]
        current_room_id = npc_info["current_room"]

        room_exits = self.map_data.get(current_room_id, {}).get("exits", {})
        if not room_exits:
            print(f"NPC {npc_info['character'].name} in {current_room_id} has no exits to move to.")
            return False

        # Choose a random exit
        destination_room_id = random.choice(list(room_exits.values()))
        
        npc_info["current_room"] = destination_room_id
        npc_info["last_moved_at"] = datetime.datetime.now()
        # print(f"NPC {npc_info['character'].name} moved to {destination_room_id}")
        return True

    def get_npc_locations_for_display(self):
        """
        Returns a dictionary suitable for map_visualizer.py, mapping room_id to list of NPC role chars.
        Example: {"room_id": ["G", "S"]}
        """
        display_locations = {}
        for npc_id, npc_info in self._npcs.items():
            room_id = npc_info["current_room"]
            role_char = npc_info["character"].role[0] # Use first letter of role as marker

            if room_id not in display_locations:
                display_locations[room_id] = []
            display_locations[room_id].append(role_char)
        return display_locations

    def get_npc_status(self, npc_id=None):
        """
        Returns detailed status for a specific NPC, or all NPCs if npc_id is None.
        Includes current room and last moved timestamp.
        """
        if npc_id and npc_id not in self._npcs:
            return f"NPC with ID {npc_id} not found."
        
        if npc_id:
            npc_info = self._npcs[npc_id]
            char = npc_info['character']
            return (
                f"{char.name} ({char.role}, ID: {npc_id})\n"
                f"  Current Room: {npc_info['current_room']}\n"
                f"  Last Moved: {npc_info['last_moved_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            all_npc_status = []
            for id, info in self._npcs.items():
                char = info['character']
                all_npc_status.append(
                    f"{char.name} ({char.role}, ID: {id}) in {info['current_room']} "
                    f"(Last Moved: {info['last_moved_at'].strftime('%Y-%m-%d %H:%M:%S')})"
                )
            return "\n".join(all_npc_status)

# For testing (can be removed later)
if __name__ == "__main__":
    from map_visualizer import load_map_data, generate_ascii_map

    # Load dummy map data
    map_data = load_map_data()
    if map_data:
        npc_manager = NPCManager(map_data)

        # Spawn some NPCs
        npc_manager.spawn_npc("Guard", "hallway_a")
        npc_manager.spawn_npc("Scientist", "control_room")
        npc_manager.spawn_npc("D-Class", "cell")
        npc_manager.spawn_npc("Guard", "hallway_b")

        print("\n--- Initial NPC Status ---")
        print(npc_manager.get_npc_status())

        # Display initial map with NPCs
        print("\n--- Initial Map with NPCs ---")
        display_locations = npc_manager.get_npc_locations_for_display()
        ascii_map = generate_ascii_map(map_data, display_locations)
        print(ascii_map)

        # Simulate some movement
        print("\n--- Simulating NPC Movement ---")
        for _ in range(5): # Move each NPC 5 times
            for npc_id in list(npc_manager._npcs.keys()): # Iterate over a copy of keys as dict might change
                npc_manager.move_npc(npc_id)

        print("\n--- NPC Status After Movement ---")
        print(npc_manager.get_npc_status())

        # Display map after movement
        print("\n--- Map After Movement ---")
        display_locations_after_move = npc_manager.get_npc_locations_for_display()
        ascii_map_after_move = generate_ascii_map(map_data, display_locations_after_move)
        print(ascii_map_after_move)

# door_manager.py

class DoorManager:
    def __init__(self, map_data):
        self.map_data = map_data

    def get_door_details(self, current_room_id, direction):
        """
        Returns the full exit dictionary for a given room and direction.
        e.g., {"destination": "hallway_a", "door_level": 1}
        Returns None if no such exit exists.
        """
        room = self.map_data.get(current_room_id)
        if room and "exits" in room:
            exit_info = room["exits"].get(direction)
            if exit_info:
                # Ensure it's in the dictionary format
                if isinstance(exit_info, str):
                    return {"destination": exit_info, "door_level": 0}
                return exit_info
        return None

    def get_door_level(self, current_room_id, direction):
        """
        Returns the door_level for a specific exit.
        Returns 0 if no explicit level is defined (i.e., open to all),
        or None if no exit exists in that direction.
        """
        door_details = self.get_door_details(current_room_id, direction)
        if door_details:
            return door_details.get("door_level", 0) # Default to 0 if not specified
        return None # No exit in that direction

    def check_access(self, entity_clearance_level, current_room_id, direction):
        """
        Checks if an entity with entity_clearance_level can open the door
        in the specified direction from current_room_id.
        Returns True if accessible, False otherwise.
        """
        required_level = self.get_door_level(current_room_id, direction)
        if required_level is None: # No exit in that direction
            return False
        
        return entity_clearance_level >= required_level

    def get_destination(self, current_room_id, direction):
        """
        Returns the destination room_id for a given room and direction.
        Returns None if no such exit exists.
        """
        door_details = self.get_door_details(current_room_id, direction)
        if door_details:
            return door_details.get("destination")
        return None


# For testing purposes
if __name__ == "__main__":
    from map_visualizer import load_map_data

    map_data = load_map_data()
    if map_data:
        door_manager = DoorManager(map_data)

        # Test cases
        print("--- Testing Door Access ---")

        # Cell east (level 1)
        print(f"Player (L0) trying to go from cell east: {door_manager.check_access(0, 'cell', 'east')}") # Should be False
        print(f"Player (L1) trying to go from cell east: {door_manager.check_access(1, 'cell', 'east')}") # Should be True
        print(f"Player (L2) trying to go from cell east: {door_manager.check_access(2, 'cell', 'east')}") # Should be True

        # Hallway A east (level 0)
        print(f"Player (L0) trying to go from hallway_a east: {door_manager.check_access(0, 'hallway_a', 'east')}") # Should be True

        # Hallway B north (level 2)
        print(f"Player (L1) trying to go from hallway_b north: {door_manager.check_access(1, 'hallway_b', 'north')}") # Should be False
        print(f"Player (L2) trying to go from hallway_b north: {door_manager.check_access(2, 'hallway_b', 'north')}") # Should be True
        
        # Non-existent exit
        print(f"Player (L0) trying to go from cell north: {door_manager.check_access(0, 'cell', 'north')}") # Should be False
        print(f"Door level for cell north: {door_manager.get_door_level('cell', 'north')}") # Should be None

        # Get destination
        print(f"Destination from cell east: {door_manager.get_destination('cell', 'east')}")
        print(f"Destination from hallway_b north: {door_manager.get_destination('hallway_b', 'north')}")

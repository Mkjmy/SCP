# navigation.py
# Assuming DoorManager will be passed as an instance, no direct import of the class is needed here
# but if type hinting or class methods were used, it would be imported.

def move(player, direction, game_map, door_manager):
    """Attempts to move the player in a given direction, checking door access."""
    current_room_id = player.location
    
    # Check if there's an exit in that direction at all
    destination_room_id = door_manager.get_destination(current_room_id, direction)
    if destination_room_id is None:
        return False, "You can't go that way."

    # Check if the player has sufficient clearance to open the door
    if not door_manager.check_access(player.clearance_level, current_room_id, direction):
        required_level = door_manager.get_door_level(current_room_id, direction)
        return False, f"Access Denied: Door requires Clearance Level {required_level}."
    
    # If access is granted, update player's location
    player.location = destination_room_id
    return True, ""

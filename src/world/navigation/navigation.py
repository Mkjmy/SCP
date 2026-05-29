# navigation.py
# Assuming DoorManager will be passed as an instance, no direct import of the class is needed here
# but if type hinting or class methods were used, it would be imported.

def move(player, direction, game_map, door_manager):
    """Attempts to move the player in a given direction, checking door access and inventory for cards."""
    current_room_id = player.location
    
    # Check if there's an exit in that direction
    destination_room_id = door_manager.get_destination(current_room_id, direction)
    if destination_room_id is None:
        return False, "You can't go that way."

    # Check for physical keycards in inventory
    effective_clearance = player.clearance_level
    for item in player.inventory:
        if "Keycard" in item:
            try:
                # Extract level from string like 'Level 2 Keycard'
                level = int(item.split("Level ")[1].split()[0])
                effective_clearance = max(effective_clearance, level)
            except: pass

    # Check if the player has sufficient clearance
    if not door_manager.check_access(effective_clearance, current_room_id, direction):
        required_level = door_manager.get_door_level(current_room_id, direction)
        return False, f"Access Denied: Door requires Clearance Level {required_level}."
    
    # If access is granted, update player's location
    player.location = destination_room_id
    return True, ""

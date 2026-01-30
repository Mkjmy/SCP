# navigation.py
def move(player, direction, game_map):
    """Attempts to move the player in a given direction."""
    current_room_id = player.location
    current_room = game_map[current_room_id]
    
    if direction in current_room['exits']:
        new_location = current_room['exits'][direction]
        player.location = new_location
        return True, ""
    else:
        return False, "You can't go that way."

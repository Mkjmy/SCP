import json
import os
import re

OPPOSITE_DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east"
}

def _parse_room_id(room_id):
    """Parses a room ID (e.g., 'room_0_0') into (x, y) coordinates."""
    match = re.match(r"room_(-?\d+)_(-?\d+)", room_id)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def visualize_map_ascii(game_map, player_location_id):
    """
    Generates an ASCII text diagram of the game map.
    
    Args:
        game_map (dict): The dictionary representation of the game map.
        player_location_id (str): The current room ID of the player.

    Returns:
        str: An ASCII string representation of the map.
    """
    if not game_map:
        return "Map is empty."

    # Determine map boundaries
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')

    coords_to_room_id = {}
    for room_id in game_map:
        x, y = _parse_room_id(room_id)
        if x is not None and y is not None:
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            coords_to_room_id[(x, y)] = room_id

    # If no valid rooms were found (e.g., if game_map was empty or all room_ids failed parsing)
    if min_x == float('inf'):
        return "No valid room coordinates found for visualization."
        
    # Add padding for better visualization
    min_x -= 1
    max_x += 1
    min_y -= 1
    max_y += 1

    width = int((max_x - min_x) * 4 + 1) # Each room block is 3 wide + 1 for separator
    height = int((max_y - min_y) * 2 + 1) # Each room block is 1 high + 1 for separator

    ascii_grid = [[' ' for _ in range(width)] for _ in range(height)]

    player_x, player_y = _parse_room_id(player_location_id)

    for y_coord in range(min_y, max_y + 1):
        for x_coord in range(min_x, max_x + 1):
            grid_x = (x_coord - min_x) * 4
            grid_y = (max_y - y_coord) * 2 # Invert Y for curses display (top-down)

            room_id = coords_to_room_id.get((x_coord, y_coord))

            if room_id:
                room_data = game_map[room_id]
                
                # Draw room center
                if x_coord == player_x and y_coord == player_y:
                    ascii_grid[grid_y][grid_x + 1] = '@' # Player location
                else:
                    ascii_grid[grid_y][grid_x + 1] = 'O' # Room marker
                
                # Draw exits
                for exit_dir, target_room_id in room_data["exits"].items():
                    target_x, target_y = _parse_room_id(target_room_id)
                    
                    # Connection between current room and neighbor
                    if exit_dir == "north" and target_y > y_coord:
                        ascii_grid[grid_y - 1][grid_x + 1] = '|'
                    elif exit_dir == "south" and target_y < y_coord:
                        ascii_grid[grid_y + 1][grid_x + 1] = '|'
                    elif exit_dir == "east" and target_x > x_coord:
                        ascii_grid[grid_y][grid_x + 2] = '-'
                        ascii_grid[grid_y][grid_x + 3] = '-'
                    elif exit_dir == "west" and target_x < x_coord:
                        ascii_grid[grid_y][grid_x] = '-'
                        ascii_grid[grid_y][grid_x - 1] = '-'
            else:
                # Fill empty cells
                pass # Already ' '

    # Convert grid to string
    map_string_lines = ["".join(row).rstrip() for row in ascii_grid]
    # Remove empty lines at the end
    while map_string_lines and not map_string_lines[-1].strip():
        map_string_lines.pop()
    
    return "\n".join(map_string_lines)

if __name__ == '__main__':
    # Example usage:
    # This dummy map must have room_X_Y IDs
    dummy_map = {
        "room_0_0": {"name": "Start", "exits": {"north": "room_0_1", "east": "room_1_0"}},
        "room_0_1": {"name": "North", "exits": {"south": "room_0_0", "east": "room_1_1"}},
        "room_1_0": {"name": "East", "exits": {"north": "room_1_1", "west": "room_0_0"}},
        "room_1_1": {"name": "Junction", "exits": {"south": "room_1_0", "west": "room_0_1"}}
    }
    print("Dummy Map:")
    print(visualize_map_ascii(dummy_map, "room_0_0"))

    dummy_map2 = {
        "room_0_0": {"name": "Cell", "exits": {"north": "room_0_1"}},
        "room_0_1": {"name": "Hall", "exits": {"north": "room_0_2", "south": "room_0_0", "east": "room_1_1"}},
        "room_0_2": {"name": "Lab", "exits": {"south": "room_0_1"}},
        "room_1_1": {"name": "Storage", "exits": {"west": "room_0_1"}}
    }
    print("\nAnother Dummy Map (Player at room_0_1):")
    print(visualize_map_ascii(dummy_map2, "room_0_1"))

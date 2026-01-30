import json
import os

def load_map_data(filename="debug_output/debug_map.json"):
    """Loads map data from a JSON file."""
    if not os.path.exists(filename):
        print(f"Error: Map file not found at '{filename}'")
        return None
    with open(filename, 'r') as f:
        return json.load(f)

def generate_ascii_map(map_data, npc_locations=None):
    """Generates an ASCII representation of the map."""
    if not map_data:
        return "Map data is empty."

    # 1. Assign coordinates to rooms
    room_coords = {}
    q = [('cell', (0, 0))]  # Start with the initial cell
    room_coords['cell'] = (0, 0)
    visited = {'cell'}

    head = 0
    while head < len(q):
        current_room_id, (x, y) = q[head]
        head += 1

        room = map_data.get(current_room_id)
        if not room:
            continue

        for direction, dest_room_id in room.get("exits", {}).items():
            if dest_room_id not in visited:
                dx, dy = 0, 0
                if direction == 'north':
                    dy = -1
                elif direction == 'south':
                    dy = 1
                elif direction == 'east':
                    dx = 1
                elif direction == 'west':
                    dx = -1

                new_coords = (x + dx, y + dy)
                room_coords[dest_room_id] = new_coords
                visited.add(dest_room_id)
                q.append((dest_room_id, new_coords))

    if not room_coords:
        return "No rooms with coordinates found."

    # 2. Determine grid boundaries
    min_x = min(c[0] for c in room_coords.values())
    max_x = max(c[0] for c in room_coords.values())
    min_y = min(c[1] for c in room_coords.values())
    max_y = max(c[1] for c in room_coords.values())

    # 3. Prepare for drawing
    room_width = 22
    room_height = 3
    h_spacing = 5
    v_spacing = 2

    grid_width = (max_x - min_x + 1) * (room_width + h_spacing)
    grid_height = (max_y - min_y + 1) * (room_height + v_spacing)

    canvas = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]

    def draw_text(x, y, text):
        for i, char in enumerate(text):
            if 0 <= y < len(canvas) and 0 <= x + i < len(canvas[y]):
                canvas[y][x+i] = char

    # 4. Draw rooms and connections
    drawn_connections = set()

    for room_id, (room_x, room_y) in room_coords.items():
        # Draw connections first
        room_info = map_data.get(room_id, {})
        for direction, dest_room_id in room_info.get("exits", {}).items():
            if dest_room_id in room_coords:
                # Use a sorted tuple to uniquely identify a connection regardless of direction
                connection = tuple(sorted((room_id, dest_room_id)))
                if connection in drawn_connections:
                    continue
                drawn_connections.add(connection)

                dest_x, dest_y = room_coords[dest_room_id]
                
                canvas_x = (room_x - min_x) * (room_width + h_spacing)
                canvas_y = (room_y - min_y) * (room_height + v_spacing)
                box_mid_y = canvas_y + 1

                # Horizontal connection
                if dest_y == room_y:
                    start_x, end_x = 0, 0
                    if room_x < dest_x: # East exit
                        start_x = canvas_x + room_width
                        end_x = (dest_x - min_x) * (room_width + h_spacing)
                    else: # West exit
                        start_x = (dest_x - min_x) * (room_width + h_spacing) + room_width
                        end_x = canvas_x

                    for x in range(start_x, end_x):
                        draw_text(x, box_mid_y, '-')

                # Vertical connection
                if dest_x == room_x:
                    start_y, end_y = 0, 0
                    if room_y < dest_y: # South exit
                        start_y = canvas_y + room_height
                        end_y = (dest_y - min_y) * (room_height + v_spacing)
                    else: # North exit
                         start_y = (dest_y - min_y) * (room_height + v_spacing) + room_height
                         end_y = canvas_y

                    for y in range(start_y, end_y):
                        draw_text(canvas_x + room_width // 2, y, '|')

    for room_id, (room_x, room_y) in room_coords.items():
        room_name = map_data[room_id].get("name", "Unknown")

        canvas_x = (room_x - min_x) * (room_width + h_spacing)
        canvas_y = (room_y - min_y) * (room_height + v_spacing)

        box_top_y, box_mid_y, box_bot_y = canvas_y, canvas_y + 1, canvas_y + 2
        
        draw_text(canvas_x, box_top_y, '+' + '-' * (room_width - 2) + '+')
        draw_text(canvas_x, box_mid_y, '|' + ' ' * (room_width - 2) + '|')
        draw_text(canvas_x, box_bot_y, '+' + '-' * (room_width - 2) + '+')
        
        # --- NPC drawing logic ---
        npc_markers = ""
        if npc_locations and room_id in npc_locations:
            for npc_role_char in npc_locations[room_id]:
                npc_markers += f"[{npc_role_char}]"
        
        display_text = room_name
        if npc_markers:
            # Try to center the room name and place markers next to it
            # Simple approach: put markers after the name
            # This might exceed room_width, for now let's prioritize markers if space is tight.
            # A more robust solution would dynamically adjust name length.
            available_width = room_width - 2 # -2 for the '|' at ends
            if len(room_name) + 1 + len(npc_markers) <= available_width:
                display_text = f"{room_name} {npc_markers}"
            elif len(npc_markers) <= available_width: # if only markers fit
                display_text = npc_markers
            else: # neither fit well, just truncate room name
                display_text = room_name[:available_width - len(npc_markers) - 1] + f" {npc_markers}"
                if len(display_text) < len(npc_markers):
                    display_text = npc_markers


        name_x = canvas_x + (room_width - len(display_text)) // 2
        # Ensure name_x is not out of bounds or negative
        if name_x < canvas_x + 1:
            name_x = canvas_x + 1 # At least 1 space from border
        if name_x + len(display_text) > canvas_x + room_width - 1:
            name_x = canvas_x + room_width - 1 - len(display_text) # Fit within border

        draw_text(name_x, box_mid_y, display_text)
        # --- End NPC drawing logic ---

    # 5. Convert canvas to string
    return "\n".join("".join(row).rstrip() for row in canvas)

def main():
    """Main function to generate and print the map."""
    map_data = load_map_data()
    if map_data:
        # Dummy NPC locations for testing: {room_id: [list of single-char NPC roles]}
        npc_locations_test = {
            "hallway_a": ["G", "G"], # Two Guards in Hallway A
            "control_room": ["S"],   # One Scientist in Control Room
            "cell": ["D"]            # One D-Class in the Cell
        }
        ascii_map = generate_ascii_map(map_data, npc_locations_test)
        print(ascii_map)

if __name__ == "__main__":
    main()
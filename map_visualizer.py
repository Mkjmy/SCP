import json
import os

def load_map_data(filename="debug_output/debug_map.json"):
    """Loads map data from a JSON file."""
    if not os.path.exists(filename):
        print(f"Error: Map file not found at '{filename}'")
        return None
    with open(filename, 'r') as f:
        return json.load(f)

def generate_ascii_map(map_data, entity_locations=None):
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

        for direction, exit_info in room.get("exits", {}).items():
            # exit_info can be a string (old format) or a dict (new format)
            if isinstance(exit_info, dict):
                destination_room_id = exit_info.get("destination")
            else: # old string format
                destination_room_id = exit_info
            
            if not destination_room_id: # Handle cases where destination might be missing in dict
                continue

            if destination_room_id not in visited:
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
                room_coords[destination_room_id] = new_coords
                visited.add(destination_room_id)
                q.append((destination_room_id, new_coords))

    if not room_coords:
        return "No rooms with coordinates found."

    # 2. Determine grid boundaries
    min_x = min(c[0] for c in room_coords.values())
    max_x = max(c[0] for c in room_coords.values())
    min_y = min(c[1] for c in room_coords.values())
    max_y = max(c[1] for c in room_coords.values())

    # 3. Prepare for drawing
    room_width = 18
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
        for direction, exit_info in room_info.get("exits", {}).items():
            if isinstance(exit_info, dict):
                destination_room_id = exit_info.get("destination")
                door_level = exit_info.get("door_level", 0)
            else: # old string format
                destination_room_id = exit_info
                door_level = 0
            
            if not destination_room_id:
                continue

            if destination_room_id in room_coords:
                # Use a sorted tuple to uniquely identify a connection regardless of direction
                connection = tuple(sorted((room_id, destination_room_id)))
                if connection in drawn_connections:
                    continue
                drawn_connections.add(connection)

                dest_x, dest_y = room_coords[destination_room_id]
                
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

                    connector_char = '-'
                    # Add door level to connector for horizontal connections
                    if door_level > 0:
                        connector_text = f"-L{door_level}-"
                        mid_x = (start_x + end_x) // 2
                        draw_text(mid_x - len(connector_text)//2, box_mid_y, connector_text)
                        # Draw normal connector around it
                        for x_coord in range(start_x, mid_x - len(connector_text)//2):
                            draw_text(x_coord, box_mid_y, connector_char)
                        for x_coord in range(mid_x + len(connector_text)//2 + 1, end_x):
                             draw_text(x_coord, box_mid_y, connector_char)
                    else:
                        for x_coord in range(start_x, end_x):
                            draw_text(x_coord, box_mid_y, connector_char)
                    

                # Vertical connection
                if dest_x == room_x:
                    start_y, end_y = 0, 0
                    if room_y < dest_y: # South exit
                        start_y = canvas_y + room_height
                        end_y = (dest_y - min_y) * (room_height + v_spacing)
                    else: # North exit
                         start_y = (dest_y - min_y) * (room_height + v_spacing) + room_height
                         end_y = canvas_y

                    connector_char = '|'
                    # Add door level to connector for vertical connections
                    if door_level > 0:
                        connector_text = f"L{door_level}"
                        mid_y = (start_y + end_y) // 2
                        draw_text(canvas_x + room_width // 2, mid_y, connector_text)
                        # Draw normal connector around it
                        for y_coord in range(start_y, mid_y):
                            draw_text(canvas_x + room_width // 2, y_coord, connector_char)
                        for y_coord in range(mid_y + 1, end_y):
                            draw_text(canvas_x + room_width // 2, y_coord, connector_char)
                    else:
                        for y_coord in range(start_y, end_y):
                            draw_text(canvas_x + room_width // 2, y_coord, connector_char)

    for room_id, (room_x, room_y) in room_coords.items():
        room_name = map_data[room_id].get("name", "Unknown")

        canvas_x = (room_x - min_x) * (room_width + h_spacing)
        canvas_y = (room_y - min_y) * (room_height + v_spacing)

        box_top_y, box_mid_y, box_bot_y = canvas_y, canvas_y + 1, canvas_y + 2
        
        draw_text(canvas_x, box_top_y, '+' + '-' * (room_width - 2) + '+')
        draw_text(canvas_x, box_mid_y, '|' + ' ' * (room_width - 2) + '|')
        draw_text(canvas_x, box_bot_y, '+' + '-' * (room_width - 2) + '+')
        
        # --- NPC drawing logic ---
        entity_markers = ""
        if entity_locations and room_id in entity_locations:
            for entity_marker in entity_locations[room_id]:
                entity_markers += f"[{entity_marker}]"
        
        display_text = room_name
        if entity_markers:
            available_width = room_width - 2 # -2 for the '|' at ends
            if len(room_name) + 1 + len(entity_markers) <= available_width:
                display_text = f"{room_name} {entity_markers}"
            elif len(entity_markers) <= available_width: # if only markers fit
                display_text = entity_markers
            else: # neither fit well, just truncate room name
                display_text = room_name[:available_width - len(entity_markers) - 1] + f" {entity_markers}"
                if len(display_text) < len(entity_markers):
                    display_text = entity_markers



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
    # Temporarily import NPCManager and SCPManager for testing combined display
    # In a full game, these would be managed by a central game loop.
    from npc_manager import NPCManager
    from scp_manager import SCPManager

    map_data = load_map_data()
    if map_data:
        # --- Setup NPCManager ---
        npc_manager = NPCManager(map_data)
        npc_manager.spawn_npc("Guard", "hallway_a")
        npc_manager.spawn_npc("Scientist", "control_room")
        npc_manager.spawn_npc("D-Class", "cell")
        
        # --- Setup SCPManager ---
        scp_manager = SCPManager(map_data)
        
        # Ensure scp_definitions.json exists for testing
        scp_definitions_file = "scp_definitions.json"
        if not os.path.exists(scp_definitions_file):
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
            with open(scp_definitions_file, "w") as f:
                json.dump(dummy_scp_definitions, f, indent=2)
            print("Created dummy scp_definitions.json for map_visualizer testing.")

        scp_manager.load_scps_from_definitions(scp_definitions_file)

        # --- Combine NPC and SCP locations ---
        all_entity_locations = {}

        # Add NPC locations
        npc_locs = npc_manager.get_npc_locations_for_display()
        for room_id, markers in npc_locs.items():
            if room_id not in all_entity_locations:
                all_entity_locations[room_id] = []
            all_entity_locations[room_id].extend(markers)

        # Add SCP locations
        scp_locs = scp_manager.get_scp_locations_for_display()
        for room_id, markers in scp_locs.items():
            if room_id not in all_entity_locations:
                all_entity_locations[room_id] = []
            all_entity_locations[room_id].extend(markers)

        # --- Generate and print combined map ---
        ascii_map = generate_ascii_map(map_data, all_entity_locations)
        print("\n--- Combined Map with NPCs and SCPs ---")
        print(ascii_map)

if __name__ == "__main__":
    main()
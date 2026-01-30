import json
import random
import copy

OPPOSITE_DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east"
}

def load_room_templates(filename="room_templates.json"):
    """Loads room templates from a JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def get_template_by_id(templates, template_id):
    """Finds a template by its ID."""
    for t in templates:
        if t["id"] == template_id:
            return t
    return None

def find_matching_templates(templates, required_exits, forbidden_exits):
    """Finds templates that match the required exit configuration."""
    matching = []
    for t in templates:
        # A room can't be a dead end if it's not tagged as one
        if "end" not in t.get("tags", []) and len(t["exits"]) == 1 and len(required_exits) == 1:
            continue
            
        valid = True
        # Must have all required exits
        for req_exit in required_exits:
            if req_exit not in t["exits"]:
                valid = False
                break
        if not valid:
            continue
            
        # Must NOT have any forbidden exits
        for fbd_exit in forbidden_exits:
            if fbd_exit in t["exits"]:
                valid = False
                break
        if not valid:
            continue
            
        matching.append(t)
        
    return matching

def generate_map(templates, num_rooms=10):
    """
    Generates a procedural map by connecting rooms from templates.
    """
    grid = {}  # (x, y) -> room_dict
    
    # Start room
    start_template = random.choice([t for t in templates if "start" in t.get("tags", [])])
    start_room_id = "room_0_0"
    start_room = copy.deepcopy(start_template)
    grid[(0, 0)] = start_room
    
    frontier = []
    for exit_dir in start_template["exits"]:
        if exit_dir == "north": frontier.append((0, 1, "south"))
        if exit_dir == "south": frontier.append((0, -1, "north"))
        if exit_dir == "east":  frontier.append((1, 0, "west"))
        if exit_dir == "west":  frontier.append((-1, 0, "east"))

    while frontier and len(grid) < num_rooms:
        x, y, required_exit_from_neighbor = frontier.pop(random.randint(0, len(frontier) - 1))

        if (x, y) in grid:
            continue

        required_exits = {required_exit_from_neighbor}
        forbidden_exits = set()
        
        # Check neighbors to determine all required and forbidden exits
        for dir_check, (dx, dy) in {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}.items():
            neighbor_coord = (x + dx, y + dy)
            if neighbor_coord in grid:
                neighbor = grid[neighbor_coord]
                opposite = OPPOSITE_DIRECTIONS[dir_check]
                
                # Check if the neighbor has an exit pointing towards the new room's coordinate
                if opposite in neighbor.get("exits", []):
                    required_exits.add(dir_check)
                else: # The neighbor exists but does not have a connecting door, so this side is a wall
                    forbidden_exits.add(dir_check)

        possible_templates = find_matching_templates(templates, required_exits, forbidden_exits)
        if not possible_templates:
            continue # Can't find a room that fits, try another frontier
            
        chosen_template = copy.deepcopy(random.choice(possible_templates))
        
        grid[(x, y)] = chosen_template
        
        # Add new frontiers from the exits of the newly placed room
        for exit_dir in chosen_template["exits"]:
            nx, ny = x, y
            required_from_new = ""
            if exit_dir == "north": ny += 1; required_from_new = "south"
            if exit_dir == "south": ny -= 1; required_from_new = "north"
            if exit_dir == "east":  nx += 1; required_from_new = "west"
            if exit_dir == "west":  nx -= 1; required_from_new = "east"
            
            if (nx, ny) not in grid:
                frontier.append((nx, ny, required_from_new))
    
    # Finalize the exits in the grid to create the final game_map
    final_map = {}
    for (x, y), room_data in grid.items():
        room_id = f"room_{x}_{y}"
        final_exits = {}
        for exit_dir in room_data.get("exits", []):
            nx, ny = x, y
            if exit_dir == "north": ny += 1
            if exit_dir == "south": ny -= 1
            if exit_dir == "east":  nx += 1
            if exit_dir == "west":  nx -= 1
            
            if (nx, ny) in grid: # Only add exits that lead to a placed room
                final_exits[exit_dir] = f"room_{nx}_{ny}"
        
        room_data["exits"] = final_exits
        final_map[room_id] = room_data
        
    return final_map, "room_0_0" # Return map and starting room id

if __name__ == '__main__':
    # This part allows testing the generator directly
    templates = load_room_templates()
    game_map, start_id = generate_map(templates, 15)
    print(json.dumps(game_map, indent=2))
    print(f"\nMap generated with {len(game_map)} rooms. Start at: {start_id}")

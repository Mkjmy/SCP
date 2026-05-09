import json
import random
import copy
import os

OPPOSITE_DIRECTIONS = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east"
}

def load_room_templates(filename="data/room_templates.json"):
    """Loads room templates from a JSON file."""
    if not os.path.exists(filename):
        return []
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
        # Avoid using suites in random generation
        if "suite" in t.get("tags", []):
            continue
            
        # A room can't be a dead end if it's not tagged as one
        if "end" not in t.get("tags", []) and len(t["exits"]) == 1 and len(required_exits) == 1:
            continue
            
        valid = True
        for req_exit in required_exits:
            if req_exit not in t["exits"]:
                valid = False
                break
        if not valid: continue
            
        for fbd_exit in forbidden_exits:
            if fbd_exit in t["exits"]:
                valid = False
                break
        if not valid: continue
            
        matching.append(t)
    return matching

def place_scp_zone(grid, x, y, entrance_dir, zone_data):
    """
    Attempts to place a 'Fork' structure for an SCP containment unit.
    Lobby connects to the hallway.
    Lobby -> Chamber (North)
    Lobby -> Observation (East)
    """
    struct = zone_data.get("structure", {})
    lobby_data = struct.get("lobby")
    chamber_data = struct.get("chamber")
    obs_data = struct.get("observation")
    
    if not lobby_data or not chamber_data:
        return False
    
    # Entrance dir is where the Hallway was. Lobby needs an exit to that dir.
    # Lobby is at (x,y)
    # Chamber is at (x, y+1)
    # Observation is at (x+1, y)
    
    lobby_pos = (x, y)
    cha_pos = (x, y + 1)
    obs_pos = (x + 1, y)
    
    # Check for collisions
    if lobby_pos in grid or cha_pos in grid:
        return False
    if obs_data and obs_pos in grid:
        return False
        
    # 1. Prepare Lobby
    lobby = copy.deepcopy(lobby_data)
    # Ensure it has the required exits for the fork
    lobby["exits"] = [entrance_dir, "north"]
    if obs_data:
        lobby["exits"].append("east")
    grid[lobby_pos] = lobby
    
    # 2. Prepare Chamber
    chamber = copy.deepcopy(chamber_data)
    chamber["exits"] = ["south"]
    chamber["scp_id"] = zone_data["entity"]["id"] # Mark for SCP placement
    grid[cha_pos] = chamber
    
    # 3. Prepare Observation (Optional)
    if obs_data:
        observation = copy.deepcopy(obs_data)
        observation["exits"] = ["west"]
        grid[obs_pos] = observation
        
    return True

def generate_map(templates, num_rooms=15, scp_defs_file="data/scp_definitions.json"):
    """
    Generates a procedural map by connecting rooms and injecting SCP Zones.
    """
    grid = {}  # (x, y) -> room_dict
    
    # Load SCP Zones to inject
    scp_zones = []
    if os.path.exists(scp_defs_file):
        try:
            with open(scp_defs_file, 'r') as f:
                defs = json.load(f)
                scp_zones = list(defs.values())
        except:
            pass

    # Start room (Cell)
    start_template = next((t for t in templates if "start" in t.get("tags", [])), templates[0])
    grid[(0, 0)] = copy.deepcopy(start_template)
    
    frontier = []
    for exit_dir in start_template["exits"]:
        dx, dy = 0, 0
        if exit_dir == "north": dy = 1
        elif exit_dir == "south": dy = -1
        elif exit_dir == "east": dx = 1
        elif exit_dir == "west": dx = -1
        frontier.append((dx, dy, OPPOSITE_DIRECTIONS[exit_dir]))

    while frontier and len(grid) < num_rooms:
        x, y, required_from_neighbor = frontier.pop(random.randint(0, len(frontier) - 1))

        if (x, y) in grid:
            continue

        # Try to inject an SCP Zone cluster if we have any left and are not at start
        if scp_zones and len(grid) > 3 and random.random() < 0.4:
            zone_data = scp_zones.pop(0)
            if place_scp_zone(grid, x, y, required_from_neighbor, zone_data):
                continue

        # Otherwise place a normal room
        required_exits = {required_from_neighbor}
        forbidden_exits = set()
        
        for d, (dx, dy) in {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}.items():
            neighbor_coord = (x + dx, y + dy)
            if neighbor_coord in grid:
                if OPPOSITE_DIRECTIONS[d] in grid[neighbor_coord].get("exits", []):
                    required_exits.add(d)
                else:
                    forbidden_exits.add(d)

        possible_templates = find_matching_templates(templates, required_exits, forbidden_exits)
        if not possible_templates:
            continue
            
        chosen_template = copy.deepcopy(random.choice(possible_templates))
        
        # Don't place another start cell
        if "start" in chosen_template.get("tags", []) and (x, y) != (0, 0):
             non_start = [t for t in possible_templates if "start" not in t.get("tags", [])]
             if non_start:
                 chosen_template = copy.deepcopy(random.choice(non_start))

        grid[(x, y)] = chosen_template
        
        # Add new frontiers
        for exit_dir in chosen_template["exits"]:
            dx, dy = 0, 0
            if exit_dir == "north": dy = 1
            elif exit_dir == "south": dy = -1
            elif exit_dir == "east": dx = 1
            elif exit_dir == "west": dx = -1
            
            nx, ny = x + dx, y + dy
            if (nx, ny) not in grid:
                frontier.append((nx, ny, OPPOSITE_DIRECTIONS[exit_dir]))
    
    # Finalize the exits with IDs and Door Levels
    final_map = {}
    for (x, y), room_data in grid.items():
        room_id = f"room_{x}_{y}"
        actual_exits = {}
        
        for exit_dir in room_data.get("exits", []):
            dx, dy = 0, 0
            if exit_dir == "north": dy = 1
            elif exit_dir == "south": dy = -1
            elif exit_dir == "east": dx = 1
            elif exit_dir == "west": dx = -1
            
            nx, ny = x + dx, y + dy
            if (nx, ny) in grid:
                # Determine Door Level
                lv = 0
                if (x, y) == (0, 0): lv = 3 # Start cell is locked
                
                # Logic for SCP Zones
                if room_data.get("id") == "containment_lobby" or "suite" in room_data.get("tags", []):
                    if exit_dir == "north": lv = 3 # Chamber door
                    else: lv = 1 # Lobby entrance/observation
                elif "security" in room_data.get("tags", []):
                    lv = 1
                
                actual_exits[exit_dir] = {
                    "destination": f"room_{nx}_{ny}",
                    "door_level": lv
                }
        
        # Match description to actual exits if possible
        required_exits_set = set(actual_exits.keys())
        forbidden_exits_set = {"north", "south", "east", "west"} - required_exits_set
        
        # (Only refine normal rooms, keep SCP rooms as they are)
        if "suite" not in room_data.get("tags", []) and "chamber" not in room_data.get("tags", []):
            perfect_templates = find_matching_templates(templates, required_exits_set, forbidden_exits_set)
            if perfect_templates:
                new_data = copy.deepcopy(random.choice(perfect_templates))
                new_data["exits"] = actual_exits
                # Keep position-based scp_id if it was there
                if "scp_id" in room_data: new_data["scp_id"] = room_data["scp_id"]
                final_map[room_id] = new_data
                continue

        room_data["exits"] = actual_exits
        final_map[room_id] = room_data
        
    return final_map, "room_0_0"

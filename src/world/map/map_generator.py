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

def get_sector_info(depth):
    """Returns sector name and thematic description based on depth."""
    if depth == 0:
        return "Sector A (Residential/Admin)", "Hyper-modern white polymer walls with soft LED lighting."
    elif depth == 1:
        return "Sector B (Light Containment)", "Clinical glass partitions and humming decontamination systems."
    else:
        return "Sector C (Heavy Containment)", "Reinforced alloy walls and deep-subterranean concrete. Shadows are long here."

def generate_map(templates, num_rooms=50, scp_defs_file="data/scp_definitions.json"):
    """
    Generates a procedural map with multiple sectors based on depth.
    Depth 0: Sector A (Residential)
    Depth 1-2: Sector B (Light Research)
    Depth 3+: Sector C (Heavy Containment)
    """
    grid = {}  # (x, y, depth) -> room_dict
    
    # Load SCP Zones to inject
    scp_zones = []
    if os.path.exists(scp_defs_file):
        try:
            with open(scp_defs_file, 'r') as f:
                defs = json.load(f)
                scp_zones = list(defs.values())
        except: pass

    # Start room (Cell) at Depth 0
    start_template = next((t for t in templates if "start" in t.get("tags", [])), templates[0])
    grid[(0, 0, 0)] = copy.deepcopy(start_template)
    
    frontier = []
    # Initial exits lead to Sector A
    for exit_dir in start_template["exits"]:
        dx, dy, dz = 0, 0, 0
        if exit_dir == "north": dy = 1
        elif exit_dir == "south": dy = -1
        elif exit_dir == "east": dx = 1
        elif exit_dir == "west": dx = -1
        frontier.append((dx, dy, dz, OPPOSITE_DIRECTIONS[exit_dir]))

    while frontier and len(grid) < num_rooms:
        x, y, z, required_from_neighbor = frontier.pop(random.randint(0, len(frontier) - 1))

        if (x, y, z) in grid:
            continue

        # Depth-based sector logic
        sector_name, sector_theme = get_sector_info(z)

        # Chance to descend deeper
        if len(grid) > (num_rooms // 3) * (z + 1) and z < 3:
            z += 1
            sector_name, sector_theme = get_sector_info(z)

        # Inject SCP Zones based on depth (Heavy SCPs go deeper)
        if scp_zones and len(grid) > 5 and random.random() < 0.3:
            # Simple check: if depth is high, try to place a zone
            zone_data = scp_zones.pop(0)
            if place_scp_zone_3d(grid, x, y, z, required_from_neighbor, zone_data):
                continue

        # Normal room placement
        required_exits = {required_from_neighbor}
        forbidden_exits = set()
        
        for d, (dx, dy) in {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}.items():
            neighbor_coord = (x + dx, y + dy, z)
            if neighbor_coord in grid:
                if OPPOSITE_DIRECTIONS[d] in grid[neighbor_coord].get("exits", []):
                    required_exits.add(d)
                else:
                    forbidden_exits.add(d)

        possible_templates = find_matching_templates(templates, required_exits, forbidden_exits)
        if not possible_templates: continue
            
        chosen_template = copy.deepcopy(random.choice(possible_templates))
        
        # Apply Sector Theme to description
        chosen_template["description"] = f"[{sector_name}] {chosen_template['description']} {sector_theme}"
        grid[(x, y, z)] = chosen_template
        
        # Add frontiers
        for exit_dir in chosen_template["exits"]:
            dx, dy = 0, 0
            if exit_dir == "north": dy = 1
            elif exit_dir == "south": dy = -1
            elif exit_dir == "east": dx = 1
            elif exit_dir == "west": dx = -1
            
            if (x+dx, y+dy, z) not in grid:
                frontier.append((x+dx, y+dy, z, OPPOSITE_DIRECTIONS[exit_dir]))

    # Finalize (IDs and Door Levels)
    final_map = {}
    for (x, y, z), room_data in grid.items():
        room_id = f"room_{x}_{y}_{z}"
        actual_exits = {}
        
        for exit_dir in room_data.get("exits", []):
            dx, dy = 0, 0
            if exit_dir == "north": dy = 1
            elif exit_dir == "south": dy = -1
            elif exit_dir == "east": dx = 1
            elif exit_dir == "west": dx = -1
            
            if (x+dx, y+dy, z) in grid:
                # Security logic based on depth
                lv = z # Base clearance = depth
                if (x, y, z) == (0, 0, 0): lv = 3
                elif "security" in room_data.get("tags", []): lv += 1
                elif "chamber" in room_data.get("tags", []): lv += 2
                
                actual_exits[exit_dir] = {
                    "destination": f"room_{x+dx}_{y+dy}_{z}",
                    "door_level": lv
                }
        
        room_data["exits"] = actual_exits
        final_map[room_id] = room_data
        
    return final_map, "room_0_0_0"

def place_scp_zone_3d(grid, x, y, z, entrance_dir, zone_data):
    # (Adapted fork logic for 3D grid)
    lobby_pos = (x, y, z)
    cha_pos = (x, y + 1, z)
    obs_pos = (x + 1, y, z)
    
    struct = zone_data.get("structure", {})
    lobby_data = struct.get("lobby")
    chamber_data = struct.get("chamber")
    observation_data = struct.get("observation")
    
    if not lobby_data or not chamber_data: return False
    if lobby_pos in grid or cha_pos in grid: return False
    if observation_data and obs_pos in grid: return False
    
    sector_name, sector_theme = get_sector_info(z)
    
    # Lobby
    lobby = copy.deepcopy(lobby_data)
    lobby["exits"] = [entrance_dir, "north"]
    if observation_data: lobby["exits"].append("east")
    lobby["description"] = f"[{sector_name}] {lobby['description']} {sector_theme}"
    grid[lobby_pos] = lobby
    
    # Chamber
    chamber = copy.deepcopy(chamber_data)
    chamber["exits"] = ["south"]
    chamber["scp_id"] = zone_data["entity"]["id"]
    chamber["description"] = f"[{sector_name}] {chamber['description']} {sector_theme}"
    grid[cha_pos] = chamber
    
    # Observation (Optional)
    if observation_data:
        obs_room = copy.deepcopy(observation_data)
        obs_room["exits"] = ["west"]
        obs_room["description"] = f"[{sector_name}] {obs_room['description']} {sector_theme}"
        grid[obs_pos] = obs_room
    
    return True

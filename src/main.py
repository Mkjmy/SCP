import curses
import json
import os
import random
from player import Player
from npc_manager import NPCManager
from scp_manager import SCPManager
from door_manager import DoorManager
from navigation import move
from actions import attack, run
from map_generator import load_room_templates, generate_map
from map_visualizer import generate_ascii_map

# Color pairs
LOCATION_PAIR = 1
PROMPT_PAIR = 2
HIGHLIGHT_PAIR = 3
NPC_PAIR = 4
DANGER_PAIR = 5
ITEM_PAIR = 6
DIALOGUE_PAIR = 7

def display_message(stdscr, message, is_danger=False, is_dialogue=False, is_item_info=False, is_debug_message=False):
    """Displays a message to the player and waits for a key press."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    
    color = curses.A_NORMAL
    if is_danger: color = curses.color_pair(DANGER_PAIR)
    elif is_dialogue: color = curses.color_pair(DIALOGUE_PAIR)
    elif is_item_info: color = curses.color_pair(ITEM_PAIR)

    lines = message.split('\n')

    # For multi-line messages or debug messages, print from the top
    if len(lines) > 1 or is_debug_message:
        for i, line in enumerate(lines):
            if i >= h - 2: # Stop before the continuation prompt
                break
            # Truncate long lines to fit width
            line_to_print = line[:w-1]
            try:
                stdscr.addstr(i, 0, line_to_print, color)
            except curses.error:
                pass
    else: # For single-line, non-debug messages, center them
        line = lines[0]
        x = (w - len(line)) // 2
        y = h // 2
        if x < 0: x = 0
        if y < 0: y = 0
        try:
            stdscr.addstr(y, x, line, color)
        except curses.error:
            try:
                stdscr.addstr(0, 0, line, color)
            except curses.error:
                pass

    # Display continuation prompt
    prompt_y = h - 2
    prompt_x = (w - len("[Press any key to continue]")) // 2
    if prompt_y >= 0 and prompt_x >=0:
        try:
            stdscr.addstr(prompt_y, prompt_x, "[Press any key to continue]", curses.A_DIM)
        except curses.error:
            pass
    stdscr.refresh()
    curses.flushinp()
    stdscr.getch()


def get_user_choice(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="What is your next move?"):
    """Generic menu selection function that maintains the narrative UI."""
    selected_idx = 0
    h, w = stdscr.getmaxyx()
    
    loc_color = curses.color_pair(LOCATION_PAIR)
    prompt_color = curses.color_pair(PROMPT_PAIR)
    highlight_attr = curses.color_pair(HIGHLIGHT_PAIR)
    npc_color = curses.color_pair(NPC_PAIR)
    danger_color = curses.color_pair(DANGER_PAIR)
    item_color = curses.color_pair(ITEM_PAIR)

    while True:
        stdscr.clear()
        # Header
        stdscr.addstr(0, 0, f"--- {current_room['name']} ---\n\n", loc_color | curses.A_BOLD)

        # Narrative
        stdscr.addstr(2, 0, f"You find yourself in the {current_room['name']}. ", curses.A_NORMAL)
        desc_words = current_room['description'].split()
        desc_lines = []; line = ""
        for word in desc_words:
            if len(line) + len(word) + 1 < w - 2: line += word + " "
            else: desc_lines.append(line); line = word + " "
        desc_lines.append(line)
        
        row = 3
        for l in desc_lines:
            if row < h - 15: stdscr.addstr(row, 0, l + "\n"); row += 1
        
        row += 1
        room_items = [all_items[item_id]["name"] for item_id in current_room.get("items", [])]
        if room_items:
            stdscr.addstr(row, 0, "Nearby, you notice:\n", item_color | curses.A_BOLD); row += 1
            for item in room_items:
                if row < h - 12: stdscr.addstr(row, 2, f"• A {item}\n", item_color); row += 1
            row += 1

        if npcs_in_room or scps_in_room:
            stdscr.addstr(row, 0, "You share this space with:\n", npc_color | curses.A_BOLD); row += 1
            for npc_info in npcs_in_room:
                if row < h - 10:
                    stdscr.addstr(row, 2, f"• {npc_info['character'].get_description()}\n", npc_color); row += 1
            for scp in scps_in_room:
                if row < h - 8:
                    stdscr.addstr(row, 2, f"• {scp.on_observe_description(player, scp.get_status())}\n", danger_color); row += 1
        
        row += 1
        stdscr.addstr(row, 0, f"{header_text}\n", prompt_color | curses.A_UNDERLINE); row += 1
        for i, opt in enumerate(options):
            if row < h - 2:
                stdscr.addstr(row, 0, f"  [{opt.replace('_', ' ').capitalize()}]\n", highlight_attr if i == selected_idx else curses.A_NORMAL)
                row += 1

        # Narrative Status
        cond = "Healthy" if player.health > 80 else "Wounded" if player.health > 40 else "In Critical Pain"
        stamina_text = "Full of Energy" if player.stamina > 80 else "Tired" if player.stamina > 40 else "Exhausted"
        sensation = "Focused"
        if player.sanity < 30: sensation = "Terrified"
        elif player.sanity < 70: sensation = "Nervous"
        if player.morale < 30: sensation = "Hopeless"
        
        hands = f"Left: {player.left_hand or 'Empty'} | Right: {player.right_hand or 'Empty'}"
        status_line = f"Physical: {cond} | Stamina: {stamina_text} | Feeling: {sensation}"
        try:
            stdscr.addstr(h - 2, 0, hands, item_color)
            stdscr.addstr(h - 1, 0, status_line, curses.A_DIM)
        except: pass

        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP: selected_idx = (selected_idx - 1) % len(options)
        elif key == curses.KEY_DOWN: selected_idx = (selected_idx + 1) % len(options)
        elif key in [curses.KEY_ENTER, ord('\n')]: return options[selected_idx]
        elif key == ord('q'): return 'quit'


def main_loop(stdscr):
    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(LOCATION_PAIR, curses.COLOR_CYAN, -1)
    curses.init_pair(PROMPT_PAIR, curses.COLOR_YELLOW, -1)
    curses.init_pair(HIGHLIGHT_PAIR, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(NPC_PAIR, curses.COLOR_GREEN, -1)
    curses.init_pair(DANGER_PAIR, curses.COLOR_RED, -1)
    curses.init_pair(ITEM_PAIR, curses.COLOR_MAGENTA, -1)
    curses.init_pair(DIALOGUE_PAIR, curses.COLOR_BLUE, -1)

    curses.curs_set(0) # Hide cursor

    # --- Load Configuration ---
    config_file = 'data/game_config.json'
    try:
        with open(config_file, 'r') as f:
            game_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        display_message(stdscr, f"Error loading config: {e}. Exiting.", is_danger=True)
        return

    map_settings = game_config.get("map_settings", {})
    map_mode = map_settings.get("mode", "generate_random")
    static_map_file = map_settings.get("static_map_file", "debug_output/debug_map.json")
    random_map_num_rooms = map_settings.get("random_map_num_rooms", 15)

    game_map = None
    start_room_id = None

    if map_mode == "load_static":
        try:
            with open(static_map_file, 'r') as f:
                game_map = json.load(f)
            start_room_id = game_config.get("player", {}).get("start_location", list(game_map.keys())[0] if game_map else "cell")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            display_message(stdscr, f"Warning: Could not load static map '{static_map_file}': {e}. Generating a random map instead.", is_danger=True)
            map_mode = "generate_random"
    
    if map_mode == "generate_random":
        try:
            room_templates = load_room_templates()
            game_map, start_room_id = generate_map(room_templates, num_rooms=random_map_num_rooms)
        except Exception as e:
            display_message(stdscr, f"Error generating random map: {e}. Cannot start game.", is_danger=True)
            return
        
    if game_map is None:
        display_message(stdscr, "Fatal Error: No game map could be loaded or generated.", is_danger=True)
        return

    # --- Load Items ---
    try:
        with open('data/items.json', 'r') as f:
            all_items = json.load(f)
    except:
        all_items = {}

    # --- Player Initialization ---
    player_config = game_config.get("player", {})
    player = Player(
        name=player_config.get("name", "Player One"),
        role="Player",
        clearance_level=0,
        start_location=start_room_id
    )
    player.inventory.extend(player_config.get("inventory", []))

    # Instantiate managers
    door_manager = DoorManager(game_map)
    npc_manager = NPCManager(game_map)
    scp_manager = SCPManager(game_map)

    # --- Distribute Items ---
    all_room_ids = list(game_map.keys())
    for item_id, item_data in all_items.items():
        if item_data.get("takeable") and random.random() < 0.4:
            target = random.choice(all_room_ids)
            if "items" not in game_map[target]: game_map[target]["items"] = []
            game_map[target]["items"].append(item_id)

    debug_active = game_config.get("game_settings", {}).get("enable_debug_option", False)
    
    # --- Initialize NPCs ---
    for _ in range(7):
        npc_manager.spawn_npc("D-Class", start_room_id)
    dorm_npcs = npc_manager.get_npcs_in_room(start_room_id)
    for i, npc_info in enumerate(dorm_npcs):
        if i < 2: npc_info["character"].personality = "Broken"
        elif i < 3: npc_info["character"].personality = "Manic"

    # --- Initialize SCPs ---
    scp_definitions_file = "data/scp_definitions.json"
    if os.path.exists(scp_definitions_file):
        scp_manager.load_scps_from_definitions(scp_definitions_file)
        assigned_scps = set()
        for rid, rdata in game_map.items():
            if "scp_id" in rdata:
                sid = rdata["scp_id"]
                if scp_manager.move_scp(sid, rid): assigned_scps.add(sid)
        for sid, scp in scp_manager._scps.items():
            if sid not in assigned_scps:
                possible = [rid for rid in game_map.keys() if rid != start_room_id]
                if possible: scp_manager.move_scp(sid, random.choice(possible))

    game_over = False
    display_message(stdscr, f"You are {player.name}, Clearance Level {player.clearance_level}.", is_item_info=True)

    message_to_show = ""
    while not game_over:
        # --- START OF TURN ---
        for npc_info in npc_manager._npcs.values():
            npc_info["character"].update_behavior()

        is_fatal, is_dialogue, is_item_info = False, False, False
        
        current_room_id = player.location
        current_room = game_map[current_room_id]
        npcs_in_room = npc_manager.get_npcs_in_room(current_room_id)
        scps_in_room = scp_manager.get_scps_in_room(current_room_id)

        if player.health <= 0:
            display_message(stdscr, message_to_show or "Your body gives out.", is_danger=True)
            game_over = True
            continue

        if message_to_show:
            display_message(stdscr, message_to_show, is_danger=is_fatal, is_dialogue=is_dialogue, is_item_info=is_item_info)
            message_to_show = ""
            if is_fatal: game_over = True; continue

        # --- Dynamic Option Generation (Primary) ---
        options = []
        for detail in sorted(current_room.get("details", {}).keys()): options.append(f"look at {detail}")
        for item_id in current_room.get("items", []):
            if all_items.get(item_id, {}).get("takeable"): options.append(f"take {item_id}")
        for d in sorted(current_room.get('exits', {}).keys()): options.append(f"go {d}")
        
        if npcs_in_room or scps_in_room:
            options.append("talk")
            options.append("attack")
        
        options.extend(["inventory", "run", "quit"])
        
        action = get_user_choice(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active)

        verb, *args = action.split(' ', 2)
        target = ' '.join(args)

        if action == 'quit': message_to_show, is_fatal = "You give up.", True
        elif verb == 'inventory': message_to_show = player.get_description(); is_item_info = True
        elif verb == 'look' and target:
            if target in current_room.get("details", {}):
                det = current_room["details"][target]
                message_to_show = det["description"]
                if "learns_knowledge" in det:
                    k = player.learn_knowledge(det["learns_knowledge"])
                    if k: message_to_show += "\n" + k
            else: message_to_show = f"Nothing special about the {target}."
        elif verb == 'take':
            item_data = all_items.get(target)
            if target in current_room.get("items", []) and item_data and item_data.get("takeable"):
                if player.right_hand is None: player.right_hand = target; message_to_show = f"Took {item_data['name']} (Right Hand)."
                elif player.left_hand is None: player.left_hand = target; message_to_show = f"Took {item_data['name']} (Left Hand)."
                else: player.inventory.append(target); message_to_show = f"Took {item_data['name']} (Backpack)."
                if "keycard_l1" in target: player.clearance_level = max(player.clearance_level, 1)
                if "keycard_l2" in target: player.clearance_level = max(player.clearance_level, 2)
                if "keycard_l3" in target: player.clearance_level = max(player.clearance_level, 3)
                current_room["items"].remove(target); is_item_info = True
        elif verb == 'talk':
            # --- SUB-MENU: CHOOSE TARGET ---
            target_options = []
            for s in scps_in_room: target_options.append(s.id.lower().replace('scp_', ''))
            for n in npcs_in_room: target_options.append(n["character"].name.lower())
            target_options.append("back")
            
            chosen_target = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Talk to who?")
            
            if chosen_target == "back":
                continue # Return to main options
            
            is_dialogue = True
            found = False
            # Check SCPs
            for s in scps_in_room:
                if chosen_target in s.id.lower():
                    res = s.on_player_talk(player, None)
                    message_to_show = "\n".join(res) or "No response."
                    found = True; break
            # Check NPCs
            if not found:
                for n_info in npcs_in_room:
                    npc = n_info["character"]
                    if chosen_target in npc.name.lower():
                        message_to_show = f'{npc.name} says: "{npc.get_dialogue()}"'
                        found = True; break
        elif verb == 'attack':
            # --- SUB-MENU: CHOOSE TARGET ---
            target_options = []
            for s in scps_in_room: target_options.append(s.id.lower().replace('scp_', ''))
            for n in npcs_in_room: target_options.append(n["character"].name.lower())
            target_options.append("back")
            
            chosen_target = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Attack who?")
            
            if chosen_target == "back":
                continue

            # Find actual target objects for logic
            target_scp = next((s for s in scps_in_room if chosen_target in s.id.lower()), None)
            target_npc = next((n["character"] for n in npcs_in_room if chosen_target in n["character"].name.lower()), None)
            
            scps_to_pass = [target_scp] if target_scp else []
            npcs_to_pass = [target_npc] if target_npc else []
            
            message_to_show, is_fatal = attack(player, npcs_to_pass, scps_in_room=scps_to_pass)
        elif verb == 'go':
            success, msg = move(player, target, game_map, door_manager)
            if not success: message_to_show = msg
            else:
                for s in scp_manager._scps.values():
                    res = s.on_player_move(player, target, None)
                    if res: message_to_show += "\n".join(res)
        elif verb == 'attack':
            message_to_show, is_fatal = attack(player, [n["character"] for n in npcs_in_room], scps_in_room=scps_in_room)
        elif verb == 'run':
            message_to_show, is_fatal = run(player, [n["character"] for n in npcs_in_room], current_room['exits'], game_map, scps_in_room=scps_in_room)

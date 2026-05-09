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
from story_manager import StoryManager

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


def get_user_choice(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="What is your next move?", story_messages=None, facility_code="GREEN"):
    """Novel-style Narrative UI with structured lists."""
    selected_idx = 0
    h, w = stdscr.getmaxyx()
    
    loc_color = curses.color_pair(LOCATION_PAIR)
    prompt_color = curses.color_pair(PROMPT_PAIR)
    highlight_attr = curses.color_pair(HIGHLIGHT_PAIR)
    npc_color = curses.color_pair(NPC_PAIR)
    danger_color = curses.color_pair(DANGER_PAIR)
    item_color = curses.color_pair(ITEM_PAIR)
    
    # Code color
    code_attr = loc_color
    if facility_code == "YELLOW": code_attr = prompt_color
    elif facility_code == "RED": code_attr = danger_color

    while True:
        stdscr.clear()
        
        # --- TITLE ---
        title = f" {current_room['name'].upper()} | SECURITY {facility_code} "
        stdscr.addstr(0, (w - len(title))//2, title, curses.A_BOLD | code_attr)
        stdscr.addstr(1, 0, "─" * (w-1), curses.A_DIM)

        # --- THE NOVEL (Narrative) ---
        row = 3
        narrative_parts = []
        
        # 1. Story/Mood integration
        if story_messages:
            for sm in story_messages:
                narrative_parts.append(sm)
        else:
            narrative_parts.append(current_room['description'])

        # 2. Subtle transition to surroundings
        # narrative_parts.append("As you look around, the environment feels heavy.")

        # Combined Prose Rendering
        full_prose = " ".join(narrative_parts)
        words = full_prose.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 < w - 6: line += word + " "
            else:
                stdscr.addstr(row, 2, line, curses.A_ITALIC if story_messages else curses.A_NORMAL)
                row += 1; line = word + " "
        stdscr.addstr(row, 2, line, curses.A_ITALIC if story_messages else curses.A_NORMAL)
        row += 2

        # --- THE SCAN (Structured Lists) ---
        # 3. Item List
        room_items = [all_items[item_id]["name"] for item_id in current_room.get("items", [])]
        if room_items:
            stdscr.addstr(row, 2, "Objects of interest:", curses.A_BOLD)
            row += 1
            for item in room_items:
                if row < h - 15:
                    stdscr.addstr(row, 4, f"─ {item}", item_color)
                    row += 1
            row += 1

        # 4. Personnel List
        if npcs_in_room or scps_in_room:
            stdscr.addstr(row, 2, "Other presences:", curses.A_BOLD)
            row += 1
            display_count = 0
            for s in scps_in_room:
                if display_count < 3:
                    stdscr.addstr(row, 4, f"─ {s.on_observe_description(player, s.get_status())}", danger_color)
                    row += 1; display_count += 1
            
            for n in npcs_in_room:
                if display_count < 6:
                    npc = n["character"]
                    stdscr.addstr(row, 4, f"─ {npc.get_description()}", npc_color)
                    row += 1; display_count += 1
            
            total = len(npcs_in_room) + len(scps_in_room)
            if total > display_count:
                stdscr.addstr(row, 6, f"... and {total - display_count} more signatures detected.", curses.A_DIM)
                row += 1
        
        row += 2
        stdscr.addstr(row, 0, "─" * (w-1), curses.A_DIM)
        row += 1

        # --- INTERFACE OPTIONS ---
        stdscr.addstr(row, 2, f"{header_text}:", prompt_color)
        row += 1
        for i, opt in enumerate(options):
            if row < h - 3:
                prefix = "  ▶ " if i == selected_idx else "    "
                stdscr.addstr(row, 2, f"{prefix}{opt.replace('_', ' ').capitalize()}", highlight_attr if i == selected_idx else curses.A_NORMAL)
                row += 1

        # --- BIOMETRICS (Bottom Bar) ---
        cond = "Healthy" if player.health > 80 else "Wounded" if player.health > 40 else "In Critical Pain"
        stamina_text = "Full of Energy" if player.stamina > 80 else "Tired" if player.stamina > 40 else "Exhausted"
        sensation = "Focused"
        if player.sanity < 30: sensation = "Terrified"
        elif player.sanity < 70: sensation = "Nervous"
        
        hands = f"Left: {player.left_hand or 'Empty'} | Right: {player.right_hand or 'Empty'}"
        status_line = f"Physical: {cond} | Stamina: {stamina_text} | Feeling: {sensation}"
        try:
            stdscr.addstr(h - 2, 2, hands, item_color)
            stdscr.addstr(h - 1, 2, status_line, curses.A_DIM)
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
    story_manager = StoryManager("data/storyline.json")

    # --- Distribute Items ---
    all_room_ids = list(game_map.keys())
    for item_id, item_data in all_items.items():
        if item_data.get("takeable") and random.random() < 0.4:
            target = random.choice(all_room_ids)
            if "items" not in game_map[target]: game_map[target]["items"] = []
            game_map[target]["items"].append(item_id)

    debug_active = game_config.get("game_settings", {}).get("enable_debug_option", False)
    
    # --- Initialize NPCs ---
    # 1. Spawn D-Class Dormitory
    for _ in range(7):
        npc_manager.spawn_npc("D-Class", start_room_id, department="D-Class")
    
    # 2. Populate Facility based on room tags (Scaling to ~200)
    # Filter rooms by function, EXCLUDING the start dormitory
    security_rooms = [rid for rid, rdata in game_map.items() if "security" in rdata.get("tags", []) and rid != start_room_id]
    research_rooms = [rid for rid, rdata in game_map.items() if ("chamber" in rdata.get("tags", []) or "end" in rdata.get("tags", [])) and rid != start_room_id]
    general_rooms = [rid for rid, rdata in game_map.items() if rid != start_room_id]
    
    for _ in range(200):
        role = random.choice(["Guard", "Scientist", "D-Class", "Janitor", "Engineer", "ISD Agent"])
        
        # Pick appropriate room
        if role == "Guard" or role == "ISD Agent":
            target_rid = random.choice(security_rooms) if security_rooms else random.choice(general_rooms)
            dept = "Security"
        elif role == "Scientist":
            target_rid = random.choice(research_rooms) if research_rooms else random.choice(general_rooms)
            dept = "Research & Science"
        elif role == "D-Class":
            target_rid = random.choice(general_rooms)
            dept = "D-Class"
        else: # Janitor/Engineer
            target_rid = random.choice(general_rooms)
            dept = "Engineering"
            
        npc_manager.spawn_npc(role, target_rid, department=dept)

    # Force some D-Class in the start room to be insane
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
    turn_counter = 0
    current_story_msgs = []
    active_story_event = None # Holds a CHOICE event if active
    
    while not game_over:
        turn_counter += 1
        
        # --- STORY ENGINE ---
        triggered_data = story_manager.check_events(turn_counter, player, npc_manager, scp_manager)
        if triggered_data:
            # Handle messages
            for sm in triggered_data.get("messages", []):
                current_story_msgs.append(sm)
            
            # Handle active CHOICE event
            if triggered_data.get("event"):
                active_story_event = triggered_data["event"]
                current_story_msgs.append(active_story_event.get("message"))

        # --- START OF TURN (Simulation Engine) ---
        sim_log = npc_manager.process_npc_sim_turn(npc_manager._npcs, player.location, game_map)
        with open("debug_output/facility_sim.log", "a") as f:
            f.write(f"--- TURN {turn_counter} START ---\n" + "\n".join(sim_log) + "\n")

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
        if active_story_event:
            # SCRIPTED CHOICE OVERRIDE
            for opt in active_story_event.get("options", []):
                options.append(f"CHOICE:{opt['id']}:{opt['text']}")
        else:
            # Normal Room Options
            for detail in sorted(current_room.get("details", {}).keys()): options.append(f"look at {detail}")
            for item_id in current_room.get("items", []):
                if all_items.get(item_id, {}).get("takeable"): options.append(f"take {item_id}")
            for d in sorted(current_room.get('exits', {}).keys()): options.append(f"go {d}")
            
            if npcs_in_room or scps_in_room:
                options.append("talk")
                options.append("attack")
            
            options.extend(["inventory", "run", "quit"])
        
        # Format labels for display (strip internal IDs)
        display_options = []
        for o in options:
            if o.startswith("CHOICE:"): display_options.append(o.split(":", 2)[2])
            else: display_options.append(o)

        action = get_user_choice(stdscr, display_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, story_messages=current_story_msgs, facility_code=story_manager.facility_code)

        # Handle Choice Execution
        if action in display_options and active_story_event:
            # Map display text back to ID
            original_option = options[display_options.index(action)]
            choice_id = original_option.split(":")[1]
            message_to_show = story_manager.execute_choice(active_story_event, choice_id, player, npc_manager)
            active_story_event = None
            current_story_msgs = []
            continue

        verb, *args = action.split(' ', 2)
        target = ' '.join(args)

        if action == 'quit': message_to_show, is_fatal = "You give up.", True
        elif verb == 'inventory': message_to_show = player.get_description(); is_item_info = True
        elif verb == 'look' and target:
            # (Rest of look logic...)
            found_char = False
            for n_info in npcs_in_room:
                npc = n_info["character"]
                if target.lower() in npc.name.lower():
                    npc.is_focused = True
                    npc.focus_timer = 5
                    mid = getattr(npc, 'master_identity', {})
                    if mid:
                        bio = mid.get('bio', {})
                        app = mid.get('appearance', {})
                        psy = mid.get('psychological_profile', {})
                        details = [
                            f"PERSONNEL FILE: {bio.get('full_name').upper()}",
                            f"Role: {mid.get('professional_file', {}).get('role')} | Gender: {bio.get('gender')}",
                            f"Appearance: {app.get('height_cm')}cm, {app.get('build')}. Eyes: {app.get('physical_features', {}).get('eyes')}.",
                            f"Mental: IQ {psy.get('iq')}. Personality: {mid.get('professional_file', {}).get('department')}.",
                            f"Personal: Hobbies: {', '.join(mid.get('personal_life', {}).get('hobbies', ['None']))}.",
                            f"Background: {bio.get('origin')}.",
                            f"Note: {app.get('physical_features', {}).get('notable_marks', [''])[0]}"
                        ]
                        message_to_show = "\n".join(details)
                    else: message_to_show = npc.get_description()
                    found_char = True; break
            
            if not found_char:
                if target in current_room.get("details", {}):
                    message_to_show = current_room["details"][target]["description"]
                else: message_to_show = f"Nothing special about the {target}."
            # After action, clear story
            current_story_msgs = []
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
                # After action, clear story
                current_story_msgs = []
        elif verb == 'talk':
            target_options = []
            for s in scps_in_room: target_options.append(s.id.lower().replace('scp_', ''))
            for n in npcs_in_room[:8]: target_options.append(n["character"].name.lower())
            target_options.append("back")
            
            chosen_target = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Talk to who?", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
            
            if chosen_target != "back":
                # --- LEVEL 2: CHOOSE TOPIC ---
                dialogue_topics = ["ask about current duties", "try to socialize", "ask about facility secrets", "gossip about others", "back"]
                topic = get_user_choice(stdscr, dialogue_topics, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text=f"What do you want to say to {chosen_target.upper()}?", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
                
                if topic == "back":
                    continue # Return to main loop (which will re-trigger talk and let them pick a new target)

                is_dialogue = True; found = False
                # Process based on topic (simplified for now)
                for s in scps_in_room:
                    if chosen_target in s.id.lower():
                        res = s.on_player_talk(player, None); message_to_show = "\n".join(res) or "No response."; found = True; break
                if not found:
                    for n_info in npcs_in_room:
                        npc = n_info["character"]; 
                        if chosen_target in npc.name.lower():
                            message_to_show = npc.get_contextual_dialogue(topic)
                            found = True; break
                # After action, clear story
                current_story_msgs = []
        elif verb == 'attack':
            target_options = []
            for s in scps_in_room: target_options.append(s.id.lower().replace('scp_', ''))
            # LIMIT: Only show up to 8 nearby NPCs
            for n in npcs_in_room[:8]: target_options.append(n["character"].name.lower())
            target_options.append("back")
            chosen_target = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Attack who?", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
            if chosen_target != "back":
                target_scp = next((s for s in scps_in_room if chosen_target in s.id.lower()), None)
                target_npc = next((n["character"] for n in npcs_in_room if chosen_target in n["character"].name.lower()), None)
                message_to_show, is_fatal = attack(player, [target_npc] if target_npc else [], scps_in_room=[target_scp] if target_scp else [])
                # After action, clear story
                current_story_msgs = []
        elif verb == 'go':
            success, msg = move(player, target, game_map, door_manager)
            if not success: message_to_show = msg
            else:
                for s in scp_manager._scps.values():
                    res = s.on_player_move(player, target, None)
                    if res: message_to_show += "\n".join(res)
                # Success move, clear story
                current_story_msgs = []
        elif verb == 'run':
            message_to_show, is_fatal = run(player, [n["character"] for n in npcs_in_room], current_room['exits'], game_map, scps_in_room=scps_in_room)
            # Action taken, clear story
            current_story_msgs = []

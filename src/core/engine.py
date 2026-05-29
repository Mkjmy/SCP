import curses
import json
import os
import random

# Modular Imports
from entities.player.player import Player
from entities.npc.manager import NPCManager
from entities.scp.scp_manager import SCPManager
from world.navigation.door_manager import DoorManager
from world.navigation.navigation import move
from mechanics.combat.actions import attack, run
from world.map.map_generator import load_room_templates, generate_map
from narrative.story.story_manager import StoryManager
from narrative.ui.terminal import init_terminal_colors, display_message
from narrative.ui.menu import get_user_choice

def main_loop(stdscr):
    init_terminal_colors()
    curses.curs_set(0)

    # --- Load Configuration ---
    config_file = 'data/game_config.json'
    try:
        with open(config_file, 'r') as f:
            game_config = json.load(f)
    except: return

    map_settings = game_config.get("map_settings", {})
    random_map_num_rooms = map_settings.get("random_map_num_rooms", 50)

    # Generate Map
    try:
        room_templates = load_room_templates()
        game_map, start_room_id = generate_map(room_templates, num_rooms=random_map_num_rooms)
    except: return

    # Load Items
    try:
        with open('data/items.json', 'r') as f: all_items = json.load(f)
    except: all_items = {}

    # Player
    player_config = game_config.get("player", {})
    player = Player(
        name=player_config.get("name", "D-902"),
        role="Player",
        clearance_level=0,
        start_location=start_room_id
    )

    # Managers
    door_manager = DoorManager(game_map)
    npc_manager = NPCManager(game_map)
    scp_manager = SCPManager(game_map)
    story_manager = StoryManager("data/storyline.json")
    # Populate NPCs
    # 1. Spawn D-Class Dormitory (STRICT: Only D-Class here)
    for _ in range(7):
        npc_manager.spawn_npc("D-Class", start_room_id, department="D-Class")

    # 2. Populate Facility based on room tags (Scaling to ~200)
    security_rooms = [rid for rid, rdata in game_map.items() if "security" in rdata.get("tags", []) and rid != start_room_id]
    research_rooms = [rid for rid, rdata in game_map.items() if ("chamber" in rdata.get("tags", []) or "end" in rdata.get("tags", [])) and rid != start_room_id]
    general_rooms = [rid for rid, rdata in game_map.items() if rid != start_room_id]

    for _ in range(200):
        # EXCLUDE start_room_id from general population to keep it pure D-Class
        role = random.choice(["Guard", "Scientist", "D-Class", "Janitor", "Engineer", "ISD Agent"])
        target_rid = start_room_id
        while target_rid == start_room_id:
            if role == "Guard" or role == "ISD Agent":
                target_rid = random.choice(security_rooms) if security_rooms else random.choice(general_rooms)
                dept = "Security"
            elif role == "Scientist":
                target_rid = random.choice(research_rooms) if research_rooms else random.choice(general_rooms)
                dept = "Research & Science"
            else:
                target_rid = random.choice(general_rooms)
                dept = "D-Class" if role == "D-Class" else "Engineering"

        npc_manager.spawn_npc(role, target_rid, department=dept)

    npc_manager.save_all_identities()
    debug_active = game_config.get("game_settings", {}).get("enable_debug_option", False)

    game_over = False
    message_to_show = ""
    turn_counter = 0
    current_story_msgs = []
    active_story_event = None

    while not game_over:
        # UI Prep
        current_room = game_map[player.location]
        npcs_in_room = npc_manager.get_npcs_in_room(player.location)
        scps_in_room = scp_manager.get_scps_in_room(player.location)

        if player.health <= 0:
            display_message(stdscr, message_to_show or "Your body gives out.", is_danger=True)
            game_over = True; continue

        if message_to_show:
            display_message(stdscr, message_to_show)
            message_to_show = ""

        # Options
        options = []
        room_tags = current_room.get("tags", [])
        if active_story_event:
            for opt in active_story_event.get("options", []): options.append(f"CHOICE:{opt['id']}:{opt['text']}")
        else:
            options.append("SECTION:SCENE")
            for d in sorted(current_room.get("details", {}).keys()): options.append(f"look at {d}")
            for d in sorted(current_room.get('exits', {}).keys()): options.append(f"go {d}")
            
            if "cafeteria" in room_tags: options.append("eat")
            if "dormitory" in room_tags or "break_room" in room_tags: options.append("rest")
            if "medibay" in room_tags: options.append("request medical aid")
            
            options.append("SECTION:ACTIONS")
            if any(t in room_tags for t in ["office", "security", "admin"]): options.append("search for files")
            if any(t in room_tags for t in ["office", "server_room"]): options.append("hack terminal")

            if npcs_in_room or scps_in_room: options.append("talk")
            options.extend(["attack", "inventory", "run", "quit"])
        
        display_options = [o.split(":", 2)[2] if o.startswith("CHOICE:") else o for o in options]
        action = get_user_choice(stdscr, display_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, story_messages=current_story_msgs, facility_code=story_manager.facility_code)

        if action in display_options and active_story_event:
            original = options[display_options.index(action)]
            message_to_show = story_manager.execute_choice(active_story_event, original.split(":")[1], player, npc_manager)
            active_story_event = None
            current_story_msgs = [] # Clear old messages after choice
            continue

        # --- TURN PROGRESSION ---
        # Clear story messages from the PREVIOUS turn before generating new ones
        current_story_msgs = [] 
        
        turn_counter += 1
        sim_log = npc_manager.process_npc_sim_turn(npc_manager._npcs, player, game_map)

        # Story Check
        triggered = story_manager.check_events(turn_counter, player, npc_manager, scp_manager)
        if triggered:
            if triggered.get("messages"): 
                for sm in triggered["messages"]: current_story_msgs.append(sm)
            
            # DATA-DRIVEN SPAWNING: Generic story injection
            if "spawns" in triggered:
                for spawn_info in triggered["spawns"]:
                    role = spawn_info.get("role", "Guard")
                    nid = npc_manager.spawn_npc(role, player.location, department=spawn_info.get("dept", "Security"))
                    if nid:
                        char = npc_manager._npcs[nid]["character"]
                        if "name" in spawn_info: char.name = spawn_info["name"]
                        if "task" in spawn_info:
                            task = spawn_info["task"].copy()
                            # Resolve dynamic destination if tag is used
                            if "dest_tag" in task:
                                dests = [rid for rid, rd in game_map.items() if task["dest_tag"] in rd.get("tags", [])]
                                task["dest"] = random.choice(dests) if dests else player.location
                            char.current_task = task

            if triggered.get("event"): 
                active_story_event = triggered["event"]
                current_story_msgs.append(active_story_event.get("message"))

        verb, *args = action.split(' ', 2)
        target = ' '.join(args)

        if action == 'quit': game_over = True
        elif action == 'eat':
            message_to_show = "You sit down and consume a tray of lukewarm, sterile Foundation rations. It tastes like nothing, but the hunger subsides."
            player.health = min(player.max_health, player.health + 5)
        elif action == 'rest':
            message_to_show = "You lie down for a moment, closing your eyes despite the constant hum of the facility. You feel a bit more alert."
            player.stamina = player.max_stamina
        elif action == 'search for files' or action == 'hack terminal':
            difficulty = 10 if action == 'hack terminal' else 7
            if player.attributes['intelligence'] + random.randint(1, 6) > difficulty:
                if npc_manager._npcs:
                    random_nid = random.choice(list(npc_manager._npcs.keys()))
                    npc_char = npc_manager._npcs[random_nid]["character"]
                    mid = getattr(npc_char, 'master_identity', {})
                    secrets = mid.get('social_and_secrets', {})
                    if secrets:
                        stype = random.choice(['debts', 'hidden_agenda', 'hidden_affiliation'])
                        val = secrets.get(stype)
                        if random_nid not in player.known_secrets: player.known_secrets[random_nid] = {}
                        player.known_secrets[random_nid][stype] = val
                        message_to_show = f"SUCCESS: You discovered leverage against {npc_char.name} ({stype.replace('_', ' ')}). This could be useful."
                    else: message_to_show = "You found files, but they contain no personal leverage."
                else: message_to_show = "The database is empty."
            else: message_to_show = "You failed to extract any useful data before being nearly spotted."
        elif action == 'request medical aid':
            message_to_show = "A medical technician patches you up. The clinical care eases your trauma."
            player.health = min(player.max_health, player.health + 30)
        elif verb == 'inventory': 
            message_to_show = player.get_description()
            # Turn doesn't progress for inventory, so we don't want new story messages yet
        elif verb == 'look':
            found = False
            for n in npcs_in_room:
                if target.lower() in n["character"].name.lower():
                    message_to_show = n["character"].get_description(player=player); found = True; break
            if not found and target in current_room.get("details", {}):
                message_to_show = current_room["details"][target]["description"]; found = True
            if not found: message_to_show = f"You look at {target}, but find nothing notable."
        elif verb == 'talk':
            target_options = [s.id.lower().replace('scp_', '') for s in scps_in_room] + [f"{n['character'].name.lower()} ({n['character'].get_perceived_role(player).lower()})" for n in npcs_in_room[:8]] + ["back"]
            chosen = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Talk to who?", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
            if chosen != "back":
                name = chosen.split(" (")[0]
                target_char = next((n["character"] for n in npcs_in_room if name in n["character"].name.lower()), None)
                if target_char:
                    topics = ["ask about current duties", "try to socialize", "ask about facility secrets", "gossip about others"]
                    if target_char.id in player.known_secrets: topics.append("manipulate using secrets")
                    topics.append("back")
                    topic = get_user_choice(stdscr, topics, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text=f"Talk to {target_char.name.upper()}:", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
                    if topic == "manipulate using secrets":
                        if random.randint(1, 20) + (player.attributes['intelligence'] // 2) > 14:
                            message_to_show = f"{target_char.name} pales. 'I'll do anything. Take my clearance card.'"
                            if "Level 2 Keycard" not in player.inventory: player.inventory.append("Level 2 Keycard")
                        else: message_to_show = f"{target_char.name} dismisses your threats with a cold glare."
                    elif topic != "back": message_to_show = target_char.get_contextual_dialogue(topic)
        elif verb == 'go':
            success, msg = move(player, target, game_map, door_manager)
            message_to_show = msg if not success else f"You move {target} into the next sterile corridor."
        elif verb == 'attack':
            target_options = [f"{n['character'].name.lower()} ({n['character'].get_perceived_role(player).lower()})" for n in npcs_in_room[:8]] + ["back"]
            chosen = get_user_choice(stdscr, target_options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="Attack who?", story_messages=current_story_msgs, facility_code=story_manager.facility_code)
            if chosen != "back":
                name = chosen.split(" (")[0]
                target_char = next((n["character"] for n in npcs_in_room if name in n["character"].name.lower()), None)
                message_to_show, is_fatal = attack(player, [target_char] if target_char else [], scps_in_room=[])
        
        if not message_to_show and action != 'quit' and not current_story_msgs:
            message_to_show = "You spend a moment observing the humming silence of the facility."

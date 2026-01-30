import curses
import sys
import time
import json
import os
from player import Player
from navigation import move
from actions import attack, run
from map_generator import generate_map, load_room_templates
from character import generate_character
from map_visualizer import visualize_map_ascii # NEW IMPORT

# ... (Color definitions remain the same) ...
HIGHLIGHT_PAIR = 1
DANGER_PAIR = 2
LOCATION_PAIR = 3
PROMPT_PAIR = 4
NPC_PAIR = 5
DIALOGUE_PAIR = 6
ITEM_PAIR = 7

def init_colors():
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(HIGHLIGHT_PAIR, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(DANGER_PAIR, curses.COLOR_RED, -1)
        curses.init_pair(LOCATION_PAIR, curses.COLOR_YELLOW, -1)
        curses.init_pair(PROMPT_PAIR, curses.COLOR_CYAN, -1)
        curses.init_pair(NPC_PAIR, curses.COLOR_GREEN, -1)
        curses.init_pair(DIALOGUE_PAIR, curses.COLOR_WHITE, -1)
        curses.init_pair(ITEM_PAIR, curses.COLOR_MAGENTA, -1)

def generate_and_load_data(items_file, debug=False):
    """
    Generates a new map or loads a static one for debug mode.
    Also loads all other game data.
    """
    try:
        if debug:
            print("DEBUG MODE: Loading static 'map.json'...")
            with open('map.json', 'r') as f:
                game_map = json.load(f)
            start_room_id = 'cell' # Default start for static map
        else:
            room_templates = load_room_templates()
            game_map, start_room_id = generate_map(room_templates, num_rooms=15)
        
        with open(items_file, 'r') as f:
            all_items = json.load(f)
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data file: {e}")
        sys.exit(1)
        
    # Populate NPCs from the loaded/generated map
    world_npcs = {}
    for room_id, room_data in game_map.items():
        if "entities" in room_data:
            world_npcs[room_id] = [generate_character(entity) for entity in room_data.get("entities", [])]

    return game_map, world_npcs, all_items, start_room_id

# ... (display_message remains mostly the same, can add item color) ...
def display_message(stdscr, message, is_danger=False, is_dialogue=False, is_item_info=False):
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    
    color = curses.A_NORMAL
    if curses.has_colors():
        if is_danger: color = curses.color_pair(DANGER_PAIR)
        elif is_dialogue: color = curses.color_pair(DIALOGUE_PAIR)
        elif is_item_info: color = curses.color_pair(ITEM_PAIR)

    max_line_length = w - 4
    lines = [line for para in message.split('\n') for line in (lambda text: [text[i:i+max_line_length] for i in range(0, len(text), max_line_length)])(para)]
    start_y = h // 2 - len(lines) // 2
    for i, line in enumerate(lines):
        start_x = w // 2 - len(line) // 2
        stdscr.addstr(start_y + i, start_x, line, color)
    stdscr.addstr(h - 2, w // 2 - 13, "[Press any key to continue]", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()


def display_status_bar(stdscr, player):
    """Draws the player's status at the bottom of the screen with no background color."""
    h, w = stdscr.getmaxyx()
    
    # --- Strings ---
    health_str = f"Health: {player.health}/{player.max_health}"
    stamina_str = f"Stamina: {player.stamina}/{player.max_stamina}"
    morale_str = f"Morale: {player.morale}/{player.max_morale}"
    hands_display = f"Hands: L-{player.left_hand if player.left_hand else 'Empty'} | R-{player.right_hand if player.right_hand else 'Empty'}"
    
    injury_messages = player.get_injury_status()
    injury_line = ""
    if injury_messages:
        injury_line = "Injuries: " + ", ".join(injury_messages)

    # --- Colors ---
    health_color = curses.color_pair(NPC_PAIR) if player.health / player.max_health > 0.6 else curses.color_pair(LOCATION_PAIR) if player.health / player.max_health > 0.3 else curses.color_pair(DANGER_PAIR)
    stamina_color = curses.color_pair(PROMPT_PAIR)
    morale_color = curses.color_pair(NPC_PAIR) if player.morale / player.max_morale > 0.6 else curses.color_pair(LOCATION_PAIR) if player.morale / player.max_morale > 0.3 else curses.color_pair(DANGER_PAIR)

    # --- Render ---
    # Clear previous status lines to prevent artifacts
    if h >= 3:
        stdscr.move(h - 3, 0)
        stdscr.clrtoeol()
    if h >= 2:
        stdscr.move(h - 2, 0)
        stdscr.clrtoeol()
    if h >= 1:
        stdscr.move(h - 1, 0)
        stdscr.clrtoeol()
    
    # Line 1: Core Stats
    stats_line = f"{health_str} | {stamina_str} | {morale_str}"
    if h >= 1:
        stdscr.addstr(h - 1, 0, stats_line)
        # Re-apply colors over the black/white text
        stdscr.addstr(h - 1, 0, health_str, health_color)
        stdscr.addstr(h - 1, len(health_str) + 3, stamina_str, stamina_color)
        stdscr.addstr(h - 1, len(health_str) + len(stamina_str) + 6, morale_str, morale_color)

    # Line 2: Hands
    if h >= 2:
        stdscr.addstr(h - 2, 0, hands_display, curses.color_pair(ITEM_PAIR))

    # Line 3: Injuries (if present)
    if injury_line and h >= 3:
        stdscr.addstr(h - 3, 0, injury_line, curses.color_pair(DANGER_PAIR))



def main_loop(stdscr, debug=False):
    curses.curs_set(0)
    init_colors()

    game_map, world_npcs, all_items, start_room_id = generate_and_load_data('items.json', debug=debug)
    player = Player(start_location=start_room_id)
    game_over = False
    
    display_message(stdscr, f"You are {player.name}, Clearance Level {player.clearance_level}.")

    while not game_over:
        message_to_show, is_fatal, is_dialogue, is_item_info = "", False, False, False

        if player.health <= 0:
            if not message_to_show:
                message_to_show = "Your body gives out. The darkness consumes you."
            display_message(stdscr, message_to_show, is_danger=True)
            game_over = True
            continue

        current_room_id = player.location
        current_room = game_map[current_room_id]
        npcs_in_room = world_npcs.get(current_room_id, [])

        # --- Dynamic Option Generation ---
        options = []
        for detail in sorted(current_room.get("details", {}).keys()):
            options.append(f"look at {detail}")
        for item_id in current_room.get("items", []):
            if all_items[item_id].get("takeable"):
                options.append(f"take {item_id}")
        for direction in sorted(current_room['exits'].keys()):
            options.append(f"go {direction}")
        if npcs_in_room:
            options.append("talk")
        options.extend(["inventory", "attack", "run", "quit"])
        if player.has_knowledge('skill_basic_lockpicking'):
            options.append("lockpick")
        if player.inventory:
            options.append("equip")
        if player.left_hand or player.right_hand:
            options.append("unequip")
        if debug:
            options.append("debug")
        
        selected_idx = 0
        action = None

        while action is None:
            stdscr.clear()
            loc_color = curses.color_pair(LOCATION_PAIR)
            prompt_color = curses.color_pair(PROMPT_PAIR)
            highlight_attr = curses.color_pair(HIGHLIGHT_PAIR)
            npc_color = curses.color_pair(NPC_PAIR)
            danger_color = curses.color_pair(DANGER_PAIR)
            item_color = curses.color_pair(ITEM_PAIR)
            desc_color = danger_color if any(c.role == 'Guard' for c in npcs_in_room) else curses.A_NORMAL

            stdscr.addstr(0, 0, f"Location: {current_room['name']} ({current_room_id})\n", loc_color)
            stdscr.addstr(current_room['description'] + "\n", desc_color)

            room_items = [all_items[item_id]["name"] for item_id in current_room.get("items", [])]
            if room_items:
                stdscr.addstr("You see: " + ", ".join(room_items) + ".\n\n", item_color)
            else:
                stdscr.addstr("\n")
            
            if npcs_in_room:
                stdscr.addstr("You see someone here:\n", npc_color)
                for npc in npcs_in_room:
                    stdscr.addstr(npc.get_description(debug=debug) + "\n", npc_color)
                stdscr.addstr("\n")

            stdscr.addstr("What do you do?\n", prompt_color)
            for i, option in enumerate(options):
                stdscr.addstr(f"  > {option.replace('_', ' ').capitalize()}\n", highlight_attr if i == selected_idx else curses.A_NORMAL)
            
            display_status_bar(stdscr, player)
            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP: selected_idx = (selected_idx - 1) % len(options)
            elif key == curses.KEY_DOWN: selected_idx = (selected_idx + 1) % len(options)
            elif key in [curses.KEY_ENTER, ord('\n')]: action = options[selected_idx]
            elif key == ord('q'): action = 'quit'

        
        verb, *args = action.split(' ', 2)
        target = ' '.join(args)
        
        if verb == 'quit':
            message_to_show, game_over, is_fatal = "You give up.", True, True
        elif verb == 'inventory':
            message_to_show = player.get_description(debug=debug) # Show full stats in debug
            is_item_info = True
        elif verb == 'debug':
            message_to_show = "DEBUG MODE\n" + player.get_description(debug=True)
            if npcs_in_room:
                for npc in npcs_in_room:
                    message_to_show += "\n\n" + npc.get_description(debug=True)
            
            # Generate and display ASCII map
            ascii_map = visualize_map_ascii(game_map, player.location)
            message_to_show += "\n\n--- ASCII MAP ---\n" + ascii_map
            message_to_show += "\n\n(Press any key to continue)" # Add a pause after ASCII map

            # Write full JSON map data to a file
            output_dir = "debug_output"
            os.makedirs(output_dir, exist_ok=True)
            map_dump_path = os.path.join(output_dir, "debug_map.json")
            try:
                with open(map_dump_path, 'w') as f:
                    json.dump(game_map, f, indent=2)
                message_to_show += f"\n\n--- FULL MAP DATA ---\nGenerated map data saved to:\n{map_dump_path}"
            except Exception as e:
                message_to_show += f"\n\n--- FULL MAP DATA ---\nFailed to save map data: {e}"
        elif verb == 'look' and target:
             if target in current_room.get("details", {}):
                 detail_data = current_room["details"][target]
                 message_to_show = detail_data["description"]
                 if "learns_knowledge" in detail_data:
                     knowledge_gained = player.learn_knowledge(detail_data["learns_knowledge"])
                     if knowledge_gained:
                         message_to_show += "\n" + knowledge_gained
             else:
                 message_to_show = f"You look closely at the {target}, but see nothing special."
        elif verb == 'take':
            item_id_to_take = target
            if item_id_to_take in current_room.get("items", []) and all_items[item_id_to_take]["takeable"]:
                if player.right_hand is None:
                    player.right_hand = item_id_to_take
                    message_to_show = f'You took the {all_items[item_id_to_take]["name"]} in your right hand.'
                elif player.left_hand is None:
                    player.left_hand = item_id_to_take
                    message_to_show = f'You took the {all_items[item_id_to_take]["name"]} in your left hand.'
                else:
                    player.inventory.append(item_id_to_take)
                    message_to_show = f'You took the {all_items[item_id_to_take]["name"]} and put it in your backpack.'
                current_room["items"].remove(item_id_to_take)
                is_item_info = True
            else:
                message_to_show = f"You can't take the {item_id_to_take}."
        elif verb == 'equip':
            parts = target.split(" to ")
            if len(parts) != 2:
                message_to_show = "Use 'equip [item] to [hand]'."
            else:
                item_to_equip, hand_to_equip = parts
                message_to_show = player.equip_item(item_to_equip, hand_to_equip)
        elif verb == 'unequip':
            if target not in ['left', 'right']:
                message_to_show = "Use 'unequip [left/right]'."
            else:
                message_to_show = player.unequip_item(target)
        elif verb == 'talk':
            if not npcs_in_room:
                message_to_show = "There is no one here to talk to."
            else:
                npc = npcs_in_room[0]
                message_to_show = f'{npc.name} says: "{npc.get_dialogue()}"'
                is_dialogue = True
        elif verb == 'go':
            success, move_message = move(player, target, game_map)
            if not success: message_to_show = move_message
        elif verb == 'attack':
            message_to_show, game_over = attack(player, npcs_in_room)
            is_fatal = game_over
        elif verb == 'run':
            message_to_show, game_over = run(player, npcs_in_room, current_room['exits'], game_map)
            is_fatal = game_over
        elif verb == 'lockpick':
            if not target:
                message_to_show = "Lockpick what?"
            elif target not in current_room.get("details", {}):
                message_to_show = f"There's no '{target}' here to lockpick."
            else:
                detail_data = current_room["details"][target]
                if not detail_data.get("lockable"):
                    message_to_show = f"The {target} isn't something you can lockpick."
                elif not detail_data.get("locked", True):
                    message_to_show = f"The {target} is already unlocked."
                else:
                    base_stamina_cost = 10
                    morale_effect_stamina = player.get_morale_effect('lockpick')
                    stamina_cost = base_stamina_cost - morale_effect_stamina

                    if player.stamina < stamina_cost:
                        message_to_show = "You're too exhausted to attempt lockpicking."
                    else:
                        player.stamina -= stamina_cost
                        
                        dexterity_for_check = player.attributes['dexterity'] - player.get_debuff(attribute='dexterity')
                        morale_effect_dex = player.get_morale_effect('dexterity')
                        dexterity_for_check += morale_effect_dex
                        
                        lock_difficulty = detail_data.get("lock_difficulty", 5)
                        
                        success_chance = max(0.1, min(0.9, 0.5 + (dexterity_for_check - lock_difficulty) * 0.1))
                        
                        if random.random() < success_chance:
                            morale_message = player.change_morale(5)
                            message_to_show = f"You successfully lockpicked the {target}! It's now unlocked."
                            if morale_message: message_to_show += f" {morale_message}"
                            detail_data["locked"] = False
                            if "unlocked_description" in detail_data:
                                detail_data["description"] = detail_data["unlocked_description"]
                        else:
                            morale_message = player.change_morale(-5)
                            message_to_show = f"You fumble with the lock on the {target} but fail to open it. It remains locked."
                            if morale_message: message_to_show += f" {morale_message}"
                            if random.random() < 0.2:
                                injury_msg = player.apply_injury(random.choice(['left_arm', 'right_arm']), 'minor_injury')
                                message_to_show += f" {injury_msg}"

        if message_to_show:
            display_message(stdscr, message_to_show, is_danger=is_fatal, is_dialogue=is_dialogue, is_item_info=is_item_info)



if __name__ == "__main__":
    DEBUG_MODE = "--debug" in sys.argv
    try:
        curses.wrapper(main_loop, debug=DEBUG_MODE)
    except curses.error as e:
        print(f"\nCurses Error: {e}")
        print("Your terminal might not support curses, or the window is too small.")
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")


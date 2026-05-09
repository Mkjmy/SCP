import curses

# Color pairs
LOCATION_PAIR = 1
PROMPT_PAIR = 2
HIGHLIGHT_PAIR = 3
NPC_PAIR = 4
DANGER_PAIR = 5
ITEM_PAIR = 6
DIALOGUE_PAIR = 7

def init_terminal_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(LOCATION_PAIR, curses.COLOR_CYAN, -1)
    curses.init_pair(PROMPT_PAIR, curses.COLOR_YELLOW, -1)
    curses.init_pair(HIGHLIGHT_PAIR, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(NPC_PAIR, curses.COLOR_GREEN, -1)
    curses.init_pair(DANGER_PAIR, curses.COLOR_RED, -1)
    curses.init_pair(ITEM_PAIR, curses.COLOR_MAGENTA, -1)
    curses.init_pair(DIALOGUE_PAIR, curses.COLOR_BLUE, -1)

def display_message(stdscr, message, is_danger=False, is_dialogue=False, is_item_info=False, is_debug_message=False):
    """Displays a message to the player with proper word-wrapping."""
    h, w = stdscr.getmaxyx()
    stdscr.clear()
    
    color = curses.A_NORMAL
    if is_danger: color = curses.color_pair(DANGER_PAIR)
    elif is_dialogue: color = curses.color_pair(DIALOGUE_PAIR)
    elif is_item_info: color = curses.color_pair(ITEM_PAIR)

    # Manual word-wrapping to prevent cutting words
    wrapped_lines = []
    for paragraph in message.split('\n'):
        words = paragraph.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 < w - 6:
                current_line += word + " "
            else:
                wrapped_lines.append(current_line.strip())
                current_line = word + " "
        wrapped_lines.append(current_line.strip())

    # Start display from middle if short, or top if long
    start_y = max(0, (h // 2) - (len(wrapped_lines) // 2)) if not is_debug_message else 0
    for i, line in enumerate(wrapped_lines):
        if start_y + i >= h - 2: break
        try:
            # Center each line for dramatic effect
            x = max(0, (w - len(line)) // 2) if not is_debug_message else 2
            stdscr.addstr(start_y + i, x, line, color)
        except: pass

    # Display continuation prompt
    prompt_y = h - 2
    prompt_x = (w - len("[Press any key to continue]")) // 2
    if prompt_y >= 0 and prompt_x >=0:
        try: stdscr.addstr(prompt_y, prompt_x, "[Press any key to continue]", curses.A_DIM)
        except: pass
    stdscr.refresh()
    curses.flushinp()
    stdscr.getch()

def render_scene(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text, story_messages, selected_idx):
    """Novel-style Narrative UI rendering with integrated word-wrapping."""
    h, w = stdscr.getmaxyx()
    
    loc_color = curses.color_pair(LOCATION_PAIR)
    prompt_color = curses.color_pair(PROMPT_PAIR)
    highlight_attr = curses.color_pair(HIGHLIGHT_PAIR)
    npc_color = curses.color_pair(NPC_PAIR)
    danger_color = curses.color_pair(DANGER_PAIR)
    item_color = curses.color_pair(ITEM_PAIR)

    stdscr.clear()
    
    # --- TITLE ---
    title = f" {current_room['name'].upper()} "
    stdscr.addstr(0, max(0, (w - len(title))//2), title, curses.A_BOLD)
    stdscr.addstr(1, 0, "─" * (w-1), curses.A_DIM)

    # --- THE NOVEL (Narrative) ---
    row = 3
    narrative_parts = []
    if story_messages:
        for sm in story_messages: narrative_parts.append(sm)
    else:
        narrative_parts.append(current_room['description'])

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
    room_items = [all_items[item_id]["name"] for item_id in current_room.get("items", []) if item_id in all_items]
    if room_items:
        stdscr.addstr(row, 2, "Objects of interest:", curses.A_BOLD); row += 1
        for item in room_items:
            if row < h - 15: stdscr.addstr(row, 4, f"─ {item}", item_color); row += 1
        row += 1

    if npcs_in_room or scps_in_room:
        stdscr.addstr(row, 2, "Other presences:", curses.A_BOLD); row += 1
        display_count = 0
        for s in scps_in_room:
            if display_count < 3:
                stdscr.addstr(row, 4, f"─ {s.on_observe_description(player, s.get_status())}", danger_color)
                row += 1; display_count += 1
        
        for n in npcs_in_room:
            if display_count < 6:
                npc = n["character"]
                stdscr.addstr(row, 4, f"─ {npc.get_description(player=player)}", npc_color)
                row += 1; display_count += 1
    
    row += 2
    if row < h - 10: stdscr.addstr(row, 0, "─" * (w-1), curses.A_DIM); row += 1

    # --- INTERFACE OPTIONS ---
    stdscr.addstr(row, 2, f"{header_text}:", prompt_color); row += 1
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

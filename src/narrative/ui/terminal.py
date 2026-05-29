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
    """Refined Hyper-Modern UI with persistent log and clear hierarchy."""
    h, w = stdscr.getmaxyx()
    
    loc_color = curses.color_pair(LOCATION_PAIR)
    prompt_color = curses.color_pair(PROMPT_PAIR)
    highlight_attr = curses.color_pair(HIGHLIGHT_PAIR)
    npc_color = curses.color_pair(NPC_PAIR)
    danger_color = curses.color_pair(DANGER_PAIR)
    item_color = curses.color_pair(ITEM_PAIR)
    diag_color = curses.color_pair(DIALOGUE_PAIR)

    stdscr.clear()
    
    # --- 1. THE HEADER ---
    title = f" {current_room['name'].upper()} "
    stdscr.addstr(0, max(0, (w - len(title))//2), title, curses.A_BOLD | loc_color)
    stdscr.addstr(1, 0, "━" * (w-1), curses.A_DIM)

    row = 2
    
    # --- 2. RECENT EVENTS (Persistent Story/Action Feedback) ---
    if story_messages:
        stdscr.addstr(row, 2, "◈ RECENT EVENTS", curses.A_BOLD | diag_color)
        row += 1
        for sm in story_messages[-3:]: # Show last 3 messages
            # Wrap story message
            words = sm.split()
            line = "  "
            for word in words:
                if len(line) + len(word) + 1 < w - 6: line += word + " "
                else:
                    if row < h - 4: stdscr.addstr(row, 2, line, curses.A_ITALIC | diag_color); row += 1
                    line = "  " + word + " "
            if row < h - 4: stdscr.addstr(row, 2, line, curses.A_ITALIC | diag_color); row += 1
        row += 1

    # --- 3. THE ENVIRONMENT (Static Context) ---
    stdscr.addstr(row, 2, "◈ ENVIRONMENT", curses.A_BOLD | curses.A_DIM)
    row += 1
    full_prose = current_room['description']
    words = full_prose.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 < w - 6: line += word + " "
        else:
            if row < h - 4: stdscr.addstr(row, 2, line, curses.A_DIM); row += 1
            line = "  " + word + " "
    if row < h - 4: stdscr.addstr(row, 2, line, curses.A_DIM); row += 1
    row += 1

    # --- 4. THE SCAN (Personnel & Items) ---
    # SORT NPCs for consistency
    sorted_npcs = sorted(npcs_in_room, key=lambda x: x["character"].name)
    
    if sorted_npcs or scps_in_room:
        stdscr.addstr(row, 2, "◈ PERSONNEL", curses.A_BOLD | npc_color); row += 1
        display_count = 0
        for s in scps_in_room:
            if display_count < 2 and row < h - 4:
                stdscr.addstr(row, 4, f"─ {s.on_observe_description(player, s.get_status())}", danger_color)
                row += 1; display_count += 1
        for n in sorted_npcs:
            if display_count < 6 and row < h - 4:
                npc = n["character"]
                stdscr.addstr(row, 4, f"─ {npc.get_description(player=player)}", npc_color)
                row += 1; display_count += 1
    
    room_items = [all_items[item_id]["name"] for item_id in current_room.get("items", []) if item_id in all_items]
    if room_items and row < h - 8:
        stdscr.addstr(row, 2, "◈ OBJECTS", curses.A_BOLD | item_color); row += 1
        for item in room_items[:3]:
            stdscr.addstr(row, 4, f"─ {item}", item_color); row += 1

    # --- 5. INTERFACE ---
    row = max(row + 1, h - len(options) - 5)
    stdscr.addstr(row, 2, f"➤ {header_text.upper()}", curses.A_BOLD | prompt_color); row += 1
    for i, opt in enumerate(options):
        if row < h - 2:
            if opt.startswith("SECTION:"):
                section_name = opt.split(":")[1].upper()
                stdscr.addstr(row, 2, f"  [{section_name}]", curses.A_DIM | prompt_color)
                row += 1
            else:
                prefix = "  ▶ " if i == selected_idx else "    "
                stdscr.addstr(row, 2, f"{prefix}{opt.replace('_', ' ').capitalize()}", highlight_attr if i == selected_idx else curses.A_NORMAL)
                row += 1

    # --- 6. BIOMETRICS ---
    cond = "Healthy" if player.health > 80 else "Wounded" if player.health > 40 else "Critical"
    stamina_text = "Ready" if player.stamina > 70 else "Tired" if player.stamina > 30 else "Exhausted"
    status_line = f" [ STATUS: {cond.upper()} | STAMINA: {stamina_text.upper()} | MORALE: {int(player.morale)}% ] "
    try:
        stdscr.addstr(h - 1, 0, "━" * (w-1), curses.A_DIM)
        stdscr.addstr(h - 1, (w - len(status_line)) // 2, status_line, curses.A_REVERSE | loc_color)
    except: pass

    stdscr.refresh()

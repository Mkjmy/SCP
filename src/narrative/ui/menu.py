import curses
from narrative.ui.terminal import render_scene

def get_user_choice(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text="What is your next move?", story_messages=None, facility_code="GREEN"):
    """Generic menu selection wrapper with section support."""
    selected_idx = 0
    # Initial skip if start is a section
    while selected_idx < len(options) and options[selected_idx].startswith("SECTION:"):
        selected_idx += 1

    while True:
        render_scene(stdscr, options, current_room, all_items, npcs_in_room, scps_in_room, player, debug_active, header_text, story_messages, selected_idx)
        
        key = stdscr.getch()
        if key == curses.KEY_UP:
            selected_idx = (selected_idx - 1) % len(options)
            while options[selected_idx].startswith("SECTION:"):
                selected_idx = (selected_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected_idx = (selected_idx + 1) % len(options)
            while options[selected_idx].startswith("SECTION:"):
                selected_idx = (selected_idx + 1) % len(options)
        elif key in [curses.KEY_ENTER, ord('\n')]:
            if not options[selected_idx].startswith("SECTION:"):
                return options[selected_idx]
        elif key == ord('q'): return 'quit'

# dev_dashboard.py
import curses
import json
import os
import time

def load_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r') as f:
        try: return json.load(f)
        except: return {}

def load_log(path, limit=10):
    if not os.path.exists(path): return []
    with open(path, 'r') as f:
        lines = f.readlines()
        return [l.strip() for l in lines if "SOCIAL:" in l or "SCIENTIST" in l or "Guard" in l][-limit:]

def draw_dashboard(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
        except:
            pass # Fallback if default colors not supported
            
        curses.init_pair(1, curses.COLOR_CYAN, -1)   # Map
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # NPCs
        curses.init_pair(3, curses.COLOR_YELLOW, -1) # Logs
        curses.init_pair(4, curses.COLOR_RED, -1)    # Danger

    while True:
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        
        # Load Data
        tracker = load_json("data/global_npc_tracker.json")
        # We'd ideally need the map layout too, but for simplicity we show status list
        # For a true visual map, we would import generate_ascii_map
        
        # --- TITLE ---
        stdscr.addstr(0, (w-25)//2, "--- SITE-LOGIC DEV DASHBOARD ---", curses.A_BOLD | curses.A_REVERSE)
        
        # --- LEFT COLUMN: NPC STATUS LIST ---
        stdscr.addstr(2, 2, "ACTIVE PERSONNEL STATUS", curses.color_pair(2) | curses.A_UNDERLINE)
        row = 4
        for npc_id, info in list(tracker.items())[:h-10]:
            name = info.get('name', '???')
            room = info.get('room', '???')
            # In a real impl, we'd pull needs from the NPCManager directly
            # but since this is a separate process, we show what's in the tracker
            status_text = f"[{npc_id}] {name:20} | Loc: {room:15}"
            stdscr.addstr(row, 2, status_text)
            row += 1

        # --- RIGHT COLUMN: SOCIAL FEED ---
        feed_start_x = w // 2
        stdscr.addstr(2, feed_start_x, "LIVE SOCIAL NEGOTIATIONS", curses.color_pair(3) | curses.A_UNDERLINE)
        social_events = load_log("debug_output/facility_sim.log", limit=h-10)
        row = 4
        for event in social_events:
            if row < h - 2:
                # Clean up string for display
                clean_event = event.replace("SOCIAL: ", "")[:(w - feed_start_x - 5)]
                stdscr.addstr(row, feed_start_x, f"» {clean_event}")
                row += 1

        # --- BOTTOM BAR ---
        help_text = "Press 'Q' to exit | Auto-refreshing every 2s"
        stdscr.addstr(h-1, (w-len(help_text))//2, help_text, curses.A_DIM)

        stdscr.refresh()
        
        # Handle Exit
        ch = stdscr.getch()
        if ch == ord('q') or ch == ord('Q'):
            break
            
        time.sleep(2)

if __name__ == "__main__":
    # Ensure folders exist
    os.makedirs("debug_output", exist_ok=True)
    try:
        curses.wrapper(draw_dashboard)
    except KeyboardInterrupt:
        pass

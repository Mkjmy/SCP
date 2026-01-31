import curses

def main(stdscr):
    # Clear screen
    stdscr.clear()

    # Curses input setup
    curses.noecho()    # Don't echo keypresses
    curses.cbreak()    # React to keys instantly, without waiting for Enter
    stdscr.keypad(True) # Enable special keys (like arrow keys)

    stdscr.addstr(0, 0, "Press any key to exit...")
    stdscr.refresh()
    
    curses.flushinp() # Attempt to flush input buffer
    stdscr.getch() # Wait for a key press

    stdscr.addstr(1, 0, "Key pressed. Exiting.")
    stdscr.refresh()
    stdscr.getch() # Wait again so user can see the message before exit

curses.wrapper(main)

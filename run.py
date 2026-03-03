#!/usr/bin/env python3
import sys
import os

# Add 'src' directory to the Python path so we can import from it
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import main_loop
import curses

if __name__ == "__main__":
    try:
        curses.wrapper(main_loop)
    except curses.error as e:
        print(f"\nCurses Error: {e}")
        print("Your terminal might not support curses, or the window is too small.")
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")

I have created a high-level plan to implement the procedural map generation system you requested. This is a major architectural change.

**Proposed Plan for Procedural Map Generation:**

1.  **Modular Room Templates (`room_templates.json`):**
    *   I will create a new `room_templates.json` file. Each room template in this file will define its properties:
        *   A unique ID (e.g., "cell", "hallway_ns", "corner_ne").
        *   A descriptive name and description.
        *   Potential items, details, and NPCs.
        *   A list of its exits (e.g., `["north", "south"]`).

2.  **Map Generation Algorithm (`map_generator.py`):**
    *   I will create a new file, `map_generator.py`, to contain the map creation logic.
    *   This will use a 2D grid system (e.g., `(x, y)` coordinates) to ensure rooms do not overlap.
    *   The algorithm will start with a single room and expand outwards, intelligently selecting and rotating new room templates from `room_templates.json` to ensure that their doors connect logically to adjacent, already-placed rooms.

3.  **Game Initialization Update (`main.py`):**
    *   I will modify the game's startup process in `main.py`. Instead of loading a static `map.json`, the game will now call the new map generator at the beginning of each playthrough to create a unique `game_map` for that session. The old `map.json` will no longer be used for the map layout.

This is a complex feature. **Please confirm if you approve of this plan before I proceed with implementation.**

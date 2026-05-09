# Foundation Site-Logic: Directory Overview

This document provides a complete map of the project's structure, explaining the purpose of each directory and its role in the hyper-detailed simulation.

## 1. Root Directory
- **`run.py`**: The main entry point. Initializes the terminal environment and starts the core engine.
- **`TODO.md`**: Tracks planned features and background system progress.

## 2. Source Code (`src/`)
The source code is strictly modularized to allow for extreme expansion of specific features.

### `core/` (The Heart)
- **`engine.py`**: Contains the `main_loop`. Manages turn progression, coordinates between simulation and story, and handles high-level initialization.

### `entities/` (The Inhabitants)
- **`player/`**: Logic for the player character, including the Master Anatomy and trauma systems.
- **`npc/`**:
    - **`manager.py`**: Handles spawning and high-level NPC coordination.
    - **`simulation.py`**: The AI brain. Handles LOD tiers, social negotiation, and pathfinding.
    - **`persistence.py`**: Manages the global tracker and physical file saving.
    - **`identity_generator.py`**: Generates unique profiles using massive trait pools.
- **`scp/`**:
    - **`scp_manager.py`**: Manages anomalous entities.
    - **`mechanics.py`**: Modular components (Reality, Spatial, etc.) for defining SCP powers.

### `world/` (The Environment)
- **`map/`**: Procedural generation and ASCII visualization logic.
- **`navigation/`**: Manages doors, clearance levels, and room-to-room movement.

### `narrative/` (The Experience)
- **`ui/`**: 
    - **`terminal.py`**: Handles novel-style prose rendering and word-wrapping.
    - **`menu.py`**: Manages nested interaction menus.
- **`story/`**: The JSON-driven event engine for scripted plot points and branching choices.

### `mechanics/` (The Rules)
- **`combat/`**: Stat-based resolution, momentum, and lethal security intervention logic.
- **`life_sim/`**: (Expansion pending) Detailed logic for long-term NPC needs and site economy.

### `utils/`
- **`dev_dashboard.py`**: A real-time monitoring tool for developers to track 1000 NPCs and social events.

## 3. Data & Persistence (`data/`)
- **`identities/`**: Stores 1000+ individual NPC profiles categorized by department (research, security, dclass, etc.).
- **`game_config.json`**: Global settings, map size, and population density.
- **`scp_definitions.json`**: Data-driven definitions for all anomalies.
- **`storyline.json`**: Scripted event sequences and branching narrative data.
- **`global_npc_tracker.json`**: Real-time registry of every NPC's location and status.

## 4. Documentation (`docs/`)
- **`MASTER_PROJECT_GUIDE.md`**: The definitive reference for project logic and contribution rules.
- **`SIMULATION_CORE.md`**: Deep dive into the LOD engine and simulation tiers.
- **`NPC_IDENTITY.md`**: Details on the Master Identity schema and professional hierarchy.

## 5. Development Output (`debug_output/`)
- **`facility_sim.log`**: Detailed record of background simulation events and social negotiations.
- **`ascii_map.txt`**: Static export of the current facility layout.

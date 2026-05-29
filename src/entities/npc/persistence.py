import json
import os
import entities.npc.identity_generator as id_gen

def save_global_tracker(npc_manager, force=False):
    """Updates the central registry of all NPC locations, throttled to prevent lag."""
    npc_manager._turns_since_last_save += 1
    if not force and npc_manager._turns_since_last_save < 10:
        return 

    npc_manager._turns_since_last_save = 0
    tracker_data = {}
    for npc_id, info in npc_manager._npcs.items():
        char = info["character"]
        tracker_data[npc_id] = {
            "name": char.name,
            "role": char.role,
            "room": info["current_room"]
        }
    
    try:
        with open(npc_manager.tracker_file, 'w') as f:
            json.dump(tracker_data, f, indent=2)
    except: pass

def save_all_identities(npc_manager):
    """Writes every NPC's master identity to their specific role folder on disk."""
    for nid, info in npc_manager._npcs.items():
        char = info["character"]
        if hasattr(char, 'master_identity'):
            id_gen.write_identity_to_disk(char.master_identity)
    save_global_tracker(npc_manager, force=True)

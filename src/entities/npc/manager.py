import random
import datetime
import json
import os

from entities.npc.character import Character, generate_character
import entities.npc.identity_generator as id_gen
from entities.npc.persistence import save_global_tracker, save_all_identities
from entities.npc.simulation import process_npc_sim_turn

class NPCManager:
    def __init__(self, map_data):
        self.map_data = map_data
        self._npcs = {} # {npc_id: {"character": Character_obj, "current_room": "room_id", "last_moved_at": datetime_obj}}
        self._next_npc_id = 1
        self.tracker_file = "data/global_npc_tracker.json"
        self._turns_since_last_save = 0

    def spawn_npc(self, role, initial_room_id, department="Special", assigned_scp=None):
        if initial_room_id not in self.map_data:
            return None

        npc_character = generate_character(role)
        npc_id = f"npc_{self._next_npc_id:03d}"
        self._next_npc_id += 1
        
        master_id = id_gen.generate_master_identity(npc_id, role, department, assigned_scp)
        id_gen.save_identity(master_id)
        
        npc_character.id = npc_id
        npc_character.master_identity = master_id

        self._npcs[npc_id] = {
            "character": npc_character,
            "current_room": initial_room_id,
            "last_moved_at": datetime.datetime.now()
        }
        return npc_id

    def save_global_tracker(self, force=False):
        return save_global_tracker(self, force)

    def save_all_identities(self):
        return save_all_identities(self)

    def process_npc_sim_turn(self, all_npcs, player_location, game_map):
        return process_npc_sim_turn(self, player_location, game_map)

    def move_npc(self, npc_id):
        """Moves an NPC to a random adjacent room, respecting door clearance."""
        if npc_id not in self._npcs: return False
        info = self._npcs[npc_id]
        char = info["character"]
        current_room_id = info["current_room"]
        
        room_data = self.map_data.get(current_room_id, {})
        room_exits = room_data.get("exits", {})
        if not room_exits: return False
        
        # Filter exits by clearance
        valid_exits = []
        for direction, exit_info in room_exits.items():
            if char.clearance_level >= exit_info.get("door_level", 0):
                valid_exits.append(exit_info["destination"])
        
        if not valid_exits:
            return False # NPC is locked in
            
        info["current_room"] = random.choice(valid_exits)
        info["last_moved_at"] = datetime.datetime.now()
        return True

    def get_npc_locations_for_display(self):
        display_locations = {}
        for npc_id, npc_info in self._npcs.items():
            room_id = npc_info["current_room"]
            role_char = npc_info["character"].role[0]
            if room_id not in display_locations: display_locations[room_id] = []
            display_locations[room_id].append(role_char)
        return display_locations

    def get_npcs_in_room(self, room_id):
        return [info for info in self._npcs.values() if info["current_room"] == room_id]

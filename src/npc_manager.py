import random
import datetime
import json
import os
from character import Character, generate_character
import identity_generator as id_gen

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
        
        # 1. Generate & Save Master Identity (Hidden)
        master_id = id_gen.generate_master_identity(npc_id, role, department, assigned_scp)
        # identity_generator.save_identity now only prepares path, doesn't write disk
        id_gen.save_identity(master_id)
        
        # 2. Attach to Character object for runtime use
        npc_character.id = npc_id
        npc_character.master_identity = master_id

        self._npcs[npc_id] = {
            "character": npc_character,
            "current_room": initial_room_id,
            "last_moved_at": datetime.datetime.now()
        }
        
        # For initial spawn, we don't save tracker each time
        return npc_id

    def save_global_tracker(self, force=False):
        """Updates the central registry of all NPC locations, throttled to prevent lag."""
        self._turns_since_last_save += 1
        if not force and self._turns_since_last_save < 10:
            return # Skip disk write

        self._turns_since_last_save = 0
        tracker_data = {}
        for npc_id, info in self._npcs.items():
            char = info["character"]
            tracker_data[npc_id] = {
                "name": char.name,
                "role": char.role,
                "room": info["current_room"]
            }
        
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(tracker_data, f, indent=2)
        except: pass

    def move_npc(self, npc_id):
        """Moves an NPC to a random adjacent room."""
        if npc_id not in self._npcs:
            return False

        npc_info = self._npcs[npc_id]
        current_room_id = npc_info["current_room"]

        room_exits = self.map_data.get(current_room_id, {}).get("exits", {})
        if not room_exits:
            return False

        # Choose a random exit (will be upgraded to pathfinding later)
        dest_dict = random.choice(list(room_exits.values()))
        destination_room_id = dest_dict["destination"]
        
        npc_info["current_room"] = destination_room_id
        npc_info["last_moved_at"] = datetime.datetime.now()
        
        self.save_global_tracker()
        return True

    def find_path(self, start_room, target_room):
        """Simple BFS to find the next room towards a target."""
        if start_room == target_room: return None
        queue = [(start_room, [])]
        visited = {start_room}
        
        while queue:
            current, path = queue.pop(0)
            exits = self.map_data.get(current, {}).get("exits", {})
            for direction, info in exits.items():
                dest = info["destination"]
                if dest == target_room:
                    return path + [dest]
                if dest not in visited:
                    visited.add(dest)
                    queue.append((dest, path + [dest]))
        return None

    def process_npc_sim_turn(self, all_npcs, player_location, game_map):
        """Processes simulation for 1000+ NPCs using Dynamic Detail Slotting (50 slots)."""
        log_entries = []
        MAX_DETAIL_SLOTS = 50
        
        # 0. SPATIAL & DISTANCE INDEXING
        room_populations = {}
        for nid, ninfo in self._npcs.items():
            rid = ninfo["current_room"]
            if rid not in room_populations: room_populations[rid] = []
            room_populations[rid].append(nid)

        # BFS from player to all rooms to get distances
        distances = {player_location: 0}
        q = [player_location]
        while q:
            curr = q.pop(0)
            exits = self.map_data.get(curr, {}).get("exits", {})
            for direction, info in exits.items():
                dest = info["destination"]
                if dest not in distances:
                    distances[dest] = distances[curr] + 1
                    q.append(dest)

        # 1. ASSIGN SLOTS BY PRIORITY
        # Priority score: Focus (0) > Proximity (Distance) > Random small noise
        npc_priorities = []
        for nid, info in self._npcs.items():
            dist = distances.get(info["current_room"], 99)
            focus_bonus = 0 if info["character"].is_focused else 100
            # Higher weight on focused and nearby characters
            priority_score = focus_bonus + dist + random.random()
            npc_priorities.append((priority_score, nid))
        
        npc_priorities.sort() # Lowest score (highest priority) first
        
        detail_nids = set()
        for i in range(min(MAX_DETAIL_SLOTS, len(npc_priorities))):
            detail_nids.add(npc_priorities[i][1])

        # 2. SIMULATION LOOP
        social_buffer = {}
        
        for npc_id, info in self._npcs.items():
            char = info["character"]
            rid = info["current_room"]
            
            # Update Focus Timer
            if char.is_focused:
                char.focus_timer = max(0, char.focus_timer - 1)
                if char.focus_timer == 0: char.is_focused = False

            # Needs always update (light math)
            char.needs_tick()
            
            # Determine processing level
            is_detail = npc_id in detail_nids
            
            if not is_detail:
                # Tier 3 Logic: Deterministic Jump
                if random.random() < 0.05: 
                    self.move_npc(npc_id)
                continue # Skip social/complex logic for abstract entities

            # --- TIER 1 LOGIC (Social & Complex Tasks) ---
            if rid not in social_buffer: social_buffer[rid] = []
            
            # A. Broadcast Phase (Social)
            if char.role == "Scientist" and not char.current_task and random.random() < 0.2:
                req = {"from": npc_id, "type": "NEED_ESCORT", "msg": "Security required for testing."}
                social_buffer[rid].append(req)
                if distances.get(rid, 99) <= 1:
                    log_entries.append(f"SOCIAL: {char.name} broadcasted: '{req['msg']}' in {rid}")

            # B. Negotiation & Cascading Promotion
            if char.role == "Guard" and not char.current_task and rid in social_buffer:
                for req in social_buffer[rid]:
                    if req["type"] == "NEED_ESCORT":
                        # CASCADING PROMOTION: Find a D-Class in the room. 
                        # Even if the D-Class is abstract, we promote them because a Detail Guard is interacting.
                        target_d_id = None
                        for d_id in room_populations.get(rid, []):
                            d_char = self._npcs[d_id]["character"]
                            if d_char.role == "D-Class" and not d_char.current_task:
                                target_d_id = d_id
                                # Borrow a detail slot for this interaction
                                detail_nids.add(d_id) 
                                break
                        
                        if target_d_id:
                            # Full logic negotiation
                            iq_bonus = (char.master_identity["psychological_profile"]["iq"] - 100) / 100
                            loyalty = char.master_identity["social_and_secrets"]["loyalty_status"] == "LOYAL"
                            cooperation_chance = 0.5 + iq_bonus + (0.2 if loyalty else -0.3)
                            
                            if random.random() < cooperation_chance:
                                requester = self._npcs[req["from"]]["character"]
                                char.current_task = {"type": "ESCORT", "target": target_d_id, "dest": rid}
                                self._npcs[target_d_id]["character"].current_task = {"type": "BEING_ESCORTED"}
                                requester.current_task = {"type": "EXPERIMENT"}
                                if distances.get(rid, 99) <= 1:
                                    log_entries.append(f"SOCIAL: {char.name} accepted request. Now escorting {self._npcs[target_d_id]['character'].name}")
                                break

            # C. Task Execution
            action_taken = "Idling"
            if char.current_task:
                task = char.current_task
                if task["type"] == "ESCORT":
                    target_id = task["target"]; dest_room = task["dest"]
                    
                    # Special check: If target is player, use player_location
                    if target_id == "player":
                        target_room = player_location
                    else:
                        subject_info = self._npcs.get(target_id)
                        target_room = subject_info["current_room"] if subject_info else None
                    
                    if not target_room:
                        char.current_task = None
                        continue

                    # Use full pathfinding for detail entities
                    path = self.find_path(rid, target_room if rid != target_room else dest_room)
                    if path:
                        info["current_room"] = path[0]
                        # If target is an NPC, move them too
                        if target_id != "player" and rid == target_room:
                            self._npcs[target_id]["current_room"] = path[0]
                        action_taken = "Performing Escort"
                    else:
                        action_taken = "Securing the perimeter"
                        char.current_task = None
                elif task["type"] == "EXPERIMENT":
                    action_taken = "Monitoring experiment"
                    if random.random() < 0.2: 
                        action_taken = "Experiment finalized"
                        char.current_task = None
            else:
                # Routine Needs
                if char.needs["hunger"] > 60:
                    self.move_npc(npc_id)
                    action_taken = "Heading to Cafeteria"
                elif random.random() < 0.1:
                    self.move_npc(npc_id)
                    action_taken = "Patrolling sector"

            char.current_behavior = f"{action_taken} ({char.get_sensation()})"
            # Log only if physically near player or explicitly focused
            if distances.get(rid, 99) <= 1 or char.is_focused:
                log_entries.append(f"[{npc_id}] {char.name}: {char.current_behavior} at {rid}")

        self.save_global_tracker()
        return log_entries

    def get_npc_locations_for_display(self):
        """
        Returns a dictionary suitable for map_visualizer.py, mapping room_id to list of NPC role chars.
        """
        display_locations = {}
        for npc_id, npc_info in self._npcs.items():
            room_id = npc_info["current_room"]
            role_char = npc_info["character"].role[0]
            if room_id not in display_locations: display_locations[room_id] = []
            display_locations[room_id].append(role_char)
        return display_locations

    def get_npcs_in_room(self, room_id):
        return [info for info in self._npcs.values() if info["current_room"] == room_id]

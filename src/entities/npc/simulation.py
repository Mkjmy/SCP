import random

def find_path(map_data, start_room, target_room):
    """Simple BFS to find the next room towards a target."""
    if start_room == target_room: return None
    queue = [(start_room, [])]
    visited = {start_room}
    
    while queue:
        current, path = queue.pop(0)
        exits = map_data.get(current, {}).get("exits", {})
        for direction, info in exits.items():
            dest = info["destination"]
            if dest == target_room:
                return path + [dest]
            if dest not in visited:
                visited.add(dest)
                queue.append((dest, path + [dest]))
    return None

def process_npc_sim_turn(npc_manager, player_location, game_map):
    """Processes simulation for 1000+ NPCs using Dynamic Detail Slotting (50 slots)."""
    log_entries = []
    MAX_DETAIL_SLOTS = 50
    
    # 0. SPATIAL & DISTANCE INDEXING
    room_populations = {}
    for nid, ninfo in npc_manager._npcs.items():
        rid = ninfo["current_room"]
        if rid not in room_populations: room_populations[rid] = []
        room_populations[rid].append(nid)

    distances = {player_location: 0}
    q = [player_location]
    while q:
        curr = q.pop(0)
        exits = game_map.get(curr, {}).get("exits", {})
        for info in exits.values():
            d = info["destination"]
            if d not in distances:
                distances[d] = distances[curr] + 1
                q.append(d)

    # 1. ASSIGN SLOTS
    npc_priorities = []
    for nid, info in npc_manager._npcs.items():
        dist = distances.get(info["current_room"], 99)
        focus_bonus = 0 if info["character"].is_focused else 100
        priority_score = focus_bonus + dist + random.random()
        npc_priorities.append((priority_score, nid))
    
    npc_priorities.sort()
    detail_nids = {p[1] for p in npc_priorities[:MAX_DETAIL_SLOTS]}

    # 2. LOOP
    social_buffer = {}
    for npc_id, info in npc_manager._npcs.items():
        char = info["character"]
        rid = info["current_room"]
        
        if char.is_focused:
            char.focus_timer = max(0, char.focus_timer - 1)
            if char.focus_timer == 0: char.is_focused = False

        char.needs_tick()
        is_detail = npc_id in detail_nids
        
        if not is_detail:
            if random.random() < 0.05: npc_manager.move_npc(npc_id)
            continue

        # Detail Logic
        if rid not in social_buffer: social_buffer[rid] = []
        
        # Broadcast (Scientist)
        if char.role == "Scientist" and not char.current_task and random.random() < 0.2:
            req = {"from": npc_id, "type": "NEED_ESCORT"}
            social_buffer[rid].append(req)

        # Negotiation
        if char.role == "Guard" and not char.current_task and rid in social_buffer:
            for req in social_buffer[rid]:
                if req["type"] == "NEED_ESCORT":
                    target_d_id = next((d for d in room_populations.get(rid, []) if npc_manager._npcs[d]["character"].role == "D-Class" and not npc_manager._npcs[d]["character"].current_task), None)
                    if target_d_id:
                        detail_nids.add(target_d_id)
                        char.current_task = {"type": "ESCORT", "target": target_d_id, "dest": rid}
                        npc_manager._npcs[target_d_id]["character"].current_task = {"type": "BEING_ESCORTED"}
                        npc_manager._npcs[req["from"]]["character"].current_task = {"type": "EXPERIMENT"}
                        break

        # Action Phase
        if char.current_task:
            task = char.current_task
            if task["type"] == "ESCORT":
                target_id = task["target"]; dest_room = task["dest"]; target_room = player_location if target_id == "player" else npc_manager._npcs[target_id]["current_room"]
                path = find_path(game_map, rid, target_room if rid != target_room else dest_room)
                if path:
                    info["current_room"] = path[0]
                    if target_id != "player" and rid == target_room: npc_manager._npcs[target_id]["current_room"] = path[0]
                else: char.current_task = None
        else:
            if char.needs["hunger"] > 60: npc_manager.move_npc(npc_id)
            elif random.random() < 0.1: npc_manager.move_npc(npc_id)

        if distances.get(rid, 99) <= 1 or char.is_focused:
            log_entries.append(f"[{npc_id}] {char.name}: {char.current_behavior} at {rid}")

    return log_entries

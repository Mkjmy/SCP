# test_door_system.py

from map_visualizer import load_map_data
from door_manager import DoorManager

def run_door_tests():
    print("--- Running Door Management System Tests ---")

    map_data = load_map_data()
    if not map_data:
        print("Error: Could not load map data for door tests.")
        return

    door_manager = DoorManager(map_data)

    test_cases = [
        # (clearance_level, current_room_id, direction, expected_access, expected_destination, description)
        (0, "cell", "east", False, "hallway_a", "Player L0, Cell East (L1)"),
        (1, "cell", "east", True, "hallway_a", "Player L1, Cell East (L1)"),
        (2, "cell", "east", True, "hallway_a", "Player L2, Cell East (L1)"),

        (0, "hallway_a", "west", False, "cell", "Player L0, Hallway A West (L1) - Should fail for 0, succeed for 1+"), # NOTE: This door is L1 as well.
        (1, "hallway_a", "west", True, "cell", "Player L1, Hallway A West (L1)"),
        
        (0, "hallway_a", "east", True, "hallway_b", "Player L0, Hallway A East (L0)"),
        
        (1, "hallway_b", "north", False, "control_room", "Player L1, Hallway B North (L2)"),
        (2, "hallway_b", "north", True, "control_room", "Player L2, Hallway B North (L2)"),
        (3, "hallway_b", "north", True, "control_room", "Player L3, Hallway B North (L2)"),

        (0, "storage_room", "west", True, "hallway_b", "Player L0, Storage Room West (L0)"),
        
        (0, "cell", "north", False, None, "Player L0, Cell North (Non-existent)"), # Non-existent exit
        (1, "cell", "north", False, None, "Player L1, Cell North (Non-existent)"), # Non-existent exit
    ]

    for cl, room, direction, expected_access, expected_dest, desc in test_cases:
        actual_access = door_manager.check_access(cl, room, direction)
        actual_dest = door_manager.get_destination(room, direction)
        door_level = door_manager.get_door_level(room, direction)

        status_access = "PASS" if actual_access == expected_access else "FAIL"
        status_dest = "PASS" if actual_dest == expected_dest else "FAIL"

        print(f"\nTest: {desc}")
        print(f"  Entity CL: {cl}, From Room: {room}, Direction: {direction}, Door Level: {door_level if door_level is not None else 'N/A'}")
        print(f"  Access: Expected={expected_access}, Actual={actual_access} [{status_access}]")
        print(f"  Destination: Expected={expected_dest}, Actual={actual_dest} [{status_dest}]")
        
        if status_access == "FAIL" or status_dest == "FAIL":
            print(f"  !!! TEST FAILED: {desc}")

    print("\n--- Door Management System Tests Complete ---")

if __name__ == "__main__":
    run_door_tests()

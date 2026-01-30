import random

# --- Constants for Body Part System ---
BODY_PARTS = ['head', 'torso', 'left_arm', 'right_arm', 'left_leg', 'right_leg']
DAMAGE_STATES = {
    'uninjured': 0,
    'minor_injury': 1,
    'major_injury': 2,
    'severe_injury': 3 # e.g., 'broken'
}

# Debuffs based on damage state severity
# This is a base value, actual debuff might depend on the attribute/action
DEBUFF_VALUES = {
    'minor_injury': 1,
    'major_injury': 2,
    'severe_injury': 3
}

class Player:
    def __init__(self, start_location):
        self.location = start_location
        self.inventory = [] # This is now the backpack
        self.role = "D-Class"
        self.name = "D-9341"
        self.clearance_level = 0
        self.level = 1 # Added for debug display
        
        self.left_hand = None
        self.right_hand = None

        self.max_health = 100
        self.health = self.max_health
        self.max_stamina = 100
        self.stamina = self.max_stamina

        self.max_morale = 100
        self.morale = self.max_morale

        self.attributes = {
            'strength': random.randint(3, 6),
            'dexterity': random.randint(3, 6),
            'intelligence': random.randint(3, 6)
        }
        
        # Body Part Damage System
        self.body_parts = {part: 'uninjured' for part in BODY_PARTS}

        # Skill & Knowledge System
        self.knowledge = set()

    def get_description(self, debug=False):
        """Returns a string with the player's details, including stats."""
        details = [
            f"  Name: {self.name} ({self.role})",
            f"  Clearance Level: {self.clearance_level}",
            f"  Health: {self.health}/{self.max_health}",
            f"  Stamina: {self.stamina}/{self.max_stamina}",
            f"  Morale: {self.morale}/{self.max_morale}",
            f"  Attributes:",
            f"    Strength: {self.attributes['strength']}",
            f"    Dexterity: {self.attributes['dexterity']}",
            f"    Intelligence: {self.attributes['intelligence']}",
            f"\n  Hands:",
            f"    Left: {self.left_hand if self.left_hand else 'Empty'}",
            f"    Right: {self.right_hand if self.right_hand else 'Empty'}",
            f"\n  Backpack: {self.inventory if self.inventory else 'Empty'}"
        ]
        
        if debug:
            details.insert(1, f"  Location ID: {self.location}")
            details.insert(2, f"  Level: {self.level}")

        injury_status = self.get_injury_status()
        if injury_status:
            details.append("\n  Injuries:")
            details.extend([f"    - {status}" for status in injury_status])

        if self.knowledge:
            details.append("\n  Knowns:")
            details.extend([f"    - {k.replace('_', ' ').title()}" for k in self.knowledge])

        return "\n".join(details)

    def equip_item(self, item_name, hand):
        """Moves an item from inventory to a hand."""
        if item_name not in self.inventory:
            return f"You don't have '{item_name}' in your backpack."
        
        if hand == 'left':
            if self.left_hand is not None:
                return "Your left hand is already full."
            self.left_hand = item_name
            self.inventory.remove(item_name)
            return f"You equipped '{item_name}' in your left hand."
        elif hand == 'right':
            if self.right_hand is not None:
                return "Your right hand is already full."
            self.right_hand = item_name
            self.inventory.remove(item_name)
            return f"You equipped '{item_name}' in your right hand."
        else:
            return "You can only equip items in your 'left' or 'right' hand."

    def unequip_item(self, hand):
        """Moves an item from a hand to inventory."""
        if hand == 'left':
            if self.left_hand is None:
                return "Your left hand is empty."
            item_name = self.left_hand
            self.inventory.append(item_name)
            self.left_hand = None
            return f"You moved '{item_name}' to your backpack."
        elif hand == 'right':
            if self.right_hand is None:
                return "Your right hand is empty."
            item_name = self.right_hand
            self.inventory.append(item_name)
            self.right_hand = None
            return f"You moved '{item_name}' to your backpack."
        else:
            return "You can only unequip from your 'left' or 'right' hand."
    
    def change_morale(self, amount):
        """Adjusts player morale within bounds."""
        old_morale = self.morale
        self.morale = max(0, min(self.max_morale, self.morale + amount))
        if self.morale > old_morale:
            return f"Your morale improved by {self.morale - old_morale}!"
        elif self.morale < old_morale:
            return f"Your morale dropped by {old_morale - self.morale}!"
        return "" # No change

    def get_morale_effect(self, stat_type):
        """Calculates a morale-based modifier for a given stat or action type."""
        morale_threshold_low = 30
        morale_threshold_mid = 70
        
        if self.morale < morale_threshold_low:
            return -2 # Significant debuff
        elif self.morale < morale_threshold_mid:
            return -1 # Minor debuff
        elif self.morale > morale_threshold_mid:
            return 1 # Minor buff
        return 0 # No significant effect

    def learn_knowledge(self, knowledge_id):
        """Adds new knowledge to the player's repertoire."""
        if knowledge_id not in self.knowledge:
            self.knowledge.add(knowledge_id)
            return f"You learned: {knowledge_id.replace('_', ' ').title()}!"
        return f"You already know: {knowledge_id.replace('_', ' ').title()}."

    def has_knowledge(self, knowledge_id):
        """Checks if the player possesses specific knowledge."""
        return knowledge_id in self.knowledge

    def apply_injury(self, part, severity='minor_injury'):
        """Applies or worsens an injury to a specific body part."""
        if part not in self.body_parts:
            return f"Invalid body part: {part}"

        current_severity_level = DAMAGE_STATES[self.body_parts[part]]
        new_severity_level = DAMAGE_STATES[severity]

        # Only worsen the injury
        if new_severity_level > current_severity_level:
            for state, level in DAMAGE_STATES.items():
                if level == new_severity_level:
                    self.body_parts[part] = state
                    return f"Your {part} is now {state.replace('_', ' ')}."
        return f"Your {part} is already {self.body_parts[part].replace('_', ' ')} or worse."

    def get_debuff(self, attribute=None, action_type=None):
        """Calculates total debuff from injuries for an attribute or action."""
        total_debuff = 0
        for part, status in self.body_parts.items():
            if status == 'uninjured':
                continue
            
            severity_value = DEBUFF_VALUES.get(status, 0)
            
            if attribute:
                if attribute == 'strength' and ('arm' in part or 'torso' in part):
                    total_debuff += severity_value
                elif attribute == 'dexterity' and ('arm' in part or 'leg' in part):
                    total_debuff += severity_value
                elif attribute == 'intelligence' and 'head' in part:
                    total_debuff += severity_value
            
            if action_type:
                if action_type == 'run' and 'leg' in part:
                    total_debuff += severity_value * 2 # Legs heavily impact running
                elif action_type == 'attack' and 'arm' in part:
                    total_debuff += severity_value * 2 # Arms heavily impact attacking
        
        return total_debuff

    def get_injury_status(self):
        """Returns a list of strings describing current injuries."""
        injuries = []
        for part, status in self.body_parts.items():
            if status != 'uninjured':
                injuries.append(f"{part.replace('_', ' ').title()}: {status.replace('_', ' ').title()}")
        return injuries

    def is_part_severely_injured(self, part):
        """Checks if a specific body part has a severe injury."""
        return DAMAGE_STATES.get(self.body_parts.get(part, 'uninjured')) >= DAMAGE_STATES['severe_injury']

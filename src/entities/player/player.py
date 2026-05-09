import random

# --- Master Anatomy System ---
ANATOMY = {
    "Nervous/Skeletal": ['brain', 'skull', 'spine', 'ribs'],
    "Internal Organs": ['heart', 'lungs', 'stomach', 'liver', 'kidneys'],
    "Upper Limbs": ['left_shoulder', 'left_arm', 'left_hand', 'right_shoulder', 'right_arm', 'right_hand'],
    "Lower Limbs": ['left_hip', 'left_leg', 'left_foot', 'right_hip', 'right_leg', 'right_foot']
}

# Flattened list for quick selection
BODY_PARTS = [part for category in ANATOMY.values() for part in category]

DAMAGE_STATES = {
    'intact': 0,
    'bruised': 1,
    'bleeding': 2,
    'fractured': 3,
    'ruptured': 4,
    'severed': 5 # Or 'failed' for organs
}

# Simplified debuff mapping for the complex system
DEBUFF_VALUES = {
    'bruised': 0,
    'bleeding': 1,
    'fractured': 2,
    'ruptured': 4,
    'severed': 6
}

class Player:
    def __init__(self, start_location, name="D-9341", role="D-Class",
                 clearance_level=0, max_health=100, health=None,
                 max_stamina=100, stamina=None, max_morale=100, morale=None,
                 max_sanity=100, sanity=None,
                 attributes=None, knowledge=None, origin="Unknown", personality="Determined", specialty="Survival"):
        
        self.location = start_location
        self.inventory = [] 
        self.role = role
        self.name = name
        self.clearance_level = clearance_level
        self.level = 1
        
        self.left_hand = None
        self.right_hand = None

        self.max_health = max_health
        self.health = health if health is not None else self.max_health
        self.max_stamina = max_stamina
        self.stamina = stamina if stamina is not None else self.max_stamina

        self.max_morale = max_morale
        self.morale = morale if morale is not None else self.max_morale

        self.max_sanity = max_sanity
        self.sanity = sanity if sanity is not None else self.max_sanity

        self.attributes = attributes if attributes is not None else {
            'strength': random.randint(3, 6),
            'dexterity': random.randint(3, 6),
            'intelligence': random.randint(3, 6)
        }
        
        # --- Expanded Body Part System ---
        self.body_parts = {}
        for category in ANATOMY.values():
            for part in category:
                self.body_parts[part] = 'intact'

        # Skill & Knowledge System
        self.knowledge = set(knowledge) if knowledge is not None else set()
        self.identified_npc_ids = set()

        # --- Primitive Engine Concepts ---
        self.mind_states = set() 
        self.active_rules = {} 
        self.perception = {
            "attention": None,
            "awareness": {},
            "memory": {},
            "memory_persistence": {}
        }

        self.origin = origin
        self.personality = personality
        self.specialty = specialty
        self.identified_npc_ids = set()
        
        # --- Combat State ---
        self.combat_momentum = 0 # Positive = Win streak, Negative = Loss streak
        self.total_kills = 0
                f"  Name: {self.name} ({self.role})",
                f"\n  Hands:",
                f"    Left: {self.left_hand if self.left_hand else 'Empty'}",
                f"    Right: {self.right_hand if self.right_hand else 'Empty'}",
                f"\n  Backpack: {self.inventory if self.inventory else 'Empty'}"
            ]
        else:
            details = [
                f"  Name: {self.name} ({self.role})",
                f"  Attributes: {self.attributes}",
                f"  Anatomy Status: {self.get_injury_status()}"
            ]

        injury_status = self.get_injury_status()
        if injury_status:
            details.append("\n  Physical Trauma:")
            details.extend([f"    - {status}" for status in injury_status])

        return "\n".join(details)

    def apply_injury(self, part, severity='bruised'):
        """Applies damage to a specific anatomical part or organ."""
        if part not in self.body_parts:
            return f"Invalid anatomical target: {part}"

        current_level = DAMAGE_STATES[self.body_parts[part]]
        new_level = DAMAGE_STATES[severity]

        if new_level > current_level:
            for state, level in DAMAGE_STATES.items():
                if level == new_level:
                    self.body_parts[part] = state
                    return f"CRITICAL: Your {part.replace('_', ' ')} is now {state.upper()}."
        return f"Your {part.replace('_', ' ')} is already in {self.body_parts[part]} condition."

    def is_incapacitated(self):
        """Checks for systemic failure or critical organ trauma."""
        # 1. Systemic failure
        if self.health < 10:
            return True, "Your circulatory system is collapsing. You lack the strength to even crawl."
        
        # 2. Critical Organ Failure
        if self.body_parts['brain'] in ['ruptured', 'severed']:
            return True, "Neural activity is erratic. You have lost all motor control."
        if self.body_parts['heart'] in ['ruptured', 'severed']:
            return True, "Your heart has stopped. The world is fading fast."
        if self.body_parts['spine'] in ['fractured', 'ruptured', 'severed']:
            return True, "Your nervous system is severed at the spine. You are paralyzed."
            
        # 3. Accumulated Trauma
        major_trauma = 0
        for status in self.body_parts.values():
            if DAMAGE_STATES[status] >= 3: # Fractured or worse
                major_trauma += 1
        
        if major_trauma >= 5:
            return True, "The sheer scale of your internal injuries has forced your body into shock."

        return False, ""

    def get_debuff(self, attribute=None, action_type=None):
        """Calculates total debuff from complex injuries."""
        total = 0
        for part, status in self.body_parts.items():
            val = DEBUFF_VALUES.get(status, 0)
            if attribute == 'strength' and ('arm' in part or 'shoulder' in part or 'spine' in part):
                total += val
            if attribute == 'dexterity' and ('hand' in part or 'leg' in part or 'foot' in part):
                total += val
            if action_type == 'run' and ('leg' in part or 'foot' in part or 'lungs' in part):
                total += val * 2
            if action_type == 'attack' and ('arm' in part or 'hand' in part or 'shoulder' in part):
                total += val * 2
        return total

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

    def change_sanity(self, amount):
        """Adjusts player sanity within bounds."""
        old_sanity = self.sanity
        self.sanity = max(0, min(self.max_sanity, self.sanity + amount))
        if self.sanity > old_sanity:
            return f"Your sanity improved by {self.sanity - old_sanity}!"
        elif self.sanity < old_sanity:
            return f"Your sanity dropped by {old_sanity - self.sanity}!"
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
        """Checks if a specific body part has a severe injury (fractured or worse)."""
        # Threshold: Fractured (level 3) is considered severe for basic action blocking
        current_status = self.body_parts.get(part, 'intact')
        return DAMAGE_STATES.get(current_status, 0) >= DAMAGE_STATES['fractured']

    def reduce_attribute(self, attribute, amount):
        """Reduces a specific base attribute. Useful for penalties after losing fights."""
        if attribute in self.attributes:
            old_val = self.attributes[attribute]
            self.attributes[attribute] = max(1, self.attributes[attribute] - amount)
            if self.attributes[attribute] < old_val:
                return f"Your {attribute.capitalize()} has decreased to {self.attributes[attribute]} due to your injuries."
        return ""

    def is_incapacitated(self):
        """Checks if the player is too mangled to act."""
        if self.health < 15:
            return True, "Your body is failing. Every movement brings a wave of blinding pain. You can't do this."
        
        severe_count = 0
        for status in self.body_parts.values():
            if status in ['major_injury', 'severe_injury']:
                severe_count += 1
        
        if severe_count >= 3:
            return True, "Your injuries are too extensive. Your limbs won't obey your commands. You are completely broken."
            
        return False, ""

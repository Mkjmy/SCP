import random

# Data pools for character generation
FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Maria", "Olga", "Kenji"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Tanaka", "Ivanov"]
ORIGINS = ["USA", "Russia", "UK", "Germany", "Japan", "Canada", "Australia", "Brazil", "China", "India"]
PERSONALITIES = ["Stoic", "Nervous", "Aggressive", "By-the-book", "Calm", "Jumpy", "Pragmatic", "Careless"]
SCIENTIST_SPECIALTIES = ["Memetics", "Anomalous Biology", "Temporal Physics", "Cognitohazards", "Thaumatology", "Robotics"]
GUARD_SPECIALTIES = ["Containment Specialist", "Tactical Response", "Perimeter Security", "MTF Operative", "Heavy Ordinance"]

# Dialogue lines based on personality
DIALOGUE_LINES = {
    "Stoic": ["...", "Go on.", "Is that all?"],
    "Nervous": ["Wh-what do you want?", "Please, don't hurt me!", "I didn't see anything, I swear!"],
    "Aggressive": ["State your purpose!", "Get out of my sight, maggot!", "One more step and I'll shoot."],
    "By-the-book": ["Do you have authorization for this area?", "I'm reporting this.", "Everything must be documented."],
    "Calm": ["How can I help you?", "Let's all just remain calm.", "There is a rational explanation for everything."],
    "Jumpy": ["Did you hear that?!", "What was that noise?", "I have a bad feeling about this."],
    "Pragmatic": ["Let's focus on the task at hand.", "What's the most logical course of action?", "Wasting time won't help us."],
    "Careless": ["Eh, whatever.", "I'm supposed to be on break.", "Not my problem."]
}


class Character:
    """Represents a single character in the game, player or NPC."""
    def __init__(self, role, name, origin, personality, specialty, clearance_level, health, stamina, attributes):
        self.role = role
        self.name = name
        self.origin = origin
        self.personality = personality
        self.specialty = specialty
        self.clearance_level = clearance_level
        self.max_health = health
        self.health = health
        self.max_stamina = stamina
        self.stamina = stamina
        self.attributes = attributes
        self.level = 1 # Added for debug display

    def get_description(self, debug=False):
        """Returns a string with the character's details, including stats."""
        details = [
            f"  Name: {self.name} ({self.role})",
            f"  Clearance Level: {self.clearance_level}",
            f"  Health: {self.health}/{self.max_health}",
            f"  Stamina: {self.stamina}/{self.max_stamina}",
            f"  Attributes:",
            f"    Strength: {self.attributes['strength']}",
            f"    Dexterity: {self.attributes['dexterity']}",
            f"    Intelligence: {self.attributes['intelligence']}",
            f"  Personality: {self.personality}",
        ]
        if debug:
            details.insert(1, f"  Level: {self.level}")
            details.extend([
                f"  Origin: {self.origin}",
                f"  Specialty: {self.specialty}",
            ])
        return "\n".join(details)
        
    def get_dialogue(self):
        """Returns a random dialogue line based on personality."""
        return random.choice(DIALOGUE_LINES.get(self.personality, ["..." ]))

def generate_character(role):
    """Generates a random character object of a given role."""
    role_str = role.lower()
    name = f"Dr. {random.choice(LAST_NAMES)}" if role_str == 'scientist' else f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    origin = random.choice(ORIGINS)
    personality = random.choice(PERSONALITIES)
    
    # Base stats
    health = random.randint(80, 120)
    stamina = random.randint(80, 120)
    attributes = {
        'strength': random.randint(4, 7),
        'dexterity': random.randint(4, 7),
        'intelligence': random.randint(4, 7)
    }

    if role_str == 'scientist':
        specialty = random.choice(SCIENTIST_SPECIALTIES)
        clearance_level = random.choice([2, 3])
        attributes['intelligence'] += random.randint(2, 4) # Scientists are smarter
        health = random.randint(70, 100) # Slightly less healthy
        stamina = random.randint(70, 100) # Slightly less stamina
    elif role_str == 'guard':
        specialty = random.choice(GUARD_SPECIALTIES)
        clearance_level = random.choice([1, 2])
        attributes['strength'] += random.randint(2, 4) # Guards are stronger
        attributes['dexterity'] += random.randint(1, 3) # Guards are also quick
        health = random.randint(90, 130) # More healthy
        stamina = random.randint(90, 130) # More stamina
    else: # D-Class
        specialty = "Expendable"
        clearance_level = 0
        attributes = { # D-Class have generally lower stats
            'strength': random.randint(3, 5),
            'dexterity': random.randint(3, 5),
            'intelligence': random.randint(3, 5)
        }
        health = random.randint(70, 90)
        stamina = random.randint(70, 90)

    return Character(role.capitalize(), name, origin, personality, specialty, clearance_level, health, stamina, attributes)
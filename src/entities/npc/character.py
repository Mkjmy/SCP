import random

# Data pools for character generation
FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Maria", "Olga", "Kenji"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Tanaka", "Ivanov"]
ORIGINS = ["USA", "Russia", "UK", "Germany", "Japan", "Canada", "Australia", "Brazil", "China", "India"]
PERSONALITIES = ["Stoic", "Nervous", "Aggressive", "By-the-book", "Calm", "Jumpy", "Pragmatic", "Careless", "Broken", "Manic", "Paranoid"]
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
    "Careless": ["Eh, whatever.", "I'm supposed to be on break.", "Not my problem."],
    "Broken": ["The walls are screaming. Can't you hear them?", "I just want to go home. Why won't they let me go home?", "Everything is red. Why is it all red?"],
    "Manic": ["Hahaha! Did you see the shadows dance?!", "The Doctor is coming, the Doctor is coming! Free surgery for everyone!", "I can see through time! It's all a loop!"],
    "Paranoid": ["They're in the vents. Don't look up.", "You're one of them, aren't you? Wearing a human face?", "The cameras... they're blinking in Morse code."]
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
        self.current_behavior = self.get_behavioral_description()
        
        # --- Sim Needs (Hidden) ---
        self.needs = {
            "hunger": random.randint(0, 30),
            "energy": random.randint(70, 100),
            "bladder": random.randint(0, 20),
            "stress": 0
        }
        
        # --- Task System ---
        self.current_task = None # { "type": "ESCORT", "target": "npc_id", "dest": "room_id" }
        self.is_on_critical_duty = False 
        
        # --- Focus / LOD System ---
        self.is_focused = False
        self.focus_timer = 0

    def needs_tick(self, current_room_tags=None):
        """Updates needs for a single turn, providing benefits for functional rooms."""
        tags = current_room_tags or []
        
        # 1. Recovery Logic (Functional Rooms)
        if "cafeteria" in tags:
            self.needs["hunger"] = max(0, self.needs["hunger"] - 20)
        else:
            self.needs["hunger"] = min(100, self.needs["hunger"] + 1)

        if "dormitory" in tags or "break_room" in tags:
            self.needs["energy"] = min(100, self.needs["energy"] + 15)
        else:
            self.needs["energy"] = max(0, self.needs["energy"] - 1)

        if "restroom" in tags:
            self.needs["bladder"] = max(0, self.needs["bladder"] - 40)
        else:
            self.needs["bladder"] = min(100, self.needs["bladder"] + 2)
        
        if "medibay" in tags:
            self.health = min(self.max_health, self.health + 10)
            self.needs["stress"] = max(0, self.needs["stress"] - 5)

        # 2. Stress & Stability
        stability = getattr(self, 'master_identity', {}).get('psychological_profile', {}).get('mental_stability', 0.5)
        if stability < 0.5 or "hazard" in tags:
            self.needs["stress"] = min(100, self.needs["stress"] + 2)
        else:
            self.needs["stress"] = max(0, self.needs["stress"] - 1)

    def get_effective_attributes(self):
        """Returns attributes modified by physical/mental state (Butterfly Effect)."""
        eff = self.attributes.copy()
        
        # Hunger Penalty: Famished NPCs are weaker and slower
        if self.needs["hunger"] > 80:
            eff['strength'] = max(1, eff['strength'] - 2)
            eff['dexterity'] = max(1, eff['dexterity'] - 1)
        
        # Energy Penalty: Exhausted NPCs lose focus and reaction time
        if self.needs["energy"] < 20:
            eff['intelligence'] = max(1, eff['intelligence'] - 2)
            eff['dexterity'] = max(1, eff['dexterity'] - 2)
            
        # Stress Penalty: Panicked NPCs make poor decisions
        if self.needs["stress"] > 70:
            eff['intelligence'] = max(1, eff['intelligence'] - 3)
            
        return eff

    def get_sensation(self):
        """Returns a narrative description of physical/mental state."""
        h = self.needs["hunger"]
        e = self.needs["energy"]
        s = self.needs["stress"]
        
        sensations = []
        if h > 80: sensations.append("famished")
        elif h > 50: sensations.append("hungry")
        
        if e < 20: sensations.append("exhausted")
        elif e < 50: sensations.append("tired")
        
        if s > 70: sensations.append("panicked")
        elif s > 40: sensations.append("on edge")
        
        if not sensations: return "feeling stable"
        return "feeling " + " and ".join(sensations)

    def update_behavior(self):
        """Updates the character's behavioral description for a new turn."""
        self.current_behavior = self.get_behavioral_description()

    def get_behavioral_description(self):
        """Returns a flavor description of what the character is currently doing."""
        if self.personality == "Broken":
            return random.choice(["is curled into a ball on a bunk, shivering.", "is staring at their own hands, whispering silently.", "is rocking back and forth slowly."])
        elif self.personality == "Manic":
            return random.choice(["is drawing invisible patterns on the wall with their finger.", "is giggling uncontrollably at nothing.", "is pacing in tight, rapid circles."])
        elif self.personality == "Paranoid":
            return random.choice(["is staring intensely at the ceiling vents.", "is huddled in a corner, watching everyone with wide eyes.", "is muttering about 'the eyes in the walls'."])
        elif self.personality == "Aggressive":
            return random.choice(["is glaring at you with clenched fists.", "is shadow-boxing against a metallic pillar.", "is standing stiffly, looking for a fight."])
        elif self.personality == "Jumpy":
            return random.choice(["flinches at every sound from the hallway.", "is nervously tapping their feet against the bed frame.", "is looking around as if expecting something to jump out."])
        
        # Default/Sane behaviors
        if self.role == "Guard":
            return random.choice(["is standing guard, hand near their holster.", "is checking their radio with a bored expression.", "is scanning the room with clinical detachment."])
        elif self.role == "ISD Agent":
            return random.choice(["is observing the personnel with an unsettling, blank stare.", "is taking precise notes on a digital tablet.", "is standing perfectly still, watching for any sign of disloyalty."])
        else:
            return random.choice(["is sitting quietly on the edge of a bunk.", "is staring at the heavy steel door.", "is resting their head against the cool concrete wall."])

    def get_perceived_role(self, player):
        """Returns the role as perceived by the player (might be inaccurate)."""
        # If already identified, show the truth
        if self.id in player.identified_npc_ids:
            return self.role
            
        # D-Class perception logic
        if player.role == "Player": # Assuming 'Player' role for D-Class character
            # Anyone with high clearance or security role looks like a GUARD
            if self.role in ["Guard", "ISD Agent", "Containment Specialist", "MTF"]:
                return "GUARD"
            # Scientists or Admins might just look like general STAFF
            if self.role in ["Scientist", "Senior Researcher", "Medical Staff"]:
                return "STAFF"
                
        return self.role # Default to true role for non-D-Class or fallback

    def get_description(self, debug=False, player=None):
        """Returns a string with the character's details, including stats."""
        behavior = self.current_behavior
        
        if not debug and player:
            role_to_show = self.get_perceived_role(player)
            health_percent = self.health / self.max_health
            if health_percent > 0.9: health_status = "unharmed"
            elif health_percent > 0.5: health_status = "visibly injured"
            else: health_status = "critically wounded"
            
            mental_state = "seems sane"
            if self.personality in ["Broken", "Manic", "Paranoid"]:
                mental_state = "completely lost to madness"
            
            return f"{self.name} ({role_to_show}) {behavior} They look {health_status} and {mental_state}."

        details = [
            f"  Name: {self.name} ({self.role})",
            f"  Level: {self.level}",
            f"  Clearance Level: {self.clearance_level}",
            f"  Health: {self.health}/{self.max_health}",
            f"  Stamina: {self.stamina}/{self.max_stamina}",
            f"  Attributes:",
            f"    Strength: {self.attributes['strength']}",
            f"    Dexterity: {self.attributes['dexterity']}",
            f"    Intelligence: {self.attributes['intelligence']}",
            f"  Personality: {self.personality}",
            f"  Origin: {self.origin}",
            f"  Specialty: {self.specialty}",
        ]
        return "\n".join(details)
        
    def get_dialogue(self):
        """Returns a random dialogue line based on personality."""
        return random.choice(DIALOGUE_LINES.get(self.personality, ["..." ]))

    def get_contextual_dialogue(self, topic):
        """Returns a deep, trait-based response for a specific topic."""
        mid = getattr(self, 'master_identity', {})
        bio = mid.get('bio', {})
        prof = mid.get('professional_file', {})
        psy = mid.get('psychological_profile', {})
        sec = mid.get('social_and_secrets', {})
        life = mid.get('personal_life', {})
        
        if topic == "ask about current duties":
            if self.role == "Scientist":
                scp = prof.get('assigned_scp', 'various anomalies')
                return f"I am currently overseeing research on {scp.replace('_', ' ').upper()}. It is... demanding work."
            elif self.role == "Guard" or self.role == "ISD Agent":
                return f"My orders are to maintain security in this sector. Standard patrol, nothing more."
            elif self.role == "D-Class":
                return "My duties? Cleaning floors and being a human guinea pig. What do you think?"
            return "Just trying to get through the shift."

        elif topic == "try to socialize":
            if self.personality in ["Broken", "Manic"]:
                return self.get_dialogue() # Random insane ramblings
            
            hobby = life.get('hobbies', ['working'])[0] if life else "staring at walls"
            family = sec.get('family', 'no one') if sec else "no one"
            return f"I'd rather be {hobby.lower()} right now. Back home, I have {family}. I miss them."

        elif topic == "ask about facility secrets":
            loyalty = sec.get('loyalty_status', 'LOYAL') if sec else "LOYAL"
            agenda = sec.get('hidden_agenda', 'nothing') if sec else "nothing"
            
            if loyalty == "TRAITOR" or self.personality == "Paranoid":
                return f"You want to know the truth? {agenda}. Don't tell the ISD."
            return "I don't know what you're talking about. Everything here is strictly classified."

        elif topic == "gossip about others":
            if self.personality == "Aggressive":
                return "The people in this Site are incompetent. Especially the engineering crew."
            return "I heard some researchers in the next wing are hiding something. But people talk too much."

        return self.get_dialogue()

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
    elif role_str == 'isd agent':
        specialty = "Internal Security"
        clearance_level = 4
        attributes['intelligence'] += random.randint(3, 5)
        attributes['dexterity'] += random.randint(2, 4)
        health = random.randint(100, 140)
        stamina = random.randint(100, 140)
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

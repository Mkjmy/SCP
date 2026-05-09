# identity_generator.py
import random
import json
import os
import identity_pools as pools

def generate_master_identity(npc_id, role, department, assigned_scp=None):
    """
    Generates an ultra-detailed identity for an NPC.
    """
    gender = random.choice(pools.GENDERS)
    first_name = random.choice(pools.FIRST_NAMES)
    last_name = random.choice(pools.LAST_NAMES)
    
    # Simple gender-based name correction if needed (optional refinement)
    
    # Professional Logic
    clearance = 0
    if department == "Research & Science": clearance = random.randint(2, 4)
    elif department == "Security": clearance = random.randint(1, 3)
    elif department == "Administration": clearance = 4
    elif department == "Engineering": clearance = 2
    
    iq = random.randint(90, 160)
    if department == "Research & Science": iq = random.randint(120, 165)
    elif department == "D-Class": iq = random.randint(80, 115)

    identity = {
        "id": npc_id,
        "bio": {
            "full_name": f"{first_name} {last_name}",
            "gender": gender,
            "orientation": random.choice(pools.ORIENTATIONS),
            "age": random.randint(22, 65) if department != "D-Class" else random.randint(20, 45),
            "blood_type": random.choice(pools.BLOOD_TYPES),
            "genetic_stability": round(random.uniform(0.85, 1.0), 3),
            "origin": random.choice(pools.BACKGROUNDS).split('.')[0]
        },
        "appearance": {
            "height_cm": random.randint(155, 200),
            "weight_kg": random.randint(50, 110),
            "build": random.choice(pools.PHYSICAL_BUILDS),
            "physical_features": {
                "hair": f"{random.choice(pools.HAIR_COLORS)}, {random.choice(pools.HAIR_STYLES)}",
                "eyes": random.choice(pools.EYE_COLORS),
                "notable_marks": random.sample(pools.HABITS, 1) # Using habits as quick marks for now
            }
        },
        "professional_file": {
            "role": role,
            "department": department,
            "assigned_scp": assigned_scp,
            "clearance": clearance,
            "skills": {skill: random.randint(10, 95) for skill in random.sample(pools.SKILLS_LIST, 3)},
            "salary_level": f"Grade-{random.choice(['A', 'B', 'C', 'D'])}"
        },
        "psychological_profile": {
            "iq": iq,
            "personality_matrix": {
                "openness": random.randint(0, 100),
                "conscientiousness": random.randint(0, 100),
                "extraversion": random.randint(0, 100),
                "agreeableness": random.randint(0, 100),
                "neuroticism": random.randint(0, 100)
            },
            "phobias": random.sample(pools.PHOBIAS, 1),
            "mental_stability": round(random.uniform(0.4, 1.0), 2)
        },
        "social_and_secrets": {
            "family": random.choice(pools.FAMILY_STATUSES),
            "debts": {"amount": random.choice([0, 1000, 5000, 20000, 100000]), "creditor": random.choice(pools.CREDITORS)},
            "loyalty_status": "LOYAL",
            "hidden_agenda": random.choice(pools.HIDDEN_AGENDAS),
            "hidden_affiliation": random.choices(
                ["None", "ISD_UNDERCOVER", "CHAOS_INSURGENCY_SPY"],
                weights=[90, 7, 3], # 90% normal, 7% ISD, 3% Chaos
                k=1
            )[0]
        }
    }
    
    return identity

def save_identity(identity):
    """(Modified) Prepares the file path but DOES NOT write to disk automatically to prevent lag."""
    dept_map = {
        "Research & Science": "research",
        "Security": "security",
        "Administration": "admin",
        "D-Class": "dclass",
        "Engineering": "engineering",
        "Special": "special"
    }
    dept_folder = dept_map.get(identity["professional_file"]["department"], "special")
    return f"data/identities/{dept_folder}/{identity['id']}.json"

def write_identity_to_disk(identity):
    """Manually write a specific identity to disk when requested."""
    file_path = save_identity(identity)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(identity, f, indent=2)
    return file_path

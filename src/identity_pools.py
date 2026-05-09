# identity_pools.py
"""
Massive data pools for hyper-detailed NPC generation.
"""

FIRST_NAMES = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua", "Olga", "Maria", "Kenji", "Elena", "Sven", "Fatima", "Chen", "Arjun", "Yuki", "Lars"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Tanaka", "Ivanov", "Kovacs", "Muller", "O'Connor", "Dubois", "Vasiliev", "Sato", "Wong", "Gupta", "Bakker", "Schmidt"]

GENDERS = ["Male", "Female", "Non-binary", "Transgender", "Agender"]
ORIENTATIONS = ["Heterosexual", "Homosexual", "Bisexual", "Pansexual", "Asexual"]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

PHYSICAL_BUILDS = ["Athletic", "Slender", "Stocky", "Lithe", "Heavily Muscular", "Frail", "Average", "Overweight"]
HAIR_STYLES = ["Buzz cut", "Shoulder-length", "Bald", "Pompadour", "Messy", "Ponytail", "Fade", "Wild and unkempt", "Manicured", "Pixie cut"]
HAIR_COLORS = ["Black", "Brown", "Blonde", "Silver", "Red", "Grey", "Dyed blue", "Dyed green", "White"]
EYE_COLORS = ["Sharp blue", "Deep brown", "Emerald green", "Hazel", "Grey", "Heterochromatic (Grey/Blue)", "Icy blue", "Amber"]

PHOBIAS = [
    "Aphenphosmphobia (Fear of being touched)",
    "Nyctophobia (Fear of darkness)",
    "Claustrophobia (Fear of confined spaces)",
    "Arachnophobia (Fear of spiders)",
    "Automatonophobia (Fear of human-like figures)",
    "Scopophobia (Fear of being stared at)",
    "Chronophobia (Fear of time passing)",
    "Achluophobia (Fear of darkness)",
    "Aphenphosmphobia (Fear of intimacy)",
    "Kenophobia (Fear of voids or empty spaces)"
]

HABITS = [
    "Drinks black coffee constantly",
    "Nail biter",
    "Taps fingers rhythmically",
    "Talks to self in whispers",
    "Check their watch every 30 seconds",
    "Hums classical music",
    "Cracks knuckles frequently",
    "Smokes heavily",
    "Obsessively cleans their glasses",
    "Twirls a pen between fingers"
]

HIDDEN_AGENDAS = [
    "Seeking a way to resurrect a loved one using anomalous means",
    "Spying for the Chaos Insurgency",
    "In debt to Marshall, Carter & Dark Ltd.",
    "Planning to leak documents to the Serpent's Hand",
    "Obsessed with reaching Site-01",
    "Seeking promotion at any cost",
    "Secretly worships the Scarlet King",
    "Attempting to steal a specific SCP object",
    "Undercover ISD agent",
    "Trying to clear their family name"
]

BACKGROUNDS = [
    "Former university professor specialized in anomalous biology.",
    "Ex-military police recruited after a classified incident.",
    "Convicted felon given a choice between execution and Foundation service.",
    "Former NASA engineer who saw too much.",
    "Rescued from a defunct GOI cell.",
    "Raised in a Foundation-sponsored orphanage.",
    "Former investigative journalist who dug too deep.",
    "Ex-special forces with experience in urban warfare.",
    "Brilliant mathematician with a history of mental instability.",
    "Former deep-sea diver with encounters in the Pacific."
]

SOCIAL_STANDINGS = ["Respected by peers", "Outcast", "Average", "Feared", "Nervous around authority", "Charismatic leader", "Introverted", "Unremarkable"]
FAMILY_STATUSES = ["Married, 2 children", "Single", "Widowed", "Divorced", "Estranged from family", "Orphaned", "Married, no children"]
CREDITORS = ["Marshall, Carter & Dark Ltd.", "Local Mob", "Student Loans", "Foundation Housing Loan", "None"]

SKILLS_LIST = ["Occult_Research", "Containment_Logic", "Firearms", "Medicine", "Engineering", "Hacking", "Persuasion", "Athletics", "Stealth", "Perception"]

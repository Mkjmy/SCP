import random
from player import BODY_PARTS # Import BODY_PARTS for random injury selection

def attack(player, characters_in_room):
    """Player attempts to attack."""
    # Check for severe arm injuries that might prevent attack
    if player.is_part_severely_injured('left_arm') and player.is_part_severely_injured('right_arm'):
        return "Your arms are too severely injured to even attempt an attack!", False

    guards = [c for c in characters_in_room if c.role == 'Guard']
    if guards:
        guard = guards[0]
        
        # Player takes damage from attacking a guard
        base_damage_taken = random.randint(30, 50) # Substantial damage
        
        # Apply debuffs to player's attack effectiveness (which might indirectly increase damage taken)
        attack_debuff = player.get_debuff(action_type='attack')
        # A simple way to model debuff: increase damage taken
        damage_taken = base_damage_taken + (attack_debuff * 5) # Each debuff point adds 5 damage

        player.health -= damage_taken
        morale_message = player.change_morale(-5) # Lose morale for taking damage

        # Apply injury to a random body part
        if damage_taken > 0:
            injured_part = random.choice(BODY_PARTS)
            # Severity scales with damage. For simplicity, if damage is high, more severe injury.
            if damage_taken >= 45:
                injury_msg = player.apply_injury(injured_part, 'severe_injury')
            elif damage_taken >= 35:
                injury_msg = player.apply_injury(injured_part, 'major_injury')
            elif damage_taken >= 25:
                injury_msg = player.apply_injury(injured_part, 'minor_injury')
            else:
                injury_msg = "" # No new injury if damage is too low

        if player.health <= 0:
            return f"You foolishly lunge at {guard.name}. They don't even break a sweat as they neutralize you. The world fades to black.", True
        else:
            final_message = f"You foolishly lunge at {guard.name}. They easily sidestep and counter, dealing {damage_taken} damage! You manage to stumble back, but that was a mistake."
            if injury_msg:
                final_message += f" {injury_msg}"
            if morale_message:
                final_message += f" {morale_message}"
            return final_message, False
    else:
        return "You swing wildly at the air. There's nothing here to attack.", False

def run(player, characters_in_room, current_room_exits, game_map):
    """Player attempts to run away."""
    # Check for severe leg injuries that might prevent running
    if player.is_part_severely_injured('left_leg') and player.is_part_severely_injured('right_leg'):
        return "Your legs are too severely injured; you can't run!", False

    guards = [c for c in characters_in_room if c.role == 'Guard']
    
    # Running consumes stamina regardless of success
    base_stamina_cost = 20
    stamina_debuff_injury = player.get_debuff(action_type='run')
    morale_effect_stamina = player.get_morale_effect('run') # Morale can affect stamina cost
    stamina_cost = base_stamina_cost + (stamina_debuff_injury * 2) - morale_effect_stamina # Injuries increase cost, good morale reduces it
    
    if player.stamina < stamina_cost:
        return "You are too exhausted to run!", False
    player.stamina -= stamina_cost

    if guards:
        guard = guards[0]
        
        # Success chance based on player dexterity vs guard dexterity, adjusted by injury debuff and morale
        dex_difference = player.attributes['dexterity'] - guard.attributes['dexterity']
        dex_injury_debuff = player.get_debuff(attribute='dexterity')
        morale_effect_dex = player.get_morale_effect('dexterity') # Morale can affect underlying attribute directly
        
        effective_player_dex = player.attributes['dexterity'] - dex_injury_debuff + morale_effect_dex

        effective_player_dex = max(1, effective_player_dex) # Ensure not negative

        dex_difference_after_debuff = effective_player_dex - guard.attributes['dexterity']
        
        success_chance = 0.40 + (dex_difference_after_debuff * 0.05) # Base 40% + 5% per effective dex difference

        success_chance = max(0.1, min(success_chance, 0.9)) # Min 10%, Max 90%

        if random.random() < success_chance:
            # On success, move to a random adjacent room.
            player.location = random.choice(list(current_room_exits.values()))
            morale_message = player.change_morale(10) # Gain morale for successful escape
            final_message = f"You make a mad dash! In the chaos, you manage to slip past {guard.name} and into another room."
            if morale_message:
                final_message += f" {morale_message}"
            return final_message, False
        else:
            damage_taken = random.randint(15, 35) # Damage on failed run
            player.health -= damage_taken
            morale_message = player.change_morale(-10) # Lose morale for failed escape
            
            # Apply injury to a random body part, biased towards legs for failed runs
            injury_msg = ""
            injured_part = random.choice(['left_leg', 'right_leg', random.choice(BODY_PARTS)]) # Higher chance for leg injury
            
            if damage_taken >= 30:
                injury_msg = player.apply_injury(injured_part, 'severe_injury')
            elif damage_taken >= 20:
                injury_msg = player.apply_injury(injured_part, 'major_injury')
            elif damage_taken >= 10:
                injury_msg = player.apply_injury(injured_part, 'minor_injury')
            
            final_message = f"You try to bolt, but {guard.name} catches you, dealing {damage_taken} damage! You stumble back, narrowly escaping their grasp."
            if injury_msg:
                final_message += f" {injury_msg}"
            if morale_message:
                final_message += f" {morale_message}"

            if player.health <= 0:
                return f"You try to bolt, but {guard.name} is too fast. They grab you and finish you off. The world fades to black.", True
            else:
                return final_message, False
    else:
        return "You run around in a circle, feeling a bit silly. There's no immediate threat here and you feel a bit winded.", False

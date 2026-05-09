import random
from entities.player.player import BODY_PARTS # Import BODY_PARTS for random injury selection

def attack(player, characters_in_room, scps_in_room=None):
    """Player attempts to attack a specific target with Momentum and Lethality."""
    # 0. Check Incapacitated
    is_mangled, reason = player.is_incapacitated()
    if is_mangled:
        return reason, False

    # 1. SCP Response
    if scps_in_room:
        for scp in scps_in_room:
            scp_responses = scp.on_player_attack(player, None)
            if scp_responses:
                return "\n".join(scp_responses), player.health <= 0

    # 2. Check for Security Intervention (Excessive Violence)
    # If the player has killed before or is in a room with many witnesses, guards might intervene
    guards_in_wing = any(c.role == "Guard" for c in characters_in_room)
    if guards_in_wing and (player.combat_momentum > 1 or random.random() < 0.2):
        player.health -= 5 # Minor impact from dart
        player.stamina = 0
        return "As you prepare to strike, a sharp sting hits your neck. A tranquilizer dart. Your vision blurs as the guards move in to restrain you.", False

    # 3. Human Combat Logic
    if characters_in_room:
        target = characters_in_room[0]
        
        if target.role == "Guard":
            player.health = 0
            return f"You attempt to strike {target.name}. Before you can even move, they draw their sidearm and fire. The world fades to black.", True

        # Combat Stats with Momentum
        p_str = player.attributes['strength']
        p_dex = player.attributes['dexterity']
        t_str = target.attributes['strength']
        t_dex = target.attributes['dexterity']
        
        p_debuff = player.get_debuff(action_type='attack')
        effective_p_str = max(1, p_str - p_debuff)
        
        # MOMENTUM IMPACT: Each point of momentum adds/removes 10% win chance
        momentum_bonus = getattr(player, 'combat_momentum', 0) * 0.1
        
        win_chance = 0.5 + (effective_p_str - t_str) * 0.1 + (p_dex - t_dex) * 0.05 + momentum_bonus
        win_chance = max(0.05, min(0.95, win_chance))
        
        if random.random() < win_chance:
            # Player Wins: Momentum increases
            player.combat_momentum = min(3, player.combat_momentum + 1)
            target.health -= 40
            
            growth_msg = ""
            if not player.is_part_severely_injured('left_arm') and not player.is_part_severely_injured('right_arm'):
                player.attributes['strength'] += 1
                growth_msg = " The adrenaline makes you feel more dangerous."

            if target.health <= 0:
                player.total_kills += 1
                return f"You deliver a crushing blow to {target.name}. Their body goes limp. They are no longer breathing.{growth_msg}", False
            
            return f"You catch {target.name} off guard with a vicious strike! They stumble back, clutching their side.{growth_msg}", False
        else:
            # Player Loses: Momentum decreases
            player.combat_momentum = max(-3, player.combat_momentum - 1)
            damage_taken = random.randint(20, 40)
            player.health -= damage_taken
            
            injured_part = random.choice(BODY_PARTS)
            severity = 'fractured' if damage_taken > 35 else 'bleeding' if damage_taken > 25 else 'bruised'
            injury_msg = player.apply_injury(injured_part, severity)
            
            if player.health <= 0:
                return f"{target.name} delivers a finishing blow. The world fades to black.", True
            
            return f"{target.name} strikes back hard, dealing {damage_taken} damage. Your confidence is shaken. {injury_msg}", False

    return "There's no one here to hit.", False

    return "You swing at shadows. There's no one here to hit.", False

def run(player, characters_in_room, current_room_exits, game_map, scps_in_room=None):
    """Player attempts to run away."""
    # 0. Check Incapacitated
    is_mangled, reason = player.is_incapacitated()
    if is_mangled:
        return reason, False

    # Check for SCP-specific run responses (e.g., pursuit, hindrance)
    if scps_in_room:
        for scp in scps_in_room:
            scp_responses = scp.on_player_run(player, None)
            if scp_responses:
                # SCP might block the run or cause damage during the attempt
                return "\n".join(scp_responses), player.health <= 0

    # Check for severe leg injuries that might prevent running
    if player.is_part_severely_injured('left_leg') and player.is_part_severely_injured('right_leg'):
        return "Your legs are too severely injured; you can't run!", False

    guards = [c for c in characters_in_room if c.role == 'Guard']
    
    # Running consumes stamina regardless of success
    base_stamina_cost = 20
    stamina_debuff_injury = player.get_debuff(action_type='run')
    morale_effect_stamina = player.get_morale_effect('run') # Morale can affect stamina cost
    stamina_cost = (base_stamina_cost + (stamina_debuff_injury * 2) - morale_effect_stamina) * player.active_rules.get('stamina_cost_multiplier', 1.0)
    
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

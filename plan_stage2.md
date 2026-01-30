

**Proposed Plan for Stage 2: Partial Body Damage System**

To proceed with the "Partial Body Damage System" as outlined in your original request, here is a detailed plan:

1.  **Define Body Parts and Damage States:**
    *   I will define a set of key body parts: `head`, `torso`, `left_arm`, `right_arm`, `left_leg`, `right_leg`.
    *   Each body part will have damage states:
        *   `uninjured`: No current debuff.
        *   `minor_injury`: Introduces a small debuff (e.g., -1 to relevant attribute, increased stamina cost).
        *   `major_injury`: Introduces a moderate debuff (e.g., -2 to relevant attribute, higher stamina cost, reduced success chance).
        *   `broken`/`severe_injury`: Introduces a severe debuff (e.g., -3 to relevant attribute, action might be impossible or have high risk).
    *   Specific effects will be:
        *   `head`: Affects `intelligence`, critical damage might cause disorientation (future, if needed).
        *   `torso`: Affects `health` regeneration (future), general `stamina` use.
        *   `arms`: Affects `strength` and `dexterity` (e.g., for `attack`, `take`).
        *   `legs`: Affects `dexterity` and `stamina` (e.g., for `run`, `go`).

2.  **Integrate into Player Class (`player.py`):**
    *   Add a dictionary `self.body_parts = {part: 'uninjured' for part in [...]}` to the `Player` class.
    *   Introduce helper methods like `get_injury_debuff(attribute)` and `apply_injury(part, severity)`.

3.  **Modify Damage Application (`actions.py` and `main.py`):**
    *   When the player takes damage (e.g., from failed `run`, `attack`), I will introduce a mechanism to randomly select a body part to apply an injury to, in addition to reducing overall `health`.
    *   The severity of the injury could scale with the damage taken or be random.

4.  **Extend UI to Display Body Part Status (`main.py`):**
    *   Modify `display_status_bar` or create a new section in the main display loop to show the status of each body part, highlighting injured parts (e.g., `Left Arm: Injured`).

5.  **Adjust Actions Based on Injuries (`actions.py`):**
    *   Modify `run`: If legs are injured, increase stamina cost or decrease success chance.
    *   Modify `attack`: If arms are injured, decrease attack effectiveness.
    *   Introduce checks for specific injuries making actions impossible (e.g., `broken_leg` prevents `run` entirely).

Please confirm if you would like me to proceed with this detailed plan for the "Partial Body Damage System".

# SCP Simulation System: Core Architecture

This document defines the backend simulation logic that creates a living, autonomous facility environment.

## 1. Turn-Based Life Simulation (LOD Engine)
The facility supports 1000+ NPCs using a Level of Detail (LOD) approach to maintain performance without sacrificing logical consistency.

### Simulation Tiers
*   **Tier 1 (High-Fidelity):** Within 0-1 rooms of the player. Full AI processing, real-time pathfinding, and detailed social negotiation.
*   **Tier 2 (Mid-Fidelity):** Within 2-4 rooms. Simplified decision-making and batched pathfinding updates.
*   **Tier 3 (Abstract):** 5+ rooms away. Deterministic calculations for arrival times and statistical outcomes for social interactions.

### The "Spotlight" (Focus) Mechanic
Any NPC that interacts with the player or is specifically targeted (e.g., Look at, Talk to) is instantly promoted to Tier 1 regardless of distance. Their abstract state is "Reified" into detailed actions based on their unique personality and needs.

## 2. NPC Needs & Sensations
All NPCs manage hidden internal states (0-100):
*   **Hunger:** Increases per turn. NPCs seek the Cafeteria at moderate (>40) or urgent (>80) levels.
*   **Energy:** Decreases per turn. NPCs seek Dormitories/Break Rooms.
*   **Bladder:** Periodic increases requiring Restroom visits.
*   **Stress:** Affected by proximity to SCPs or witnessing trauma.

**Sensations:** Technical numbers are converted into narrative strings like "famished", "exhausted", or "on edge".

## 3. Task & Duty System
NPCs prioritize professional duties over personal needs based on urgency:
*   **Critical Duties:** Containment breaches, escorted test subjects, or security alerts override basic needs.
*   **Escort Missions:** Coordination between Scientists (requesting subjects) and Guards (fetching D-Class via pathfinding).

## 4. Social Negotiation Layer
Cooperation is not guaranteed. NPCs "broadcast" needs or orders, and nearby entities evaluate them based on:
*   **IQ:** Understanding mission importance.
*   **Loyalty:** Commitment to Foundation mandates.
*   **Physical State:** A tired or hungry NPC is more likely to refuse a non-critical request.

## 5. Dynamic Detail Slotting (Priority Queue)
The facility maintains a constant pool of 50 Detail Slots (Tier 1 processing). This ensures maximum fidelity for the most relevant entities at any given time.

### Slot Priority Logic
Slots are assigned in the following order:
1.  **Focused NPCs:** Entities explicitly targeted by the player (Look, Talk).
2.  **Proximity NPCs:** Entities in the same room as the player.
3.  **Neighboring NPCs:** Entities in adjacent rooms.
4.  **Peripheral Relevance:** Remaining slots are given to the closest NPCs in the same wing.

### 6. Cascading Promotion (Interaction Consistency)
To prevent "Detail vs. Abstract" logic conflicts:
*   If a Detail NPC (Slot holder) initiates an interaction (Social Negotiation) with an Abstract NPC:
    *   The Abstract NPC is instantly Promoted to a Detail Slot for the duration of the turn.
    *   If the slot limit is reached, a low-priority peripheral NPC is temporarily demoted.
*   This ensures that all coordinated actions (Escorts, Experiments, Conversations) are calculated with 100% logic consistency before returning to an optimized state.

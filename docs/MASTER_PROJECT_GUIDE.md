# Project SCP: Foundation Site-Logic (Master Guide)

Welcome to the Foundation. This document provides a comprehensive overview of the Site-Logic simulation engine, its core systems, and known logical complexities.

## 1. Core Systems Architecture

### 🧪 Modular SCP Framework (`src/scp.py`, `src/mechanics.py`)
- **Data-Driven:** SCPs are defined in `data/scp_definitions.json`.
- **Mechanics:** Modular components (Perception, Reality, Spatial, etc.) that can be mixed and matched to create complex anomalies without hardcoding Python logic.

### 📖 Narrative OS Interface (`src/main.py`)
- **Novel Style:** Replaces technical lists with fluid prose, weaving room descriptions, NPC actions, and story events into a cohesive narrative.
- **Visual Scans:** Items and personnel are presented as structured terminal logs (─) for tactical awareness.
- **Integrated HUD:** Biometric data (Health/Stamina) is described through sensations (e.g., "Feeling Tired" instead of "Stamina: 45%").

### 🧬 Hyper-Scale Life Simulation (`src/npc_manager.py`)
- **LOD (Level of Detail):** Supports 200+ NPCs. Processing is divided into tiers:
    - **Tier 1 (Detail):** NPCs near the player (max 50 slots). Full AI, social negotiation, and detailed pathfinding.
    - **Tier 3 (Abstract):** Distant NPCs. Statistical movement and math-only needs updates.
- **Deterministic Consistency:** NPCs follow "Virtual Paths." If a player encounters a Tier 3 NPC, they "materialize" at the exact logical point on their journey.
- **Social Negotiation:** NPCs broadcast needs. Others evaluate requests based on IQ, Loyalty, and Physical State before cooperating.

### 🕵️ Master Identity & ISD (`src/identity_generator.py`)
- **Deep Profiles:** Every NPC has a JSON file (`data/identities/`) containing blood type, Big Five personality traits, debts, and **Hidden Agendas**.
- **The ISD Factor:** Internal Security agents monitor staff. Characters practicing "Forbidden Acts" are flagged as **Traitors**.
- **Spies:** Chaos Insurgency infiltrators exist within the population, capable of recruiting Traitors or sabotaging containment.

### 🎬 Scripted Story Engine (`src/story_manager.py`)
- **Chapter System:** JSON-driven sequences (`data/storyline.json`) that can override autonomous AI for key plot points.
- **Branching Choices:** Major events present unique choices (e.g., "Comply" vs "Resist") with persistent consequences.

## 2. Logical Hierarchy & Priorities
As the system evolves, keep in mind which logic takes precedence:
1.  **Scripted Story:** Overrides EVERYTHING. If an MTF is scripted to kill the player, they ignore their own hunger and safety.
2.  **Professional Duty:** Overrides personal needs. A Guard on escort duty will not leave for lunch until the task is complete.
3.  **Personal Needs:** Active only when an NPC is idling or on patrol.

## 3. The Cascading Promotion Logic
If an NPC in Tier 1 (Detail) interacts with an NPC in Tier 3 (Abstract), the system **promotes** the Tier 3 entity into a Detail Slot temporarily. To maintain the 50-slot limit, the furthest NPC from the player is demoted. This ensures logical consistency during all social and professional coordination.

## 4. Combat & Growth
Combat is stat-based (Strength/Dexterity). Attacking security forces results in lethal retaliation (Instant Death). Survival in combat leads to subtle, narrative-driven strength increases ("You feel your resolve hardening").

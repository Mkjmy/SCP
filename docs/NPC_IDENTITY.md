# NPC Identity & Professional Hierarchy

This document defines the data structures and organizational logic for all personnel within the Site.

## 1. Master Identity Schema
Every NPC possesses a unique JSON profile containing:
*   **Biological Data:** Blood type (affects infection), Genetic stability, Gender, and Orientation.
*   **Appearance:** Detailed physical traits (height, build, scars, tattoos, voice type).
*   **Psychology:** Big Five personality matrix, IQ/EQ, specific Phobias, and Addictions.
*   **Clandestine Data:** Loyalty status, Hidden Agendas (e.g., "Spying for Chaos Insurgency"), and Social Debts.

## 2. Professional Departments
Personnel are categorized into specialized wings:
*   **Research & Science:** Researchers, Senior Scientists, Medical Staff, and Psionics Specialists.
*   **Security Force:** Guards, Containment Specialists, RRT, and MTF.
*   **Administration:** Site Director, Facility Manager, Ethics Committee Liaisons.
*   **Engineering:** Engineers, IT Specialists, Maintenance Crews.

## 3. Internal Security (ISD) & Traitor Mechanics
The Internal Security Department (ISD) acts as the facility's secret police.
*   **Monitoring:** ISD agents (often disguised) scan for unauthorized violations.
*   **Violations:** Collecting artifacts, practicing occultism, or leaking documents.
*   **Consequences:** Detection leads to the TRAITOR status, resulting in amnesticization, termination, or defection to the Chaos Insurgency.

## 4. Data Persistence
Profiles are stored hierarchically in data/identities/[department]/npc_[id].json. A global tracker (data/global_npc_tracker.json) monitors real-time locations and activity across the entire 1000-member population.

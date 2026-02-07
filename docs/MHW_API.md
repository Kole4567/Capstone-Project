Monster Hunter World API Documentation

API Version: v1

==================================================
1. Overview
==================================================

This document describes the Monster Hunter World (MHW) Backend API.

The purpose of this API is to provide structured Monster Hunter World game data
(monsters, weaknesses, weapons, skills, etc.) from our internal database for:

- Frontend UI rendering
- Build recommendation algorithms
- Custom build creation and sharing

This API acts as the single source of truth for all game data used in this project.

==================================================
2. Data Source
==================================================

All Monster Hunter World game data is originally sourced from:

https://docs.mhw-db.com/

The backend imports and stores this data into its own database.

Important:
- Frontend and recommendation logic MUST NOT call mhw-db.com directly.
- Always use the internal API endpoints described in this document.
- This ensures stability, performance, and consistent data formatting.

==================================================
3. One-Click Local Setup (Team Standard)
==================================================

This section defines the recommended start-to-finish local setup flow.
Following these steps guarantees a clean, identical environment for all team members.

--------------------------------------------------
Step 1. Environment Setup
--------------------------------------------------

- git clone <repository-url>
- cd Capstone-Project/mysite
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

--------------------------------------------------
Step 2. Database Initialization
--------------------------------------------------

- python manage.py migrate

Optional (local development only, if schema conflicts occur):
- python manage.py flush
  - Type "yes" to confirm

--------------------------------------------------
Step 3. Import Monster Data
--------------------------------------------------

Required (first-time setup only):
- python manage.py import_mhw --monsters data/mhw_monsters.json --reset

Optional (development / verification):
- python manage.py import_mhw --monsters data/mhw_monsters.json --dry-run --limit 10
- python manage.py import_mhw --monsters data/mhw_monsters.json --limit 10

Notes:
- --reset should only be used for first-time setup or full reinitialization.
- Re-running the import without --reset is safe and idempotent.

--------------------------------------------------
Step 4. Import Weapon Data
--------------------------------------------------

Required (first-time setup only):
- python manage.py import_weapons --weapons data/mhw_weapons.json --reset

Optional (development / verification):
- python manage.py import_weapons --weapons data/mhw_weapons.json --dry-run --limit 10

--------------------------------------------------
Step 5. Import Skill Data
--------------------------------------------------

Required (first-time setup only):
- python manage.py import_skills --skills data/mhw_skills.json --reset

Optional (development / verification):
- python manage.py import_skills --skills data/mhw_skills.json --dry-run --limit 10

--------------------------------------------------
Step 6. Run Server
--------------------------------------------------

- python manage.py runserver

--------------------------------------------------
Step 7. Verify API Endpoints
--------------------------------------------------

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/weapons/
- GET /api/v1/mhw/skills/

--------------------------------------------------
Step 8. Run Backend Tests (Recommended)
--------------------------------------------------

- python manage.py test MonsterHunterWorld

==================================================
4. Import Pipeline – Stability Design
==================================================

The import pipeline is intentionally defensive to handle real-world data issues.

Design Goals:
- One bad record must not crash the entire import
- Each monster is imported inside its own database transaction
- Duplicate data must never cause UNIQUE constraint failures
- Re-importing data must be safe and idempotent
- Internal database is the single source of truth

Key Design Decisions:
- Per-monster transaction isolation
- In-memory deduplication before database insertion
- Deduplication uses the same unique key as the database schema
- Existing weaknesses are replaced per monster to ensure consistency

==================================================
5. Core Data Models (Conceptual)
==================================================

--------------------------------------------------
5.1 Monster
--------------------------------------------------

Fields:
- id (integer): Internal database ID
- external_id (integer): Stable ID from mhw-db (unique)
- name (string)
- monster_type (string)
- is_elder_dragon (boolean)

--------------------------------------------------
5.2 MonsterWeakness
--------------------------------------------------

Fields:
- kind (string): "element" or "ailment"
- name (string)
- stars (integer): positive integer (typically 1–3)
- condition (string, optional)
- condition_key (string): normalized key derived from condition

Notes:
- Multiple weaknesses may exist for the same element under different conditions
- Uniqueness is enforced on:
  (monster, kind, name, condition_key)
- condition_key is used to guarantee consistent uniqueness across imports

--------------------------------------------------
5.3 Weapon
--------------------------------------------------

Represents a craftable weapon.

Fields:
- id (integer): Internal database ID
- external_id (integer): mhw-db weapon ID (unique)
- name (string)
- weapon_type (string)
- rarity (integer)
- attack_raw (integer)
- attack_display (integer)
- affinity (integer)
- element (string, optional)
- element_damage (integer, optional)
- elderseal (string, optional)

Notes:
- Weapons are independent of monsters
- Some weapons have no elemental damage
- Raw and display attack values are stored separately

--------------------------------------------------
5.4 Skill
--------------------------------------------------

Represents a passive skill used in builds
(e.g., Attack Boost, Critical Eye).

Fields:
- id (integer): Internal database ID
- external_id (integer): Stable ID from mhw-db (unique)
- name (string)
- description (string)
- max_level (integer)

Notes:
- max_level is derived from mhw-db ranks data
- MVP stores only high-level descriptions and max level
- Per-rank modifiers may be added later

==================================================
6. API Documentation (Swagger / OpenAPI)
==================================================

Auto-generated documentation endpoints:

- OpenAPI Schema:
  /api/schema/

- Swagger UI:
  /api/docs/

- Redoc:
  /api/redoc/

==================================================
7. API Endpoints
==================================================

Base URL:
/api/v1/mhw/

--------------------------------------------------
7.1 Get All Monsters
--------------------------------------------------

GET /api/v1/mhw/monsters/

Optional Query Parameters:
- is_elder_dragon (boolean)
- element (string)
- min_stars (integer)
- order_by (id, name, monster_type, is_elder_dragon)

--------------------------------------------------
7.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}/

--------------------------------------------------
7.3 Get All Weapons
--------------------------------------------------

GET /api/v1/mhw/weapons/

Optional Query Parameters:
- weapon_type (string)
- element (string)
- min_rarity (integer)
- max_rarity (integer)
- min_attack (integer)
- order_by (id, name, weapon_type, rarity, attack_raw, affinity, element)

Examples:
- /api/v1/mhw/weapons/?weapon_type=Long%20Sword&min_rarity=6&max_rarity=8
- /api/v1/mhw/weapons/?element=Fire&order_by=-attack_raw

--------------------------------------------------
7.4 Get Weapons (Paged)
--------------------------------------------------

GET /api/v1/mhw/weapons/paged/

Query Parameters:
- limit (default: 50)
- offset (default: 0)

--------------------------------------------------
7.5 Get Weapon Detail
--------------------------------------------------

GET /api/v1/mhw/weapons/{id}/

--------------------------------------------------
7.6 Get All Skills
--------------------------------------------------

GET /api/v1/mhw/skills/

Optional Query Parameters:
- name (string): case-insensitive contains filter
- min_level (integer): max_level >= N
- order_by (id, name, max_level)

--------------------------------------------------
7.7 Get Skills (Paged)
--------------------------------------------------

GET /api/v1/mhw/skills/paged/

Query Parameters:
- limit (default: 50)
- offset (default: 0)

--------------------------------------------------
7.8 Get Skill Detail
--------------------------------------------------

GET /api/v1/mhw/skills/{id}/

==================================================
8. API Contract Rules
==================================================

This document is an API contract.

- Any API change must update this document
- Breaking changes require an API version bump (v2)

==================================================
9. FAQ
==================================================

Q: Monsters list is empty?
A: Monster import was skipped. Run import_mhw with --reset (first-time setup only).

Q: Weapons list is empty?
A: Weapon import was skipped. Run import_weapons with --reset.

Q: Skills list is empty?
A: Skill import was skipped. Run import_skills with --reset.

Q: Why are some fields null?
A: Some entities do not have elemental or conditional data.

==================================================
10. Future Extensions
==================================================

- Armor
- Armor Sets
- Decorations
- Build saving and sharing
- Skill rank modifiers

==================================================
11. Contact
==================================================

For backend or data-related questions,
contact the backend/database maintainer.
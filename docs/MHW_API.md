Monster Hunter World API Documentation

API Version: v1

==================================================
1. Overview
==================================================

This document describes the Monster Hunter World (MHW) Backend API.

The purpose of this API is to provide structured Monster Hunter World game data
(monsters, weaknesses, weapons, etc.) from our internal database for:

- Frontend UI rendering
- Build recommendation algorithms
- Custom build creation and sharing

This API acts as the single source of truth for game data within this project.

==================================================
2. Data Source
==================================================

All Monster Hunter World game data is originally sourced from:

https://docs.mhw-db.com/

The backend imports and stores this data into our own database.

Important
- Frontend and recommendation logic must NOT call mhw-db.com directly.
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

Optional (only if schema changes cause conflicts during development):
- python manage.py flush
  - Type "yes" to confirm (local DB only)

--------------------------------------------------
Step 3. Import Monster Data (Required)
--------------------------------------------------

- python manage.py import_mhw --monsters data/mhw_monsters.json --reset

Optional (development only):
- python manage.py import_mhw --monsters data/mhw_monsters.json --dry-run --limit 10

--------------------------------------------------
Step 4. Import Weapon Data (Required)
--------------------------------------------------

- python manage.py import_weapons --weapons data/mhw_weapons.json --reset

Optional (development only):
- python manage.py import_weapons --weapons data/mhw_weapons.json --dry-run --limit 10

--------------------------------------------------
Step 5. Run Server
--------------------------------------------------

- python manage.py runserver

--------------------------------------------------
Step 6. Verify API Endpoints
--------------------------------------------------

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/weapons/

--------------------------------------------------
Step 7. Run Backend Tests (Recommended)
--------------------------------------------------

- python manage.py test MonsterHunterWorld

==================================================
4. Import Pipeline – Stability Design
==================================================

The import pipeline is intentionally defensive to handle real-world data issues.

Design Goals
- One bad record must not crash the entire import
- Partial data should be tolerated when possible
- Re-import must always result in a clean database
- Internal DB is the single source of truth

==================================================
5. Core Data Models (Conceptual)
==================================================

--------------------------------------------------
5.1 Monster
--------------------------------------------------

Fields
- id (integer): Internal database ID
- external_id (integer): Stable ID from mhw-db (unique)
- name (string)
- monster_type (string)
- is_elder_dragon (boolean)

--------------------------------------------------
5.2 MonsterWeakness
--------------------------------------------------

Fields
- kind (string): "element" or "ailment"
- name (string)
- stars (integer, 1–3)
- condition (string, optional)

Notes
- Multiple weaknesses may exist for the same element with different conditions
- Stars are constrained at the database level (1–3 only)

--------------------------------------------------
5.3 Weapon
--------------------------------------------------

Represents a craftable weapon.

Fields
- id (integer): Internal database ID
- external_id (integer): mhw-db weapon ID
- name (string)
- weapon_type (string): Great Sword, Long Sword, Bow, etc.
- rarity (integer)
- attack_raw (integer)
- attack_display (integer)
- affinity (integer)
- element (string, optional)

Notes
- Weapons are independent of monsters
- Element data is used later for build calculations
- Some weapons have no elemental damage

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

Optional Query Parameters
- is_elder_dragon (boolean)
- element (string)
- min_stars (integer, 1–3)
- order_by (id, name, monster_type, is_elder_dragon)

--------------------------------------------------
7.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}

--------------------------------------------------
7.3 Get All Weapons
--------------------------------------------------

GET /api/v1/mhw/weapons/

Optional Query Parameters
- weapon_type (string, exact match)
- element (string, case-insensitive)
- min_rarity (integer)
- max_rarity (integer)
- order_by (id, name, weapon_type, rarity, attack_raw, affinity, element)

Example
- /api/v1/mhw/weapons/?weapon_type=Long%20Sword&min_rarity=6&max_rarity=8
- /api/v1/mhw/weapons/?element=Fire&order_by=-attack_raw

--------------------------------------------------
7.4 Get Weapons (Paged)
--------------------------------------------------

GET /api/v1/mhw/weapons/paged/

Pagination Parameters
- limit (default: 50)
- offset (default: 0)

--------------------------------------------------
7.5 Get Weapon Detail
--------------------------------------------------

GET /api/v1/mhw/weapons/{id}

==================================================
8. API Contract Rules
==================================================

This document is an API contract.

- Any API change must update this document
- Breaking changes require version bump (v2)

==================================================
9. FAQ
==================================================

Q: Monsters list is empty?
A: Monster import was skipped. Run import_mhw with --reset.

Q: Weapons list is empty?
A: Weapon import was skipped. Run import_weapons with --reset.

Q: Why are some fields null?
A: Some weapons or monsters do not have element or conditional data.

==================================================
10. Future Extensions
==================================================

- Armor
- Armor Sets
- Skills
- Decorations
- Build saving and sharing

==================================================
11. Contact
==================================================

For backend or data-related questions,
contact the backend/database maintainer.
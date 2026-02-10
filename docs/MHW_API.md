Monster Hunter World API Documentation

API Version: v1

==================================================
1. Overview
==================================================

This document describes the Monster Hunter World (MHW) Backend API.

The purpose of this API is to provide structured Monster Hunter World game data
(monsters, weaknesses, weapons, skills, armors, charms, decorations, builds, etc.)
from our internal database for:

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
Step 6. Import Armor Data
--------------------------------------------------

Required (first-time setup only):
- python manage.py import_armors --armors data/mhw_armors.json --reset

Optional (development / verification):
- python manage.py import_armors --armors data/mhw_armors.json --dry-run --limit 10

Notes:
- Armor import is idempotent.
- ArmorSkill join rows are rebuilt per armor to ensure consistency.

--------------------------------------------------
Step 7. Import Charm Data
--------------------------------------------------

Charm data is retrieved from mhw-db and imported into the internal database.

Step 7.1 Download charms JSON from mhw-db:
- curl -L "https://mhw-db.com/charms" -o data/mhw_charms_raw.json

Step 7.2 Import charms into the database:

Required (first-time setup only):
- python manage.py import_charms --path data/mhw_charms_raw.json --reset

Optional (re-import without reset is safe):
- python manage.py import_charms --path data/mhw_charms_raw.json

Notes:
- mhw-db represents charms as a base charm with multiple ranks.
- The import expands each rank into a separate internal Charm row.
- This makes Build linking and future stat calculation simpler and deterministic.

--------------------------------------------------
Step 8. Import Decoration Data
--------------------------------------------------

Decoration data is retrieved from mhw-db and imported into the internal database.

Step 8.1 Download decorations JSON from mhw-db:
- curl -L "https://mhw-db.com/decorations" -o data/mhw_decorations_raw.json

Step 8.2 Import decorations into the database:

Required (first-time setup only):
- python manage.py import_decorations --path data/mhw_decorations_raw.json --reset

Optional (re-import without reset is safe):
- python manage.py import_decorations --path data/mhw_decorations_raw.json

Notes:
- Decorations are imported as standalone entities.
- Skill linkage may be deferred if referenced skills are not yet resolvable.
- Final skill effects are expected to be calculated in the Build Stats layer.

--------------------------------------------------
Step 9. Run Server
--------------------------------------------------

- python manage.py runserver

--------------------------------------------------
Step 10. Verify API Endpoints
--------------------------------------------------

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/monsters/paged/
- GET /api/v1/mhw/weapons/
- GET /api/v1/mhw/weapons/paged/
- GET /api/v1/mhw/skills/
- GET /api/v1/mhw/skills/paged/
- GET /api/v1/mhw/armors/
- GET /api/v1/mhw/armors/paged/
- GET /api/v1/mhw/charms/
- GET /api/v1/mhw/charms/paged/
- GET /api/v1/mhw/charms/{id}/
- GET /api/v1/mhw/decorations/
- GET /api/v1/mhw/decorations/paged/
- GET /api/v1/mhw/decorations/{id}/
- GET /api/v1/mhw/builds/
- GET /api/v1/mhw/builds/paged/
- GET /api/v1/mhw/builds/{id}/
- GET /api/v1/mhw/builds/{id}/stats/

--------------------------------------------------
Step 11. Run Backend Tests (Recommended)
--------------------------------------------------

- python manage.py test MonsterHunterWorld

==================================================
4. Import Pipeline – Stability Design
==================================================

The import pipeline is intentionally defensive to handle real-world data issues.

Design Goals:
- One bad record must not crash the entire import
- Duplicate data must never cause UNIQUE constraint failures
- Re-importing data must be safe and idempotent
- Internal database is the single source of truth

Key Design Decisions:
- Per-entity transaction isolation
- In-memory deduplication before database insertion
- Deduplication uses the same unique keys as the database schema
- Child records (weaknesses, armor skills, charm skills, decoration skills)
  are replaced per parent entity when applicable

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

--------------------------------------------------
5.3 Weapon
--------------------------------------------------

Fields:
- id (integer)
- external_id (integer, unique)
- name (string)
- weapon_type (string)
- rarity (integer)
- attack_raw (integer)
- attack_display (integer)
- affinity (integer)
- element (string, optional)
- element_damage (integer, optional)
- elderseal (string, optional)

--------------------------------------------------
5.4 Skill
--------------------------------------------------

Fields:
- id (integer)
- external_id (integer, unique)
- name (string)
- description (string)
- max_level (integer)

--------------------------------------------------
5.5 Armor
--------------------------------------------------

Fields:
- id (integer)
- external_id (integer, unique)
- name (string)
- armor_type (string)
- rarity (integer)
- defense_base (integer)
- defense_max (integer)
- defense_augmented (integer)
- slot_1 (integer)
- slot_2 (integer)
- slot_3 (integer)

--------------------------------------------------
5.6 Charm
--------------------------------------------------

Represents a single charm rank.

Fields:
- id (integer)
- external_id (integer, unique)
- name (string)
- rarity (integer, optional)

--------------------------------------------------
5.7 Decoration
--------------------------------------------------

Represents a single decoration jewel.

Fields:
- id (integer)
- external_id (integer, unique)
- name (string)
- rarity (integer)

--------------------------------------------------
5.8 Build
--------------------------------------------------

Represents a user-created build.

Fields:
- id (integer)
- name (string)
- description (string)
- weapon (optional)
- charm (optional)
- armor_pieces (0..N)
- decorations (0..N)
- created_at (datetime)
- updated_at (datetime)

--------------------------------------------------
5.9 Build Stats (Calculated Results)
--------------------------------------------------

Build stats endpoint provides a computed view for a build.
Currently the implementation is a placeholder, but the JSON response contract is fixed.

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
7.1 Monsters
--------------------------------------------------

GET /monsters/
GET /monsters/paged/
GET /monsters/{id}/

--------------------------------------------------
7.2 Weapons
--------------------------------------------------

GET /weapons/
GET /weapons/paged/
GET /weapons/{id}/

--------------------------------------------------
7.3 Skills
--------------------------------------------------

GET /skills/
GET /skills/paged/
GET /skills/{id}/

--------------------------------------------------
7.4 Armors
--------------------------------------------------

GET /armors/
GET /armors/paged/
GET /armors/{id}/

--------------------------------------------------
7.5 Charms
--------------------------------------------------

GET /charms/
GET /charms/paged/
GET /charms/{id}/

--------------------------------------------------
7.6 Decorations
--------------------------------------------------

GET /decorations/
GET /decorations/paged/
GET /decorations/{id}/

--------------------------------------------------
7.7 Builds
--------------------------------------------------

GET /builds/
POST /builds/

GET /builds/paged/
GET /builds/{id}/
PATCH /builds/{id}/
PUT /builds/{id}/
DELETE /builds/{id}/

--------------------------------------------------
7.8 Build Stats (Calculated View – Placeholder Contract)
--------------------------------------------------

GET /builds/{id}/stats/

==================================================
8. API Contract Rules
==================================================

This document is an API contract.

- Any API change must update this document
- Breaking changes require an API version bump (v2)

==================================================
9. FAQ
==================================================

Q: Decorations have no linked skills?
A: This is expected. Skill effects are calculated in the Build Stats layer.

==================================================
10. Future Extensions
==================================================

- Decoration skill resolution
- Conditional skill logic
- Real build stat calculations
- Build sharing / voting

==================================================
11. Contact
==================================================

For backend or data-related questions,
contact the backend/database maintainer.
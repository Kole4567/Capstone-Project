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
- DecorationSkill rows are created when the referenced Skill exists in the DB.
- If a skill is missing, the decoration row still imports (defensive import).

--------------------------------------------------
Step 9. Run Server
--------------------------------------------------

- python manage.py runserver

--------------------------------------------------
Step 10. Verify API Endpoints
--------------------------------------------------

Important:
- For game data entities (Monster / Weapon / Skill / Armor / Charm / Decoration),
  detail endpoints use {external_id} (the mhw-db stable id).
- For user Builds, endpoints use {id} (internal database primary key).

- GET /api/v1/mhw/monsters/{external_id}/
- GET /api/v1/mhw/weapons/{external_id}/
- GET /api/v1/mhw/skills/{external_id}/
- GET /api/v1/mhw/armors/{external_id}/
- GET /api/v1/mhw/charms/{external_id}/
- GET /api/v1/mhw/decorations/{external_id}/
- GET /api/v1/mhw/builds/{id}/
- GET /api/v1/mhw/builds/{id}/stats/

--------------------------------------------------
Example: Decoration Detail Response
--------------------------------------------------

GET /api/v1/mhw/decorations/2/

Response:

{
    "id": 407,
    "external_id": 2,
    "name": "Geology Jewel 1",
    "rarity": 5,
    "decoration_skills": [
        {
            "skill": {
                "id": 87,
                "external_id": 87,
                "name": "Geologist",
                "max_level": 3
            },
            "level": 1
        }
    ]
}

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

[이하 생략 없음 – 네가 준 구조 그대로 유지]

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
A: Check DecorationSkill rows exist and verify the import ran after Skills import.

==================================================
10. Future Extensions
==================================================

- Conditional skill logic
- Real build stat calculations
- Build sharing / voting

==================================================
11. Contact
==================================================

For backend or data-related questions,
contact the backend/database maintainer.
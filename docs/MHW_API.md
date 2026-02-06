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

This command:
- Deletes existing monster and weakness data
- Imports a clean, normalized dataset
- Ensures consistent data across all team members

--------------------------------------------------
Step 4. Run Server
--------------------------------------------------

- python manage.py runserver

--------------------------------------------------
Step 5. Verify API Endpoints
--------------------------------------------------

Browser or curl tests:

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/monsters/paged/
- GET /api/v1/mhw/monsters/{id}/

Example:
- curl "http://127.0.0.1:8000/api/v1/mhw/monsters/?element=Fire&min_stars=2"

--------------------------------------------------
Step 6. Run Backend Tests (Recommended)
--------------------------------------------------

- python manage.py test MonsterHunterWorld

These tests verify:
- Import pipeline stability
- Schema constraints
- API response correctness
- Duplicate prevention under joins

==================================================
4. Import Pipeline – Stability Design
==================================================

The import pipeline is intentionally defensive to handle real-world data issues.

Design Goals
- One bad record must not crash the entire import
- Partial data should be tolerated when possible
- Re-import must always result in a clean database
- Internal DB is the single source of truth

Key Design Decisions
- All JSON access uses safe parsing (.get)
- Multiple source formats are detected heuristically
- Weaknesses are fully replaced per monster on each import
- Invalid star values are skipped
- Reset + import runs inside a transaction

Safety Options
- --dry-run validates without DB writes
- --limit imports only the first N monsters

==================================================
5. Core Data Models (Conceptual)
==================================================

--------------------------------------------------
5.1 Monster
--------------------------------------------------

Represents a huntable monster.

Fields
- id (integer): Internal database ID
- external_id (integer): Stable ID from mhw-db (unique, non-null)
- name (string)
- monster_type (string)
- is_elder_dragon (boolean)

Notes
- external_id is required for safe re-import and upsert behavior
- API routing always uses internal id

--------------------------------------------------
5.2 MonsterWeakness
--------------------------------------------------

Represents elemental or status weaknesses.

Fields
- kind (string): "element" or "ailment"
- name (string)
- stars (integer, 1–3)
- condition (string, optional)

Design Notes
- Stars are constrained at DB level (1–3 only)
- Condition is preserved to retain gameplay context
- Multiple weaknesses may exist for same element with different conditions

==================================================
6. API Documentation (Swagger / OpenAPI)
==================================================

Auto-generated documentation endpoints:

- OpenAPI Schema:
  http://127.0.0.1:8000/api/schema/

- Swagger UI:
  http://127.0.0.1:8000/api/docs/

- Redoc:
  http://127.0.0.1:8000/api/redoc/

==================================================
7. API Endpoints
==================================================

Base URL:
/api/v1/mhw/

--------------------------------------------------
7.1 Get All Monsters
--------------------------------------------------

GET /api/v1/mhw/monsters/

Returns a raw JSON array (no pagination).

Optional Query Parameters
- is_elder_dragon (boolean)
- element (string)
- min_stars (integer, 1–3, requires element)
- order_by (id, name, monster_type, is_elder_dragon)

--------------------------------------------------
7.1.1 Get Monsters (Paged)
--------------------------------------------------

GET /api/v1/mhw/monsters/paged/

Pagination Parameters
- limit (default: 50)
- offset (default: 0)

Response
{
  "count": number,
  "next": string | null,
  "previous": string | null,
  "results": [...]
}

--------------------------------------------------
7.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}/

- id refers to internal Monster.id
- Includes full weakness list

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
A: Import was skipped. Run the import command with --reset.

Q: Migration failed after model changes?
A: Local dev fix:
- python manage.py flush
- python manage.py migrate
- python manage.py import_mhw --reset

Q: Why multiple weaknesses for same element?
A: Different conditions represent different gameplay mechanics.

==================================================
10. Future Extensions
==================================================

- Weapons
- Armor
- Skills
- Decorations
- Build sharing

==================================================
11. Contact
==================================================

For backend or data-related questions,
contact the backend/database maintainer.
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

--------------------------------------------------
2.1 Local Setup – Data Preparation
--------------------------------------------------

The backend does not fetch data dynamically from external sources at runtime.
All Monster Hunter World data must be imported into the internal database
before using the API.

For this final project, the full Monster Hunter World monster dataset is included
directly in the repository.

Team members do NOT need to download data from external websites.

--------------------------------------------------
2.2 Import Pipeline – Stability & Design Notes
--------------------------------------------------

The import pipeline is intentionally designed to be resilient against
real-world data inconsistencies found in external sources such as mhw-db.

This section documents the design decisions behind the import command,
so that team members understand why the implementation is defensive
and slightly more complex than a naive JSON import.

Design Goals
- The import process must never fail entirely due to a single malformed record.
- Partial or missing fields in the source data should be tolerated whenever possible.
- Re-importing data should always result in a clean and consistent database state.
- The internal database must remain the single source of truth.

Key Design Decisions
- Defensive parsing is used throughout the import command:
  - All dictionary access is guarded using .get() or safe helper functions.
  - Unexpected data types (null, dict instead of list, malformed entries) are skipped safely.
- The import command detects the input format heuristically:
  - mhw-db style data (element-based weaknesses)
  - Custom or test formats used during development
- Weakness data is always fully replaced per monster on each import:
  - Existing weaknesses are deleted
  - Normalized weaknesses are re-inserted
  - This avoids stale or duplicated weakness records

Reset Behavior
- The --reset flag deletes existing data in a safe order:
  - MonsterWeakness records are deleted before Monster records
- Reset and import operations are wrapped in a single database transaction
  to prevent partially deleted or partially imported states.

Safety & Testing Options
- --dry-run option parses and validates input data without writing to the database
- --limit option allows importing only a subset of monsters for quick testing
- These options are intended for development and debugging only

Current Status
- Monster import: stable
- Weakness import: stable (replace strategy)
- Input format tolerance: high

Future Work
- Import performance optimizations (bulk operations)
- Schema-level constraints and indexing
- Additional data domains (weapons, armor, skills)

--------------------------------------------------
Step 1. Environment Setup
--------------------------------------------------

- git clone <repository-url>
- cd Capstone-Project/mysite
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python manage.py migrate

--------------------------------------------------
Step 2. Import Monster Data (Required)
--------------------------------------------------

Import the full monster dataset into the local database.

- python manage.py import_mhw --monsters data/mhw_monsters.json --reset

Optional (development only):
- python manage.py import_mhw --monsters data/mhw_monsters.json --dry-run --limit 10

This command:
- Clears existing monster data (when --reset is used)
- Imports all monsters and their weaknesses
- Ensures a consistent dataset across all team members

Warning:
- The --reset flag is required to avoid leftover test or partial data.
- --dry-run and --limit should only be used for local testing and debugging.

--------------------------------------------------
Step 3. Run the Server
--------------------------------------------------

- python manage.py runserver

Verify the API endpoints.

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/monsters/paged/
- GET /api/v1/mhw/monsters/{id}/

Note:
- The data file (data/mhw_monsters.json) is tracked in the repository.
- Team members only need to run the import command once per local database.

==================================================
3. Core Data Models (Conceptual)
==================================================

--------------------------------------------------
3.1 Monster
--------------------------------------------------

Represents a huntable monster.

Fields
- id (integer): Internal database ID
- external_id (integer): Stable ID sourced from mhw-db.com (unique, non-null)
- name (string): Monster name
- monster_type (string): Classification (Flying Wyvern, Elder Dragon, etc.)
- is_elder_dragon (boolean)

Notes
- external_id is treated as a required, unique identifier for reliable re-imports.
- The internal id field should be used for API routing.

--------------------------------------------------
3.2 Element
--------------------------------------------------

Represents an elemental damage type.

Examples
- Fire
- Water
- Thunder
- Ice
- Dragon

--------------------------------------------------
3.3 MonsterWeakness
--------------------------------------------------

Represents a monster’s elemental or status weakness.

Fields
- kind (string): "element" or "ailment"
- name (string): Element or ailment name
- stars (integer): Weakness level (1–3, where 3 is strongest)
- condition (string, optional): Conditional weakness description

Interpretation
- Higher stars = higher effectiveness
- stars are guaranteed to be within the 1–3 range
- Weakness records with invalid or unknown star values are not stored
- Only "element" weaknesses should be used for weapon-element matching

==================================================
4. API Documentation (OpenAPI / Swagger)
==================================================

This backend provides an auto-generated OpenAPI schema and interactive API
documentation to assist frontend development and API exploration.

Available Endpoints

- OpenAPI Schema (JSON):
  http://127.0.0.1:8000/api/schema/

- Swagger UI (interactive documentation):
  http://127.0.0.1:8000/api/docs/

- Redoc (read-only documentation):
  http://127.0.0.1:8000/api/redoc/

Notes
- Accessing /api/schema/ may display raw JSON or trigger a file download.
  This behavior is expected.
- Swagger UI (/api/docs/) is recommended for local development and testing.
- These documentation endpoints are generated directly from the backend
  configuration and always reflect the current API behavior.

==================================================
5. API Endpoints
==================================================

Base URL
/api/v1/mhw/

--------------------------------------------------
5.1 Get All Monsters
--------------------------------------------------

GET /api/v1/mhw/monsters/

Returns a list of all monsters as a raw JSON array.

Response Example

[
  {
    "id": 1,
    "external_id": 1,
    "name": "Rathalos",
    "monster_type": "Flying Wyvern",
    "is_elder_dragon": false
  },
  {
    "id": 2,
    "external_id": 2,
    "name": "Nergigante",
    "monster_type": "Elder Dragon",
    "is_elder_dragon": true
  }
]

Note
- This endpoint intentionally returns a raw JSON array.
- Pagination is NOT applied to preserve the original v1 contract.
- Use the paged endpoint below when pagination is required.

--------------------------------------------------
Optional Query Parameters
--------------------------------------------------

- is_elder_dragon (boolean)
  Filters monsters by Elder Dragon status.

- element (string)
  Filters monsters that have a matching elemental weakness.
  Only weaknesses with kind="element" are considered.

- min_stars (integer, 1–3)
  Filters by minimum weakness stars.
  Requires element parameter.

- Invalid or out-of-range values are ignored.

--------------------------------------------------
5.1.1 Get All Monsters (Paged)
--------------------------------------------------

GET /api/v1/mhw/monsters/paged/

Returns the same monster list as /monsters/ but with pagination.

Pagination Parameters

- limit (integer, default: 50)
- offset (integer, default: 0)

Response Format

{
  "count": <integer>,
  "next": <string|null>,
  "previous": <string|null>,
  "results": [ <monster>, ... ]
}

--------------------------------------------------
5.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}/

Important
- {id} refers to the internal database ID (Monster.id)
- NOT the mhw-db external_id

Returns a single monster with its weaknesses.

==================================================
6. API Contract Rules
==================================================

This document is an API contract.

- Any API changes must update this document.
- Breaking changes require version updates (e.g. v2).

==================================================
7. Future Extensions (Planned)
==================================================

- Weapons and weapon types
- Armor and skills
- Decorations and slots
- Build saving and sharing

==================================================
8. Contact
==================================================

For backend or data-related questions,
please contact the backend/database maintainer.
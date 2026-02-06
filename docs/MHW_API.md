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

This command:
- Clears existing monster data
- Imports all monsters and their weaknesses
- Ensures a consistent dataset across all team members

Warning:
- The --reset flag is required to avoid leftover test or partial data.

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
- external_id (integer): ID from mhw-db.com
- name (string): Monster name
- monster_type (string): Classification (Flying Wyvern, Elder Dragon, etc.)
- is_elder_dragon (boolean)

Notes
- external_id is sourced from mhw-db.com and treated as stable within this project.

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
- stars range is guaranteed to be between 1 and 3
- Only "element" weaknesses should be used for weapon-element matching

==================================================
4. API Endpoints
==================================================

Base URL
/api/v1/mhw/

--------------------------------------------------
4.1 Get All Monsters
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
  Example:
  /api/v1/mhw/monsters/?is_elder_dragon=true

- element (string)
  Filters monsters that have a matching elemental weakness.
  Only weaknesses with kind="element" are considered.
  Example:
  /api/v1/mhw/monsters/?element=Fire

- min_stars (integer, 1–3)
  Filters by minimum weakness stars.
  Requires element parameter.
  Example:
  /api/v1/mhw/monsters/?element=Fire&min_stars=2

- min_stars is only applied when element is provided.

- Invalid or out-of-range query parameter values are ignored and do not produce errors.

--------------------------------------------------
4.1.1 Get All Monsters (Paged)
--------------------------------------------------

GET /api/v1/mhw/monsters/paged/

Returns the same monster list as /monsters/ but with pagination.

This endpoint exists to support large result sets without breaking the v1
response format of /monsters/.

Pagination Parameters (Limit / Offset)

- limit (integer)
  Number of results to return.
  Default: 50

- offset (integer)
  Starting index for results.
  Default: 0

Response Format

{
  "count": <integer>,
  "next": <string|null>,
  "previous": <string|null>,
  "results": [ <monster>, ... ]
}

Example

- curl "http://127.0.0.1:8000/api/v1/mhw/monsters/paged/?limit=5&offset=0"

All filtering and ordering parameters supported by /monsters/ are also supported
by this endpoint.

--------------------------------------------------
4.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}/

Important
- {id} refers to the internal database ID (Monster.id)
- NOT the mhw-db external_id
- Always retrieve the id from the monster list endpoint first

Returns a single monster with its weaknesses.

Response Example

{
  "id": 1,
  "external_id": 1,
  "name": "Rathalos",
  "monster_type": "Flying Wyvern",
  "is_elder_dragon": false,
  "weaknesses": [
    {
      "kind": "element",
      "name": "Dragon",
      "stars": 3,
      "condition": null
    },
    {
      "kind": "element",
      "name": "Thunder",
      "stars": 2,
      "condition": null
    },
    {
      "kind": "ailment",
      "name": "Poison",
      "stars": 1,
      "condition": null
    }
  ]
}

--------------------------------------------------
4.2.1 Quick Test (Local)
--------------------------------------------------

Start server
- python manage.py runserver

Get monster list
- curl http://127.0.0.1:8000/api/v1/mhw/monsters/

Get monster list (paged)
- curl http://127.0.0.1:8000/api/v1/mhw/monsters/paged/?limit=5&offset=0

Get monster detail (example: id = 5)
- curl http://127.0.0.1:8000/api/v1/mhw/monsters/5/

Expected Results
- Monster list returns many monsters
- Paged list returns count, next/previous, and results
- Monster detail returns a weaknesses array

If only a few monsters appear:
- Re-run the import command with --reset

--------------------------------------------------
4.2.2 Testing Dataset (Optional)
--------------------------------------------------

A small test dataset is included for development purposes only.

- python manage.py import_mhw --monsters test_monsters.json

Warning
- test_monsters.json contains only a small subset of monsters
- Using this file will result in limited API data
- Do NOT use for frontend or recommendation development

==================================================
4.3 Error Responses
==================================================

404 Not Found

Returned when the requested resource does not exist.

Example

{
  "error": "Monster not found"
}

==================================================
5. Usage Notes
==================================================

For Frontend Team
- Use name for display purposes
- Convert stars into visual indicators (e.g. star icons)
- Elder Dragons can be highlighted using is_elder_dragon
- Do not derive game logic from display values

For Recommendation Algorithm Team
- Use element-type weaknesses only
- Higher stars should be treated as higher weight
- Monsters may have multiple effective elements
- Do not hardcode element effectiveness outside the API

==================================================
6. API Contract Rules
==================================================

This document is an API contract.

- Any API changes must update this document
- Breaking changes require version updates (e.g. v2)

External ID Policy
- external_id is an integer (mhw-db numeric ID)
- Human-readable identifiers will be added as new fields if needed

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
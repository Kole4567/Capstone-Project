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

2.1 Local Setup – Data Preparation

The backend does not fetch data dynamically from external sources at runtime.
All Monster Hunter World data must be imported into the internal database
before using the API.

For this final project, the Monster Hunter World monster dataset is included
directly in the repository to simplify team setup.

Team members do NOT need to download data from external websites.

Step 1. Environment Setup

- git clone <repository-url>
- cd Capstone-Project/mysite
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python manage.py migrate

Step 2. Import Monster Data

Import the included monster dataset into the local database.

- python manage.py import_mhw --monsters data/mhw_monsters.json --reset

This command populates the database with all monsters and their weaknesses.

Step 3. Run the Server

Start the development server.

- python manage.py runserver

Verify the API endpoints.

- GET /api/v1/mhw/monsters/
- GET /api/v1/mhw/monsters/{id}/

Note:
- The data file (data/mhw_monsters.json) is tracked in the repository for
  final project convenience.
- Team members only need to run the import command once.

==================================================
3. Core Data Models (Conceptual)
==================================================

3.1 Monster

Represents a huntable monster.

Fields
- id (integer): Internal database ID
- external_id (integer): ID from mhw-db.com
- name (string): Monster name
- monster_type (string): Classification (Flying Wyvern, Elder Dragon, etc.)
- is_elder_dragon (boolean)
- external_id is a numeric ID sourced from mhw-db.com and is treated as stable within this project.


--------------------------------------------------

3.2 Element

Represents an elemental damage type.

Examples
- Fire
- Water
- Thunder
- Ice
- Dragon

--------------------------------------------------

3.3 MonsterWeakness

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

Returns a list of all monsters.

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

--------------------------------------------------
4.2 Get Monster Detail
--------------------------------------------------

GET /api/v1/mhw/monsters/{id}/

Important
- {id} refers to the internal database ID (Monster.id), not the mhw-db external_id.
- To fetch a specific monster, first call GET /api/v1/mhw/monsters/ and use the returned "id" field.

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

This section provides a minimal verification workflow to confirm that the API
is running and returning data according to this contract.

Start server
- cd mysite
- source venv/bin/activate
- python manage.py runserver

Get monster list
- curl http://127.0.0.1:8000/api/v1/mhw/monsters/

Get monster detail (example: id = 59)
- curl http://127.0.0.1:8000/api/v1/mhw/monsters/59/

Expected Results
- GET /api/v1/mhw/monsters/ returns a JSON array of monsters.
- GET /api/v1/mhw/monsters/{id}/ returns a JSON object including a weaknesses array.

Note
If the database is empty, run the import command before testing.

--------------------------------------------------
4.2.2 Importing Data (Required for Local Testing)
--------------------------------------------------

The backend does not fetch data dynamically from external sources.
All data must be imported into the internal database.

Run migrations
- python manage.py migrate

Import monster data
- python manage.py import_mhw --monsters test_monsters.json

After importing, re-run the API requests in section 4.2.1.

--------------------------------------------------
4.3 Error Responses
--------------------------------------------------

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
- Use name for display purposes.
- Convert stars into visual indicators (e.g. star icons).
- Elder Dragons can be highlighted using is_elder_dragon.
- Do not derive game logic from display values.
- All calculations must rely on raw API fields.

For Recommendation Algorithm Team
- Use element-type weaknesses only when matching weapons.
- Higher stars values should be treated as higher weight.
- Monsters may have multiple effective elements.
- Do not hardcode element effectiveness outside the API.

==================================================
6. API Contract Rules
==================================================

This document is an API contract.

- If API responses or data structures change, this document must be updated.
- Frontend and recommendation logic depend on the structures defined here.
- Breaking changes require version updates (e.g. v2).

External ID Policy

- external_id is an integer (mhw-db numeric ID).
- If a human-readable identifier is needed later, a new field (e.g. external_slug) will be added instead of changing the type.

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
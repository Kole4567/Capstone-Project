Monster Hunter World API Documentation

API Version: v1

1. Overview

This document describes the Monster Hunter World (MHW) Backend API.

The purpose of this API is to provide structured Monster Hunter World game data
(monsters, weaknesses, weapons, etc.) from our internal database for:

- Frontend UI rendering
- Build recommendation algorithms
- Custom build creation and sharing

This API acts as the single source of truth for game data within this project.

2. Data Source

All Monster Hunter World game data is originally sourced from:

https://docs.mhw-db.com/

The backend imports and stores this data into our own database.

Important
- Frontend and recommendation logic must NOT call mhw-db.com directly.
- Always use the internal API endpoints described in this document.
- This ensures stability, performance, and consistent data formatting.

3. Core Data Models (Conceptual)

3.1 Monster

Represents a huntable monster.

Fields
- id (integer): Internal database ID
- external_id (string): ID from mhw-db.com
- name (string): Monster name
- monster_type (string): Classification (Flying Wyvern, Elder Dragon, etc.)
- is_elder_dragon (boolean)

3.2 Element

Represents an elemental damage type.

Examples
- Fire
- Water
- Thunder
- Ice
- Dragon

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

4. API Endpoints

Base URL
/api/v1/mhw/

4.1 Get All Monsters

GET /api/v1/mhw/monsters/

Returns a list of all monsters.

Response Example
[
  {
    "id": 1,
    "external_id": "rathalos",
    "name": "Rathalos",
    "is_elder_dragon": false
  },
  {
    "id": 2,
    "external_id": "nergigante",
    "name": "Nergigante",
    "is_elder_dragon": true
  }
]

4.2 Get Monster Detail

GET /api/v1/mhw/monsters/{id}/

Returns a single monster with its weaknesses.

Response Example
{
  "id": 1,
  "external_id": "rathalos",
  "name": "Rathalos",
  "is_elder_dragon": false,
  "weaknesses": [
    {
      "kind": "element",
      "name": "Dragon",
      "stars": 3
    },
    {
      "kind": "element",
      "name": "Thunder",
      "stars": 2
    },
    {
      "kind": "ailment",
      "name": "Poison",
      "stars": 1
    }
  ]
}

4.3 Error Responses

404 Not Found  
Returned when the requested resource does not exist.

Example
{
  "error": "Monster not found"
}

5. Usage Notes

For Frontend Team
- Use name for display purposes.
- Convert stars into visual indicators (e.g. ⭐ icons).
- Elder Dragons can be highlighted using is_elder_dragon.
- Do not derive game logic from display values.
- All calculations must rely on raw API fields.

For Recommendation Algorithm Team
- Use element-type weaknesses only when matching weapons.
- Higher stars should be treated as higher weight.
- Monsters may have multiple effective elements.
- Do not hardcode element effectiveness outside the API.

6. API Contract Rules

This document is an API contract.

- If API responses or data structures change, this document must be updated.
- Frontend and recommendation logic depend on the structures defined here.
- Breaking changes require version updates (e.g. v2).

7. Future Extensions (Planned)

- Weapons and weapon types
- Armor and skills
- Decorations and slots
- Build saving and sharing

8. Contact

For backend or data-related questions,
please contact the backend/database maintainer.
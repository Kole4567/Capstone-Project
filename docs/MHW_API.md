Monster Hunter World API Documentation
API Version: v1 (Implementation-Aligned)

==================================================
1. Overview
==================================================

This document describes the fully implemented Monster Hunter World (MHW) Backend API.

This backend is NOT a thin wrapper over mhw-db.
It is an internally controlled, normalized, defensive data system.

The backend:

- Imports mhw-db raw JSON
- Normalizes data into internal schema
- Rebuilds relational joins (ArmorSkill, CharmSkill, etc.)
- Provides stable API contracts
- Computes Build Stats internally
- Supports external_id-based linking (MHW-style)

This API is the SINGLE SOURCE OF TRUTH.

Frontend and recommendation logic MUST ONLY use this backend.

==================================================
2. Architecture Philosophy
==================================================

This backend is designed around:

1) Idempotent imports
2) Defensive JSON parsing
3) Replace semantics for child rows
4) Stable API contracts
5) Internal computation layer for builds

We DO NOT rely on mhw-db structure at runtime.

==================================================
3. Full Local Setup (Team Standard)
==================================================

Step 1 — Clone & Environment

git clone <repository-url>
cd Capstone-Project/mysite
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

--------------------------------------------------

Step 2 — Database

python manage.py migrate

Optional full reset:
python manage.py flush

--------------------------------------------------

Step 3 — Import Order (IMPORTANT)

The import order matters because of foreign keys.

1) Monsters
python manage.py import_mhw --monsters data/mhw_monsters.json --reset

2) Weapons
python manage.py import_weapons --weapons data/mhw_weapons.json --reset

3) Skills
python manage.py import_skills --skills data/mhw_skills.json --reset

4) Armors (REQUIRES Skills already imported)
python manage.py import_armors --armors data/mhw_armors.json --reset

5) Armor Sets / Set Bonuses
python manage.py import_set_bonuses --sets data/mhw_armor_sets.json --reset

6) Charms (REQUIRES Skills)
python manage.py import_charms --charms data/mhw_charms_raw.json --reset

7) Decorations (REQUIRES Skills)
python manage.py import_decorations --decorations data/mhw_decorations_raw.json --reset

--------------------------------------------------

Step 4 — Run Server

python manage.py runserver

==================================================
4. Import Pipeline – What Was Actually Built
==================================================

The import system is NOT a naive insert.

It includes:

✔ Defensive JSON shape detection
✔ Support for embedded skill payloads OR skill id references
✔ update_or_create for idempotency
✔ Per-parent child row replacement
✔ external_id as unique stable key

--------------------------------------------------
4.1 Armor Import – Critical Design
--------------------------------------------------

The armor import does ALL of the following:

1) Reads defense:
   defense.base
   defense.max
   defense.augmented

2) Reads slots:
   slots: [{rank:1}, {rank:2}]

3) Reads resistances:
   fire
   water
   thunder
   ice
   dragon

4) Extracts armorSet:
   armor_set_external_id
   armor_set_name
   armor_set_rank
   armor_set_bonus_external_id

5) Rebuilds ArmorSkill table:

   For each armor:
   - Deletes existing ArmorSkill rows
   - Recreates from JSON
   - Resolves Skill by external_id
   - Creates Skill if embedded payload exists

This guarantees consistency and no duplicate skill stacking.

--------------------------------------------------
4.2 ArmorSkill Relationship
--------------------------------------------------

ArmorSkill is a join table:

Armor 1 ---- N ArmorSkill N ---- 1 Skill

Fields:
- armor_id
- skill_id
- level

Import uses REPLACE semantics per armor.

--------------------------------------------------
4.3 Charm Import
--------------------------------------------------

Charm JSON includes ranks.

Import expands each rank into a separate Charm row.

CharmSkill join table:

Charm 1 ---- N CharmSkill N ---- 1 Skill

--------------------------------------------------
4.4 Decoration Import
--------------------------------------------------

Decoration is standalone.
DecorationSkill links decoration to skill.

BuildDecoration stores:

- slot (head/chest/gloves/waist/legs/weapon)
- socket_index (1..3)
- decoration_id

==================================================
5. Core Models (Real Implementation View)
==================================================

Monster
- id
- external_id (unique)
- name
- monster_type
- is_elder_dragon

MonsterWeakness
- monster (FK)
- kind
- name
- stars
- condition
- condition_key

Weapon
- id
- external_id (unique)
- name
- weapon_type
- rarity
- attack_raw
- attack_display
- affinity
- element
- element_damage
- elderseal

Skill
- id
- external_id (unique)
- name
- description
- max_level

Armor
- id
- external_id (unique)
- name
- armor_type
- rarity
- defense_base
- defense_max
- defense_augmented
- slot_1
- slot_2
- slot_3
- res_fire
- res_water
- res_thunder
- res_ice
- res_dragon
- armor_set_external_id
- armor_set_name
- armor_set_rank
- armor_set_bonus_external_id

ArmorSkill
- armor (FK)
- skill (FK)
- level

Charm
- id
- external_id
- name
- rarity

CharmSkill
- charm (FK)
- skill (FK)
- level

Decoration
- id
- external_id
- name
- rarity

DecorationSkill
- decoration (FK)
- skill (FK)
- level

Build
- id
- name
- description
- weapon (nullable FK)
- charm (nullable FK)
- created_at
- updated_at

BuildArmorPiece
- build (FK)
- slot
- armor (FK)

BuildDecoration
- build (FK)
- slot
- socket_index
- decoration (FK)

==================================================
6. Build Create/Update Logic (IMPORTANT)
==================================================

BuildCreateUpdateSerializer supports TWO payload styles:

Style A (internal id):
"armor_pieces": [
  {"slot":"head","armor_id":5032}
]

Style B (MHW-style external id):
"armors": {
  "head": 1,
  "chest": 2
}

Replace semantics:

- If "armors" exists → delete all existing armor pieces → rebuild
- If "armor_pieces" exists → delete all → rebuild
- If "decorations" exists → delete all → rebuild

Weapon supports:
- weapon_id
- weapon_external_id

Charm supports:
- charm_id
- charm_external_id

==================================================
7. Build Stats Layer (Implemented)
==================================================

GET /api/v1/mhw/builds/{id}/stats/

This endpoint computes:

1) Weapon stats
   - attack_raw
   - attack_display
   - affinity
   - element

2) Armor defense sum
   defense = sum(defense_base)

3) Resistances sum
   res_fire = sum(res_fire)
   res_water = sum(res_water)
   etc.

4) Skill aggregation
   Aggregates levels from:
   - ArmorSkill
   - CharmSkill
   - DecorationSkill
   - SetBonusRank (active thresholds)

IMPORTANT CONTRACT NOTE (v1):
- In the Build Stats response, "skills[].skill_id" refers to Skill.external_id (mhw-db stable ID),
  NOT the internal database primary key Skill.id.

Returns stable contract:

{
  "build_id": 5,
  "stats": {
    "attack": { "raw": 80, "display": 384 },
    "affinity": 0,
    "element": { "type": null, "value": 0 },
    "defense": 10,
    "resistances": {
      "fire": 10,
      "water": 0,
      "thunder": 0,
      "ice": 0,
      "dragon": 0
    }
  },
  "skills": [
    {
      "skill_id": 429,
      "name": "Hunger Resistance",
      "level": 1,
      "max_level": 3,
      "sources": { "armor": 1 }
    }
  ],
  "set_bonuses": [
    {
      "name": "Leather",
      "pieces": 5,
      "active": false
    }
  ]
}

This JSON structure is FIXED for API v1.

==================================================
8. What Has Been Fully Implemented
==================================================

✔ ArmorSkill join rebuild logic
✔ Skill max_level derivation from ranks
✔ Armor resistances storage
✔ Armor set metadata storage
✔ Build weapon integration
✔ external_id linking support
✔ Replace semantics for build update
✔ Defensive import parsing
✔ Idempotent imports
✔ Build stats calculation (weapon + armor + resistances + skills + set bonuses)

==================================================
9. What Is NOT Yet Implemented
==================================================

- True damage calculation
- Conditional skill activation
- Decoration size validation
- Advanced set bonus scaling logic
- Skill caps beyond max_level enforcement

==================================================
10. API Contract Rule
==================================================

If you change:

- JSON response shape
- field names
- stat computation logic

You MUST update this document.

Breaking change → API v2.

==================================================
END OF DOCUMENT
==================================================
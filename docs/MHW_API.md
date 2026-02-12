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

1) Monsters
python manage.py import_mhw --monsters data/mhw_monsters.json --reset

2) Weapons
python manage.py import_weapons --weapons data/mhw_weapons.json --reset

3) Skills
python manage.py import_skills --skills data/mhw_skills.json --reset

4) Armors (REQUIRES Skills)
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
4. Import Pipeline – What Was Built
==================================================

✔ Defensive JSON shape detection
✔ update_or_create for idempotency
✔ Per-parent child row replacement
✔ external_id as unique stable key
✔ Offensive identity extraction for Monsters
✔ Element & damage extraction for Weapons
✔ Resistance extraction for Armors

--------------------------------------------------
4.1 Monster Import
--------------------------------------------------

Extracted fields:

- external_id
- name
- monster_type
- is_elder_dragon
- primary_element
- primary_ailment

primary_element:
Derived from monster["elements"][0].
Only FIRST element stored (v1 design).

primary_ailment:
Derived from monster["ailments"][0]["name"].
Only FIRST ailment stored.

Weakness handling:
- Replace all MonsterWeakness rows per monster
- Deduplicate by (monster, kind, name, condition_key)
- Keep highest star value

--------------------------------------------------
4.2 Weapon Import
--------------------------------------------------

Extracted fields:

- external_id
- weapon_type
- rarity
- attack_raw
- attack_display
- affinity
- elderseal
- element
- element_damage

If multiple elements exist,
ONLY FIRST element entry is stored (v1).

Example:

"elements": [
  { "type": "fire", "damage": 240 }
]

Stored as:

element = "Fire"
element_damage = 240

--------------------------------------------------
4.3 Armor Import
--------------------------------------------------

Defense:
- defense_base
- defense_max
- defense_augmented

Slots:
- slot_1
- slot_2
- slot_3

Resistances:
- res_fire
- res_water
- res_thunder
- res_ice
- res_dragon

Set metadata:
- armor_set_external_id
- armor_set_name
- armor_set_rank
- armor_set_bonus_external_id

ArmorSkill:
- Delete all per armor
- Recreate from JSON
- Resolve Skill by external_id

--------------------------------------------------
4.4 Charm Import
--------------------------------------------------

Each charm rank becomes a separate Charm row.

CharmSkill join table:

Charm 1 ---- N CharmSkill N ---- 1 Skill

--------------------------------------------------
4.5 Decoration Import
--------------------------------------------------

DecorationSkill links decoration to skill.

BuildDecoration stores:

- slot (head/chest/gloves/waist/legs/weapon)
- socket_index (1..3)
- decoration_id

==================================================
5. Core Models (Implementation View)
==================================================

Monster
- id (internal PK)
- external_id (unique)
- name
- monster_type
- is_elder_dragon
- primary_element
- primary_ailment

MonsterWeakness
- monster (FK)
- kind
- name
- stars
- condition
- condition_key

Weapon
- id
- external_id
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
- external_id
- name
- description
- max_level

Armor
- id
- external_id
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
6. Build Create/Update Logic
==================================================

Supports two payload styles:

Style A:
"armor_pieces": [
  {"slot":"head","armor_id":5032}
]

Style B:
"armors": {
  "head": 1,
  "chest": 2
}

Replace semantics:
If armor list present → delete all → rebuild
If decorations present → delete all → rebuild

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

Computes:

1) Weapon stats
   - attack_raw
   - attack_display
   - affinity
   - element

2) Defense sum
   defense = sum(defense_base)

3) Resistance sum
   fire
   water
   thunder
   ice
   dragon

4) Skill aggregation from:
   - ArmorSkill
   - CharmSkill
   - DecorationSkill
   - SetBonusRank

IMPORTANT:

skills[].skill_id refers to Skill.external_id
NOT internal Skill.id.

Example response:

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
  ]
}

==================================================
8. ID Contract (CRITICAL)
==================================================

URL routing uses INTERNAL primary key (id).

Example:
GET /api/v1/mhw/monsters/81/

81 = internal database id

external_id is exposed for linking,
but NOT used in URL routing in v1.

==================================================
9. Not Yet Implemented
==================================================

- True damage calculation
- Conditional skill activation
- Decoration size validation
- Advanced set bonus scaling
- Damage vs monster weakness multiplier logic

==================================================
END OF DOCUMENT
==================================================
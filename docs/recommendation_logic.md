---

---

# Build Recommendation Logic — Member 3

## Overview

This module generates an optimal equipment build for a given monster by
evaluating **weapons, armor pieces, decorations, and charms** using a scoring-based algorithm.

The system considers:

* Monster weaknesses and elemental properties
* Weapon performance
* Armor defense, skills, and elemental resistances
* Decoration slot compatibility and skill synergy
* Charm skills and synergy with armor

The algorithm returns the best build configuration for the monster.

---

# Responsibilities

Member 3 is responsible for:

* Designing and implementing build optimization algorithms
* Calculating equipment scores based on monster attributes
* Integrating Django ORM data into the algorithm
* Implementing decoration slot optimization
* Providing results that can be used by backend APIs

---

# File Structure

```
MonsterHunterWorld/
    build_logic.py          # Core recommendation logic
    build_logic_api.py      # Django integration (API usage)
```

---

# Scoring System

The recommendation is based on a weighted scoring system.

---

# Weapon Score

Weapon score is calculated using:

1. Raw attack power
2. Elemental effectiveness against monster weakness
3. Affinity bonus

Formula:

```
Weapon Score =
    attack_raw
    + (weakness_stars × 30 if element matches)
    + (affinity × 0.25)
```

Element bonus is applied only if the weapon element matches one of the monster’s elemental weaknesses.

---

# Armor Score

Armor score considers three major factors:

1. Defense value
2. Total skill levels
3. Resistance against monster primary element

Formula:

```
Armor Score =
    defense_max
    + (sum of skill max levels × 10)
    + resistance_bonus
```

Resistance bonus rules:

* Positive resistance → resistance × 15
* Negative resistance → resistance × 30 (penalty)

The resistance type is automatically selected based on the monster’s primary element.

---

# Decoration System

Decorations are now included in the build generation process.

Decorations provide additional skills and are inserted into armor slots.

Each armor piece may contain up to **three decoration slots**.

```
slot_1
slot_2
slot_3
```

If a slot value is **0**, it means the slot cannot accept decorations.

Example:

```
slot_1 = 2
slot_2 = 1
slot_3 = 0
```

This armor can equip:

* Level 2 decoration
* Level 1 decoration
* No third decoration

---

# Decoration Slot Rules

A decoration can only be inserted if:

```
decoration_level == slot_level
```

Example:

```
Armor slot = 2
Allowed decoration = Jewel 2
```

Invalid examples:

```
slot = 2
Jewel 1 = NO
Jewel 3 = NO
```

The level is extracted from the decoration name:

```
Attack Jewel 1
Tenderizer Jewel 2
Expert Jewel 3
```

---

# Decoration Score

Decorations are evaluated using their skill strength and synergy with armor skills.

Formula:

```
Decoration Score =
    (sum of skill max levels × 8)
    + synergy_bonus
```

Synergy bonus rule:

If the decoration provides a skill already present on the armor piece:

```
+20 bonus
```

This encourages stacking related skills on the same armor part.

---

# Armor + Decoration Score

The final armor evaluation includes both base armor score and decoration bonuses.

Formula:

```
Total Armor Score =
    Armor Score
    + Decoration Scores
```

Steps:

1. Determine available armor slots
2. Find decorations with matching level
3. Score all valid decorations
4. Select the highest scoring decoration per slot
5. Add decoration score to armor score

This ensures the armor evaluation reflects its full potential when decorations are equipped.

---

# Charm Score

Charm score includes:

1. Base skill levels
2. Synergy bonus with armor skills

Formula:

```
Charm Score =
    (sum of skill max levels × 10)
    + synergy_bonus
```

If a charm contains a skill already provided by armor pieces,
a synergy bonus of **+25** is added per matching skill.

This encourages builds with strong skill stacking.

---

# Build Generation Algorithm

To reduce computational complexity, a lightweight optimization strategy is used.

---

# Steps

1. Retrieve all equipment from the database using Django ORM
2. Retrieve all decorations
3. Calculate weapon scores
4. Calculate armor scores including decoration optimization
5. Sort each armor category by score
6. Select the highest scoring armor for each body part
7. Collect armor skills
8. Select the best charm based on synergy
9. Select the best weapon
10. Return the final build

This approach avoids generating all possible combinations,
which significantly improves performance.

---

# Armor Categories

The system currently supports:

* Head
* Chest
* Legs
* Gloves
* Waist
* Charm
* Weapon

Decorations are automatically attached to each armor piece during evaluation.

---

# Output Format

The function returns a dictionary:

```python
{
    "weapon": Weapon,
    "head": Armor,
    "chest": Armor,
    "legs": Armor,
    "gloves": Armor,
    "waist": Armor,
    "charm": Charm,
    "decorations": {
        "head": [Decoration],
        "chest": [Decoration],
        "legs": [Decoration],
        "gloves": [Decoration],
        "waist": [Decoration]
    }
}
```

Each value is a Django model instance.

---

# Main Function

```
best_build_fast(monster)
```

Input:

```
monster → Monster model instance
```

Output:

```
Dictionary containing the best build configuration
```

---

# Key Design Decisions

## Performance Optimization

Instead of evaluating every possible equipment combination
(which grows exponentially), the algorithm:

* Ranks equipment individually
* Evaluates decorations per armor
* Selects top candidates directly

This significantly reduces runtime while maintaining build quality.

---

# Skill Synergy System

The system encourages builds that stack related skills.

Synergy bonuses apply between:

* Armor + Decoration
* Armor + Charm

This improves realism and aligns with common Monster Hunter build strategies.

---

# Future Improvements

Planned enhancements include:

* Generating **Top N builds instead of one**
* Implementing **skill level cap validation**
* Full **decoration optimization across the entire build**
* Weapon type filtering
* User preference weighting
* Monster behavior based optimization

---

# Integration with Backend API

This logic is designed to be called from a Django API endpoint.

Example workflow:

```
Frontend Request
      ↓
Django View
      ↓
Build Logic
      ↓
JSON Response
```

---
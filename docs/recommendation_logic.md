# Build Recommendation Logic — Member 3

## Overview

This module generates an optimal equipment build for a given monster by
evaluating weapons, armor pieces, and charms using a scoring-based algorithm.

The system considers:

* Monster weaknesses and elemental properties
* Weapon performance
* Armor defense, skills, and elemental resistances
* Charm skills and synergy with armor

The algorithm returns the best build configuration for the monster.

---

## Responsibilities

Member 3 is responsible for:

* Designing and implementing build optimization algorithms
* Calculating equipment scores based on monster attributes
* Integrating Django ORM data into the algorithm
* Providing results that can be used by backend APIs

---

## File Structure

```
MonsterHunterWorld/
    build_logic.py          # Core recommendation logic
    build_logic_api.py      # Django integration (API usage)
```

---

## Scoring System

The recommendation is based on a weighted scoring system.

### Weapon Score

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

### Armor Score

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

### Charm Score

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

## Build Generation Algorithm

To reduce computational complexity, a lightweight optimization strategy is used.

### Steps

1. Retrieve all equipment from the database using Django ORM
2. Sort each equipment category by score
3. Select the highest-scoring armor for each body part
4. Determine armor skill set
5. Select the best charm considering synergy
6. Select the best weapon
7. Return the final build

This approach avoids generating all possible combinations,
which significantly improves performance.

---

## Armor Categories

The system currently supports:

* Head
* Chest
* Legs
* Gloves
* Waist
* Charm
* Weapon

---

## Output Format

The function returns a dictionary:

```python
{
    "weapon": Weapon,
    "head": Armor,
    "chest": Armor,
    "legs": Armor,
    "gloves": Armor,
    "waist": Armor,
    "charm": Charm
}
```

Each value is a Django model instance.

---

## Main Function

```python
best_build_fast(monster)
```

Input:

* `monster` → Monster model instance

Output:

* Dictionary containing the best build configuration

---

## Key Design Decisions

### Performance Optimization

Instead of evaluating every possible combination
(which grows exponentially), the algorithm:

* Ranks equipment individually
* Selects top candidates directly

This reduces runtime dramatically while still producing high-quality builds.

### Skill Synergy System

Armor and charm skills are combined to reward:

* Skill stacking
* Consistent build themes

This makes recommendations more realistic for gameplay.

---

## Future Improvements

Planned enhancements include:

* Generating Top N builds instead of only one
* Including decoration optimization
* Considering monster behavior patterns
* Weapon type filtering
* User preference weighting

---

## Integration with Backend API

This logic is designed to be called from a Django API endpoint.

Example workflow:

```
Frontend Request → Django View → Build Logic → JSON Response
```

---

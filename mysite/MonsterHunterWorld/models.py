from django.db import models
from django.db.models import Q


# ==================================================
# Monsters
# ==================================================
class Monster(models.Model):
    """
    Monster model (core entity).

    Design notes
    - Represents a large monster in Monster Hunter World.
    - This is a core reference entity used across the API.
    - external_id comes from mhw-db and is treated as stable.

    Constraints
    - external_id must be unique to allow safe re-imports (upsert behavior).
    """

    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=120)
    monster_type = models.CharField(max_length=80)
    is_elder_dragon = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MonsterWeakness(models.Model):
    """
    Represents a monster’s elemental or status weakness.

    Design notes
    - Weaknesses are attached to monsters via FK.
    - A monster may have multiple weaknesses of the same element
      under different conditions.
    - stars represent effectiveness (1–3).

    Special handling
    - condition is optional because mhw-db sometimes omits it.
    - condition_key normalizes condition for uniqueness when condition is NULL.

    Example
    - Fire (stars=3, condition=None)
    - Ice (stars=2, condition="when enraged")
    """

    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="weaknesses",
    )

    kind = models.CharField(max_length=40)   # "element" or "ailment"
    name = models.CharField(max_length=60)   # e.g. Fire, Poison
    stars = models.PositiveSmallIntegerField()

    condition = models.CharField(max_length=200, null=True, blank=True)

    # Normalized value used only for uniqueness
    # Import code should set this consistently
    condition_key = models.CharField(max_length=200, default="", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["monster", "kind", "name", "condition_key"],
                name="uniq_monsterweakness_monster_kind_name_conditionkey",
            ),
            models.CheckConstraint(
                condition=Q(stars__gte=1) & Q(stars__lte=3),
                name="chk_monsterweakness_stars_1_3",
            ),
        ]
        indexes = [
            models.Index(fields=["monster", "kind"], name="idx_weak_monster_kind"),
            models.Index(fields=["kind", "name"], name="idx_weak_kind_name"),
            models.Index(fields=["condition_key"], name="idx_weak_condition_key"),
        ]

    def __str__(self):
        return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars})"


# ==================================================
# Weapons
# ==================================================
class Weapon(models.Model):
    """
    Weapon model (MHW Weapons MVP).

    Design goals
    - Support list/detail endpoints with minimal but useful fields.
    - Enable filtering by type, element, rarity, and attack.
    - Keep schema easy to extend later (slots, sharpness, crafting, etc.).

    Notes
    - attack_display and attack_raw are stored separately.
    - element is optional because many weapons are raw-only.
    """

    external_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=200)
    weapon_type = models.CharField(max_length=50)
    rarity = models.PositiveSmallIntegerField()

    attack_display = models.IntegerField(default=0)
    attack_raw = models.IntegerField(default=0)

    element = models.CharField(max_length=40, null=True, blank=True)
    element_damage = models.IntegerField(null=True, blank=True)

    affinity = models.SmallIntegerField(default=0)
    elderseal = models.CharField(max_length=40, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["weapon_type"], name="idx_weapon_type"),
            models.Index(fields=["element"], name="idx_weapon_element"),
            models.Index(fields=["rarity"], name="idx_weapon_rarity"),
        ]

    def __str__(self):
        return f"{self.name} ({self.weapon_type})"


# ==================================================
# Skills
# ==================================================
class Skill(models.Model):
    """
    Skill model (MHW Skills MVP).

    Design goals
    - Represent passive skills used in builds.
    - Store only high-level description and max level for MVP.
    - Allow reuse by weapons, armor, and future decorations.

    Notes
    - max_level is derived from mhw-db ranks data.
    - Per-rank modifiers are intentionally excluded for now.
    """

    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    max_level = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="idx_skill_name"),
            models.Index(fields=["max_level"], name="idx_skill_max_level"),
        ]

    def __str__(self):
        return f"{self.name} (Lv {self.max_level})"


# ==================================================
# Armor
# ==================================================
class Armor(models.Model):
    """
    Armor model (MHW Armor MVP).

    Design goals
    - Represent a single armor piece (not a set).
    - Store defense values and decoration slots.
    - Attach skills with levels via a through model.

    Notes about mhw-db
    - Armor includes defense values and a list of skills with levels.
    - MVP stores:
      * base/max/augmented defense
      * up to 3 decoration slots
      * skill + level pairs
    """

    external_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=200)
    armor_type = models.CharField(max_length=40)  # head, chest, gloves, waist, legs
    rarity = models.PositiveSmallIntegerField(default=1)

    defense_base = models.PositiveSmallIntegerField(default=0)
    defense_max = models.PositiveSmallIntegerField(default=0)
    defense_augmented = models.PositiveSmallIntegerField(default=0)

    # Decoration slots (rank/level, 0 = empty)
    slot_1 = models.PositiveSmallIntegerField(default=0)
    slot_2 = models.PositiveSmallIntegerField(default=0)
    slot_3 = models.PositiveSmallIntegerField(default=0)

    # Skills are linked via ArmorSkill to store level
    skills = models.ManyToManyField(
        Skill,
        through="ArmorSkill",
        related_name="armors",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["armor_type"], name="idx_armor_type"),
            models.Index(fields=["rarity"], name="idx_armor_rarity"),
            models.Index(fields=["defense_base"], name="idx_armor_defense_base"),
        ]

    def __str__(self):
        return f"{self.name} ({self.armor_type})"


class ArmorSkill(models.Model):
    """
    Through model connecting Armor and Skill with a level.

    Why this exists
    - Armor skills in MHW always have a level.
    - ManyToManyField alone cannot store extra attributes.

    Rules
    - One armor piece can grant a given skill only once.
    - level must be >= 1.
    """

    armor = models.ForeignKey(
        Armor,
        on_delete=models.CASCADE,
        related_name="armor_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="skill_armors",
    )

    level = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["armor", "skill"],
                name="uniq_armorskill_armor_skill",
            ),
            models.CheckConstraint(
                condition=Q(level__gte=1),
                name="chk_armorskill_level_gte_1",
            ),
        ]
        indexes = [
            models.Index(fields=["skill", "level"], name="idx_armorskill_skill_level"),
            models.Index(fields=["armor"], name="idx_armorskill_armor"),
        ]

    def __str__(self):
        return f"{self.armor.name} - {self.skill.name} (Lv {self.level})"
from django.db import models
from django.db.models import Q


class Monster(models.Model):
    """
    Monster model (core entity).

    Notes
    - external_id is the stable identifier from the external source (mhw-db).
    - We treat external_id as required and unique so re-imports can reliably "upsert".
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

    Notes
    - condition is optional because mhw-db sometimes omits it.
    - condition_key is used for stable uniqueness even when condition is NULL.
    - stars are constrained at the DB level to the valid domain (1–3).
    """

    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="weaknesses",
    )

    kind = models.CharField(max_length=40)
    name = models.CharField(max_length=60)
    stars = models.PositiveSmallIntegerField()

    condition = models.CharField(max_length=200, null=True, blank=True)

    # A normalized key for uniqueness. Import code should set this consistently.
    # Example: condition_key = (condition or "").strip().lower()
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


class Weapon(models.Model):
    """
    Weapon model (MHW Weapons MVP).

    Design goals
    - Store only the fields needed for v1.1 list/detail endpoints and simple filtering.
    - Keep the schema stable and easy to extend later (durability, slots, crafting, assets, etc.).
    - external_id is required + unique to support safe re-imports (upsert-like behavior).
    """

    # Stable ID from external data source (mhw-db)
    external_id = models.IntegerField(unique=True)

    # Weapon name (e.g., "Buster Sword 1")
    name = models.CharField(max_length=200)

    # Weapon type from mhw-db (e.g., "great-sword", "long-sword", "bow")
    weapon_type = models.CharField(max_length=50)

    # Rarity (usually 1-12)
    rarity = models.PositiveSmallIntegerField()

    # Attack values
    # - attack_display: the "display" attack shown in UI (varies by weapon type)
    # - attack_raw: the raw/base attack value from mhw-db
    attack_display = models.IntegerField(default=0)
    attack_raw = models.IntegerField(default=0)

    # Optional element (we keep MVP as "one element" even if some weapons have multiple)
    # Example: element="Fire", element_damage=240
    element = models.CharField(max_length=40, null=True, blank=True)
    element_damage = models.IntegerField(null=True, blank=True)

    # Optional combat attributes
    affinity = models.SmallIntegerField(default=0)  # can be negative
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


class Skill(models.Model):
    """
    Skill model (MHW Skills MVP).

    Design goals
    - Keep the schema minimal but useful for API list/detail and future build logic.
    - external_id is required + unique to support safe re-imports (upsert-like behavior).
    - Store the maximum level so frontend/build logic can reason about valid ranges.
    - Description can be long (skill text), so use TextField.

    Notes about mhw-db
    - Skills typically include:
      id, name, description, ranks (each rank has level, description, modifiers, etc.)
    - MVP stores:
      * max_level derived from ranks
      * description as the base skill description (plus ranks later if needed)
    """

    # Stable ID from external data source (mhw-db)
    external_id = models.IntegerField(unique=True)

    # Skill name (e.g., "Attack Boost")
    name = models.CharField(max_length=200)

    # High-level description (skill summary)
    description = models.TextField(blank=True, default="")

    # Max level derived from ranks (e.g., 7 for Attack Boost)
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
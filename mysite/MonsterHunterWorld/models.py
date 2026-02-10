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

    def __str__(self):
        return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars})"


# ==================================================
# Weapons
# ==================================================
class Weapon(models.Model):
    """
    Weapon model (MHW Weapons MVP).
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

    def __str__(self):
        return f"{self.name} ({self.weapon_type})"


# ==================================================
# Skills
# ==================================================
class Skill(models.Model):
    """
    Skill model (MHW Skills MVP).
    """

    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    max_level = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Lv {self.max_level})"


# ==================================================
# Armor
# ==================================================
class Armor(models.Model):
    """
    Armor model (MHW Armor MVP).
    """

    external_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=200)
    armor_type = models.CharField(max_length=40)
    rarity = models.PositiveSmallIntegerField(default=1)

    defense_base = models.PositiveSmallIntegerField(default=0)
    defense_max = models.PositiveSmallIntegerField(default=0)
    defense_augmented = models.PositiveSmallIntegerField(default=0)

    slot_1 = models.PositiveSmallIntegerField(default=0)
    slot_2 = models.PositiveSmallIntegerField(default=0)
    slot_3 = models.PositiveSmallIntegerField(default=0)

    skills = models.ManyToManyField(
        Skill,
        through="ArmorSkill",
        related_name="armors",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.armor_type})"


class ArmorSkill(models.Model):
    """
    Join table between Armor and Skill with a level.
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
        ]

    def __str__(self):
        return f"{self.armor.name} - {self.skill.name} (Lv {self.level})"


# ==================================================
# Charms
# ==================================================
class Charm(models.Model):
    """
    Charm model (MHW Charms MVP).

    Design notes
    - external_id comes from mhw-db and is treated as stable.
    - We keep CharmSkill as a separate join table so a charm can grant multiple skills.
    """

    external_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    rarity = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CharmSkill(models.Model):
    """
    Join table between Charm and Skill with a level.
    """

    charm = models.ForeignKey(
        Charm,
        on_delete=models.CASCADE,
        related_name="charm_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="skill_charms",
    )

    level = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["charm", "skill"],
                name="uniq_charmskill_charm_skill",
            ),
        ]

    def __str__(self):
        return f"{self.charm.name} - {self.skill.name} (Lv {self.level})"


# ==================================================
# Builds
# ==================================================
class Build(models.Model):
    """
    Build model (MHW Builds MVP).

    Represents a saved loadout:
    - One weapon (optional)
    - Exactly one armor per slot (via BuildArmorPiece)
    - One charm (optional)
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    weapon = models.ForeignKey(
        Weapon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="builds",
    )

    charm = models.ForeignKey(
        Charm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="builds",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BuildArmorPiece(models.Model):
    """
    Join table between Build and Armor for a specific slot.

    Enforces:
    - One armor per slot per build
    """

    SLOT_HEAD = "head"
    SLOT_CHEST = "chest"
    SLOT_GLOVES = "gloves"
    SLOT_WAIST = "waist"
    SLOT_LEGS = "legs"

    SLOT_CHOICES = [
        (SLOT_HEAD, "Head"),
        (SLOT_CHEST, "Chest"),
        (SLOT_GLOVES, "Gloves"),
        (SLOT_WAIST, "Waist"),
        (SLOT_LEGS, "Legs"),
    ]

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name="armor_pieces",
    )

    slot = models.CharField(
        max_length=20,
        choices=SLOT_CHOICES,
    )

    armor = models.ForeignKey(
        Armor,
        on_delete=models.CASCADE,
        related_name="build_usages",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["build", "slot"],
                name="uniq_buildarmorpiece_build_slot",
            ),
        ]

    def __str__(self):
        return f"{self.build.name} - {self.slot}: {self.armor.name}"
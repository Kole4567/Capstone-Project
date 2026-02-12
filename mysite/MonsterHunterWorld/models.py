from django.db import models
from django.db.models import Q


# ==================================================
# Monsters
# ==================================================
class Monster(models.Model):
    """
    Monster model (core entity).

    Design notes:
    - Represents a large monster in Monster Hunter World.
    - external_id comes from mhw-db and is treated as stable.

    Constraints:
    - external_id must be unique to allow safe re-imports (upsert behavior).

    Import mapping notes (mhw_monsters.json):
    - primary_element  <- monster["elements"][0] (first element only, if present)
    - primary_ailment  <- monster["ailments"][0]["name"] (first ailment only, if present)
    """

    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=120)
    monster_type = models.CharField(max_length=80)
    is_elder_dragon = models.BooleanField(default=False)

    # ==================================================
    # Monster Offensive Identity (MVP)
    # ==================================================
    # "elements" is a list of strings like: ["fire"], ["water"], ...
    # "ailments" is a list of dicts; we store the first ailment name only.
    # These fields are intended for build recommendation logic (defensive planning).
    primary_element = models.CharField(max_length=40, null=True, blank=True)
    primary_ailment = models.CharField(max_length=80, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MonsterWeakness(models.Model):
    """
    Represents a monster's elemental or status weakness.
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


class MonsterResistance(models.Model):
    """
    Represents a monster's elemental resistance (NOT weakness).

    Source (mhw_monsters.json):
      "resistances": [
        { "element": "water", "condition": null },
        { "element": "fire", "condition": "covered in mud" }
      ]

    Design notes:
    - Resistances can be conditional, so we store condition + a slugified condition_key.
    - Uniqueness should match (monster, element, condition_key).
    """

    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="resistances",
    )

    # mhw-db uses lowercase strings like: "fire", "water", "thunder", "ice", "dragon"
    element = models.CharField(max_length=40)

    condition = models.CharField(max_length=200, null=True, blank=True)
    condition_key = models.CharField(max_length=200, default="", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["monster", "element", "condition_key"],
                name="uniq_monsterresistance_monster_element_conditionkey",
            ),
        ]

    def __str__(self):
        cond = f" ({self.condition})" if self.condition else ""
        return f"{self.monster.name} - res:{self.element}{cond}"


# ==================================================
# Weapons
# ==================================================
class Weapon(models.Model):
    """
    Weapon model (MHW Weapons MVP).

    Import mapping notes (mhw_weapons.json):
    - external_id  <- weapon["id"]
    - weapon_type  <- weapon["type"]
    - attack_*     <- weapon["attack"]["display"], weapon["attack"]["raw"]
    - element      <- weapon["elements"][0]["type"] (first element only, if present)
    - element_damage <- weapon["elements"][0]["damage"] (first element only, if present)
    - affinity     <- weapon["attributes"].get("affinity", 0)
    - elderseal    <- weapon.get("elderseal")
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

    IMPORTANT (Build Stats roadmap):
    - To compute MHW-like "total resistances" and "total defense" from equipped armor,
      we must store per-piece elemental resistances on Armor.
    - mhw-db armor payload includes: resistances { fire, water, thunder, ice, dragon }
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

    # ==================================================
    # Elemental Resistances (MHW Armor piece stats)
    # ==================================================
    # These are per-armor-piece values and should be populated from mhw-db armor.resistances.
    # We keep them as simple integers to allow easy summation in BuildStatsView.
    res_fire = models.SmallIntegerField(default=0)
    res_water = models.SmallIntegerField(default=0)
    res_thunder = models.SmallIntegerField(default=0)
    res_ice = models.SmallIntegerField(default=0)
    res_dragon = models.SmallIntegerField(default=0)

    # ==================================================
    # Armor Set / Set Bonus (Domain C - Minimal fields)
    # ==================================================
    # mhw-db: armorSet.id / armorSet.name / armorSet.rank / armorSet.bonus
    armor_set_external_id = models.IntegerField(null=True, blank=True, db_index=True)
    armor_set_name = models.CharField(
        max_length=120, null=True, blank=True, db_index=True
    )
    armor_set_rank = models.CharField(max_length=40, null=True, blank=True)

    # mhw-db armorSet.bonus -> set bonus external id (can be null)
    armor_set_bonus_external_id = models.IntegerField(
        null=True, blank=True, db_index=True
    )

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
# Set Bonuses (Domain C - Skill Granting)
# ==================================================
class SetBonus(models.Model):
    """
    Represents a set bonus entity.

    Source:
    - mhw-db armor sets endpoint: GET https://mhw-db.com/armor/sets
    - armorSet.bonus.id and armorSet.bonus.name
    """

    external_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (#{self.external_id})"


class SetBonusRank(models.Model):
    """
    Threshold rank within a SetBonus.

    Example:
    - pieces=2 -> grants skill X level 1
    - pieces=4 -> grants another skill, etc.

    Notes:
    - We store the granted skill as a FK to Skill (based on skill external_id).
    """

    set_bonus = models.ForeignKey(
        SetBonus,
        on_delete=models.CASCADE,
        related_name="ranks",
    )

    pieces = models.PositiveSmallIntegerField(default=2)

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="set_bonus_ranks",
    )

    level = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["set_bonus", "pieces", "skill"],
                name="uniq_setbonusrank_setbonus_pieces_skill",
            ),
        ]

    def __str__(self):
        return f"{self.set_bonus.name} - {self.pieces}p: {self.skill.name} Lv{self.level}"


# ==================================================
# Charms
# ==================================================
class Charm(models.Model):
    """
    Charm model (MHW Charms MVP).

    Design notes:
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
# Decorations
# ==================================================
class Decoration(models.Model):
    """
    Decoration model (MHW Decorations MVP).

    Design notes:
    - mhw-db provides decorations with skills and rarity.
    - external_id is the stable mhw-db id (unique).
    - DecorationSkill is a join table to allow multiple skills per decoration.
    """

    external_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=200)
    rarity = models.PositiveSmallIntegerField(default=1)

    skills = models.ManyToManyField(
        Skill,
        through="DecorationSkill",
        related_name="decorations",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (R{self.rarity})"


class DecorationSkill(models.Model):
    """
    Join table between Decoration and Skill with a level.
    """

    decoration = models.ForeignKey(
        Decoration,
        on_delete=models.CASCADE,
        related_name="decoration_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="skill_decorations",
    )

    level = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["decoration", "skill"],
                name="uniq_decorationskill_decoration_skill",
            ),
        ]

    def __str__(self):
        return f"{self.decoration.name} - {self.skill.name} (Lv {self.level})"


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
    - Decorations are stored via BuildDecoration with a socket location
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


class BuildDecoration(models.Model):
    """
    Join table between Build and Decoration for a specific socket location.

    Stores:
    - which slot (head/chest/gloves/waist/legs/weapon)
    - which socket index (1..3)
    - which decoration is inserted

    Notes:
    - Replace semantics are recommended at the serializer level:
      delete all build decorations and recreate from input.
    """

    SLOT_HEAD = "head"
    SLOT_CHEST = "chest"
    SLOT_GLOVES = "gloves"
    SLOT_WAIST = "waist"
    SLOT_LEGS = "legs"
    SLOT_WEAPON = "weapon"

    SLOT_CHOICES = [
        (SLOT_HEAD, "Head"),
        (SLOT_CHEST, "Chest"),
        (SLOT_GLOVES, "Gloves"),
        (SLOT_WAIST, "Waist"),
        (SLOT_LEGS, "Legs"),
        (SLOT_WEAPON, "Weapon"),
    ]

    build = models.ForeignKey(
        Build,
        on_delete=models.CASCADE,
        related_name="decorations",
    )

    slot = models.CharField(
        max_length=20,
        choices=SLOT_CHOICES,
    )

    socket_index = models.PositiveSmallIntegerField(default=1)

    decoration = models.ForeignKey(
        Decoration,
        on_delete=models.CASCADE,
        related_name="build_usages",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["build", "slot", "socket_index"],
                name="uniq_builddecoration_build_slot_socketindex",
            ),
            models.CheckConstraint(
                condition=Q(socket_index__gte=1) & Q(socket_index__lte=3),
                name="chk_builddecoration_socket_index_1_3",
            ),
        ]

    def __str__(self):
        return f"{self.build.name} - {self.slot}[{self.socket_index}]: {self.decoration.name}"
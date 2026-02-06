from django.db import models


class Monster(models.Model):
    """
    Monster model (core entity).

    Notes
    - external_id is the stable identifier from the external source (mhw-db).
    - We treat external_id as required and unique so re-imports can reliably "upsert".
    - If external_id were nullable, multiple NULL rows could exist depending on DB behavior,
      which can break the assumption that external_id uniquely identifies a monster.
    """

    # Stable ID from external data source (e.g., mhw-db)
    external_id = models.IntegerField(unique=True)

    # Monster name (e.g., Rathalos)
    name = models.CharField(max_length=120)

    # Monster classification (e.g., Flying Wyvern, Elder Dragon)
    monster_type = models.CharField(max_length=80)

    # Whether the monster is an Elder Dragon
    is_elder_dragon = models.BooleanField(default=False)

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MonsterWeakness(models.Model):
    """
    Represents a monster’s elemental or status weakness.

    Design decisions
    - We keep condition optional because some sources omit it.
    - We enforce uniqueness at (monster, kind, name) to prevent duplicate rows
      while avoiding "condition-string mismatch" duplicates (extra spaces, wording variants).
      Since the import strategy fully replaces weaknesses per monster, this is both safe and stable.
    """

    # Reference to the related monster
    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="weaknesses",
    )

    # Weakness category (e.g. "element", "ailment")
    kind = models.CharField(max_length=40)

    # Weakness name (e.g. Fire, Water, Poison)
    name = models.CharField(max_length=60)

    # Effectiveness level (usually represented as stars, e.g. 1–3)
    # PositiveSmallIntegerField prevents negative values.
    stars = models.PositiveSmallIntegerField()

    # Optional condition describing when the weakness applies
    condition = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        # Prevent duplicate weaknesses per monster (ignore condition differences)
        constraints = [
            models.UniqueConstraint(
                fields=["monster", "kind", "name"],
                name="uniq_monsterweakness_monster_kind_name",
            )
        ]
        # Helpful indexes for filtering and joins
        indexes = [
            models.Index(fields=["monster", "kind"], name="idx_weak_monster_kind"),
            models.Index(fields=["kind", "name"], name="idx_weak_kind_name"),
        ]

    def __str__(self):
        return f"{self.monster.name} - {self.kind}:{self.name} ({self.stars})"